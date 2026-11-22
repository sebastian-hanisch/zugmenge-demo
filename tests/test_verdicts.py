"""Verdikt-Funktionen: jede Schwelle, jeder Fall, Nenner 0 und zu wenige Instanzen; dazu die Schwellen auf den Rohzahlen der Vormessung."""

import re
from pathlib import Path

import pytest

import zgm_constants as C
import zgm_evaluation as EV

K = "Voraussetzung"


def test_zahlformate():
    assert EV.de(1.5) == "1,50" and EV.de_v(-0.25) == "−0,25" and EV.de_v(0.5, 1) == "+0,5" and EV.de_v(-0.001) == "0,00" and EV.de_v(0.004) == "0,00"
    assert EV.tausender(1500000) == "1 500 000" and EV.prozent(0.583, 1) == "58,3 %"
    assert "8 Instanzen mit 30 Städten, 1 Lauf je Instanz" in EV.kontext(8, 1, "rr", 50, 30) and "50·n = 1 500 Auswertungen" in EV.kontext(8, 1, "rr", 50, 30)
    assert "2 Läufe je Instanz" in EV.kontext(8, 2, "la", 400, 60)


# ---------------------------------------------------------------- Rechengrenze
def test_plan_runs():
    p = EV.plan_runs(30, 50, 2, 8, 1)
    assert (p["instanzen"], p["laeufe"], p["gekuerzt"], p["kosten"]) == (8, 1, False, 2 * 8 * 1500)
    p = EV.plan_runs(60, 400, 2, 8, 3)                       # 2 * 24 000 je Instanz und Lauf: erst die Läufe auf 1, dann reichen 8 Instanzen (384 000)
    assert (p["instanzen"], p["laeufe"], p["gekuerzt"], p["kosten"]) == (8, 1, True, 384000) and "Läufe je Instanz von 3 auf 1" in p["text"]
    p = EV.plan_runs(60, 400, 4, 8, 3)                       # 4 * 24 000 = 96 000: 5 Instanzen
    assert (p["instanzen"], p["laeufe"]) == (5, 1) and "Instanzen von 8 auf 5" in p["text"] and p["kosten"] <= C.RECHENGRENZE
    p = EV.plan_runs(60, 400, 9, 8, 3)                       # 9 * 24 000 = 216 000: 2 Instanzen, kein Urteil mehr
    assert p["instanzen"] == 2 < C.MIN_INSTANZEN
    p = EV.plan_runs(60, 400, 30, 8, 3)                      # auch eine Instanz sprengt die Grenze: es bleibt bei einer
    assert (p["instanzen"], p["laeufe"]) == (1, 1) and p["kosten"] > C.RECHENGRENZE


@pytest.mark.parametrize("n", C.N_GEMESSEN)
@pytest.mark.parametrize("f", C.STUFEN)
@pytest.mark.parametrize("varianten", [1, 2, 4, 9])
def test_plan_runs_haelt_die_grenze_an_jedem_reglerwert(n, f, varianten):
    for m in range(C.INSTANZEN_MIN, C.INSTANZEN_MAX + 1):
        for s in range(C.LAEUFE_MIN, C.LAEUFE_MAX + 1):
            p = EV.plan_runs(n, f, varianten, m, s)
            assert p["kosten"] <= C.RECHENGRENZE or (p["instanzen"], p["laeufe"]) == (1, 1)
            assert 1 <= p["instanzen"] <= m and 1 <= p["laeufe"] <= s


