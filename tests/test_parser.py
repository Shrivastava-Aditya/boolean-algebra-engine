import pytest
from core.parser import get_variables, validate, infix_to_prefix


# --- get_variables ---

def test_get_variables_sorted():
    assert get_variables('B+A') == ['A', 'B']

def test_get_variables_deduped():
    assert get_variables('A+A.A') == ['A']

def test_get_variables_three():
    assert get_variables('A.(B+C)') == ['A', 'B', 'C']


# --- validate ---

def test_validate_empty():
    assert validate('') is not None

def test_validate_spaces():
    assert validate('A + B') is not None

def test_validate_invalid_char():
    assert validate('A@B') is not None

def test_validate_unmatched_open():
    assert validate('(A+B') is not None

def test_validate_unmatched_close():
    assert validate('A+B)') is not None

def test_validate_valid_simple():
    assert validate('A+B') is None

def test_validate_valid_with_parens():
    assert validate('A.(B+C)') is None

def test_validate_valid_not():
    assert validate('!A.B') is None


# --- infix_to_prefix ---

def test_prefix_simple_or():
    assert infix_to_prefix('A+B') == '+AB'

def test_prefix_simple_and():
    assert infix_to_prefix('A.B') == '.AB'

def test_prefix_not():
    assert infix_to_prefix('!A') == '!A'

def test_prefix_and_over_or():
    # A+B.C → A+(B.C) → +A.BC
    assert infix_to_prefix('A+B.C') == '+A.BC'

def test_prefix_parens_override():
    # (A+B).C → .+ABC
    assert infix_to_prefix('(A+B).C') == '.+ABC'

def test_prefix_three_vars():
    assert infix_to_prefix('A.(B+C)') == '.A+BC'
