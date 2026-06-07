"""
core/models.py — data structures returned by the engine.

All public functions in evaluator.py and synthesizer.py return these types.
Nothing in this file does computation — it is pure data.
"""
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
    """A single row in a truth table — one combination of inputs and its output."""
    inputs: dict[str, int]
    output: int


@dataclass
class TruthTable:
    """
    A fully evaluated truth table for a boolean expression.

    Attributes:
        expression: The original infix expression string.
        variables:  Sorted list of variable names found in the expression.
        rows:       All 2^n rows, ordered from all-0 inputs to all-1 inputs.
    """
    expression: str
    variables: list[str]
    rows: list[TruthTableRow]

    @property
    def satisfiable(self) -> bool:
        """True if at least one row has output = 1."""
        return any(row.output == 1 for row in self.rows)

    @property
    def tautology(self) -> bool:
        """True if every row has output = 1."""
        return all(row.output == 1 for row in self.rows)

    @property
    def minterms(self) -> list[int]:
        """Row indices where output = 1."""
        return [i for i, row in enumerate(self.rows) if row.output == 1]

    @property
    def maxterms(self) -> list[int]:
        """Row indices where output = 0."""
        return [i for i, row in enumerate(self.rows) if row.output == 0]


@dataclass
class EvaluationResult:
    """
    Combined result of evaluate() + synthesize() in a single object.

    Used by higher layers (CLI, API, MCP) that want everything in one place.
    For direct engine use, call evaluate() and synthesize() separately.
    """
    truth_table: TruthTable
    minimal_expression: str | None = None
    error: str | None = None
    metrics: PerformanceMetrics | None = None

    @property
    def ok(self) -> bool:
        """True when no error occurred."""
        return self.error is None
