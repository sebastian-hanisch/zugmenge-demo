"""Statistik: Abstand, gepaarte Differenz, Bootstrap-Intervall, Klassen an handgesetzten Werten."""

import pytest

import zgm_constants as C
import zgm_stats as ST


def test_abstand_in_prozent():
    assert ST.gap(105.0, 100.0) == pytest.approx(5.0)
    assert ST.gap(100.0, 100.0) == 0.0
    assert ST.gap(99.0, 100.0) == pytest.approx(-1.0)          # unterbotene Referenz: negativ, die App meldet das


def test_klasse_an_den_marken():
    assert ST.klasse(0.25, 0.01, 0.5) == "klar"                # Marke 0,25 gilt inklusive
    assert ST.klasse(-0.25, -0.5, -0.01) == "klar"
    assert ST.klasse(0.2499, 0.01, 0.5) == "klein"
    assert ST.klasse(0.5, -0.01, 1.0) == "gleich"              # Intervall mit 0
    assert ST.klasse(0.5, 0.0, 1.0) == "gleich"                # Grenze 0 zählt als „mit 0“
    assert ST.klasse(0.0999, 0.01, 0.2) == "gleich"            # unter 0,10
    assert ST.klasse(0.10, 0.01, 0.2) == "klein"               # genau 0,10 ist nicht mehr „gleich“
    assert ST.klasse(-0.15, -0.2, -0.1) == "klein"
    assert (C.MARKE_KLAR, C.MARKE_GLEICH) == (0.25, 0.10)


def test_bootstrap_intervall():
    assert ST.bootstrap_ci([1.0], 7) is None and ST.bootstrap_ci([], 7) is None     # eine Instanz: kein Intervall
    assert ST.bootstrap_ci([2.0] * 10, 7) == pytest.approx((2.0, 2.0))
    werte = [float(i % 7) - 3.0 for i in range(70)]                                  # Mittel 0, Streuung 2
    lo, hi = ST.bootstrap_ci(werte, 7)
    assert lo < 0 < hi and 0.3 < hi < 0.7 and -0.7 < lo < -0.3                       # etwa +-1,96 * 2 / sqrt(70) = +-0,47
    assert ST.bootstrap_ci(werte, 7) == (lo, hi)                                     # fester Zufalls-Seed, feste Ausgabe
    assert ST.bootstrap_ci(werte, 8) != (lo, hi)


def test_compare_zaehlt_und_klassifiziert():
    einzel = [5.0, 2.0, 4.0, 6.0]
    misch = [4.0, 3.0, 7.0, 6.0]
    r = ST.compare(einzel, misch)
    assert r["v"] == pytest.approx((1 - 1 - 3 + 0) / 4) and r["besser"] == 1 and r["m"] == 4       # Gleichstand zählt nicht als besser
    assert r["lo"] <= r["v"] <= r["hi"] and r["klasse"] in ("klar", "gleich", "klein")
    eins = ST.compare([5.0], [4.0])
    assert eins["v"] == pytest.approx(1.0) and eins["lo"] is None and eins["klasse"] is None and eins["besser"] == 1
    leer = ST.compare([], [])
    assert leer["m"] == 0 and leer["v"] == 0.0 and leer["besser"] == 0
    with pytest.raises(ValueError):
        ST.paired_diff([1.0], [1.0, 2.0])
