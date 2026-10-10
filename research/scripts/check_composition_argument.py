"""Check a one-decision contract argument, not async/source/SDK correctness."""
from itertools import product


def contracts(a, k, r, h, d, scoped):
    gate = not d or a
    cancellation_applies = k and (not r if scoped else True)
    cancellation = not cancellation_applies or not d
    replay = not r or d == h
    return gate and cancellation and replay


def main():
    counts = {}
    for scoped in (False, True):
        feasible = 0
        for a, k, r, h in product((False, True), repeat=4):
            solutions = [d for d in (False, True) if contracts(a, k, r, h, d, scoped)]
            # Closed-form elimination of the local decision variable d.
            expected = not (r and h and (not a or (k and not scoped)))
            assert bool(solutions) == expected, (scoped, a, k, r, h)
            if expected:
                # Also meets the optional normal fresh-path dispatch requirement.
                witness = h if r else a and not k
                assert witness in solutions
                feasible += 1
        counts['scoped' if scoped else 'unscoped'] = feasible

    # Minimal cancellation/replay inconsistency: authorization is still true.
    assert not any(contracts(True, True, True, True, d, False) for d in (False, True))
    assert contracts(True, True, True, True, True, True)
    # Even the scoped version cannot replay a required unauthorized command.
    assert not any(contracts(False, False, True, True, d, True) for d in (False, True))
    # Permission alone is not an unconditional dispatch requirement.
    assert contracts(True, True, False, False, False, True)
    # At k=r=h=True, verify the conflicting pair is a minimal unsatisfiable core.
    clauses = (lambda d: not d, lambda d: d)
    assert not any(all(clause(d) for clause in clauses) for d in (False, True))
    for removed in range(len(clauses)):
        remaining = [clause for i, clause in enumerate(clauses) if i != removed]
        assert any(all(clause(d) for clause in remaining) for d in (False, True))
    assert counts == {'unscoped': 13, 'scoped': 14}
    print('Composition argument: 32 environments / 64 decision valuations checked; '
          '13 unscoped and 14 scoped environments feasible. No new composition rule required.')


if __name__ == '__main__':
    main()