# ---------------------------------------------------------------- Kernfrage 1
def test_verdict_beitrag_schwellen():
    a = [1 / 12] * 7 + [5 / 12]
    voll = C.ALLE_ZUGARTEN
    e = [0.05, 0.10, 0.30, 0.05, 0.05, 0.05, 0.0, 0.40]     # Familie 0,30 + 0,05 + 0,40 = 0,75
    v = EV.verdict_beitrag(e, a, voll, 8, K)
    assert v["kind"] == "fam_liefert" and "75 %" in v["text"] and "58 %" in v["text"] and K in v["text"]
    e = [0.10, 0.20, 0.30, 0.0, 0.0, 0.0, 0.0, 0.40]         # genau 0,70
    assert EV.verdict_beitrag(e, a, voll, 8, K)["kind"] == "fam_liefert"
    e = [0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.0, 0.1]             # 0,40: gerade noch „teils“
    v = EV.verdict_beitrag(e, a, voll, 8, K)
    assert v["kind"] == "fam_teils" and "nur 40 %" in v["text"] and "swap 20 %" in v["text"]
    e = [0.3, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0, 0.1]             # 0,30
    assert EV.verdict_beitrag(e, a, voll, 8, K)["kind"] == "fam_wenig"
    e = [0.2, 0.5, 0.0, 0.0, 0.2, 0.1, 0.0, 0.0]
    v = EV.verdict_beitrag(e, a, (0, 1, 4, 5, 6), 8, K)
    assert v["kind"] == "fam_fehlt" and "insert" in v["text"] and "50 %" in v["text"]
    assert EV.verdict_beitrag([0.0] * 8, a, voll, 0, K)["kind"] == "keine_verbesserung"


def test_verdict_zustand_faelle():
    assert EV.verdict_zustand([0] * 8, C.ALLE_ZUGARTEN)["kind"] == "optimum"
    p0 = [0, 1 / 12, 0, 0, 1 / 15, 1 / 16, 1 / 10, 0]        # das Handbeispiel an T0
    v = EV.verdict_zustand(p0, C.ALLE_ZUGARTEN)
    assert v["kind"] == "fam_fertig" and "insert, oropt2, oropt3, dbridge" in v["text"]
    assert EV.verdict_zustand(p0, C.T3)["kind"] == "optimum"
    assert EV.verdict_zustand(p0, (1, 4, 5, 6))["kind"] == "alle_aktiv"
    v = EV.verdict_zustand(p0, (0, 1, 6))                    # keine Familie in der Menge, swap findet nichts
    assert v["kind"] == "teils" and "swap" in v["text"]
    assert EV.verdict_zustand([0.1] * 8, C.ALLE_ZUGARTEN)["kind"] == "alle_aktiv"
    v = EV.verdict_zustand([0.1, 0.1, 0.2, 0, 0.1, 0.1, 0.1, 0.5], C.ALLE_ZUGARTEN)
    assert v["kind"] == "teils" and "2opt_lokal" in v["text"]


# ---------------------------------------------------------------- Kernfrage 2 und 4
@pytest.mark.parametrize("d,lo,hi,kind", [
    (0.25, 0.01, 0.5, "hilft"), (0.24, 0.01, 0.5, "rauschen"), (0.6, -0.01, 1.2, "rauschen"), (0.6, 0.0, 1.2, "rauschen"),
    (-0.25, -0.5, -0.01, "schadet"), (-0.24, -0.5, -0.01, "rauschen"), (-0.9, -1.8, 0.02, "rauschen"), (0.0, 0.0, 0.0, "rauschen"),
])
def test_verdict_menge_und_lernregel_schwellen(d, lo, hi, kind):
    assert EV.verdict_menge(d, lo, hi, 8, "ohne dbridge", K)["kind"] == kind
    assert EV.verdict_lernregel(d, lo, hi, 8, "cf", K)["kind"] == kind


