"""Das Handbeispiel exakt (Brüche): sechs Städte, 60 Touren, Ziehungen, Verbesserungswahrscheinlichkeiten, K(S), lokale Optima, Markov-Kette.

Die Erwartungswerte stehen als Rechnung im Test (von Hand prüfbar); sie stammen aus der Planung (handbeispiele_02.py) und werden hier mit
dem Code der Demo nachgerechnet."""

import itertools
from fractions import Fraction as F

import pytest

import zgm_constants as C
import zgm_exact as X
from zgm_scenario import tour_cost

D = X.hand_matrix()
T0 = X.HAND_T0
TOUREN = X.all_tours(6)
P0 = X.improve_probs(T0, D)
MENGEN = {name: C.MENGEN[name] for name in X.HAND_MENGEN}


def L(t):
    return tour_cost(D, list(t))


def test_matrix_ist_symmetrisch_und_ganzzahlig():
    for a in range(6):
        assert X.HAND_D[a][a] == 0
        for b in range(6):
            assert X.HAND_D[a][b] == X.HAND_D[b][a] and isinstance(X.HAND_D[a][b], int)


def test_sechzig_touren_start_23_und_eindeutiges_optimum_19():
    assert len(TOUREN) == 60 == 120 // 2                                            # (6 - 1)! / 2
    assert L(T0) == 7 + 2 + 3 + 5 + 2 + 4 == 23
    assert L(X.HAND_OPT_TOUR) == 4 + 5 + 2 + 2 + 2 + 4 == 19
    assert [t for t in TOUREN if L(t) == min(L(x) for x in TOUREN)] == [X.HAND_OPT_TOUR]
    assert X.held_karp(D) == 19


def test_zahl_und_gewichte_der_ziehungen():
    # swap 6*3, insert 6*4, 2opt 3+3+3+2+1, 2opt_lokal 5+4+3, oropt2 5*3*2, oropt3 4*2*2, dbridge C(5,3)
    assert [len(X.move_draws(h, 6)) for h in range(7)] == [18, 24, 12, 12, 30, 16, 10]
    for h in range(7):
        assert sum(w for w, _ in X.move_draws(h, 6)) == 1
    gewichte = [w for w, _ in X.move_draws(2, 6)]
    # 2opt: i = 0, 1, 2 je Längen 2, 3, 4 mit 1/5 * 1/3; i = 3 Längen 2, 3 mit 1/5 * 1/2; i = 4 nur Länge 2 mit 1/5
    assert sorted(set(gewichte)) == [F(1, 15), F(1, 10), F(1, 5)]
    assert gewichte.count(F(1, 15)) == 9 and gewichte.count(F(1, 10)) == 2 and gewichte.count(F(1, 5)) == 1
    with pytest.raises(ValueError):
        X.move_draws(7, 6)


def test_ziehungen_bei_dreissig_und_sechzig_staedten():
    # Zahl der Ziehungen je Zugart bei n = 60 (die exakte Ansicht der App zählt sie alle durch)
    assert [len(X.move_draws(h, 60)) for h in range(7)] == [60 * 57, 60 * 58, 1767, 59 + 58 + 57 + 56 + 55 + 54 + 53, 59 * 57 * 2, 58 * 56 * 2, 32509]
    assert sum(len(X.move_draws(h, 60)) for h in range(7)) == 54790
    assert sum(w for w, _ in X.move_draws(3, 30)) == 1 and sum(w for w, _ in X.move_draws(2, 30)) == 1


def test_delta_formel_gegen_neuberechnung_auf_allen_touren():
    faelle = 0
    for t in TOUREN:
        alt = L(t)
        for h in range(7):
            for (_, mv), (_, neu) in zip(X.move_draws(h, 6), X.outcomes(h, t)):
                assert sorted(neu) == list(range(6))
                assert L(neu) - alt == X.move_delta(t, D, h, mv), (t, h, mv)
                faelle += 1
    assert faelle == 60 * 122 == 7320


