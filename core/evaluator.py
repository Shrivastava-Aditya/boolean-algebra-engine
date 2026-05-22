from __future__ import annotations
import time
import tracemalloc
from .models import TruthTable, TruthTableRow, PerformanceMetrics
from .parser import get_variables, validate, infix_to_prefix


def _evaluate_prefix(prefix: str, variable_values: dict[str, int]) -> int:
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
