"""
Edge case tests — boundary conditions, degenerate inputs, and stress cases.

Covers inputs that are valid but unusual, inputs that should fail cleanly,
and synthesizer behaviour on near-full or near-empty truth tables.
"""
import pytest
from boolean_algebra_engine.core.evaluator import evaluate
from boolean_algebra_engine.core.synthesizer import synthesize
from boolean_algebra_engine.core.parser import validate, get_variables


# --- Single variable ---

def test_single_variable_true():
    t = evaluate('A')[0]
    assert [r.output for r in t.rows] == [0, 1]

def test_single_variable_not():
    t = evaluate('!A')[0]
    assert [r.output for r in t.rows] == [1, 0]

def test_single_variable_minterms():
    t = evaluate('A')[0]
    assert t.minterms == [1]
    assert t.maxterms == [0]


# --- Synthesizer edge cases ---

def test_synthesize_single_minterm():
    t = evaluate('A.B.C')[0]
    minimal, _ = synthesize(t)
    rebuilt = evaluate(minimal)[0]
    assert rebuilt.minterms == t.minterms

def test_synthesize_all_but_one_minterm():
    t = evaluate('A+B+C')[0]
    minimal, _ = synthesize(t)
    rebuilt = evaluate(minimal)[0]
    assert rebuilt.minterms == t.minterms

def test_synthesize_single_variable_true():
    t = evaluate('A')[0]
    assert synthesize(t)[0] == 'A'

def test_synthesize_single_variable_false():
    t = evaluate('!A')[0]
    assert synthesize(t)[0] == '!A'

def test_synthesize_empty_minterms():
    t = evaluate('A.!A')[0]
    assert synthesize(t)[0] == '0'

def test_synthesize_full_minterms():
    t = evaluate('A+!A')[0]
    assert synthesize(t)[0] == '1'


# --- Deeply nested parentheses ---

def test_nested_parens_two_levels():
    t1 = evaluate('((A+B)).C')[0]
    t2 = evaluate('(A+B).C')[0]
    assert t1.minterms == t2.minterms

def test_nested_parens_three_levels():
    t = evaluate('((A+B).(C+D))')[0]
    assert t.variables == ['A', 'B', 'C', 'D']
    assert len(t.rows) == 16

def test_nested_parens_not():
    t1 = evaluate('!(A.B)')[0]
    t2 = evaluate('!A+!B')[0]
    assert t1.minterms == t2.minterms


# --- All operators together ---

def test_all_operators():
    t = evaluate('A.B+!C^D')[0]
    assert t.variables == ['A', 'B', 'C', 'D']
    assert len(t.rows) == 16

def test_operator_precedence_not_binds_tightest():
    t1 = evaluate('!A.B')[0]
    t2 = evaluate('(!A).B')[0]
    assert t1.minterms == t2.minterms

def test_operator_precedence_and_over_or():
    t1 = evaluate('A+B.C')[0]
    t2 = evaluate('A+(B.C)')[0]
    assert t1.minterms == t2.minterms


# --- 4+ variable stress tests ---

def test_four_variable_expression():
    t = evaluate('A.B+C.D')[0]
    assert len(t.rows) == 16
    assert t.variables == ['A', 'B', 'C', 'D']

def test_four_variable_round_trip():
    t = evaluate('A.B.C+A.B.D+A.C.D+B.C.D')[0]
    minimal, _ = synthesize(t)
    rebuilt = evaluate(minimal)[0]
    assert t.minterms == rebuilt.minterms

def test_five_variable_row_count():
    t = evaluate('A.B+C.D+E')[0]
    assert len(t.rows) == 32


# --- Invalid input handling ---

def test_empty_string_raises():
    with pytest.raises(ValueError, match='empty'):
        evaluate('')

def test_spaces_raise():
    with pytest.raises(ValueError, match='spaces'):
        evaluate('A + B')

def test_invalid_char_raises():
    with pytest.raises(ValueError, match="'@'"):
        evaluate('A@B')

def test_unmatched_open_paren_raises():
    with pytest.raises(ValueError, match='parenthesis'):
        evaluate('(A+B')

def test_unmatched_close_paren_raises():
    with pytest.raises(ValueError, match='parenthesis'):
        evaluate('A+B)')

def test_validate_returns_none_for_valid():
    assert validate('A.B+!C') is None

def test_get_variables_empty_expression():
    assert get_variables('') == []

def test_get_variables_only_operators():
    assert get_variables('+.!^') == []
