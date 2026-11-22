"""Jede Zahl der README zur eingefrorenen Messung, nachgerechnet aus zgm_band.json (Zählungen exakt, Werte auf Rundung, Intervalle als Band).

Die README nennt Werte mit zwei Nachkommastellen: Toleranz 0,006. Bootstrap-Intervalle hängen an numpy-Perzentilen: Toleranz 0,02."""

import re
from pathlib import Path

import pytest

import zgm_band as B
import zgm_constants as C
import zgm_texts as T

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
W, I = 0.006, 0.02          # noqa: E741
OB, RR, LA = "ob", "rr", "la"


def w(x):
    return pytest.approx(x, abs=W)


def test_groesse_der_messung():
    meta = B.load()["meta"]
    assert meta["instanzen"] == 120 and meta["seeds"] == 3 and meta["auswertungen_gesamt"] == 1182600000
    assert "1 182 600 000 Auswertungen" in README and "**120 Instanzen**" in README
    assert B.load()["unterboten"] == 44 and "in 44 von 120 Instanzen" in README and "in 44 von 120 Instanzen" in T.ASSUMPTIONS_MARKDOWN
    assert 1200 * 5 * 1000 * (30 + 60) // 2 == 270000000 and "270 000 000" in README
    assert 12 * 3 * 9 == 324 and 6 * 9 == 54 and 400 * 30 == 12000 and 400 * 60 == 24000


TABELLE_B1 = {
    "voll": ((6.01, 3.45, 2.31), (7.68, 3.82, 1.98), (9.81, 3.89, 2.08)),
    "ohne_2opt": ((5.93, 3.42, 2.25), (7.41, 3.64, 1.89), (9.66, 3.89, 2.10)),
    "ohne_2opt_b5": ((7.14, 3.58, 2.12), (9.30, 4.51, 2.18), (9.61, 3.92, 1.98)),
    "ohne_2opt_Familie": ((10.82, 6.31, 4.07), (12.37, 7.96, 4.54), (12.44, 6.98, 4.11)),
    "nur_schwache": ((11.94, 7.85, 5.39), (13.27, 9.23, 5.74), (13.25, 8.54, 5.53)),
    "T3": ((5.33, 4.28, 4.15), (6.12, 3.34, 2.36), (10.25, 4.11, 2.66)),
}


def test_abstand_der_zufallsauswahl_je_menge():
    for menge, zeilen in TABELLE_B1.items():
        for akz, werte in zip((OB, RR, LA), zeilen):
            assert [B.mean_gap(akz, menge, "rand", j) for j in range(3)] == pytest.approx(list(werte), abs=W), (menge, akz)
            assert " / ".join(f"{x:.2f}".replace(".", ",") for x in werte) in README
    # Kernfrage: Spanne über die 12 Mengen bei kleinem Budget
    for akz, lo, hi in ((RR, 6.12, 13.27), (OB, 5.33, 11.94), (LA, 9.48, 13.25)):
        z = B.cell_summary(akz, 0)
        assert z["lo_gap"] == w(lo) and z["hi_gap"] == w(hi)


def test_eine_der_sechs_uebrigen_zugarten_weglassen():
    alle = B.weak_rows()
    assert B.count_classes(alle) == {"plus": 7, "minus": 4, "rauschen": 43}
    klein = B.weak_rows((0,))
    assert B.count_classes(klein) == {"plus": 5, "minus": 0, "rauschen": 13} and max(abs(r["d"]) for r in klein) == w(0.66)
    assert {(r["akz"], r["menge"]) for r in klein if r["klasse"] == "plus"} == {
        (OB, "ohne_swap"), (RR, "ohne_swap"), (RR, "ohne_oropt2"), (RR, "ohne_oropt3"), (RR, "ohne_dbridge")}
    minus = sorted((r["menge"], r["j"]) for r in alle if r["klasse"] == "minus")
    assert [m for m, _ in minus] == ["ohne_insert"] * 3 + ["ohne_oropt2"] and all(j >= 1 for _, j in minus)
    assert B.set_vs_full(RR, "ohne_dbridge", 0)["d"] == w(0.44)


