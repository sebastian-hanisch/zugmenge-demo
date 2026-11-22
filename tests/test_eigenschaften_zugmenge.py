"""Läufe mit festen Zufalls-Seeds, der Mitschreiber (Beitrag zum Bestwert) und die Live-Messung: Eigenschaften und Randfälle."""

import pytest

import zgm_constants as C
import zgm_exact as X
import zgm_experiments as E
import zgm_scenario as S
import zgm_select as SE
from zgm_beitrag import Recorder
from zgm_rngblock import BlockSplitMix64
from zgm_search import run_search

FAELLE = [(fam, n, idx) for fam in C.FAMILIEN for n in C.N_GEMESSEN for idx in (0, 5)]


def test_mitschreiber_von_hand():
    """Arme (2, 6), Startlänge 100: eine Verbesserung um 10 durch Arm 0, eine angenommene Verschlechterung um 4, dann 7 besser durch Arm 1."""
    rec = Recorder(SE.make_selector("rand", 2, 10.0), (2, 6), 100.0, checkpoints=(2, 3), app_checkpoints=(1, 4))
    rec.update(0, -10.0, 1, True)       # Bestwert 90: Beitrag von Zugart 2 = 10
    rec.update(1, 4.0, 1, True)         # Länge 94, Bestwert bleibt 90
    rec.update(1, -7.0, 1, True)        # Länge 87: neuer Bestwert, Beitrag von Zugart 6 = 90 - 87 = 3, brutto 7
    rec.update(0, -50.0, 1, False)      # abgelehnt: zählt nicht
    rec.finish()
    assert rec.gain_best[2] == 10.0 and rec.gain_best[6] == 3.0 and sum(rec.gain_best) == 100.0 - rec.best == 13.0
    assert rec.gain_brutto[2] == 10.0 and rec.gain_brutto[6] == 7.0
    assert rec.ck_gain[0][2] == 10.0 and rec.ck_gain[0][6] == 0.0 and rec.ck_gain[1][6] == 3.0
    assert rec.app_best == [90.0, 87.0] and rec.used == 4 and rec.apps == 4


@pytest.mark.parametrize("fam,n,idx", FAELLE)
def test_lauf_eigenschaften(fam, n, idx):
    st = E.checkpoints_for(n, (10, 30, 60))
    for akz in C.AKZEPTANZEN:
        for menge, regel in ((C.ALLE_ZUGARTEN, "rand"), (C.T3, "cf"), (C.MENGEN["ohne_2opt_b5"], "laut"), (C.MENGEN["nur_schwache"], "q")):
            r = E.run_set(fam, n, idx, 0, menge, regel, akz, st[-1], checkpoints=st)
            assert r["used"] == st[-1] == sum(r["evals"])                                   # Budget exakt
            assert all(r["apps"][h] == 0 for h in range(C.K) if h not in menge)             # nur Zugarten der Menge
            assert abs(sum(r["gain_best"]) - (r["start"] - r["best"])) < 1e-9               # Beiträge ergänzen sich exakt
            assert all(g >= 0 for g in r["gain_best"]) and all(b >= g - 1e-9 for b, g in zip(r["gain_brutto"], r["gain_best"]))
            assert r["start"] >= r["ck"][0] >= r["ck"][1] >= r["ck"][2] == r["best"]        # Bestwert monoton
            assert [abs(sum(g) - (r["start"] - c)) < 1e-9 for g, c in zip(r["ck_gain"], r["ck"])] == [True] * 3
            if akz == "ob":
                assert r["final"] == r["best"]


def test_zufallsauswahl_ist_bitgleich_zur_eingebauten_auswahl_der_suche():
    for fam, n, idx in FAELLE[:4]:
        _, D = E.instance(fam, n, idx)
        t0 = S.start_tour(D, fam, n, idx, 1)
        for arms in (C.ALLE_ZUGARTEN, C.T3, (2,), (7,)):
            a = run_search(D, t0, 40 * n, arms, "rr", BlockSplitMix64(S.run_seed(fam, n, idx, 1)), checkpoints=(20 * n,))
            b = E.run_set(fam, n, idx, 1, arms, "rand", "rr", 40 * n, checkpoints=(20 * n,))
            assert (a["best"], a["ck"], a["apps"], a["succ"]) == (b["best"], b["ck"], b["apps"], b["succ"])