def test_verdict_menge_texte_und_zu_wenige_instanzen():
    v = EV.verdict_menge(-1.5, -2.07, -0.95, 8, "ohne 2opt_b5", K)
    assert "1,50 Prozentpunkte größer" in v["text"] and "−2,07 bis −0,95" in v["text"] and v["level"] == "warning" and K in v["text"]
    v = EV.verdict_menge(0.76, 0.16, 1.33, 8, "ohne oropt3", K)
    assert "0,76 Prozentpunkte kleiner" in v["text"] and v["level"] == "success"
    v = EV.verdict_menge(0.39, -0.14, 0.95, 8, "ohne dbridge", K)
    assert "+0,39" in v["text"] and "kein belegter Unterschied" in v["text"]
    for fn in (EV.verdict_menge, EV.verdict_lernregel):
        v = fn(-5.0, -6.0, -4.0, 3, "cf", K, 120)
        assert v["kind"] == "zu_wenig" and "mindestens 4" in v["text"] and "120 Instanzen" in v["text"]
    assert EV.verdict_menge(0.5, None, None, 8, "x", K)["kind"] == "rauschen"          # ohne Intervall kein Urteil
    v = EV.verdict_lernregel(-1.87, -2.47, -1.24, 8, "cf", K)
    assert v["text"].startswith("Choice Function verliert 1,87 Prozentpunkte")
    assert EV.verdict_lernregel(0.87, 0.44, 1.30, 8, "laut", K)["text"].startswith("Lernautomat gewinnt 0,87")


# ---------------------------------------------------------------- Kernfrage 3
def test_verdict_teilmenge_muster():
    plus, minus, null = (0.73, 0.13, 1.35), (-2.56, -3.0, -2.15), (0.1, -0.4, 0.6)
    v = EV.verdict_teilmenge([plus, null, minus], 8, "alle acht", K)
    assert v["kind"] == "kreuzung" and v["je_stufe"] == ["t3_vorn", "gleich", "s_vorn"] and "zwischen 50·n und 400·n" in v["text"]
    v = EV.verdict_teilmenge([plus, minus, minus], 8, "alle acht", K)
    assert v["kind"] == "kreuzung" and "zwischen 50·n und 150·n" in v["text"]
    v = EV.verdict_teilmenge([plus, plus, minus], 8, "alle acht", K)
    assert "zwischen 150·n und 400·n" in v["text"]
    assert EV.verdict_teilmenge([minus] * 3, 8, "alle acht", K)["kind"] == "s_immer"
    assert EV.verdict_teilmenge([plus] * 3, 8, "alle acht", K)["kind"] == "t3_immer"
    v = EV.verdict_teilmenge([plus, null, null], 8, "alle acht", K)
    assert v["kind"] == "gemischt" and "klein (50·n): feste Teilmenge vorn (+0,73)" in v["text"]
    assert EV.verdict_teilmenge([null] * 3, 8, "alle acht", K)["kind"] == "gemischt"
    assert EV.verdict_teilmenge([minus, null, plus], 8, "alle acht", K)["kind"] == "gemischt"
    assert EV.verdict_teilmenge([plus] * 3, 2, "alle acht", K, 120)["kind"] == "zu_wenig"


def test_verdict_menge_vs_lernen():
    v = EV.verdict_menge_vs_lernen(6.91, 1.22, -0.4, 12, K)
    assert v["kind"] == "menge_mehr" and "6,91" in v["text"] and "mehr als 1,22" in v["text"] and "verliert bis zu 0,40" in v["text"]
    assert "verliert" not in EV.verdict_menge_vs_lernen(3.0, 0.3, -0.1, 12, K)["text"]
    assert EV.verdict_menge_vs_lernen(0.5, 0.1, 0.0, 12, K)["kind"] == "menge_mehr"          # 0,5 >= 2 * max(0,1; 0,25)
    assert EV.verdict_menge_vs_lernen(0.49, 0.1, 0.0, 12, K)["kind"] == "gleich_gross"
    assert EV.verdict_menge_vs_lernen(1.0, 0.8, 0.0, 12, K)["kind"] == "gleich_gross"
    assert EV.verdict_menge_vs_lernen(0.5, 0.8, 0.0, 12, K)["kind"] == "lernen_mehr"
    assert EV.verdict_menge_vs_lernen(0.0, 0.0, 0.0, 12, K)["kind"] == "gleich_gross"        # Spannweite null: kein „Menge bewegt mehr“
    v = EV.verdict_menge_vs_lernen(4.0, -0.2, -3.3, 12, K)
    assert v["kind"] == "menge_mehr" and "keine der drei Lernregeln gewinnt" in v["text"] and "3,30" in v["text"]


