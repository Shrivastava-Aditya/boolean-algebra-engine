"""
boolean_algebra_engine/mcp/server.py — MCP server wrapping the boolean algebra engine.

Exposes five tools Claude can call mid-conversation:

  evaluate           expression → full truth table + metrics
  simplify           expression → minimal equivalent expression
  equivalent         expr1, expr2 → bool (same truth table?)
  satisfiable        expression → bool (any row outputs 1?)
  check_prompt_logic list of rules → contradiction/conflict audit

Run with:
    python3 -m boolean_algebra_engine.mcp.server
or via the MCP CLI:
    mcp dev boolean_algebra_engine/mcp/server.py
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from boolean_algebra_engine.core.evaluator import evaluate as _evaluate
from boolean_algebra_engine.core.synthesizer import synthesize as _synthesize

mcp = FastMCP(
    "boolean-algebra-engine",
    instructions=(
        "Tools for evaluating boolean algebra expressions. "
        "Use these to verify logic exactly — do not predict boolean results yourself. "
        "Variables must be uppercase letters A-Z. "
        "Operators: ! (NOT), . (AND), ^ (XOR), + (OR). "
        "Parentheses override precedence."
    ),
)


@mcp.tool()
def evaluate(expression: str) -> dict:
    """
    Evaluate a boolean expression and return its full truth table.

    Args:
        expression: Boolean expression using variables A-Z and operators ! . ^ +
                    Example: "A.(B+C)", "!(A.B)", "A^B"

    Returns:
        Dictionary with keys: expression, variables, rows (list of input/output dicts),
        satisfiable, tautology, minterms, maxterms, eval_time_ms, rows_evaluated.
    """
    table, metrics = _evaluate(expression)
    return {
        "expression": table.expression,
        "variables": table.variables,
        "rows": [{**row.inputs, "output": row.output} for row in table.rows],
        "satisfiable": table.satisfiable,
        "tautology": table.tautology,
        "minterms": table.minterms,
        "maxterms": table.maxterms,
        "eval_time_ms": metrics.eval_time_ms,
        "rows_evaluated": metrics.rows_evaluated,
    }


@mcp.tool()
def simplify(expression: str) -> dict:
    """
    Simplify a boolean expression to its minimal sum-of-products form.

    Useful for finding redundant conditions, dead branches, or the canonical
    form of a complex expression.

    Args:
        expression: Boolean expression using variables A-Z and operators ! . ^ +
                    Example: "A.B+A.!B" simplifies to "A"

    Returns:
        Dictionary with keys: original, minimal, changed (bool),
        prime_implicant_count, synth_time_ms.
    """
    table, _ = _evaluate(expression)
    minimal, metrics = _synthesize(table)
    return {
        "original": expression,
        "minimal": minimal,
        "changed": minimal != expression,
        "prime_implicant_count": metrics.prime_implicant_count,
        "synth_time_ms": metrics.synth_time_ms,
    }


@mcp.tool()
def equivalent(expression1: str, expression2: str) -> dict:
    """
    Check whether two boolean expressions are logically equivalent.

    Two expressions are equivalent if they produce identical output columns
    for all possible input combinations.

    Args:
        expression1: First boolean expression.
        expression2: Second boolean expression.

    Returns:
        Dictionary with keys: equivalent (bool), expression1, expression2,
        and on mismatch: differing_rows (list of input combos where they differ).
    """
    t1, _ = _evaluate(expression1)
    t2, _ = _evaluate(expression2)

    vars1 = set(t1.variables)
    vars2 = set(t2.variables)
    all_vars = sorted(vars1 | vars2)

    # Re-evaluate both over the union variable set for fair comparison
    from boolean_algebra_engine.core.parser import get_variables
    combined_expr1 = expression1
    combined_expr2 = expression2

    # Evaluate over shared variable space
    n = len(all_vars)
    differing = []
    for i in range(2 ** n):
        values = {var: (i >> (n - 1 - j)) & 1 for j, var in enumerate(all_vars)}
        # Filter to each expression's variables
        from boolean_algebra_engine.core.evaluator import _evaluate_prefix
        from boolean_algebra_engine.core.parser import infix_to_prefix
        p1 = infix_to_prefix(expression1)
        p2 = infix_to_prefix(expression2)
        v1 = {k: v for k, v in values.items() if k in vars1}
        v2 = {k: v for k, v in values.items() if k in vars2}
        out1 = _evaluate_prefix(p1, v1)
        out2 = _evaluate_prefix(p2, v2)
        if out1 != out2:
            differing.append({**values, expression1: out1, expression2: out2})

    result: dict = {
        "equivalent": len(differing) == 0,
        "expression1": expression1,
        "expression2": expression2,
    }
    if differing:
        result["differing_rows"] = differing[:10]  # cap at 10 for readability
        result["total_differing"] = len(differing)
    return result


@mcp.tool()
def satisfiable(expression: str) -> dict:
    """
    Check whether a boolean expression is satisfiable.

    A satisfiable expression has at least one input combination that outputs 1.
    An unsatisfiable expression is a contradiction (always 0).

    Args:
        expression: Boolean expression. Example: "A.!A" is unsatisfiable.

    Returns:
        Dictionary with keys: satisfiable (bool), expression,
        and if satisfiable: example (first input combo that satisfies it).
    """
    table, _ = _evaluate(expression)
    result: dict = {
        "satisfiable": table.satisfiable,
        "expression": expression,
    }
    if table.satisfiable:
        first = table.rows[table.minterms[0]]
        result["example"] = {**first.inputs, "output": first.output}
    return result


@mcp.tool()
def check_prompt_logic(rules: list[str]) -> dict:
    """
    Check a set of boolean rules (e.g. from a system prompt) for contradictions,
    tautologies, and pairwise equivalences.

    Each rule should be a boolean expression using A-Z variables. Use consistent
    variable naming across rules (e.g. A=user_authenticated, B=is_admin).

    Args:
        rules: List of boolean expressions representing logical conditions.
               Example: ["A.B", "!A+!B", "A^B"]

    Returns:
        Dictionary with per-rule analysis (satisfiable, tautology, minimal form)
        and pairwise checks (equivalent pairs, contradictory pairs).
    """
    analysis = []
    for rule in rules:
        try:
            table, _ = _evaluate(rule)
            minimal, _ = _synthesize(table)
            analysis.append({
                "rule": rule,
                "satisfiable": table.satisfiable,
                "tautology": table.tautology,
                "contradiction": not table.satisfiable,
                "minimal": minimal,
                "simplified": minimal != rule,
            })
        except ValueError as e:
            analysis.append({"rule": rule, "error": str(e)})

    # Pairwise equivalence and contradiction checks
    pairs = []
    valid = [a for a in analysis if "error" not in a]
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            r1, r2 = valid[i]["rule"], valid[j]["rule"]
            try:
                eq = equivalent(r1, r2)
                t1, _ = _evaluate(r1)
                t2, _ = _evaluate(r2)
                # Contradiction: rules can never both be true simultaneously
                combined = f"({r1}).({r2})"
                combined_table, _ = _evaluate(combined)
                pairs.append({
                    "rule1": r1,
                    "rule2": r2,
                    "equivalent": eq["equivalent"],
                    "can_both_be_true": combined_table.satisfiable,
                    "always_conflict": not combined_table.satisfiable,
                })
            except ValueError:
                pass

    return {
        "rules": analysis,
        "pairwise": pairs,
        "summary": {
            "total": len(rules),
            "contradictions": sum(1 for a in analysis if a.get("contradiction")),
            "tautologies": sum(1 for a in analysis if a.get("tautology")),
            "equivalent_pairs": sum(1 for p in pairs if p.get("equivalent")),
            "conflicting_pairs": sum(1 for p in pairs if p.get("always_conflict")),
        },
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
