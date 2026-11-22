"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Handbeispiel: sechs Orte auf dem Rand eines Rechtecks 8 x 3, 0 = (0, 0), 1 = (4, 0), 2 = (8, 0), 3 = (8, 3), 4 = (4, 3), 5 = (0, 3).
Starttour (0, 2, 1, 3, 4, 5) mit einer Kreuzung: 8 + 4 + 5 + 4 + 4 + 3 = 28. Umfang des Rechtecks (0, 1, 2, 3, 4, 5): 22 (Optimum)."""

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import zgm_scenario as S  # noqa: E402


@pytest.fixture
def hand():
    """(Abstandsmatrix, Starttour) des Handbeispiels."""
    _, D = S.hand_instance()
    return D, list(S.HAND_START)


def zufallsinstanz(n: int, seed: int):
    """Kleine Zufallsinstanz für Orakel-Tests (Python-random nur hier in den Tests, nie im Kern)."""
    z = random.Random(seed)
    punkte = [(z.random() * 100.0, z.random() * 100.0) for _ in range(n)]
    tour = list(range(n))
    z.shuffle(tour)
    return S.distance_matrix(punkte), tour


def brute_force(D) -> float:
    """Exaktes Optimum per Aufzählung aller Rundtouren (n bis 9), unabhängig von zgm_exact.held_karp."""
    import itertools

    n = len(D)
    best = 1e300
    for perm in itertools.permutations(range(1, n)):
        if perm[0] > perm[-1]:
            continue
        c = D[0][perm[0]] + D[perm[-1]][0] + sum(D[a][b] for a, b in zip(perm, perm[1:]))
        best = min(best, c)
    return best