def test_reihenfolge_der_mengenangabe_aendert_nichts_und_seed_schon():
    a = E.run_set("gleich", 30, 2, 0, (7, 2, 3, 3), "cf", "la", 900)
    b = E.run_set("gleich", 30, 2, 0, (2, 3, 7), "cf", "la", 900)
    assert a["best"] == b["best"] and a["apps"] == b["apps"] and a["arms"] == (2, 3, 7)
    c = E.run_set("gleich", 30, 2, 1, (2, 3, 7), "cf", "la", 900)
    assert (c["best"], c["apps"]) != (a["best"], a["apps"])
    assert E.run_set("gleich", 30, 2, 0, (2, 3, 7), "cf", "la", 900)["best"] == a["best"]


def test_leere_und_unbekannte_menge():
    with pytest.raises(ValueError):
        E.normalize_set(())
    with pytest.raises(ValueError):
        E.normalize_set((3, 8))
    assert E.set_name((7, 3, 2)) == "T3" and E.set_name((0, 1)) is None and E.set_label((0, 1)) == "{swap, insert}"
    assert E.set_label(C.ALLE_ZUGARTEN) == "alle acht"


def test_jede_zugart_wirkt():
    """Zweig-Test: die Menge ohne h liefert auf mindestens einer Instanz einen anderen Bestwert als die volle Menge (keine Nullspalte)."""
    for h in range(C.K):
        ohne = tuple(x for x in C.ALLE_ZUGARTEN if x != h)
        assert any(E.run_set(fam, 30, idx, 0, ohne, "rand", "rr", 600)["best"] != E.run_set(fam, 30, idx, 0, C.ALLE_ZUGARTEN, "rand", "rr", 600)["best"]
                   for fam in C.FAMILIEN for idx in (0, 1))


def test_jede_auswahlregel_wirkt():
    werte = {regel: tuple(E.run_set("cluster", 30, idx, 0, C.ALLE_ZUGARTEN, regel, "rr", 900)["best"] for idx in range(3)) for regel in C.REGELN}
    assert len(set(werte.values())) == len(C.REGELN)


def test_2opt_b5_am_budgetrand_und_einzelne_zugart():
    r = E.run_set("gleich", 30, 0, 0, (7,), "rand", "ob", 13)
    assert r["used"] == 13 and r["apps"][7] == 3 and r["evals"][7] == 13                    # 5 + 5 + 3: die letzte Anwendung ist gekürzt
    r = E.run_set("gleich", 30, 0, 0, (7,), "rand", "ob", 4)
    assert r["used"] == 4 and r["apps"][7] == 1
    r = E.run_set("gleich", 30, 0, 0, (0,), "q", "rr", 200)
    assert r["apps"][0] == 200 and sum(r["apps"]) == 200


def test_anwendungs_kontrollpunkte():
    r = E.run_set("gleich", 30, 1, 0, C.T3, "rand", "rr", 600, app_checkpoints=(50, 100, 10 ** 6))
    assert len(r["app_best"]) == 3 and r["start"] >= r["app_best"][0] >= r["app_best"][1] >= r["app_best"][2] == r["best"]
    ohne = E.run_set("gleich", 30, 1, 0, C.MENGEN["nur_schwache"], "rand", "rr", 300, checkpoints=(100, 300), app_checkpoints=(100, 300))
    assert ohne["app_best"] == ohne["ck"]                                                    # Kosten 1: Anwendungen = Auswertungen


def test_verschieben_und_strecken_der_instanz():
    """Verschieben aller Städte ändert Wahl und Verlauf nicht; Strecken mit s > 0 multipliziert die Längen mit s (bis auf Rundung)."""
    punkte, D = E.instance("gleich", 30, 3)
    t0 = S.start_tour(D, "gleich", 30, 3, 0)
    basis = run_search(D, t0, 1500, C.ALLE_ZUGARTEN, "ob", BlockSplitMix64(5))
    D2 = S.distance_matrix([(x * 2.0, y * 2.0) for x, y in punkte])                          # Faktor 2: exakt in Gleitkomma
    r2 = run_search(D2, t0, 1500, C.ALLE_ZUGARTEN, "ob", BlockSplitMix64(5))
    assert r2["best"] == pytest.approx(2.0 * basis["best"], rel=1e-12) and r2["apps"] == basis["apps"] and r2["tour"] == basis["tour"]
    D3 = S.distance_matrix([(x + 4096.0, y - 2048.0) for x, y in punkte])
    r3 = run_search(D3, t0, 1500, C.ALLE_ZUGARTEN, "ob", BlockSplitMix64(5))
    assert r3["best"] == pytest.approx(basis["best"], rel=1e-9) and r3["apps"] == basis["apps"]