def test_2opt_und_2opt_b5_weglassen():
    o2 = B.set_rows("ohne_2opt")
    assert B.count_classes(o2) == {"plus": 0, "minus": 0, "rauschen": 9} and max(abs(r["d"]) for r in o2) == w(0.27)
    assert [B.set_vs_full(a, "ohne_2opt", 0)["d"] for a in (OB, RR, LA)] == pytest.approx([0.08, 0.27, 0.14], abs=W)
    b5 = B.set_rows("ohne_2opt_b5")
    assert B.count_classes(b5) == {"plus": 0, "minus": 3, "rauschen": 6}
    assert {(r["akz"], r["j"]): round(r["d"], 2) for r in b5 if r["klasse"] == "minus"} == {(OB, 0): -1.13, (RR, 0): -1.62, (RR, 1): -0.69}
    assert B.set_vs_full(LA, "ohne_2opt_b5", 0)["d"] == w(0.19)


def test_familie_und_nur_schwache():
    fam, schwach = B.set_rows("ohne_2opt_Familie"), B.set_rows("nur_schwache")
    assert B.count_classes(fam)["minus"] == 9 and B.count_classes(schwach)["minus"] == 9
    assert (min(abs(r["d"]) for r in fam), max(abs(r["d"]) for r in fam)) == (w(1.76), w(4.81))
    assert (min(abs(r["d"]) for r in schwach), max(abs(r["d"]) for r in schwach)) == (w(3.08), w(5.93))
    assert [B.set_vs_full(a, "ohne_2opt_Familie", 0)["d"] for a in (OB, RR, LA)] == pytest.approx([-4.81, -4.68, -2.64], abs=W)
    assert [B.set_vs_full(a, "nur_schwache", 0)["d"] for a in (OB, RR, LA)] == pytest.approx([-5.93, -5.59, -3.44], abs=W)
    assert "in allen neun\nZellen hinten" in T.HAND_K_TEXT


def test_rangkorrelation_budgetanteil_gegen_abstand():
    rho = {z: B.spearman_cell(*z) for z in B.ZELLEN}
    assert rho[(OB, 0)] == w(-0.92) and rho[(RR, 0)] == w(-0.95) and rho[(RR, 1)] == w(-0.80)
    rest = [v for z, v in rho.items() if z not in ((OB, 0), (RR, 0), (RR, 1))]
    assert len(rest) == 6 and min(rest) == w(-0.51) and max(rest) == w(0.02)
    assert B.family_share("voll") == pytest.approx(7 / 12) and round(100 * 7 / 12, 1) == 58.3 and round(100 * 2 / 7, 1) == 28.6


def test_feste_teilmenge():
    t3 = B.set_rows("T3")
    assert B.count_classes(t3) == {"plus": 3, "minus": 5, "rauschen": 1}
    assert {(r["akz"], r["j"]): round(r["d"], 2) for r in t3 if r["klasse"] == "plus"} == {(OB, 0): 0.68, (RR, 0): 1.56, (RR, 1): 0.48}
    assert [(r["akz"], r["j"]) for r in t3 if r["klasse"] == "rauschen"] == [(LA, 1)]
    assert [B.set_vs_full(OB, "T3", j)["d"] for j in range(3)] == pytest.approx([0.68, -0.83, -1.84], abs=W)
    assert B.set_vs_full(LA, "T3", 0)["d"] == w(-0.44) and B.set_vs_full(LA, "T3", 2)["d"] == w(-0.58)
    assert B.mean_gap(OB, "T3", "rand", 2) == w(4.15) and B.mean_gap(OB, "voll", "rand", 2) == w(2.31)


def test_feste_teilmenge_gegen_lernregel_auf_allen_acht():
    klein = [B.t3_vs_rule(a, r, 0) for a in C.AKZEPTANZEN for r in C.LERNREGELN]
    assert sum(1 for r in klein if r["klasse"] == "plus") == 8
    assert B.t3_vs_rule(OB, "q", 0)["klasse"] == "rauschen" and B.t3_vs_rule(OB, "q", 0)["d"] == w(0.17)
    plus = [r["d"] for r in klein if r["klasse"] == "plus"]
    assert min(plus) == w(0.32) and max(plus) == w(1.13)
    gross = [B.t3_vs_rule(a, r, 2) for a in C.AKZEPTANZEN for r in C.LERNREGELN]
    assert sum(1 for r in gross if r["klasse"] == "minus") == 7 and min(r["d"] for r in gross) == w(-1.95)