def test_verbesserungswahrscheinlichkeiten_am_start():
    # insert 2 von 24 Ziehungen, oropt2 2 von 30, oropt3 1 von 16, dbridge 1 von 10; swap und die 2-opt-Familie: keine
    assert P0 == [0, F(2, 24), 0, 0, F(2, 30), F(1, 16), F(1, 10), 0]
    assert sum(P0) == F(5, 16)
    verb = sorted((C.HNAMEN[h], X.canon(neu), L(neu)) for h in range(7) for _, neu in X.outcomes(h, T0) if L(neu) < 23)
    assert verb == sorted([
        ("insert", (0, 1, 2, 4, 5, 3), 22), ("insert", (0, 3, 1, 2, 4, 5), 19), ("oropt2", (0, 3, 1, 2, 4, 5), 19), ("oropt2", (0, 1, 2, 4, 5, 3), 22),
        ("oropt3", (0, 1, 2, 4, 5, 3), 22), ("dbridge", (0, 3, 1, 2, 4, 5), 19)])
    assert sorted(X.move_delta(T0, D, 2, mv) for _, mv in X.move_draws(2, 6)) == [0, 0, 2, 3, 3, 3, 5, 5, 7, 11, 11, 12]
    assert min(X.move_delta(T0, D, 0, mv) for _, mv in X.move_draws(0, 6)) == 0


def test_einschritt_kennzahl_am_start():
    assert X.k_of_set(MENGEN["voll"], P0) == F(12) / F(5, 16) == F(192, 5)             # 38,4
    assert X.k_of_set(MENGEN["ohne_2opt_b5"], P0) == F(7) / F(5, 16) == F(112, 5)      # 22,4
    assert X.k_of_set(MENGEN["ohne_2opt_Familie"], P0) == F(5) / F(5, 16) == 16
    assert X.k_of_set(MENGEN["nur_schwache"], P0) == F(4) / F(11, 48) == F(192, 11)    # 17,45
    assert round(float(F(192, 11)), 2) == 17.45
    assert X.k_of_set(MENGEN["T3"], P0) is None                                        # die 2-opt-Familie kann T0 nicht verbessern
    assert [X.k_of_set((h,), P0) for h in (1, 4, 5, 6)] == [12, 15, 16, 10]


def test_2opt_b5_aus_2opt():
    t1 = (0, 2, 1, 3, 4, 5)
    p = X.improve_probs(t1, D)
    assert p[2] > 0 and p[7] == 1 - (1 - p[2]) ** 5
    gleit = X.improve_probs(t1, D, exakt=False)
    assert gleit == pytest.approx([float(x) for x in p], abs=1e-12)


def test_mediant_satz_und_regel_weglassen_fuer_alle_mengen_und_touren():
    n_mediant = n_regel = 0
    for t in TOUREN:
        p = X.improve_probs(t, D)
        for r in range(1, 9):
            for S_ in itertools.combinations(range(8), r):
                ks = X.k_of_set(S_, p)
                if ks is None:
                    continue
                assert ks >= min(F(C.KOSTEN[h]) / p[h] for h in S_ if p[h] > 0)     # Satz 1: nie schneller als die beste Zugart allein
                n_mediant += 1
                if r >= 2:
                    for h in S_:
                        rest = X.k_of_set([x for x in S_ if x != h], p)
                        besser = rest is not None and rest < ks
                        assert besser == (p[h] == 0 or F(C.KOSTEN[h]) / p[h] > ks), (t, S_, h)   # Satz 2
                        n_regel += 1
    assert (n_mediant, n_regel) == (15014, 59905)


