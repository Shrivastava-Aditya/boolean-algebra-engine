"""
Unit tests for core/models.py.

Tests the TruthTable, TruthTableRow, and EvaluationResult dataclasses directly,
independent of the parser or evaluator. Uses a helper to build tables from raw
output columns so tests don't depend on evaluate().
"""
from boolean_algebra_engine.core.models import TruthTable, TruthTableRow, EvaluationResult


def _make_table(outputs: list[int], variables: list[str] = ['A', 'B']) -> TruthTable:
    """Build a TruthTable directly from an output column, bypassing the evaluator."""
    n = len(variables)
    rows = []
    for i, out in enumerate(outputs):
        inputs = {var: (i >> (n - 1 - j)) & 1 for j, var in enumerate(variables)}
        rows.append(TruthTableRow(inputs=inputs, output=out))
    return TruthTable(expression='test', variables=variables, rows=rows)


# --- TruthTable.satisfiable ---

def test_satisfiable_true():
    """At least one output row is 1."""
    t = _make_table([0, 1, 0, 0])
    assert t.satisfiable is True


def test_satisfiable_false():
    """All output rows are 0 — contradiction."""
    t = _make_table([0, 0, 0, 0])
    assert t.satisfiable is False


# --- TruthTable.tautology ---

def test_tautology_true():
    """All output rows are 1."""
    t = _make_table([1, 1, 1, 1])
    assert t.tautology is True


def test_tautology_false():
    """At least one output row is 0."""
    t = _make_table([1, 1, 0, 1])
    assert t.tautology is False


# --- TruthTable.minterms / maxterms ---

def test_minterms():
    """Minterms are indices of rows where output = 1."""
    t = _make_table([0, 1, 1, 0])
    assert t.minterms == [1, 2]


def test_maxterms():
    """Maxterms are indices of rows where output = 0."""
    t = _make_table([0, 1, 1, 0])
    assert t.maxterms == [0, 3]


# --- EvaluationResult.ok ---

def test_evaluation_result_ok():
    """ok is True when no error is set."""
    t = _make_table([1, 0])
    result = EvaluationResult(truth_table=t)
    assert result.ok is True


def test_evaluation_result_error():
    """ok is False when an error message is present."""
    t = _make_table([1, 0])
    result = EvaluationResult(truth_table=t, error='something went wrong')
    assert result.ok is False