def test_gewinn_der_lernregeln():
    gs = B.gain_summary()
    assert (gs["n"], gs["marke"], gs["verlust_marke"], gs["unter_null"]) == (324, 46, 93, 95)
    g, v = gs["groesster"], gs["kleinster"]
    assert (g["akz"], g["j"], g["menge"], g["regel"]) == (RR, 0, "ohne_2opt_b5", "laut") and g["d"] == w(1.67)
    assert (g["lo"], g["hi"]) == (pytest.approx(1.27, abs=I), pytest.approx(2.07, abs=I))
    assert (v["akz"], v["j"], v["menge"], v["regel"]) == (LA, 1, "ohne_swap", "cf") and v["d"] == w(-2.89)
    assert (v["lo"], v["hi"]) == (pytest.approx(-3.34, abs=I), pytest.approx(-2.44, abs=I))
    assert [B.gain(RR, "voll", r, 0)["d"] for r in C.LERNREGELN] == pytest.approx([1.15, 0.84, 0.88], abs=W)
    assert all(B.gain(RR, "voll", r, 0)["klasse"] == "plus" for r in C.LERNREGELN)
    assert [B.gain(LA, "voll", r, 0)["d"] for r in C.LERNREGELN] == pytest.approx([-1.57, -1.18, -1.36], abs=W)
    assert all(B.gain(LA, "voll", r, 0)["klasse"] == "minus" for r in C.LERNREGELN)
    # Zählung je Akzeptanz bei kleinem Budget (36 Intervalle = 12 Mengen x 3 Regeln)
    rr = [B.gain(RR, m, r, 0)["klasse"] for m in C.MENGEN for r in C.LERNREGELN]
    la = [B.gain(LA, m, r, 0)["klasse"] for m in C.MENGEN for r in C.LERNREGELN]
    assert rr.count("plus") == 21 and la.count("minus") == 27 and "21 von 36" in README and "27 von 36" in README
    assert B.cell_summary(LA, 0)["gmin"] == w(-2.08)


def test_gewinn_haengt_an_der_menge():
    ohne = [B.gain(LA, "ohne_2opt_b5", r, 0) for r in C.LERNREGELN]
    assert [r["d"] for r in ohne] == pytest.approx([0.30, 1.08, -0.09], abs=W) and [r["klasse"] for r in ohne] == ["rauschen", "plus", "rauschen"]
    assert (ohne[1]["lo"], ohne[1]["hi"]) == (pytest.approx(0.74, abs=I), pytest.approx(1.40, abs=I))
    zeilen = [r for r in B.gain_rows() if r["menge"] in ("ohne_2opt_Familie", "nur_schwache")]
    assert len(zeilen) == 54 and sum(1 for r in zeilen if r["klasse"] == "plus") == 4 and max(r["d"] for r in zeilen) == w(0.64)


def test_menge_bewegt_mehr_als_die_lernregel():
    zellen = [B.cell_summary(a, j) for a, j in B.ZELLEN]
    assert all(z["menge_mehr"] for z in zellen)
    assert (min(z["spann"] for z in zellen), max(z["spann"] for z in zellen)) == (w(3.27), w(7.15))
    assert (min(z["gplus"] for z in zellen), max(z["gplus"] for z in zellen)) == (w(0.14), w(1.67))
    lm = B.cell_summary(LA, 1)
    assert lm["gmin"] == w(-2.89) and lm["spann"] == w(5.10)


