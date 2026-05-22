from __future__ import annotations
from .models import TruthTable, TruthTableRow
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


def evaluate(expression: str) -> TruthTable:
    error = validate(expression)
    if error:
        raise ValueError(error)

    variables = get_variables(expression)
    prefix = infix_to_prefix(expression)
    n = len(variables)
    rows = []

    for i in range(2 ** n):
        values = {
            var: (i >> (n - 1 - j)) & 1
            for j, var in enumerate(variables)
        }
        output = _evaluate_prefix(prefix, values)
        rows.append(TruthTableRow(inputs=values, output=output))

    return TruthTable(expression=expression, variables=variables, rows=rows)
