"""
Unit tests for core/evaluator.py.

Tests evaluate(), which takes an infix boolean expression string and returns
a TruthTable. Covers all four operators, Boolean laws (De Morgan, distribution,
contradiction, tautology), variable auto-detection, minterm/maxterm indexing,
and error handling for invalid expressions.
"""
import pytest
from boolean_algebra_engine.core.evaluator import evaluate


# --- Basic operators ---

def test_or_truth_table():
    """OR is false only when both inputs are false."""
    t = evaluate('A+B')[0]
    assert [row.output for row in t.rows] == [0, 1, 1, 1]

def test_and_truth_table():
    """AND is true only when both inputs are true."""
    t = evaluate('A.B')[0]
    assert [row.output for row in t.rows] == [0, 0, 0, 1]

def test_xor_truth_table():
    """XOR is true only when inputs differ."""
    t = evaluate('A^B')[0]
    assert [row.output for row in t.rows] == [0, 1, 1, 0]

def test_not_truth_table():
    """NOT inverts the input."""
    t = evaluate('!A')[0]
    assert [row.output for row in t.rows] == [1, 0]


# --- Boolean laws ---

def test_contradiction():
    """A.!A is always false — a contradiction."""
    t = evaluate('A.!A')[0]
    assert t.satisfiable is False
    assert all(row.output == 0 for row in t.rows)

def test_tautology():
    """A+!A is always true — a tautology."""
    t = evaluate('A+!A')[0]
    assert t.tautology is True
    assert all(row.output == 1 for row in t.rows)

def test_distribution_law():
    """A.(B+C) == A.B+A.C (distributive law)."""
    t1 = evaluate('A.(B+C)')[0]
    t2 = evaluate('A.B+A.C')[0]
    assert t1.minterms == t2.minterms

def test_demorgan_and():
    """!(A.B) == !A+!B (De Morgan's law for AND)."""
    t1 = evaluate('!(A.B)')[0]
    t2 = evaluate('!A+!B')[0]
    assert [r.output for r in t1.rows] == [r.output for r in t2.rows]

def test_demorgan_or():
    """!(A+B) == !A.!B (De Morgan's law for OR)."""
    t1 = evaluate('!(A+B)')[0]
    t2 = evaluate('!A.!B')[0]
    assert [r.output for r in t1.rows] == [r.output for r in t2.rows]


# --- Variable detection, minterms, maxterms ---

def test_variables_auto_detected():
    """Variables are inferred from the expression, sorted alphabetically."""
    t = evaluate('A.(B+C)')[0]
    assert t.variables == ['A', 'B', 'C']

def test_minterms():
    """Minterms are row indices where output = 1."""
    t = evaluate('A+B')[0]
    assert t.minterms == [1, 2, 3]

def test_maxterms():
    """Maxterms are row indices where output = 0."""
    t = evaluate('A.B')[0]
    assert t.maxterms == [0, 1, 2]


# --- Error handling ---

def test_invalid_expression_raises():
    """Spaces in expression raise ValueError."""
    with pytest.raises(ValueError):
        evaluate('A + B')