def test_lokale_optima_je_zugart_und_schnittmengen():
    opt = [{t for t in TOUREN if X.is_local_optimum(t, D, (h,))} for h in range(8)]
    assert [len(s) for s in opt] == [6, 1, 2, 2, 2, 2, 6, 2]
    assert opt[7] == opt[2] and {L(t) for t in opt[2]} == {19, 23} and T0 in opt[2] and T0 in opt[3]
    n = 0
    for r in range(1, 9):
        for S_ in itertools.combinations(range(8), r):
            vereinigung = {t for t in TOUREN if X.is_local_optimum(t, D, S_)}
            assert vereinigung == set.intersection(*[opt[h] for h in S_])             # Satz 3
            if r < 8:
                for h in range(8):
                    if h not in S_:
                        assert len(vereinigung & opt[h]) <= len(vereinigung)          # Obermenge: höchstens so viele
            n += 1
    assert n == 255
    je_menge = {name: set.intersection(*[opt[h] for h in S_]) for name, S_ in MENGEN.items()}
    assert {k: len(v) for k, v in je_menge.items()} == {"voll": 1, "ohne_2opt_b5": 1, "ohne_2opt_Familie": 1, "nur_schwache": 1, "T3": 2}
    assert je_menge["voll"] == {X.HAND_OPT_TOUR} and je_menge["T3"] == {X.HAND_OPT_TOUR, T0}


def test_lokales_optimum_stimmt_mit_den_wahrscheinlichkeiten_ueberein():
    for t in TOUREN:
        p = X.improve_probs(t, D)
        for h in range(8):
            assert X.is_local_optimum(t, D, (h,)) == (p[h] == 0)


def test_erwartete_beste_laenge_der_ganzen_suche():
    e20 = [round(X.hand_expected_best(S_, 20), 3) for S_ in MENGEN.values()]
    e80 = [round(X.hand_expected_best(S_, 80), 3) for S_ in MENGEN.values()]
    assert e20 == [21.637, 21.051, 20.702, 20.844, 23.0]
    assert e80 == [19.611, 19.189, 19.132, 19.229, 23.0]
    assert [round(X.hand_expected_best(S_, 160, start=None), 3) for S_ in MENGEN.values()] == [19.016, 19.002, 19.005, 19.023, 19.619]
    assert [round(X.hand_expected_best(S_, 10, start=None), 3) for S_ in MENGEN.values()] == [22.769, 22.533, 22.658, 22.758, 23.170]


def test_anteil_der_familie_an_den_auswertungen():
    assert X.share_of_family(C.MENGEN["voll"]) == F(7, 12) and round(float(F(7, 12)), 3) == 0.583
    assert X.share_of_family(C.MENGEN["ohne_2opt_b5"]) == F(2, 7) and X.share_of_family(C.MENGEN["T3"]) == 1
    assert X.share_of_family(C.MENGEN["nur_schwache"]) == 0
    assert F(C.KOSTEN[7], sum(C.KOSTEN)) == F(5, 12)                                   # 2opt_b5 unter Zufallsauswahl: 41,7 % der Auswertungen


def test_an_welchen_touren_welche_menge_schneller_ist():
    """Die Aussage des Handbeispiel-Textes: K(T3) gegen K(ohne 2-opt-Familie) an allen 60 Touren."""
    t3_schneller = ohne_schneller = fertig = 0
    for t in TOUREN:
        p = X.improve_probs(t, D)
        a, b = X.k_of_set(C.T3, p), X.k_of_set(C.MENGEN["ohne_2opt_Familie"], p)
        if a is None and b is None:
            fertig += 1
        elif b is None or (a is not None and a < b):
            t3_schneller += 1
        elif a is None or b < a:
            ohne_schneller += 1
    assert (t3_schneller, ohne_schneller, fertig) == (5, 54, 1) and t3_schneller + ohne_schneller + fertig == 60
    import zgm_texts as T

    assert "an 5 der 60 Touren" in T.HAND_K_TEXT and "an 54 die Menge ohne die 2-opt-Familie" in T.HAND_K_TEXT
