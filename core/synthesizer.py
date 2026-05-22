from __future__ import annotations
from .models import TruthTable


def _can_merge(a: str, b: str) -> tuple[bool, str]:
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
    bits = format(minterm, f'0{n}b')
    return all(p == '-' or p == b for p, b in zip(implicant, bits))


def _minimum_cover(prime_implicants: list[str], minterms: list[int], n: int) -> list[str]:
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
    terms = []
    for bit, var in zip(pi, variables):
        if bit == '1':
            terms.append(var)
        elif bit == '0':
            terms.append(f'!{var}')
    return '.'.join(terms) if terms else '1'


def synthesize(truth_table: TruthTable) -> str:
    minterms = truth_table.minterms
    variables = truth_table.variables
    n = len(variables)

    if not minterms:
        return '0'
    if len(minterms) == 2 ** n:
        return '1'

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
    return '+'.join(_pi_to_expr(pi, variables) for pi in selected)
