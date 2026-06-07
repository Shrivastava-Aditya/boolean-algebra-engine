"""
nl/nl.py — Natural Language layer for the boolean algebra engine.

Pipeline:
  plain English → LLM (parse) → boolean expression
               → core engine  → truth table + minimal form
               → LLM (explain) → plain English result

Supports any LLM via the Provider protocol. Built-in providers:
  AnthropicProvider  — Claude (default)
  OpenAIProvider     — GPT-4o, GPT-4, etc.
  OllamaProvider     — local models via Ollama (llama3, mistral, etc.)
  OpenAICompatProvider — any OpenAI-compatible endpoint (Groq, Together, etc.)

Public API:
  ask(sentence, provider) → NLResult
  check_rules(rules, provider) → dict

Quick start:
  from boolean_algebra_engine.nl.nl import ask, AnthropicProvider
  result = ask("lights on when door open or motion detected but not both",
               provider=AnthropicProvider())   # uses ANTHROPIC_API_KEY env var
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from boolean_algebra_engine.core.evaluator import evaluate
from boolean_algebra_engine.core.synthesizer import synthesize
from boolean_algebra_engine.core.parser import validate


# ---------------------------------------------------------------------------
# Prompts — shared across all providers
# ---------------------------------------------------------------------------

_PARSE_SYSTEM = """\
You are a boolean algebra parser. Your job is to convert a natural language
description of a logical rule or condition into a boolean expression.

Rules:
- Variables must be single uppercase letters: A, B, C, D, ...
- Operators: ! (NOT), . (AND), ^ (XOR), + (OR)
- Parentheses for grouping
- Return ONLY valid JSON, no markdown, no explanation

Output format:
{
  "expression": "<boolean expression>",
  "variables": {
    "A": "<what A represents>",
    "B": "<what B represents>",
    ...
  },
  "assumptions": "<any assumptions you made parsing ambiguous language>"
}

Examples:
  Input: "lights on when door open or motion detected but not both"
  Output: {"expression": "D^M", "variables": {"D": "door is open", "M": "motion detected"}, "assumptions": "interpreted 'but not both' as XOR"}

  Input: "access granted if user is admin and authenticated, or if read-only and authenticated"
  Output: {"expression": "A.(B+C)", "variables": {"A": "user is authenticated", "B": "user is admin", "C": "request is read-only"}, "assumptions": "factored out authentication as common condition"}
"""

_EXPLAIN_SYSTEM = """\
You are a boolean logic explainer. You are given the result of evaluating a
boolean expression and must explain it in plain English clearly and concisely.

Be direct. Lead with the most important finding (contradiction, tautology, or
key insight). Then explain what the minimal form means. Keep it under 150 words.
"""


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------

class Provider(ABC):
    """
    Abstract base for LLM providers. Implement complete() to add a new model.

    The NL layer calls complete() twice per request — once to parse the sentence
    into a boolean expression, once to explain the result. Both are plain
    text-in, text-out with a system prompt and a user message.
    """

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        """
        Call the LLM and return the response text.

        Args:
            system: System prompt.
            user: User message.
            max_tokens: Maximum tokens in the response.

        Returns:
            Response text as a plain string.
        """


# ---------------------------------------------------------------------------
# Built-in providers
# ---------------------------------------------------------------------------

class AnthropicProvider(Provider):
    """
    Claude via Anthropic SDK.

    Args:
        api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        model: Model ID. Defaults to claude-sonnet-4-6.

    Install: pip install anthropic
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
    ):
        try:
            import anthropic as _anthropic
        except ImportError:
            raise ImportError("pip install anthropic")
        self._client = _anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()


class OpenAIProvider(Provider):
    """
    GPT-4o, GPT-4, GPT-3.5, or any OpenAI model.

    Args:
        api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
        model: Model ID. Defaults to gpt-4o.

    Install: pip install openai
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai")
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content.strip()


class OllamaProvider(Provider):
    """
    Local models via Ollama (llama3, mistral, phi3, gemma, etc.).
    Ollama must be running locally: https://ollama.com

    Args:
        model: Ollama model name. Defaults to llama3.
        base_url: Ollama API base URL. Defaults to http://localhost:11434.

    Install: pip install ollama  (or use OllamaProvider via openai SDK)
    No API key needed — runs fully locally.
    """

    def __init__(
        self,
        model: str = "deepseek-r1:7b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        import urllib.request
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        return data["message"]["content"].strip()


class OpenAICompatProvider(Provider):
    """
    Any OpenAI-compatible endpoint: Groq, Together AI, Fireworks, Mistral API,
    LM Studio, vLLM, etc.

    Args:
        api_key: API key for the provider.
        base_url: Base URL of the OpenAI-compatible API.
        model: Model ID as accepted by the provider.

    Install: pip install openai

    Examples:
        # Groq
        OpenAICompatProvider(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
            model="llama3-8b-8192",
        )
        # Together AI
        OpenAICompatProvider(
            api_key=os.environ["TOGETHER_API_KEY"],
            base_url="https://api.together.xyz/v1",
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        )
        # Local LM Studio
        OpenAICompatProvider(
            api_key="lm-studio",
            base_url="http://localhost:1234/v1",
            model="local-model",
        )
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai")
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 512) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content.strip()


