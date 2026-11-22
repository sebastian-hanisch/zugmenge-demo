"""Zugarten an der Mini-Instanz (DEMO-PLAYBOOK §1b): Vorschlag, Kantenformel, Anwenden, Kosten.

Jede Zugart einzeln: das Ergebnis ist eine Permutation, und das Delta der Kantenformel stimmt mit der vollen Neubewertung überein."""

import pytest

import zgm_constants as C
import zgm_moves as M
import zgm_scenario as S
from zgm_rngblock import BlockSplitMix64
from zgm_search import check_feasible


class Folge:
    """Zufallsstrom mit vorgegebenen Gleichverteilten (für Handrechnungen)."""

    def __init__(self, werte):
        self._werte = iter(werte)

    def random(self):
        return next(self._werte)


def test_2opt_zug_der_handrechnung(hand):
    D, t = hand
    # i = int(0.3 * 5) = 1; Länge 2 + int(0.1 * 3) = 2, also Positionen 1 bis 2 (Orte 2, 1) umdrehen
    delta, move = M.propose_2opt(t, D, 6, Folge([0.3, 0.1]))
    assert move == (1, 2)
    assert delta == pytest.approx(4 + 3 - 8 - 5)          # neue Kanten 0-1 und 2-3, entfernte 0-2 und 1-3
    M.apply_move(t, C.H_2OPT, move)
    assert t == [0, 1, 2, 3, 4, 5] and S.tour_cost(D, t) == pytest.approx(22.0)


def test_zweiter_verbessernder_2opt_zug_der_handrechnung(hand):
    D, t = hand
    # i = int(0.5 * 5) = 2, Länge 2: Orte 1, 3 umdrehen; neue Kanten 2-3 (3) und 1-4 (3), entfernte 2-1 (4) und 3-4 (4)
    delta, move = M.propose_2opt(t, D, 6, Folge([0.5, 0.0]))
    assert move == (2, 3) and delta == pytest.approx(3 + 3 - 4 - 4)
    M.apply_move(t, C.H_2OPT, move)
    assert S.tour_cost(D, t) == pytest.approx(26.0)


def test_swap_von_hand(hand):
    D, t = hand
    # i = 1 (Ort 2), j = (1 + 2 + 0) % 6 = 3 (Ort 3): Tour 0, 3, 1, 2, 4, 5 = 8,544 + 5 + 4 + 5 + 4 + 3
    delta, move = M.propose_swap(t, D, 6, Folge([0.2, 0.0]))
    assert move == (1, 3)
    M.apply_move(t, 0, move)
    assert t == [0, 3, 1, 2, 4, 5]
    assert delta == pytest.approx(S.tour_cost(D, t) - 28.0) == pytest.approx(73 ** 0.5 + 5 + 4 + 5 + 4 + 3 - 28)


def test_insert_von_hand(hand):
    D, t = hand
    # i = 1 (Ort 2) hinter Position j = (1 + 1 + 0) % 6 = 2 (Ort 1): Tour 0, 1, 2, 3, 4, 5 (das Optimum)
    delta, move = M.propose_insert(t, D, 6, Folge([0.2, 0.0]))
    assert move == (1, 2) and delta == pytest.approx(-6.0)
    M.apply_move(t, 1, move)
    assert t == [0, 1, 2, 3, 4, 5]


def test_oropt_und_dbridge_von_hand(hand):
    D, t = hand
    # oropt2: i = 1 (Stück 2, 1), j = (1 + 2 + 0) % 6 = 3 (hinter Ort 3), umgedreht (u < 0,5): Tour 0, 3, 1, 2, 4, 5
    delta, move = M.propose_oropt2(t, D, 6, Folge([0.25, 0.0, 0.4]))
    assert move == (1, 3, 2, True)
    neu = list(t)
    M.apply_move(neu, 4, move)
    assert neu == [0, 3, 1, 2, 4, 5] and delta == pytest.approx(S.tour_cost(D, neu) - 28.0)
    # dbridge: Schnitte 1, 2, 4 (aus u = 0,1 / 0,3 / 0,7 bei n - 1 = 5): Stücke [2] und [1, 3] tauschen: Tour 0, 1, 3, 2, 4, 5
    delta, move = M.propose_dbridge(t, D, 6, Folge([0.1, 0.3, 0.7]))
    assert move == (1, 2, 4)
    neu = list(t)
    M.apply_move(neu, 6, move)
    assert neu == [0, 1, 3, 2, 4, 5] and delta == pytest.approx(S.tour_cost(D, neu) - 28.0)


