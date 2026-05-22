from core.models import TruthTable, TruthTableRow, EvaluationResult


def _make_table(outputs: list[int], variables: list[str] = ['A', 'B']) -> TruthTable:
    n = len(variables)
    rows = []
    for i, out in enumerate(outputs):
        inputs = {var: (i >> (n - 1 - j)) & 1 for j, var in enumerate(variables)}
        rows.append(TruthTableRow(inputs=inputs, output=out))
    return TruthTable(expression='test', variables=variables, rows=rows)


def test_satisfiable_true():
    t = _make_table([0, 1, 0, 0])
    assert t.satisfiable is True


def test_satisfiable_false():
    t = _make_table([0, 0, 0, 0])
    assert t.satisfiable is False


def test_tautology_true():
    t = _make_table([1, 1, 1, 1])
    assert t.tautology is True


def test_tautology_false():
    t = _make_table([1, 1, 0, 1])
    assert t.tautology is False


def test_minterms():
    t = _make_table([0, 1, 1, 0])
    assert t.minterms == [1, 2]


def test_maxterms():
    t = _make_table([0, 1, 1, 0])
    assert t.maxterms == [0, 3]


def test_evaluation_result_ok():
    t = _make_table([1, 0])
    result = EvaluationResult(truth_table=t)
    assert result.ok is True


def test_evaluation_result_error():
    t = _make_table([1, 0])
    result = EvaluationResult(truth_table=t, error='something went wrong')
    assert result.ok is False
