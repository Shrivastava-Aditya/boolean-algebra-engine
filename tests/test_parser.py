"""
Unit tests for core/parser.py.

Tests three functions independently:
- get_variables: extracts sorted, deduplicated variable list from an expression
- validate: returns None for valid expressions, an error string for invalid ones
- infix_to_prefix: converts infix boolean expressions to prefix (Polish) notation

Operator precedence under test: ! (NOT, highest) > . (AND) > ^ (XOR) > + (OR, lowest).
"""
import pytest
from boolean_algebra_engine.core.parser import get_variables, validate, infix_to_prefix


# --- get_variables ---

def test_get_variables_sorted():
    """Variables are returned in alphabetical order regardless of appearance order."""
    assert get_variables('B+A') == ['A', 'B']

def test_get_variables_deduped():
    """Each variable appears only once even if repeated in the expression."""
    assert get_variables('A+A.A') == ['A']

def test_get_variables_three():
    """Extracts all unique variables from a multi-variable expression."""
    assert get_variables('A.(B+C)') == ['A', 'B', 'C']


# --- validate ---

def test_validate_empty():
    """Empty string is invalid."""
    assert validate('') is not None

def test_validate_spaces():
    """Spaces are not allowed — expression must be compact."""
    assert validate('A + B') is not None

def test_validate_invalid_char():
    """Characters outside A-Z and operators are rejected."""
    assert validate('A@B') is not None

def test_validate_unmatched_open():
    """Unclosed opening parenthesis is invalid."""
    assert validate('(A+B') is not None

def test_validate_unmatched_close():
    """Closing parenthesis with no matching open is invalid."""
    assert validate('A+B)') is not None

def test_validate_valid_simple():
    """Basic two-variable OR expression is valid."""
    assert validate('A+B') is None

def test_validate_valid_with_parens():
    """Balanced parentheses with multiple operators are valid."""
    assert validate('A.(B+C)') is None

def test_validate_valid_not():
    """NOT operator on a variable followed by AND is valid."""
    assert validate('!A.B') is None


# --- infix_to_prefix ---

def test_prefix_simple_or():
    """A+B → +AB."""
    assert infix_to_prefix('A+B') == '+AB'

def test_prefix_simple_and():
    """A.B → .AB."""
    assert infix_to_prefix('A.B') == '.AB'

def test_prefix_not():
    """!A → !A (unary, single operand)."""
    assert infix_to_prefix('!A') == '!A'

def test_prefix_and_over_or():
    """AND binds tighter than OR: A+B.C → A+(B.C) → +A.BC."""
    assert infix_to_prefix('A+B.C') == '+A.BC'

def test_prefix_parens_override():
    """Parentheses override precedence: (A+B).C → .+ABC."""
    assert infix_to_prefix('(A+B).C') == '.+ABC'

def test_prefix_three_vars():
    """Distribution form: A.(B+C) → .A+BC."""
    assert infix_to_prefix('A.(B+C)') == '.A+BC'