def test_dbridge_zieht_neu_bei_gleichen_schnitten(hand):
    D, t = hand
    _, move = M.propose_dbridge(t, D, 6, Folge([0.1, 0.1, 0.7, 0.9, 0.5, 0.1]))   # erste Ziehung 1, 1, 4 verworfen; zweite 5, 3, 1
    assert move == (1, 3, 5)


def test_2opt_b5_nimmt_den_besten_und_bei_gleichstand_den_frueheren(hand):
    D, t = hand
    # Stichproben: (2, 3) Delta -2, (1, 2) Delta -6, (1, 2) Delta -6: der zweite gewinnt und bleibt
    delta, move = M.propose_2opt_b5(t, D, 6, Folge([0.5, 0.0, 0.3, 0.1, 0.3, 0.1]), 3)
    assert move == (1, 2) and delta == pytest.approx(-6.0)
    delta1, move1 = M.propose_2opt_b5(t, D, 6, Folge([0.5, 0.0]), 1)
    assert move1 == (2, 3) and delta1 == pytest.approx(-2.0)


def test_kosten_je_anwendung_und_am_budgetrand():
    assert [M.cost_of(h, 100) for h in range(C.K)] == [1, 1, 1, 1, 1, 1, 1, 5]
    assert [M.cost_of(7, rest) for rest in (1, 2, 4, 5, 6)] == [1, 2, 4, 5, 5]
    # Folge swap, 2opt, 2opt_b5, insert, dbridge: 1 + 1 + 5 + 1 + 1 = 9 Auswertungen für 5 Anwendungen
    assert sum(M.cost_of(h, 100) for h in (0, 2, 7, 1, 6)) == 9
    # Budget 10: nach der Folge bleibt 1, die nächste 2opt_b5 zieht nur eine Stichprobe, Summe genau 10
    verbraucht = 0
    for h in (0, 2, 7, 1, 6, 7, 7):
        if verbraucht >= 10:
            break
        verbraucht += M.cost_of(h, 10 - verbraucht)
    assert verbraucht == 10


@pytest.mark.parametrize("h", range(C.K))
@pytest.mark.parametrize("n", [6, 7, 9, 10, 13, 30])
def test_delta_stimmt_mit_voller_neubewertung_und_ergebnis_ist_permutation(h, n):
    from conftest import zufallsinstanz

    D, t = zufallsinstanz(n, 100 + n)
    rng = BlockSplitMix64(1000 * n + h)
    for _ in range(300):
        delta, move = M.PROPOSE[h](t, D, n, rng)
        neu = list(t)
        M.apply_move(neu, h, move)
        assert check_feasible(neu, n)
        assert delta == pytest.approx(S.tour_cost(D, neu) - S.tour_cost(D, t), abs=1e-9)
        if _ % 7 == 0:
            t = neu                                    # auch auf veränderten Touren prüfen


@pytest.mark.parametrize("h", range(C.K))
def test_vorschlag_aendert_die_tour_nicht_und_jede_zugart_wirkt(h):
    """Zweig-Test: jede Zugart erzeugt auf mindestens einer Tour eine andere Tour als jede andere Zugart (keine tote Variante)."""
    from conftest import zufallsinstanz

    D, t = zufallsinstanz(12, 5)
    vorher = list(t)
    rng = BlockSplitMix64(50 + h)
    ergebnisse = set()
    for _ in range(200):
        _, move = M.PROPOSE[h](t, D, 12, rng)
        assert t == vorher
        neu = list(t)
        M.apply_move(neu, h, move)
        ergebnisse.add(tuple(neu))
    assert tuple(vorher) not in ergebnisse or h in (4, 5)     # nur ein umgesetztes Stück kann wieder an seinem Platz landen
    assert len(ergebnisse) > 10


def test_2opt_lokal_dreht_hoechstens_acht_orte_um():
    from conftest import zufallsinstanz

    D, t = zufallsinstanz(30, 1)
    rng = BlockSplitMix64(3)
    laengen = set()
    for _ in range(2000):
        _, (i, j) = M.propose_2opt_lokal(t, D, 30, rng)
        laengen.add(j - i + 1)
    assert laengen == set(range(2, 9))
    D6, t6 = zufallsinstanz(6, 1)
    assert {m[1] - m[0] + 1 for m in (M.propose_2opt_lokal(t6, D6, 6, rng)[1] for _ in range(500))} == {2, 3, 4}
