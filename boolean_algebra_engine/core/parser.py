"""
core/parser.py — expression validation and infix-to-prefix conversion.

Three public functions:
  get_variables(expression)     → sorted list of unique variable names
  validate(expression)          → None if valid, error string if not
  infix_to_prefix(expression)   → prefix (Polish notation) string

Operator precedence: ! (NOT, 4) > . (AND, 3) > ^ (XOR, 2) > + (OR, 1).
Variables must be uppercase A–Z. Parentheses override precedence.
"""
from __future__ import annotations

PRECEDENCE = {'!': 4, '.': 3, '^': 2, '+': 1}
OPERATORS = set(PRECEDENCE)


def get_variables(expression: str) -> list[str]:
    """Return sorted, deduplicated list of uppercase variable names in expression."""
    return sorted(set(c for c in expression if c.isupper()))


def validate(expression: str) -> str | None:
    """Return None if expression is valid, or an error message string if not."""
    if not expression:
        return "Expression cannot be empty"
    if ' ' in expression:
        return "Expression must not contain spaces"
    depth = 0
    for i, c in enumerate(expression):
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth < 0:
                return f"Unmatched closing parenthesis at position {i}"
        elif not (c.isupper() or c in OPERATORS or c in '()'):
            return f"Unexpected character '{c}' at position {i}"
    if depth != 0:
        return "Unmatched opening parenthesis"
    return None


def infix_to_prefix(expression: str) -> str:
    """Convert an infix boolean expression to prefix (Polish) notation."""
    result = []
    stack = []

    chars = list(reversed(expression))
    for i, c in enumerate(chars):
        if c == '(':
            chars[i] = ')'
        elif c == ')':
            chars[i] = '('

    for c in chars:
        if c.isupper():
            result.append(c)
        elif c in PRECEDENCE:
            while stack and stack[-1] in PRECEDENCE and PRECEDENCE[stack[-1]] >= PRECEDENCE[c]:
                result.append(stack.pop())
            stack.append(c)
        elif c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                result.append(stack.pop())
            stack.pop()

    while stack:
        result.append(stack.pop())

    return ''.join(reversed(result))
