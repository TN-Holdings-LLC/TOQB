"""A chain that turns before a hole (DRAFT, workplace 2026-11-06; not declared). No score, fixed order, first fit.

Heron r2 labels as in daily/du91.py: 8 rows of 16 qubits (20 r + c), bridges 20 r + 16 + k between rows r and r + 1 at
column 3 + 4k (r even) or 1 + 4k (r odd).

The rule (fixed before any device record is read):
  * A start is (vertical direction v, first row, first column 0 or 15). The starts are tried in the fixed order
    START_ORDER; the first start whose chain reaches N sites is used. Nothing is compared between starts.
  * In each row the chain runs from its entry column in the row's direction over healthy qubits and healthy couplers
    and stops at the first hole (failed qubit, failed or missing coupler) or at the row's end.
  * It turns at the farthest column of that run that has a healthy bridge to the next row (row + v) and a healthy
    qubit below it. Without holes this is the row's last bridge column, so the start (+1, row 0, column 0) gives
    exactly du91's shape S1 (du91's S2 starts with a two-site row and is not reproduced).
  * If the run has no such column, the row is run once in the other direction from the entry column (fixed second
    choice). The next row runs opposite to the direction used. Rows are never revisited (v is fixed per start).
  * The chain is the first N sites. If a start cannot reach N, the next start is tried; if none can, Refused.
The part of a row beyond a hole is given up (not used); that is the price of having no search.

Rule B (bypass=True; a fixed addition, not a different search): at a hole inside a row, before giving the rest of the
row up, the chain goes round the hole through the heavy-hex cell below it (row + v): down the last bridge before the
hole, along the cell's 5 qubits of the next row, up the next bridge, and on along its own row, when every element is
healthy and not yet used. Used qubits count as holes for later rows. Taken whenever possible (no comparison).
"""
from __future__ import annotations

ROWS, COLS = 8, 16
START_ORDER = [(v, r, c) for v in (+1, -1) for r in (range(ROWS) if v > 0 else range(ROWS - 1, -1, -1))
               for c in (0, COLS - 1)]


