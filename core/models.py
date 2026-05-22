from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PerformanceMetrics:
    """
    Timing and memory measurements for a single engine operation.

    Captured automatically by evaluate() and synthesize(). Use these as
    your baseline before applying CUDA parallelism or expression caching —
    the numbers make the speedup concrete and measurable.

    Attributes:
        eval_time_ms:        Time to evaluate the expression (ms).
        synth_time_ms:       Time to synthesize the minimal form (ms). None if not run.
        peak_memory_bytes:   Peak memory allocated during the operation.
        rows_evaluated:      Number of truth table rows (2^n). This is the unit
                             of work that CUDA will parallelise — each row is
                             independent and maps directly to a GPU thread.
        prime_implicant_count: Number of prime implicants found during synthesis.
                             Indicates Quine-McCluskey complexity — a good target
                             for caching repeated sub-expressions.
    """
    eval_time_ms: float = 0.0
    synth_time_ms: float | None = None
    peak_memory_bytes: int = 0
    rows_evaluated: int = 0
    prime_implicant_count: int | None = None


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
    metrics: PerformanceMetrics | None = None

    @property
    def ok(self) -> bool:
        return self.error is None