# ---------------------------------------------------------------- O6: die Schwellen auf den Rohzahlen der Vormessung
ROH = Path(__file__).resolve().parent.parent.parent / "hyperheuristiken-planung" / "vormessung" / "out_m1b_analyse3.txt"
ZEILE = re.compile(
    r"^(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+) \|\s*([+-][\d.]+) \[\s*([+-][\d.]+),\s*([+-][\d.]+)\] \|"
    r" cf\s*([+-][\d.]+)\[\s*([+-][\d.]+),\s*([+-][\d.]+)\](.) laut\s*([+-][\d.]+)\[\s*([+-][\d.]+),\s*([+-][\d.]+)\](.) q\s*([+-][\d.]+)\[\s*([+-][\d.]+),\s*([+-][\d.]+)\](.)")
KOPF = re.compile(r"^==== Akzeptanz (\w+), Stufe (\w+) ")


def test_o6_schwellen_auf_den_zahlen_der_vormessung_falls_vorhanden():
    """Die Verdikt-Schwellen ergeben auf der Rohausgabe der Vormessung (numpy-Zufall, 60 Instanzen) die Zählungen des Plans."""
    if not ROH.exists():
        pytest.skip("Rohausgabe der Vormessung nicht vorhanden (CI ohne den Planungsordner)")
    zellen, cur = {}, None
    for zeile in ROH.read_text(encoding="utf-8").splitlines():
        kp = KOPF.match(zeile)
        if kp:
            cur = (kp.group(1), kp.group(2))
            zellen[cur] = {}
            continue
        m = ZEILE.match(zeile)
        if m and cur:
            g = m.groups()
            zellen[cur][g[0]] = dict(rand=float(g[1]), d=float(g[5]), lo=float(g[6]), hi=float(g[7]),
                                     gain=[(float(g[8]), float(g[9]), float(g[10])), (float(g[12]), float(g[13]), float(g[14])), (float(g[16]), float(g[17]), float(g[18]))])
    assert len(zellen) == 9 and all(len(v) == 12 for v in zellen.values())
    art = lambda z: EV.verdict_menge(z["d"], z["lo"], z["hi"], 60, "x", K)["kind"]   # noqa: E731
    schwach = ["ohne_swap", "ohne_insert", "ohne_2opt_lokal", "ohne_oropt2", "ohne_oropt3", "ohne_dbridge"]
    v54 = [art(zellen[k][s]) for k in zellen for s in schwach]
    assert (v54.count("hilft"), v54.count("schadet"), v54.count("rauschen")) == (3, 6, 45)
    assert all(art(zellen[k]["ohne_2opt_Familie"]) == "schadet" and art(zellen[k]["nur_schwache"]) == "schadet" for k in zellen)
    t3 = [art(zellen[k]["T3"]) for k in zellen]
    assert (t3.count("hilft"), t3.count("schadet"), t3.count("rauschen")) == (2, 5, 2)
    gewinne = [g for v in zellen.values() for z in v.values() for g in z["gain"]]
    assert len(gewinne) == 324
    assert sum(1 for g, lo, hi in gewinne if EV.verdict_lernregel(g, lo, hi, 60, "cf", K)["kind"] == "hilft") == 25
    assert sum(1 for g, lo, hi in gewinne if hi < 0) == 84
    for v in zellen.values():
        spann = max(z["rand"] for z in v.values()) - min(z["rand"] for z in v.values())
        gplus = max(g[0] for z in v.values() for g in z["gain"])
        gmin = min(g[0] for z in v.values() for g in z["gain"])
        assert EV.verdict_menge_vs_lernen(spann, gplus, gmin, 12, K)["kind"] == "menge_mehr"