def test_anteile_der_anwendungen_und_beitraege():
    assert [100 * B.app_share(LA, "voll", r)[7] for r in C.REGELN] == pytest.approx([12.5, 37.9, 79.9, 23.5], abs=0.06)
    assert [100 * B.app_share(LA, "T3", r)[7] for r in C.REGELN] == pytest.approx([33.3, 58.4, 89.0, 41.6], abs=0.06)
    assert 100 * B.app_share(LA, "nur_schwache", "laut")[4] == pytest.approx(35.3, abs=0.06)
    assert 100 * B.app_share(LA, "ohne_2opt_Familie", "laut")[1] == pytest.approx(51.8, abs=0.06)
    assert [round(100 * B.contribution(a, "voll", "rand", 0)["e_fam"]) for a in (OB, RR, LA)] == [84, 84, 85]
    assert B.contribution(RR, "voll", "rand", 0)["laeufe"] == 360 and round(100 * B.contribution(RR, "voll", "rand", 0)["e"][7]) == 57
    ohne = [100 * B.contribution(a, "ohne_2opt_b5", "rand", 0)["e_fam"] for a in (OB, RR, LA)]
    assert 63.5 <= min(ohne) and max(ohne) <= 66.5
    mit_familie = [m for m in C.MENGEN if set(C.MENGEN[m]) & set(C.FAMILIE_2OPT)]
    assert len(mit_familie) == 10 and min(B.contribution(a, m, "rand", j)["e_fam"] for a, j in B.ZELLEN for m in mit_familie) > 0.60
    assert "in allen neun Zellen mehr als 60 % der Verbesserung" in T.ASSUMPTIONS_MARKDOWN
    assert f"({round(100 * B.contribution(RR, 'voll', 'rand', 0)['e'][7])} % mit allen acht" in C.PRESET_HELP["Die stärkste Zugart fehlt"]


def test_einzelzugarten():
    for akz, werte in ((OB, (15.95, 10.88, 6.21, 11.84, 12.16, 13.00, 17.19, 6.17)), (RR, (16.02, 12.38, 6.90, 11.45, 13.17, 13.90, 17.88, 6.82)),
                       (LA, (16.15, 12.44, 8.33, 11.88, 13.14, 13.86, 17.51, 11.65))):
        assert B.dominance(akz, 0)["werte"] == pytest.approx(list(werte), abs=W)
        assert " / ".join(f"{x:.2f}".replace(".", ",") for x in werte) in README
    dom = [B.dominance(a, j) for a, j in B.ZELLEN]
    assert (min(d["vorsprung"] for d in dom), max(d["vorsprung"] for d in dom)) == (w(2.52), w(4.82))
    assert max(B.dominance(a, j)["zwilling"] for a, j in B.ZELLEN if a != LA) == w(0.09)
    la = [B.dominance(LA, j)["zwilling"] for j in range(3)]
    assert (min(la), max(la)) == (w(1.04), w(3.32))
    # Passung zur Wurzel-Demo: bessere der beiden 2-opt-Zugarten gegen die Zufallsauswahl über alle acht bei 50 n
    assert (B.single_mean(RR, 7, 0), B.mean_gap(RR, "voll", "rand", 0)) == (w(6.82), w(7.68))
    assert (B.single_mean(LA, 2, 0), B.mean_gap(LA, "voll", "rand", 0)) == (w(8.33), w(9.81))
    assert (B.single_mean(OB, 7, 0), B.mean_gap(OB, "voll", "rand", 0)) == (w(6.17), w(6.01))


def test_zaehleinheit_anwendungen():
    assert [B.applications_row(a, "T3", 0)["d"] for a in (OB, RR, LA)] == pytest.approx([0.54, 2.35, 1.89], abs=W)
    assert all(B.applications_row(a, "T3", 0)["klasse"] == "plus" for a in C.AKZEPTANZEN)
    assert [B.applications_row(a, "ohne_2opt_b5", 0)["d"] for a in (OB, RR, LA)] == pytest.approx([-2.24, -3.21, -2.35], abs=W)
    assert all(B.applications_row(a, "ohne_2opt_b5", 0)["klasse"] == "minus" for a in C.AKZEPTANZEN)
    # Mengen ohne 2opt_b5: eine Anwendung ist eine Auswertung, die Werte der Menge sind die der Hauptmessung
    assert B.applications_row(RR, "ohne_2opt_Familie", 0)["gap_menge"] == pytest.approx(B.mean_gap(RR, "ohne_2opt_Familie", "rand", 0))