def _ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Return True if Ollama is reachable."""
    import urllib.request
    try:
        urllib.request.urlopen(f"{base_url}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _default_provider() -> Provider:
    """Auto-detect: Ollama first, then Anthropic, then clear error."""
    if _ollama_running():
        return OllamaProvider()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicProvider()
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIProvider()
    raise ValueError(
        "No provider available.\n"
        "Easiest option — run Ollama locally (free, no API key):\n"
        "  1. Install: https://ollama.com\n"
        "  2. Pull model: ollama pull deepseek-r1:7b\n"
        "  3. Re-run your command\n\n"
        "Or set an API key:\n"
        "  export ANTHROPIC_API_KEY=...\n"
        "  export OPENAI_API_KEY=..."
    )


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class NLResult:
    input_sentence: str
    expression: str
    variables: dict[str, str]
    minimal: str
    satisfiable: bool
    tautology: bool
    contradiction: bool
    minterms: list[int]
    maxterms: list[int]
    explanation: str
    rows: list[dict]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ask(sentence: str, provider: Provider | None = None) -> NLResult:
    """
    Convert a plain English logical statement into a verified boolean result.

    Args:
        sentence: Plain English description of a logical rule or condition.
        provider: LLM provider to use. Defaults to AnthropicProvider() if
                  ANTHROPIC_API_KEY is set, otherwise raises ValueError.

    Returns:
        NLResult with expression, truth table, minimal form, and explanation.

    Raises:
        ValueError: If the LLM cannot parse the sentence into a valid expression.

    Examples:
        from boolean_algebra_engine.nl.nl import ask, AnthropicProvider, OpenAIProvider, OllamaProvider

        # Claude
        result = ask("door opens when key valid and not locked",
                     provider=AnthropicProvider())

        # GPT-4o
        result = ask("...", provider=OpenAIProvider())

        # Local llama3 via Ollama (no API key, free)
        result = ask("...", provider=OllamaProvider(model="llama3"))

        # Groq (fast, cheap)
        result = ask("...", provider=OpenAICompatProvider(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
            model="llama3-8b-8192",
        ))
    """
    llm = provider or _default_provider()

    # Step 1: NL → expression
    raw = llm.complete(_PARSE_SYSTEM, sentence, max_tokens=512)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned non-JSON: {raw}")

    expression = parsed.get("expression", "")
    variables = parsed.get("variables", {})
    assumptions = parsed.get("assumptions", "")

    error = validate(expression)
    if error:
        raise ValueError(
            f"LLM produced invalid expression '{expression}': {error}\n"
            f"Assumptions: {assumptions}"
        )

    # Step 2: evaluate + synthesize
    table, _ = evaluate(expression)
    minimal, _ = synthesize(table)

    # Step 3: result → explanation
    explain_prompt = (
        f"Sentence: {sentence}\n"
        f"Parsed as: {expression}\n"
        f"Variables: {json.dumps(variables)}\n"
        f"Minimal form: {minimal}\n"
        f"Satisfiable: {table.satisfiable}\n"
        f"Tautology: {table.tautology}\n"
        f"Contradiction: {not table.satisfiable}\n"
        f"Minterms (rows where true): {table.minterms}\n"
        f"Total rows: {len(table.rows)}\n"
        f"Assumptions made: {assumptions}"
    )
    explanation = llm.complete(_EXPLAIN_SYSTEM, explain_prompt, max_tokens=300)

    return NLResult(
        input_sentence=sentence,
        expression=expression,
        variables=variables,
        minimal=minimal,
        satisfiable=table.satisfiable,
        tautology=table.tautology,
        contradiction=not table.satisfiable,
        minterms=table.minterms,
        maxterms=table.maxterms,
        explanation=explanation,
        rows=[{**row.inputs, "output": row.output} for row in table.rows],
    )


def check_rules(rules: list[str], provider: Provider | None = None) -> dict:
    """
    Parse and verify a list of plain English rules for contradictions,
    tautologies, and pairwise conflicts.

    Args:
        rules: List of plain English rule descriptions.
        provider: LLM provider to use. Defaults to AnthropicProvider().

    Returns:
        Dictionary with per-rule analysis and pairwise conflict/equivalence checks.
    """
    from boolean_algebra_engine.mcp.server import check_prompt_logic as _check

    llm = provider or _default_provider()
    expressions = []
    variable_maps = []
    errors = []

    for rule in rules:
        try:
            raw = llm.complete(_PARSE_SYSTEM, rule, max_tokens=512)
            parsed = json.loads(raw)
            expr = parsed.get("expression", "")
            error = validate(expr)
            if error:
                errors.append({"rule": rule, "error": error})
            else:
                expressions.append(expr)
                variable_maps.append({
                    "rule": rule,
                    "expression": expr,
                    "variables": parsed.get("variables", {}),
                })
        except Exception as e:
            errors.append({"rule": rule, "error": str(e)})

    engine_result = _check(expressions) if expressions else {
        "rules": [], "pairwise": [], "summary": {}
    }

    for i, item in enumerate(engine_result.get("rules", [])):
        if i < len(variable_maps):
            item["original_rule"] = variable_maps[i]["rule"]
            item["variables"] = variable_maps[i]["variables"]

    engine_result["parse_errors"] = errors
    return engine_result
