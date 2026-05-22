import pytest
from core.evaluator import evaluate


def test_or_truth_table():
    t = evaluate('A+B')
    outputs = [row.output for row in t.rows]
    assert outputs == [0, 1, 1, 1]

def test_and_truth_table():
    t = evaluate('A.B')
    outputs = [row.output for row in t.rows]
    assert outputs == [0, 0, 0, 1]

def test_xor_truth_table():
    t = evaluate('A^B')
    outputs = [row.output for row in t.rows]
    assert outputs == [0, 1, 1, 0]

def test_not_truth_table():
    t = evaluate('!A')
    outputs = [row.output for row in t.rows]
    assert outputs == [1, 0]

def test_contradiction():
    t = evaluate('A.!A')
    assert t.satisfiable is False
    assert all(row.output == 0 for row in t.rows)

def test_tautology():
    t = evaluate('A+!A')
    assert t.tautology is True
    assert all(row.output == 1 for row in t.rows)

def test_distribution_law():
    # A.(B+C) == A.B + A.C
    t1 = evaluate('A.(B+C)')
    t2 = evaluate('A.B+A.C')
    assert t1.minterms == t2.minterms

def test_demorgan_and():
    # !(A.B) == !A+!B
    t1 = evaluate('!(A.B)')
    t2 = evaluate('!A+!B')
    assert [r.output for r in t1.rows] == [r.output for r in t2.rows]

def test_demorgan_or():
    # !(A+B) == !A.!B
    t1 = evaluate('!(A+B)')
    t2 = evaluate('!A.!B')
    assert [r.output for r in t1.rows] == [r.output for r in t2.rows]

def test_variables_auto_detected():
    t = evaluate('A.(B+C)')
    assert t.variables == ['A', 'B', 'C']

def test_invalid_expression_raises():
    with pytest.raises(ValueError):
        evaluate('A + B')

def test_minterms():
    t = evaluate('A+B')
    assert t.minterms == [1, 2, 3]

def test_maxterms():
    t = evaluate('A.B')
    assert t.maxterms == [0, 1, 2]