def test_live_messung_von_hand_zusammengesetzt():
    refs = {"refs": {"gleich": {"30": [1.0] * 200}}}                                          # Referenz 1: jeder Abstand ist riesig, aber definiert
    live = E.measure(refs, "gleich", 30, 1, 3, 2, "rr", {"voll": (C.ALLE_ZUGARTEN, "rand"), "T3": (C.T3, "rand")}, (10, 20))
    assert live["m"] == 3 and len(live["gaps"]["voll"]) == 3 and len(live["gaps"]["voll"][0]) == 2 and live["kosten"] == 2 * 3 * 2 * 600
    r = [E.run_set("gleich", 30, 8, lauf, C.T3, "rand", "rr", 600, checkpoints=(300, 600)) for lauf in range(2)]
    erwartet = sum(100.0 * (x["ck"][1] - 1.0) / 1.0 for x in r) / 2
    assert live["gaps"]["T3"][0][1] == pytest.approx(erwartet) and live["unterboten"] == 0
    assert E.instance_indices(1, 3) == [8, 9, 10]
    z = live["zaehler"]["T3"]
    assert sum(z["evals"]) == 3 * 2 * 600 and all(z["apps"][h] == 0 for h in (0, 1, 4, 5, 6))
    sh = E.family_shares(z)
    assert sh["e_fam"] == pytest.approx(1.0) and sh["a_fam"] == pytest.approx(1.0) and sh["laeufe"] <= 6


def test_referenz_wird_im_klick_nachgezogen():
    assert E.effective_reference(100.0, [101.0, 99.0]) == (99.0, True)
    assert E.effective_reference(100.0, [101.0, 100.0]) == (100.0, False)
    assert E.effective_reference(None, [5.0, 7.0]) == (5.0, False)
    refs = {"refs": {"gleich": {"30": [10.0 ** 9] * 200}}}                                    # absichtlich viel zu groß: jeder Lauf unterbietet
    live = E.measure(refs, "gleich", 30, 0, 2, 1, "ob", {"a": (C.ALLE_ZUGARTEN, "rand")}, (10,))
    assert live["unterboten"] == 2 and all(g[0] == 0.0 for g in live["gaps"]["a"])
    assert E.reference(refs, "gleich", 60, 0) is None and E.reference(refs, "gleich", 30, 500) is None


def test_k_der_mischung_liegt_zwischen_den_k_der_zugarten():
    for fam, n, idx in FAELLE[:6]:
        r = E.run_set(fam, n, idx, 0, C.ALLE_ZUGARTEN, "rand", "rr", 50 * n)
        k = E.k_per_improvement(r)
        werte = [x for x in k["kh"] if x is not None]
        assert min(werte) - 1e-9 <= k["k"]                                      # nie besser als die beste Zugart
        if len(werte) == C.K:                                                   # ohne Erfolg ist K_h unendlich: dann gibt es keine obere Schranke
            assert k["k"] <= max(werte) + 1e-9
    leer = E.k_per_improvement(dict(evals=[5] * 8, succ=[0] * 8))
    assert leer["k"] is None and leer["kh"] == [None] * 8


def test_spur_und_zustand():
    r = E.run_set("gitter", 30, 4, 0, C.ALLE_ZUGARTEN, "rand", "rr", 1500, trace=True)
    _, D = E.instance("gitter", 30, 4)
    ende = E.replay(r["t0"], r["trace"], len(r["trace"]))
    assert ende == r["tour"] and abs(S.tour_cost(D, ende) - r["final"]) < 1e-6
    punkte = E.best_points(r["start"], r["trace"])
    assert punkte and punkte[-1][1] == r["best"] and all(a[1] > b[1] for a, b in zip(punkte, punkte[1:]))
    p = X.improve_probs(ende, D, exakt=False)
    assert all(0.0 <= x <= 1.0 for x in p) and p[7] == pytest.approx(1 - (1 - p[2]) ** 5)
    assert (sum(p) == 0) == X.is_local_optimum(ende, D, C.ALLE_ZUGARTEN)


def test_gepaarter_unterschied():
    r = E.diff_ci([3.0, 4.0, 5.0, 6.0], [1.0, 2.0, 3.0, 4.0])
    assert r["d"] == 2.0 and r["lo"] == 2.0 and r["hi"] == 2.0 and r["m"] == 4
    einer = E.diff_ci([3.0], [1.0])
    assert einer["d"] == 2.0 and einer["lo"] is None
