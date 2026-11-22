"""Orakel-Tests: unabhängige Rechenwege gegen die Suche und die Zugarten der Demo (ORACLE-PLAYBOOK §2).

O1  Längenänderung jeder Zugart gegen volle Neubewertung und Permutationsprüfung nach jedem angenommenen Zug, auch mit gelernter Auswahl.
O2  Held-Karp (n = 11) gegen Aufzählung (n = 8); die Suche unterbietet das Optimum nie und erreicht es in einem Band der Läufe.
O3  Die Ziehung der App (SplitMix64) gegen die exakte Verteilung aus der Aufzählung: Anteil verbessernder Ziehungen im Band 4,5 Standardfehler.
O4  Die ganze Suche gegen die exakte Markov-Kette über die 60 Touren des Handbeispiels (anderer Rechenweg als die Schleife).
O5  Die Einschritt-Kennzahl K(S) gegen die gemessene Wartezeit bis zur ersten Verbesserung."""

import math

import pytest
from conftest import brute_force, zufallsinstanz

import zgm_constants as C
import zgm_exact as X
import zgm_experiments as E
import zgm_moves as M
import zgm_scenario as S
import zgm_select as SE
from zgm_rng import SplitMix64
from zgm_rngblock import BlockSplitMix64
from zgm_search import run_search

D6 = X.hand_matrix()
T0 = list(X.HAND_T0)


# ---------------------------------------------------------------- O1
@pytest.mark.parametrize("familie", C.FAMILIEN)
@pytest.mark.parametrize("n", C.N_GEMESSEN)
@pytest.mark.parametrize("regel", C.REGELN)
def test_o1_delta_und_permutation_in_jedem_angenommenen_zug(familie, n, regel):
    _, D = E.instance(familie, n, 1)
    t0 = S.start_tour(D, familie, n, 1, 0)
    for akz in C.AKZEPTANZEN:
        sel = SE.make_selector(regel, C.K, S.tour_cost(D, t0) / n)
        r = run_search(D, t0, 3000, C.ALLE_ZUGARTEN, akz, BlockSplitMix64(S.run_seed(familie, n, 1, 0)), selector=sel, check=True)
        assert r["used"] == 3000 and sum(r["evals"]) == 3000
        assert abs(S.tour_cost(D, r["tour"]) - r["final"]) < 1e-6 and r["best"] <= S.tour_cost(D, t0) + 1e-9


# ---------------------------------------------------------------- O2
def test_o2_held_karp_gegen_aufzaehlung():
    for seed in range(5):
        D, _ = zufallsinstanz(8, seed)
        assert X.held_karp(D) == pytest.approx(brute_force(D), rel=1e-12)


def test_o2_suche_unterbietet_das_optimum_nie_und_erreicht_es_meist():
    treffer = 0
    laeufe = 0
    for seed in range(12):
        D, _ = zufallsinstanz(11, 100 + seed)
        opt = X.held_karp(D)
        for lauf in range(3):
            t0 = S.nn_tour(D, lauf)
            best = run_search(D, t0, 5000, C.ALLE_ZUGARTEN, "la", BlockSplitMix64(1000 * seed + lauf))["best"]
            assert best >= opt - 1e-7
            treffer += best <= opt + 1e-7
            laeufe += 1
    assert laeufe == 36 and treffer >= 30          # Band: mindestens 30 von 36 Läufen erreichen das Optimum (gemessen 36)


# ---------------------------------------------------------------- O3
@pytest.mark.parametrize("tour", [(0, 1, 2, 3, 4, 5), (0, 2, 1, 3, 4, 5), (0, 4, 2, 5, 1, 3)])
def test_o3_ziehung_der_app_gegen_exakte_verteilung(tour):
    t = list(tour)
    p = X.improve_probs(t, D6)
    rng = SplitMix64(20261121)
    ns = 40000
    for h in range(8):
        k = sum(1 for _ in range(ns) if M.PROPOSE[h](t, D6, 6, rng)[0] < -C.EPS)
        pe = float(p[h])
        se = math.sqrt(max(pe * (1 - pe), 1e-12) / ns)
        assert abs(k / ns - pe) <= 4.5 * se + (1e-9 if pe in (0.0, 1.0) else 0), (C.HNAMEN[h], k / ns, pe)
        if pe == 0:
            assert k == 0


def test_o3_haeufigkeit_jedes_einzelnen_zugs():
    rng = SplitMix64(7)
    ns = 60000
    for h in range(7):
        exakt = {}
        for w, mv in X.move_draws(h, 6):
            exakt[mv] = exakt.get(mv, 0) + float(w)
        zahl = {}
        for _ in range(ns):
            mv = M.PROPOSE[h](T0, D6, 6, rng)[1]
            zahl[mv] = zahl.get(mv, 0) + 1
        assert set(zahl) <= set(exakt)
        for mv, pe in exakt.items():
            assert abs(zahl.get(mv, 0) / ns - pe) <= 4.5 * math.sqrt(pe * (1 - pe) / ns), (C.HNAMEN[h], mv)


# ---------------------------------------------------------------- O4
@pytest.mark.parametrize("name", ["voll", "ohne_2opt_Familie", "T3", "ohne_2opt_b5", "nur_schwache"])
@pytest.mark.parametrize("budget", [20, 80])
def test_o4_suchschleife_gegen_exakte_markov_kette(name, budget):
    menge = C.MENGEN[name]
    exakt = X.hand_expected_best(menge, budget)
    rng = BlockSplitMix64(7 + budget + len(menge))        # ein Strom für alle Läufe: unabhängige Läufe hintereinander
    nl = 4000
    werte = [run_search(D6, T0, budget, menge, "ob", rng)["best"] for _ in range(nl)]
    mittel = sum(werte) / nl
    se = max(math.sqrt(sum((w - mittel) ** 2 for w in werte) / (nl - 1) / nl), 1e-9)
    assert abs(mittel - exakt) <= 4.5 * se + 1e-9, (name, budget, mittel, exakt)


# ---------------------------------------------------------------- O5
@pytest.mark.parametrize("name,k_exakt", [("voll", 38.4), ("ohne_2opt_b5", 22.4), ("ohne_2opt_Familie", 16.0), ("nur_schwache", 192 / 11)])
def test_o5_einschritt_kennzahl_gegen_gemessene_wartezeit(name, k_exakt):
    """Satz 4: erwartete Auswertungen bis zur ersten Verbesserung ab T0 = K(S) (Zufallsauswahl, nur besser)."""
    menge = C.MENGEN[name]
    assert float(X.k_of_set(menge, X.improve_probs(T0, D6))) == pytest.approx(k_exakt)
    rng = BlockSplitMix64(99)
    nl = 4000
    warte = []
    for _ in range(nl):                               # Wartezeit direkt: Zugart ziehen, Vorschlag bewerten, bis einer streng verbessert
        used = 0
        while True:
            h = menge[int(rng.random() * len(menge))]
            used += C.KOSTEN[h]
            if M.PROPOSE[h](T0, D6, 6, rng)[0] < -C.EPS:
                break
        warte.append(used)
    mittel = sum(warte) / nl
    se = math.sqrt(sum((w - mittel) ** 2 for w in warte) / (nl - 1) / nl)
    assert abs(mittel - k_exakt) <= 4.5 * se, (name, mittel, k_exakt)


def test_o5_die_familie_haelt_den_start_fuer_fertig():
    r = run_search(D6, T0, 2000, C.T3, "ob", BlockSplitMix64(1), trace=True)
    assert r["trace"] == [] and r["best"] == 23 and sum(r["succ"]) == 0
