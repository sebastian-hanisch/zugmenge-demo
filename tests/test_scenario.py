"""Instanzen: Handbeispiel von Hand, die drei Familien, Startlösung."""

import math

import pytest

import zgm_constants as C
import zgm_scenario as S
from zgm_rng import SplitMix64


def test_handbeispiel_laengen(hand):
    D, start = hand
    assert S.tour_cost(D, start) == pytest.approx(8 + 4 + 5 + 4 + 4 + 3)        # 28
    assert S.tour_cost(D, [0, 1, 2, 3, 4, 5]) == pytest.approx(4 + 4 + 3 + 4 + 4 + 3)   # 22, Umfang des Rechtecks
    assert D[1][3] == pytest.approx(5.0) and D[0][2] == pytest.approx(8.0)


@pytest.mark.parametrize("familie", C.FAMILIEN)
@pytest.mark.parametrize("n", C.N_GEMESSEN)
def test_instanz_hat_n_orte_und_eine_symmetrische_matrix(familie, n):
    punkte, D = S.make_instance(familie, n, 3)
    assert len(punkte) == n == len(D) and all(len(z) == n for z in D)
    assert len(set(punkte)) == n
    for i in range(n):
        assert D[i][i] == 0.0
        for j in range(n):
            assert D[i][j] == D[j][i]
    assert D[0][1] == pytest.approx(math.dist(punkte[0], punkte[1]))


def test_gleicher_zufalls_seed_gleiche_instanz_anderer_andere():
    for familie in C.FAMILIEN:
        assert S.make_instance(familie, 30, 5)[0] == S.make_instance(familie, 30, 5)[0]
        assert S.make_instance(familie, 30, 5)[0] != S.make_instance(familie, 30, 6)[0]
    assert S.make_instance("gleich", 30, 5)[0] != S.make_instance("gitter", 30, 5)[0]


def test_gleichverteilte_orte_liegen_im_quadrat():
    for seed in range(20):
        for x, y in S.make_instance("gleich", 60, seed)[0]:
            assert 0.0 <= x < C.SEITE and 0.0 <= y < C.SEITE


@pytest.mark.parametrize("n", C.N_GEMESSEN)
def test_gitter_benutzt_keine_zelle_doppelt(n):
    for seed in range(20):
        g, zellen = S.gitter_zellen(n, SplitMix64(seed))
        assert g == math.ceil(math.sqrt(1.5 * n))
        assert len(zellen) == n == len(set(zellen)) and all(0 <= z < g * g for z in zellen)


def test_gruppen_sind_enger_als_gleichverteilte_orte():
    """Fünf Haufen mit Streuung 40: der mittlere Abstand zum nächsten Nachbarn ist kleiner als bei gleichverteilten Orten (20 Instanzen je Familie)."""
    def naechster(familie):
        werte = []
        for seed in range(20):
            _, D = S.make_instance(familie, 60, seed)
            werte += [min(D[i][j] for j in range(60) if j != i) for i in range(60)]
        return sum(werte) / len(werte)

    assert naechster("cluster") < 0.6 * naechster("gleich")


def test_naechster_nachbar_tour_von_hand(hand):
    D, _ = hand
    # ab Ort 0: nächster ist 5 (Abstand 3), dann 4 (4), dann 1 (3), dann 2 (4), dann 3 (3)
    assert S.nn_tour(D, 0) == [0, 5, 4, 1, 2, 3]
    assert sorted(S.nn_start(D, SplitMix64(1))) == list(range(6))


def test_startloesung_haengt_nur_an_instanz_und_lauf():
    _, D = S.make_instance("gleich", 30, 0)
    a = S.start_tour(D, "gleich", 30, 0, 0)
    assert a == S.start_tour(D, "gleich", 30, 0, 0) and sorted(a) == list(range(30))
    starts = {S.start_tour(D, "gleich", 30, 0, lauf)[0] for lauf in range(12)}
    assert len(starts) > 1
    assert S.start_tour(S.hand_instance()[1], C.FAMILIE_HAND, 6, 0, 3) == list(S.HAND_START)