def bridge(r, col):
    """Bridge between row r and r + 1 at column col, or None."""
    if not 0 <= r < ROWS - 1:
        return None
    k, ok = ((col - 3) // 4, (col - 3) % 4 == 0) if r % 2 == 0 else ((col - 1) // 4, (col - 1) % 4 == 0)
    return 20 * r + 16 + k if ok and 0 <= k <= 3 else None


class Refused(Exception):
    pass


def _health(dev):
    bad = set(dev.failed_qubits)
    badc = {frozenset(c) for c in dev.failed_couplers}
    cpl = {frozenset(c) for c in dev.couplers}

    def q_ok(q):
        return q is not None and 0 <= q < dev.num_qubits and q not in bad

    def e_ok(a, b):
        return frozenset((a, b)) in cpl and frozenset((a, b)) not in badc and q_ok(a) and q_ok(b)

    return q_ok, e_ok


def chain_from(dev, n, v, r, c, bypass=False):
    """(chain, None) for one start, or (longest chain reached, reason). bypass: rule B (below)."""
    q_ok, e_ok0 = _health(dev)
    used = set()

    def e_ok(a, b):
        return e_ok0(a, b) and b not in used

    if not q_ok(20 * r + c):
        return [], "start qubit failed"
    out, col, d = [], c, (1 if c == 0 else -1)
    used.add(20 * r + c)

    def run_from(r, col, dd):
        """Columns (and inserted bypass labels) of row r from col in direction dd; rule B goes round a hole through
        the cell of the next row: down at the last bridge column before the hole, along row r + v, up at the next
        bridge column, if every element is healthy and unused."""
        cols, path = [col], [20 * r + col]
        while True:
            x = cols[-1]
            if 0 <= x + dd < COLS and e_ok(20 * r + x, 20 * r + x + dd):
                cols.append(x + dd)
                path.append(20 * r + x + dd)
                continue
            if not (bypass and 0 <= x + dd < COLS and 0 <= r + v < ROWS):
                return cols, path
            rn = r + v
            b1 = bridge(min(r, rn), x)
            x2 = x + 4 * dd
            b2 = bridge(min(r, rn), x2) if 0 <= x2 < COLS else None
            if b1 is None or b2 is None:
                return cols, path
            detour = [b1] + [20 * rn + y for y in range(x, x2 + dd, dd)] + [b2, 20 * r + x2]
            seq = [20 * r + x] + detour
            if all(e_ok(a, b) for a, b in zip(seq, seq[1:])) and len(set(detour)) == len(detour):
                cols.append(x2)
                path += detour
                used.update(detour)
                continue
            return cols, path

    while True:
        best = None
        for dd in (d, -d):
            snap = set(used)
            cols, path = run_from(r, col, dd)
            if len(out) + len(path) >= n:
                return out + path[: n - len(out)], None
            rn = r + v
            turn = None
            for x in reversed(cols):
                b = bridge(min(r, rn), x)
                if 0 <= rn < ROWS and b is not None and e_ok(20 * r + x, b) and e_ok(b, 20 * rn + x):
                    turn = x
                    break
            if turn is not None:
                cut = path.index(20 * r + turn) + 1
                used.clear()
                used.update(snap | set(path[:cut]))
                best = (dd, path[:cut], turn, b)
                break
            used.clear()
            used.update(snap)
        if best is None:
            cols, path = run_from(r, col, d)
            return out + path, f"no bridge onward from row {r}"
        dd, path, turn, b = best
        out += path + [b]
        used.update(path + [b, 20 * (r + v) + turn])
        if len(out) >= n:
            return out[:n], None
        r, col, d = r + v, turn, -dd


def place(dev, n, bypass=False):
    """(chain, start, passed over) of the first start in START_ORDER that reaches n sites."""
    passed = []
    for st in START_ORDER:
        ch, why = chain_from(dev, n, *st, bypass=bypass)
        if why is None:
            return ch, st, passed
        passed.append(dict(start=st, reached=len(ch), why=why))
    raise Refused(f"no start reaches {n} sites; best {max(p['reached'] for p in passed)}")


def check(dev, chain):
    """Independent check: distinct labels, every link a healthy coupler of the record."""
    q_ok, e_ok = _health(dev)
    assert len(set(chain)) == len(chain), "a label repeats"
    bad = [(a, b) for a, b in zip(chain, chain[1:]) if not e_ok(a, b)]
    return dict(sites=len(chain), distinct=True, bad_links=bad, all_healthy=all(q_ok(q) for q in chain))


# ---- Rule C (an option for the owner to judge; it backtracks): a fixed-order depth-first walk ----
# The candidates are all simple paths from a start, in one fixed order: at a row qubit, first along the row in the
# row's direction, then the bridge toward row + v, then the bridge toward row - v, then back along the row; at a bridge,
# first toward row + v. Entering a new row reverses the row direction (a snake). The first path of N sites in this
# order is used; there is no score and no comparison, but the walk backtracks, and it stops after BUDGET steps per
# start (a start that does not finish within the budget counts as not reaching N). The budget is fixed here.
BUDGET = 200000


def _bridge_ends(dev, b):
    """(upper row label, lower row label) of bridge b."""
    r, k = divmod(b - 16, 20)
    col = 3 + 4 * k if r % 2 == 0 else 1 + 4 * k
    return 20 * r + col, 20 * (r + 1) + col


def chain_dfs(dev, n, v, r, c, budget=BUDGET):
    q_ok, e_ok = _health(dev)
    s = 20 * r + c
    if not q_ok(s):
        return [], "start qubit failed"
    steps = [0]
    best = [[s]]

    def nbrs(q, d):
        rr, cc = divmod(q, 20)
        out = []
        if cc < 16:  # row qubit
            if 0 <= cc + d < COLS:
                out.append((q + d, d))
            for rn in (rr + v, rr - v):
                if 0 <= rn < ROWS:
                    b = bridge(min(rr, rn), cc)
                    if b is not None:
                        out.append((b, -d))
            if 0 <= cc - d < COLS:
                out.append((q - d, -d))
        else:  # bridge: d already reversed for the new row
            up, dn = _bridge_ends(dev, q)
            out += [(dn, d), (up, d)] if v > 0 else [(up, d), (dn, d)]
        return out

    path, seen = [s], {s}

    def go(q, d):
        steps[0] += 1
        if len(path) > len(best[0]):
            best[0] = list(path)
        if len(path) >= n or steps[0] > budget:
            return len(path) >= n
        for x, dx in nbrs(q, d):
            if x not in seen and e_ok(q, x):
                path.append(x)
                seen.add(x)
                if go(x, dx):
                    return True
                path.pop()
                seen.discard(x)
                if steps[0] > budget:
                    return False
        return False

    import sys
    sys.setrecursionlimit(max(10000, 4 * n))
    ok = go(s, 1 if c == 0 else -1)
    return (list(path), None) if ok else (best[0], "budget spent" if steps[0] > budget else "exhausted")


def place_dfs(dev, n, budget=BUDGET):
    passed = []
    for st in START_ORDER:
        ch, why = chain_dfs(dev, n, *st, budget=budget)
        if why is None:
            return ch, st, passed
        passed.append(dict(start=st, reached=len(ch), why=why))
    raise Refused(f"no start reaches {n} sites (rule C); best {max(p['reached'] for p in passed)}")
