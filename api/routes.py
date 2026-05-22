"""
api/routes.py — REST API wrapping the boolean algebra engine.

Endpoints:
  POST /evaluate           expression → truth table
  POST /simplify           expression → minimal form
  POST /equivalent         two expressions → same truth table?
  POST /satisfiable        expression → any row outputs 1?
  POST /check-rules        list of expressions → contradictions, conflicts
  POST /nl/ask             plain English → verified boolean result
  POST /nl/check-rules     list of plain English rules → analysis
  GET  /health             liveness check

Run:
  uvicorn api.routes:app --host 0.0.0.0 --port 8080 --reload

Environment variables:
  ANTHROPIC_API_KEY   — for nl/* endpoints with anthropic provider
  OPENAI_API_KEY      — for nl/* endpoints with openai provider
  REDIS_URL           — optional, enables caching (default: redis://localhost:6379)
  API_KEY             — optional, enables auth (Pro/Team tiers)
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.evaluator import evaluate as _evaluate
from core.synthesizer import synthesize as _synthesize
from core.parser import validate, infix_to_prefix
from core.evaluator import _evaluate_prefix

app = FastAPI(
    title="Boolean Algebra Engine",
    description="Deterministic boolean logic verification API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Redis cache — optional, degrades gracefully if not available
# ---------------------------------------------------------------------------

_redis = None

def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        _redis = r
    except Exception:
        _redis = None
    return _redis


def _cache_get(key: str) -> dict | None:
    r = _get_redis()
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def _cache_set(key: str, value: dict, ttl: int = 86400):
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass


def _cache_key(*parts) -> str:
    raw = ":".join(str(p) for p in parts)
    return "bae:" + hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Auth — optional, enabled when API_KEY env var is set
# ---------------------------------------------------------------------------

def _check_auth(request: Request):
    required = os.environ.get("API_KEY")
    if not required:
        return
    provided = request.headers.get("X-API-Key")
    if provided != required:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class EvaluateRequest(BaseModel):
    expression: str

class SimplifyRequest(BaseModel):
    expression: str

class EquivalentRequest(BaseModel):
    expression1: str
    expression2: str

class SatisfiableRequest(BaseModel):
    expression: str

class CheckRulesRequest(BaseModel):
    rules: list[str]

class NLAskRequest(BaseModel):
    sentence: str
    provider: str = "anthropic"
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None

class NLCheckRulesRequest(BaseModel):
    rules: list[str]
    provider: str = "anthropic"
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper — build provider from request fields
# ---------------------------------------------------------------------------

def _build_provider(provider: str, api_key: Optional[str], model: Optional[str], base_url: Optional[str]):
    from nl.nl import AnthropicProvider, OpenAIProvider, OllamaProvider, OpenAICompatProvider
    if provider == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model or "claude-sonnet-4-6")
    if provider == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    if provider == "ollama":
        return OllamaProvider(model=model or "llama3", base_url=base_url or "http://localhost:11434")
    if provider == "compat":
        if not base_url or not model:
            raise HTTPException(status_code=400, detail="base_url and model required for compat provider")
        return OpenAICompatProvider(api_key=api_key or "", base_url=base_url, model=model)
    raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'. Choose: anthropic, openai, ollama, compat")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    redis_ok = _get_redis() is not None
    return {"status": "ok", "version": "0.1.0", "redis": redis_ok}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest, request: Request, response: Response):
    _check_auth(request)

    cache_key = _cache_key("evaluate", req.expression)
    cached = _cache_get(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached

    error = validate(req.expression)
    if error:
        raise HTTPException(status_code=422, detail={"error": "invalid_expression", "message": error, "expression": req.expression})

    t0 = time.perf_counter()
    table, metrics = _evaluate(req.expression)
    elapsed = round((time.perf_counter() - t0) * 1000, 4)

    result = {
        "expression": table.expression,
        "variables": table.variables,
        "rows": [{**row.inputs, "output": row.output} for row in table.rows],
        "satisfiable": table.satisfiable,
        "tautology": table.tautology,
        "minterms": table.minterms,
        "maxterms": table.maxterms,
        "eval_time_ms": elapsed,
        "rows_evaluated": metrics.rows_evaluated,
    }

    _cache_set(cache_key, result, ttl=86400)
    response.headers["X-Cache"] = "MISS"
    response.headers["X-Eval-Time-Ms"] = str(elapsed)
    return result


@app.post("/simplify")
def simplify(req: SimplifyRequest, request: Request, response: Response):
    _check_auth(request)

    cache_key = _cache_key("simplify", req.expression)
    cached = _cache_get(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached

    error = validate(req.expression)
    if error:
        raise HTTPException(status_code=422, detail={"error": "invalid_expression", "message": error, "expression": req.expression})

    table, _ = _evaluate(req.expression)
    minimal, metrics = _synthesize(table)

    result = {
        "original": req.expression,
        "minimal": minimal,
        "changed": minimal != req.expression,
        "prime_implicant_count": metrics.prime_implicant_count,
        "synth_time_ms": metrics.synth_time_ms,
    }

    _cache_set(cache_key, result, ttl=86400)
    response.headers["X-Cache"] = "MISS"
    return result


@app.post("/equivalent")
def equivalent(req: EquivalentRequest, request: Request, response: Response):
    _check_auth(request)

    cache_key = _cache_key("equivalent", req.expression1, req.expression2)
    cached = _cache_get(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached

    for expr in [req.expression1, req.expression2]:
        error = validate(expr)
        if error:
            raise HTTPException(status_code=422, detail={"error": "invalid_expression", "message": error, "expression": expr})

    from core.parser import get_variables
    vars1 = set(get_variables(req.expression1))
    vars2 = set(get_variables(req.expression2))
    all_vars = sorted(vars1 | vars2)
    n = len(all_vars)

    p1 = infix_to_prefix(req.expression1)
    p2 = infix_to_prefix(req.expression2)

    differing = []
    for i in range(2 ** n):
        values = {var: (i >> (n - 1 - j)) & 1 for j, var in enumerate(all_vars)}
        v1 = {k: v for k, v in values.items() if k in vars1}
        v2 = {k: v for k, v in values.items() if k in vars2}
        out1 = _evaluate_prefix(p1, v1)
        out2 = _evaluate_prefix(p2, v2)
        if out1 != out2:
            differing.append({**values, req.expression1: out1, req.expression2: out2})

    result: dict = {
        "equivalent": len(differing) == 0,
        "expression1": req.expression1,
        "expression2": req.expression2,
    }
    if differing:
        result["differing_rows"] = differing[:10]
        result["total_differing"] = len(differing)

    _cache_set(cache_key, result, ttl=86400)
    response.headers["X-Cache"] = "MISS"
    return result


@app.post("/satisfiable")
def satisfiable(req: SatisfiableRequest, request: Request, response: Response):
    _check_auth(request)

    cache_key = _cache_key("satisfiable", req.expression)
    cached = _cache_get(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached

    error = validate(req.expression)
    if error:
        raise HTTPException(status_code=422, detail={"error": "invalid_expression", "message": error, "expression": req.expression})

    table, _ = _evaluate(req.expression)
    result: dict = {"satisfiable": table.satisfiable, "expression": req.expression}
    if table.satisfiable:
        first = table.rows[table.minterms[0]]
        result["example"] = {**first.inputs, "output": first.output}

    _cache_set(cache_key, result, ttl=86400)
    response.headers["X-Cache"] = "MISS"
    return result


@app.post("/check-rules")
def check_rules(req: CheckRulesRequest, request: Request, response: Response):
    _check_auth(request)

    cache_key = _cache_key("check-rules", *sorted(req.rules))
    cached = _cache_get(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached

    from mcp_server.server import check_prompt_logic
    result = check_prompt_logic(req.rules)

    _cache_set(cache_key, result, ttl=3600)
    response.headers["X-Cache"] = "MISS"
    return result


@app.post("/nl/ask")
def nl_ask(req: NLAskRequest, request: Request, response: Response):
    _check_auth(request)

    cache_key = _cache_key("nl-ask", req.sentence, req.provider, req.model or "")
    cached = _cache_get(cache_key)
    if cached:
        response.headers["X-Cache"] = "HIT"
        return cached

    try:
        from nl.nl import ask
        prov = _build_provider(req.provider, req.api_key, req.model, req.base_url)
        result = ask(req.sentence, provider=prov)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"error": "parse_failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "internal", "message": str(e)})

    data = {
        "input": result.input_sentence,
        "expression": result.expression,
        "variables": result.variables,
        "minimal": result.minimal,
        "satisfiable": result.satisfiable,
        "tautology": result.tautology,
        "contradiction": result.contradiction,
        "minterms": result.minterms,
        "maxterms": result.maxterms,
        "explanation": result.explanation,
        "rows": result.rows,
    }

    _cache_set(cache_key, data, ttl=3600)
    response.headers["X-Cache"] = "MISS"
    return data


@app.post("/nl/check-rules")
def nl_check_rules(req: NLCheckRulesRequest, request: Request, response: Response):
    _check_auth(request)

    try:
        from nl.nl import check_rules as _check_rules
        prov = _build_provider(req.provider, req.api_key, req.model, req.base_url)
        result = _check_rules(req.rules, provider=prov)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={"error": "parse_failed", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "internal", "message": str(e)})

    response.headers["X-Cache"] = "MISS"
    return result
