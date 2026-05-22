from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TruthTableRow:
    inputs: dict[str, int]
    output: int


@dataclass
class TruthTable:
    expression: str
    variables: list[str]
    rows: list[TruthTableRow]

    @property
    def satisfiable(self) -> bool:
        return any(row.output == 1 for row in self.rows)

    @property
    def tautology(self) -> bool:
        return all(row.output == 1 for row in self.rows)

    @property
    def minterms(self) -> list[int]:
        return [i for i, row in enumerate(self.rows) if row.output == 1]

    @property
    def maxterms(self) -> list[int]:
        return [i for i, row in enumerate(self.rows) if row.output == 0]


@dataclass
class EvaluationResult:
    truth_table: TruthTable
    minimal_expression: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None
