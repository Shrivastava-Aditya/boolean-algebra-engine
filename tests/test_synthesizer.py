"""
Unit tests for core/synthesizer.py.

Tests synthesize(), which takes a TruthTable and returns the minimal boolean
expression (sum of products) via Quine-McCluskey. Correctness is verified by
re-evaluating the synthesized expression and comparing minterms to the original.

Note: synthesize() may return terms in a different order than the original
expression. Tests compare logical equivalence, not string equality, except where
a specific minimal form is known (e.g. tautology → '1', contradiction → '0',
A.B+A.!B → 'A').
"""
from core.evaluator import evaluate
from core.synthesizer import synthesize


def _round_trip(expression: str) -> bool:
    """Evaluate an expression, synthesize minimal form, verify logical equivalence."""
    original = evaluate(expression)[0]
    minimal = synthesize(original)[0]
    rebuilt = evaluate(minimal)[0] if minimal not in ('0', '1') else None

    if minimal == '0':
        return original.minterms == []
    if minimal == '1':
        return original.tautology
    return original.minterms == rebuilt.minterms


# --- Special cases ---

def test_contradiction_returns_zero():
    """Unsatisfiable expressions synthesize to the literal string '0'."""
    t = evaluate('A.!A')[0]
    assert synthesize(t)[0] == '0'

def test_tautology_returns_one():
    """Tautologies synthesize to the literal string '1'."""
    t = evaluate('A+!A')[0]
    assert synthesize(t)[0] == '1'


# --- Round-trip correctness ---

def test_round_trip_or():
    """Synthesized form of A+B is logically equivalent to A+B."""
    assert _round_trip('A+B')

def test_round_trip_and():
    """Synthesized form of A.B is logically equivalent to A.B."""
    assert _round_trip('A.B')

def test_round_trip_xor():
    """Synthesized form of A^B is logically equivalent to A^B."""
    assert _round_trip('A^B')

def test_round_trip_not():
    """Synthesized form of !A is logically equivalent to !A."""
    assert _round_trip('!A')

def test_round_trip_distribution():
    """Synthesized form of A.(B+C) is logically equivalent to the original."""
    assert _round_trip('A.(B+C)')

def test_three_variable_expression():
    """Round-trip holds for a three-variable majority function."""
    assert _round_trip('A.B+B.C+A.C')


# --- Minimization correctness ---

def test_equivalent_expressions_same_minimal():
    """Logically equivalent expressions produce the same minimal form."""
    t1 = evaluate('A.(B+C)')[0]
    t2 = evaluate('A.B+A.C')[0]
    assert synthesize(t1)[0] == synthesize(t2)[0]

def test_minimal_form_is_simpler_or_equal():
    """A.B+A.!B reduces to A — adjacent minterms merge into a single term."""
    t = evaluate('A.B+A.!B')[0]
    assert synthesize(t)[0] == 'A'
