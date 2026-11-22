"""Akzeptanzregeln an der Delta-Folge des Handbeispiels: Start 28, Änderungen +2, -1, +0,5, -2, +1, +0,2.

Handrechnung (Late Acceptance mit L = 3, Rekord-zu-Rekord mit 1 %):
  nur besser:        nimmt Schritt 2 und 4                    -> Längen 28, 27, 27, 25, 25, 25
  Rekord-zu-Rekord:  nimmt 2, 4 und 6 (25,2 <= 1,01 * 25)     -> 28, 27, 27, 25, 25, 25,2   (Schritt 3: 27,5 > 27,27)
  Late Acceptance:   nimmt 2 bis 6 (Historie 28, 28, 28)      -> 28, 27, 27,5, 25,5, 26,5, 26,7"""

import math

import pytest

import zgm_accept as AC
import zgm_constants as C

DELTAS = [2.0, -1.0, 0.5, -2.0, 1.0, 0.2]


def _folge(regel, laenge=3):
    cost = 28.0
    best = cost
    hist = AC.new_hist(cost, laenge)
    out = []
    for step, d in enumerate(DELTAS):
        neu = cost + d
        if regel == "ob":
            ok = AC.accept_ob(d)
        elif regel == "rr":
            ok = AC.accept_rr(d, neu, best)
        else:
            ok = AC.accept_la(d, neu, hist, step)
        if ok:
            cost = neu
            best = min(best, cost)
        if regel == "la":
            AC.update_hist(hist, step, cost)
        out.append((ok, cost))
    return out, best


def test_nur_besser():
    folge, best = _folge("ob")
    assert [ok for ok, _ in folge] == [False, True, False, True, False, False]
    assert [c for _, c in folge] == pytest.approx([28, 27, 27, 25, 25, 25])
    assert best == pytest.approx(25.0)


def test_rekord_zu_rekord():
    folge, best = _folge("rr")
    assert [ok for ok, _ in folge] == [False, True, False, True, False, True]
    assert [c for _, c in folge] == pytest.approx([28, 27, 27, 25, 25, 25.2])
    assert best == pytest.approx(25.0)


def test_late_acceptance():
    folge, best = _folge("la")
    assert [ok for ok, _ in folge] == [False, True, True, True, True, True]
    assert [c for _, c in folge] == pytest.approx([28, 27, 27.5, 25.5, 26.5, 26.7])
    assert best == pytest.approx(25.5)                       # Bestwert schlechter als bei nur besser (25), Endstand 26,7 gegen 25


def test_grenzen_der_regeln_sind_inklusive_wie_dokumentiert():
    assert not AC.accept_ob(0.0) and not AC.accept_ob(-C.EPS) and AC.accept_ob(-2 * C.EPS)     # streng besser
    assert AC.accept_rr(0.0, 30.0, 20.0) and AC.accept_rr(C.EPS, 30.0, 20.0)                  # gleich lang bleibt immer
    assert AC.accept_rr(1.0, 101.0, 100.0) and not AC.accept_rr(1.0, 101.0001, 100.0)         # genau (1 + rho) * Bestwert bleibt
    hist = [10.0, 12.0]
    assert AC.accept_la(1.0, 12.0, hist, 1) and not AC.accept_la(1.0, 12.0001, hist, 1)       # genau der Eintrag bleibt
    assert AC.accept_la(1.0, 10.0, hist, 2) and not AC.accept_la(1.0, 11.0, hist, 2)          # Schritt 2 liest wieder Eintrag 0


def test_historie_wird_auch_nach_ablehnung_ueberschrieben():
    hist = AC.new_hist(28.0, 3)
    AC.update_hist(hist, 0, 28.0)
    AC.update_hist(hist, 1, 27.0)
    AC.update_hist(hist, 5, 26.5)
    assert hist == [28.0, 27.0, 26.5]


def test_einstellungen_und_listenlaengen():
    assert AC.REGELN["la"] == ("la", 50) and AC.REGELN["la10"] == ("la", 10)
    assert set(C.AKZEPTANZEN) <= set(AC.REGELN)
    assert set(C.AKZEPTANZEN) <= set(AC.BUDGETFREI)


def test_sintflut_pegel_faellt_linear_auf_80_prozent():
    # Start 100, Budget 1000: nach 500 Auswertungen Pegel 90, am Ende 80
    assert AC.accept_gd(1.0, 90.0, 100.0, 500, 1000) and not AC.accept_gd(1.0, 90.01, 100.0, 500, 1000)
    assert AC.accept_gd(1.0, 80.0, 100.0, 1000, 1000) and not AC.accept_gd(1.0, 80.01, 100.0, 1000, 1000)
    assert AC.accept_gd(0.0, 500.0, 100.0, 1000, 1000)


def test_annealing_temperatur_und_metropolis():
    assert AC.sa_temperature(0, 1000, 10.0) == pytest.approx(3.0)            # 0,3 Kantenlängen
    assert AC.sa_temperature(1000, 1000, 10.0) == pytest.approx(0.03)        # 0,003 Kantenlängen
    assert AC.sa_temperature(500, 1000, 10.0) == pytest.approx(0.3)          # geometrisches Mittel
    p = math.exp(-1.0 / 2.0)
    assert AC.accept_sa(1.0, 2.0, p - 1e-9) and not AC.accept_sa(1.0, 2.0, p + 1e-9)
    assert AC.accept_sa(-1.0, 2.0, 0.999)
