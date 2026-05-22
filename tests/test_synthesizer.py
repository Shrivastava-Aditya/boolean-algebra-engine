from core.evaluator import evaluate
from core.synthesizer import synthesize


def _round_trip(expression: str) -> bool:
    """Synthesize a minimal expression, re-evaluate it, check minterms match."""
    original = evaluate(expression)
    minimal = synthesize(original)
    rebuilt = evaluate(minimal) if minimal not in ('0', '1') else None

    if minimal == '0':
        return original.minterms == []
    if minimal == '1':
        return original.tautology
    return original.minterms == rebuilt.minterms


def test_contradiction_returns_zero():
    t = evaluate('A.!A')
    assert synthesize(t) == '0'

def test_tautology_returns_one():
    t = evaluate('A+!A')
    assert synthesize(t) == '1'

def test_round_trip_or():
    assert _round_trip('A+B')

def test_round_trip_and():
    assert _round_trip('A.B')

def test_round_trip_xor():
    assert _round_trip('A^B')

def test_round_trip_not():
    assert _round_trip('!A')

def test_round_trip_distribution():
    assert _round_trip('A.(B+C)')

def test_equivalent_expressions_same_minimal():
    t1 = evaluate('A.(B+C)')
    t2 = evaluate('A.B+A.C')
    assert synthesize(t1) == synthesize(t2)

def test_three_variable_expression():
    assert _round_trip('A.B+B.C+A.C')

def test_minimal_form_is_simpler_or_equal():
    # A.B+A.!B simplifies to A
    t = evaluate('A.B+A.!B')
    minimal = synthesize(t)
    assert minimal == 'A'