def test_keine_menge_mit_gleich_starken_zugarten():
    assert B.pool_candidates() == []
    naechste = B.pool_closest()
    assert min(naechste[a]["spann3"] for a in naechste) == w(4.63)
    assert all(set(naechste[a]["rang"][:2]) == {"2opt", "2opt_b5"} for a in naechste)
    mittel = B.pool_means()
    unterschied = max(abs(mittel[a][h + "_b5"] - mittel[a][h]) for a in mittel for h in ("swap", "insert", "oropt2", "oropt3"))
    assert unterschied == w(0.18) and len(mittel["ob"]) == 12
    assert "wurde mit den 12 geprüften Zugarten nicht gefunden" in T.band_zusatz()


def test_texte_aus_der_messung_nennen_die_gemessenen_zahlen():
    z = T.band_zaehlungen()
    for teil in ("43 ohne belegten Unterschied", "7 mit „ohne ist besser“", "4 mit „ohne ist schlechter“", "belegt sind dort 5 von 18", "0,66 Punkte",
                 "belegt schlechter in 9 von 9 Zellen, um 1,76 bis 4,81 Punkte", "belegt schlechter in 9 von 9, um 3,08 bis 5,93 Punkte",
                 "vorn in 3, hinten in 5, ohne belegten Unterschied in 1 von 9", "324 Intervalle): 46 mit belegtem Gewinn, 93 mit belegtem", "95 Intervalle ganz unter 0",
                 "Größter Gewinn +1,67", "größter Verlust −2,89", "in 9 von 9 Zellen", "zwischen 3,27 und 7,15 Punkten"):
        assert teil in z, teil
    assert "1,18 Milliarden Auswertungen" in T.band_kopf() and "120 Instanzen (3 Familien × n = 30 und 60 × 20 Instanzen), 3 Läufe" in T.band_kopf()
    hilfe = C.PRESET_HELP
    assert "−1,62 Prozentpunkte" in hilfe["Die stärkste Zugart fehlt"] and "+0,44 Prozentpunkte" in hilfe["Eine schwache Zugart fehlt"]
    assert "−4,68" in hilfe["Ohne die 2-opt-Familie"] and "−5,59" in hilfe["Nur schwache Zugarten"]
    assert "+0,68" in hilfe["Feste Teilmenge, kleines Budget"] and "1,84 Prozentpunkte hinter" in hilfe["Feste Teilmenge, großes Budget"]
    assert "Choice Function −1,57" in hilfe["Lernen unter Late Acceptance"] and "Lernautomat +1,08" in hilfe["Lernen ohne 2opt_b5"] and "Lernautomat −1,18" in hilfe["Lernen ohne 2opt_b5"]
    assert "Rechengrenze" not in hilfe["Feste Teilmenge, großes Budget"]


def test_annahmen_stehen_wortgleich_in_der_readme_und_formeln_haben_eigene_bloecke():
    assert T.ASSUMPTIONS_MARKDOWN in README
    assert T.FORMELN.count("$$") % 2 == 0 and T.FORMELN.count("$$") // 2 == 12
    for block in re.findall(r"\$\$(.+?)\$\$", T.FORMELN, flags=re.S):
        assert "%" not in block and "\n\n" not in block.strip()
    for teil in ("54 790 Ziehungen", "38,4", "22,4", "17,45", "21,637 / 19,611", "20,702 / 19,132", "6, 1, 2, 2, 2, 2, 6, 2"):
        assert teil in README, teil


def test_readme_nennt_keine_veralteten_zahlen_der_vormessung_als_befund():
    """Nach der Neumessung: die alten Zahlen stehen nur in der Tabelle der Korrekturen (linke Spalte), nicht in den Befunden."""
    befunde = README.split("## Befunde (gemessen, keine Behauptungen)")[1].split("## Ehrliche Grenzen")[0]
    for alt in ("1,22", "3,33", "25 von 324", "84 von 324", "2 von 18", "0,76", "45 von 54", "351", "13 Mengen", "385"):
        assert alt not in befunde, alt
    kern = README.split("## Kernfrage")[1].split("## Befunde und Korrekturen gegenüber der Vormessung")[0]
    for alt in ("1,22", "13,9", "7,0 und", "5,25", "2,15"):
        assert alt not in kern, alt


