"""
core/synthesizer.py — minimal expression synthesis via Quine-McCluskey.

Public API:
  synthesize(truth_table) → (str, PerformanceMetrics)

The inverse of evaluate(): given a TruthTable, returns the minimal sum-of-
products boolean expression that produces it. Uses the Quine-McCluskey
algorithm: iteratively merge minterms that differ by one bit to find prime
implicants, then select the minimum cover using essential prime implicants
first, greedy cover for the remainder.

Special cases:
  No minterms (contradiction) → '0'
  All minterms (tautology)    → '1'
"""
from __future__ import annotations
import time
import tracemalloc
from .models import TruthTable, PerformanceMetrics


def _can_merge(a: str, b: str) -> tuple[bool, str]:
    """Return (True, merged) if two implicants differ in exactly one non-dash bit."""
    diff_count = 0
    diff_pos = -1
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            if x == '-' or y == '-':
                return False, ''
            diff_count += 1
            diff_pos = i
            if diff_count > 1:
                return False, ''
    if diff_count == 1:
        result = list(a)
        result[diff_pos] = '-'
        return True, ''.join(result)
    return False, ''


def _covers(implicant: str, minterm: int, n: int) -> bool:
    """Return True if an implicant pattern covers a given minterm index."""
    bits = format(minterm, f'0{n}b')
    return all(p == '-' or p == b for p, b in zip(implicant, bits))


def _minimum_cover(prime_implicants: list[str], minterms: list[int], n: int) -> list[str]:
    """Select the minimum set of prime implicants that covers all minterms."""
    coverage = {pi: {m for m in minterms if _covers(pi, m, n)} for pi in prime_implicants}
    selected = []
    covered = set()

    for m in minterms:
        covering = [pi for pi in prime_implicants if m in coverage[pi]]
        if len(covering) == 1 and covering[0] not in selected:
            selected.append(covering[0])
            covered |= coverage[covering[0]]

    remaining = set(minterms) - covered
    while remaining:
        best = max(
            (pi for pi in prime_implicants if pi not in selected),
            key=lambda pi: len(coverage[pi] & remaining),
            default=None,
        )
        if best is None:
            break
        selected.append(best)
        covered |= coverage[best]
        remaining -= coverage[best]

    return selected


def _pi_to_expr(pi: str, variables: list[str]) -> str:
    """Convert a prime implicant bit pattern to a boolean product term string."""
    terms = []
    for bit, var in zip(pi, variables):
        if bit == '1':
            terms.append(var)
        elif bit == '0':
            terms.append(f'!{var}')
    return '.'.join(terms) if terms else '1'


def synthesize(truth_table: TruthTable) -> tuple[str, PerformanceMetrics]:
    """
    Synthesize the minimal boolean expression for a given truth table.

    Uses Quine-McCluskey to find all prime implicants, then selects the
    minimum cover — essential prime implicants first, greedy for the rest.

    Args:
        truth_table: A TruthTable returned by evaluate().

    Returns:
        (expression, PerformanceMetrics) — minimal SOP expression string
        and timing/memory data. Returns '0' for contradictions, '1' for
        tautologies.

    Example:
        table, _ = evaluate('A.B+A.!B')
        expr, metrics = synthesize(table)
        print(expr)                          # 'A'
        print(metrics.prime_implicant_count) # 1
    """
    minterms = truth_table.minterms
    variables = truth_table.variables
    n = len(variables)

    tracemalloc.start()
    t_start = time.perf_counter()

    if not minterms:
        synth_time_ms = (time.perf_counter() - t_start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return '0', PerformanceMetrics(synth_time_ms=round(synth_time_ms, 4), peak_memory_bytes=peak, prime_implicant_count=0)

    if len(minterms) == 2 ** n:
        synth_time_ms = (time.perf_counter() - t_start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return '1', PerformanceMetrics(synth_time_ms=round(synth_time_ms, 4), peak_memory_bytes=peak, prime_implicant_count=0)

    current: dict[str, set[int]] = {format(m, f'0{n}b'): {m} for m in minterms}
    prime_implicants: list[str] = []

    while True:
        next_round: dict[str, set[int]] = {}
        used: set[str] = set()
        items = list(current.items())

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, a_cov = items[i]
                b, b_cov = items[j]
                ok, merged = _can_merge(a, b)
                if ok:
                    if merged not in next_round:
                        next_round[merged] = set()
                    next_round[merged] |= a_cov | b_cov
                    used.add(a)
                    used.add(b)

        for term in current:
            if term not in used:
                prime_implicants.append(term)

        if not next_round:
            break
        current = next_round

    selected = _minimum_cover(prime_implicants, minterms, n)
    expr = '+'.join(_pi_to_expr(pi, variables) for pi in selected)

    synth_time_ms = (time.perf_counter() - t_start) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics = PerformanceMetrics(
        synth_time_ms=round(synth_time_ms, 4),
        peak_memory_bytes=peak,
        prime_implicant_count=len(prime_implicants),
    )
    return expr, metrics
