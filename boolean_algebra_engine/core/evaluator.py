"""
core/evaluator.py — truth table generation.

Public API:
  evaluate(expression) → (TruthTable, PerformanceMetrics)

Raises ValueError for invalid expressions (delegates to parser.validate).
Each row in the truth table is evaluated independently — this is the
sequential baseline that CUDA will later parallelise (one thread per row).
"""
from __future__ import annotations
import time
import tracemalloc
from .models import TruthTable, TruthTableRow, PerformanceMetrics
from .parser import get_variables, validate, infix_to_prefix


def _evaluate_prefix(prefix: str, variable_values: dict[str, int]) -> int:
    """Evaluate a prefix expression for a single row of variable assignments."""
    stack = []
    for c in reversed(prefix):
        if c.isupper():
            stack.append(variable_values[c])
        elif c == '!':
            stack.append(1 - stack.pop())
        else:
            a, b = stack.pop(), stack.pop()
            if c == '.':
                stack.append(a & b)
            elif c == '+':
                stack.append(a | b)
            elif c == '^':
                stack.append(a ^ b)
    return stack[0]


def evaluate(expression: str) -> tuple[TruthTable, PerformanceMetrics]:
    """
    Evaluate a boolean expression and return its full truth table.

    Args:
        expression: Infix boolean expression string. Variables must be
                    uppercase letters. Operators: ! . ^ +

    Returns:
        (TruthTable, PerformanceMetrics) — truth table and timing/memory data.

    Raises:
        ValueError: If the expression fails validation.

    Example:
        table, metrics = evaluate('A.(B+C)')
        print(table.minterms)       # [5, 6, 7]
        print(metrics.eval_time_ms) # 0.21
    """
    error = validate(expression)
    if error:
        raise ValueError(error)

    variables = get_variables(expression)
    prefix = infix_to_prefix(expression)
    n = len(variables)

    tracemalloc.start()
    t_start = time.perf_counter()

    rows = []
    for i in range(2 ** n):
        values = {
            var: (i >> (n - 1 - j)) & 1
            for j, var in enumerate(variables)
        }
        output = _evaluate_prefix(prefix, values)
        rows.append(TruthTableRow(inputs=values, output=output))

    eval_time_ms = (time.perf_counter() - t_start) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    table = TruthTable(expression=expression, variables=variables, rows=rows)
    metrics = PerformanceMetrics(
        eval_time_ms=round(eval_time_ms, 4),
        peak_memory_bytes=peak,
        rows_evaluated=2 ** n,
    )
    return table, metrics