def test_testzahl_der_readme_stimmt_mit_der_suite(request):
    """Nur wenn die ganze Suite gesammelt wurde (nicht bei einem Lauf über eine einzelne Datei)."""
    gesammelt = {Path(str(item.fspath)).name for item in request.session.items}
    alle = {p.name for p in (ROOT / "tests").glob("test_*.py")}
    if gesammelt != alle or request.config.getoption("keyword") or request.config.getoption("markexpr"):
        pytest.skip("nicht die ganze Suite gesammelt")
    m = re.search(r"^(\d+) Tests \(`pytest --collect-only -q tests`\)", README, re.M)
    assert m and int(m.group(1)) == len(request.session.items)


def test_aussagenpruefung_einschraenkungen():
    """Zahlen der Einschränkungen nach der unabhängigen Prüfung: Bootstrap-Abhängigkeit, Spannweite über Mengen mit 2-opt-Zugart, Late Acceptance, EINFACH."""
    import zgm_stats as ST

    # 5 von 18 hängt an der Bootstrap-Ziehung: 40 andere Zufalls-Seeds geben 5 bis 7, nie ein belegter Verlust bei kleinem Budget
    zaehl = set()
    for seed in range(1, 41):
        plus = minus = 0
        for akz in C.AKZEPTANZEN:
            for m in C.SCHWACHE_EINZELN:
                d = [x - y for x, y in zip(B.gaps(akz, "voll", "rand", 0), B.gaps(akz, m, "rand", 0), strict=True)]
                lo, hi = ST.bootstrap_ci(d, seed)
                k = B.klasse(ST.mean(d), lo, hi)
                plus += k == "plus"
                minus += k == "minus"
        assert minus == 0
        zaehl.add(plus)
    assert zaehl <= {5, 6, 7} and 5 in zaehl and max(zaehl) > 5
    assert B.count_classes(B.weak_rows((0,)))["plus"] == 5
    assert "belegt sind dort 5 von 18 (je nach Bootstrap-Ziehung 5 bis 7)" in T.band_zaehlungen()

    # Spannweite über die zehn Mengen mit 2-opt-Zugart
    zellen = {(a, j): B.cell_summary(a, j) for a, j in B.ZELLEN}
    s10 = [z["spann_mit_2opt"] for z in zellen.values()]
    assert (min(s10), max(s10)) == (w(0.52), w(3.18))
    la = [zellen[LA, j]["spann_mit_2opt"] for j in (0, 1, 2)]
    assert (min(la), max(la)) == (w(0.68), w(0.77))
    assert zellen[LA, 0]["spann_mit_2opt"] == w(0.77) and zellen[LA, 0]["gplus"] == w(1.08) and zellen[LA, 0]["spann_mit_2opt"] < zellen[LA, 0]["gplus"]
    assert "zwischen 0,52 und 3,18 Punkten" in T.band_zaehlungen()

    # Late Acceptance: die nächste Zugart hinter der besten (2opt, Index 2) liegt 3,55 Punkte dahinter (nur die acht Zugarten gemessen)
    la_wert = {h: B.single_mean(LA, h, 0) for h in range(C.K)}
    assert min(la_wert, key=la_wert.get) == 2
    assert min(v - la_wert[2] for h, v in la_wert.items() if h not in (2, 7)) == w(3.55)
    assert "mindestens 3,55" in README and "unter nur besser und Rekord-zu-Rekord mindestens 4,63" in README

    # Einsteigertext: 4 belegte Gewinne in 54 Intervallen auf den zwei Mengen ohne 2-opt-Zugart
    rows = [B.gain(a, m, r, j) for a in C.AKZEPTANZEN for m in ("ohne_2opt_Familie", "nur_schwache") for r in C.LERNREGELN for j in (0, 1, 2)]
    assert len(rows) == 54 and sum(1 for r in rows if r["klasse"] == "plus") == 4
    assert "in 4 von 54 Fällen einen belegten Gewinn" in T.EINFACH
