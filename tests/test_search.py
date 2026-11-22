"""Die Suche: Zählung der Auswertungen, Kontrollpunkte, Spur, Eigenschaften (Determinismus, Monotonie, Invarianzen)."""

import pytest

import zgm_accept as AC
import zgm_constants as C
import zgm_moves as M
import zgm_scenario as S
from zgm_rngblock import BlockSplitMix64
from zgm_search import check_feasible, run_search

ALLE = C.ALLE_ZUGARTEN


def _instanz(familie="gleich", n=30, seed=0, lauf=0):
    _, D = S.make_instance(familie, n, seed)
    return D, S.start_tour(D, familie, n, seed, lauf)


@pytest.mark.parametrize("akz", list(AC.REGELN))
@pytest.mark.parametrize("arms", [ALLE, (7,), (2,), (0,), (6,)])
@pytest.mark.parametrize("budget", [1, 3, 5, 7, 300, 1001])
def test_die_suche_verbraucht_genau_das_budget(akz, arms, budget):
    D, t0 = _instanz("cluster", 20, 1)
    r = run_search(D, t0, budget, arms, akz, BlockSplitMix64(9), check=True)
    assert r["used"] == budget == sum(r["evals"])
    assert sum(r["apps"]) == r["steps"]
    assert all(r["apps"][h] == 0 for h in range(C.K) if h not in arms)                 # eine Einzelheuristik wählt nie eine andere Zugart
    assert all(r["evals"][h] == r["apps"][h] for h in range(7))
    assert r["apps"][7] <= r["evals"][7] <= 5 * r["apps"][7]
    assert check_feasible(r["tour"], 20) and S.tour_cost(D, r["tour"]) == pytest.approx(r["final"], abs=1e-6)
    assert r["best"] <= r["final"] + 1e-9 and r["best"] <= S.tour_cost(D, t0)
    assert all(r["succ"][h] <= r["apps"][h] and r["accd"][h] <= r["apps"][h] for h in range(C.K))


def test_2opt_b5_allein_am_budgetrand():
    D, t0 = _instanz()
    r = run_search(D, t0, 12, (7,), "ob", BlockSplitMix64(1))
    assert r["apps"][7] == 3 and r["evals"][7] == 12                                  # 5 + 5 + 2
    r = run_search(D, t0, 4, (7,), "ob", BlockSplitMix64(1))
    assert r["apps"][7] == 1 and r["used"] == 4                                       # Budget kleiner als der Preis einer Anwendung


def test_budget_null_laesst_die_starttour_stehen():
    D, t0 = _instanz()
    r = run_search(D, t0, 0, ALLE, "ob", BlockSplitMix64(1), checkpoints=(0, 10))
    assert r["used"] == 0 and r["steps"] == 0 and r["tour"] == t0 and r["ck"] == [r["best"], r["best"]]


def test_gleicher_zufalls_seed_gleiche_ausgabe_anderer_andere():
    D, t0 = _instanz()
    a = run_search(D, t0, 3000, ALLE, "rr", BlockSplitMix64(5))
    b = run_search(D, t0, 3000, ALLE, "rr", BlockSplitMix64(5))
    c = run_search(D, t0, 3000, ALLE, "rr", BlockSplitMix64(6))
    assert a == b
    assert a["apps"] != c["apps"]


@pytest.mark.parametrize("arms", [ALLE, (2,), (7,)])
def test_nur_besser_ist_monoton(arms):
    for seed in range(20):
        D, t0 = _instanz("gitter", 30, seed)
        r = run_search(D, t0, 1500, arms, "ob", BlockSplitMix64(seed), trace=True)
        assert r["final"] == pytest.approx(r["best"], abs=1e-9)
        laengen = [e[4] for e in r["trace"]]
        assert laengen == sorted(laengen, reverse=True) and all(e[3] < -C.EPS for e in r["trace"])
        assert r["accd"] == r["succ"]                                                 # angenommen wird genau jede strenge Verbesserung


@pytest.mark.parametrize("akz", AC.BUDGETFREI)
def test_groesseres_budget_verschlechtert_den_bestwert_nie(akz):
    for seed in range(20):
        D, t0 = _instanz("gleich", 30, seed)
        werte = [run_search(D, t0, b, ALLE, akz, BlockSplitMix64(100 + seed))["best"] for b in (300, 750, 1500, 3000)]
        assert all(x >= y - 1e-9 for x, y in zip(werte, werte[1:]))


@pytest.mark.parametrize("akz", AC.BUDGETFREI)
def test_kontrollpunkte_sind_der_bestwert_des_laengeren_laufs(akz):
    D, t0 = _instanz("gleich", 30, 4)
    ck = (750, 1500, 3000)
    lang = run_search(D, t0, 3000, (2,), akz, BlockSplitMix64(8), checkpoints=ck)
    assert len(lang["ck"]) == 3 and lang["ck"][-1] == lang["best"]
    for b, wert in zip(ck, lang["ck"]):                                               # 2opt kostet 1: Kontrollpunkt = Lauf mit genau diesem Budget
        assert run_search(D, t0, b, (2,), akz, BlockSplitMix64(8))["best"] == wert
    misch = run_search(D, t0, 3000, ALLE, akz, BlockSplitMix64(8), checkpoints=ck)
    assert misch["ck"] == sorted(misch["ck"], reverse=True)


def test_spur_laesst_sich_nachspielen():
    D, t0 = _instanz("cluster", 30, 2)
    r = run_search(D, t0, 3000, ALLE, "la10", BlockSplitMix64(3), trace=True)
    t = list(t0)
    cost = S.tour_cost(D, t)
    best = cost
    letzte = 0
    for used, h, move, delta, danach, best_danach in r["trace"]:
        M.apply_move(t, h, move)
        assert S.tour_cost(D, t) == pytest.approx(cost + delta, abs=1e-7) == pytest.approx(danach, abs=1e-7)
        cost = danach
        best = min(best, cost)
        assert best == pytest.approx(best_danach, abs=1e-9) and letzte < used <= 3000
        letzte = used
    assert t == r["tour"] and len(r["trace"]) == sum(r["accd"]) and best == pytest.approx(r["best"])


def test_skalieren_der_koordinaten_skaliert_nur_die_laengen():
    """Faktor 4 (Zweierpotenz, exakt in Gleitkomma): dieselben Entscheidungen, alle Längen mal 4; eps skaliert nicht mit, bei Abständen
    um 100 und Änderungen über 1e-6 kippt kein Vergleich."""
    punkte, D = S.make_instance("gleich", 30, 7)
    D4 = S.distance_matrix([(4 * x, 4 * y) for x, y in punkte])
    t0 = S.start_tour(D, "gleich", 30, 7, 0)
    for akz in AC.BUDGETFREI:
        a = run_search(D, t0, 3000, ALLE, akz, BlockSplitMix64(2))
        b = run_search(D4, t0, 3000, ALLE, akz, BlockSplitMix64(2))
        assert a["tour"] == b["tour"] and a["apps"] == b["apps"] and b["best"] == pytest.approx(4 * a["best"], rel=1e-12)


def test_spiegeln_der_koordinaten_aendert_nichts():
    punkte, D = S.make_instance("gitter", 30, 7)
    Ds = S.distance_matrix([(C.SEITE - x, y) for x, y in punkte])
    t0 = S.start_tour(D, "gitter", 30, 7, 0)
    a = run_search(D, t0, 3000, ALLE, "ob", BlockSplitMix64(2))
    b = run_search(Ds, t0, 3000, ALLE, "ob", BlockSplitMix64(2))
    assert b["best"] == pytest.approx(a["best"], rel=1e-9) and a["apps"] == b["apps"]


def test_umnummerieren_der_orte_aendert_nur_die_namen():
    """Mit festem Zufallsstrom hängen die Vorschläge an Positionen, nicht an Ortsnummern: die umnummerierte Instanz mit umnummerierter
    Starttour durchläuft dieselben Längen."""
    punkte, D = S.make_instance("gleich", 20, 3)
    perm = list(range(20))[::-1]
    D2 = S.distance_matrix([punkte[perm[i]] for i in range(20)])
    t0 = S.start_tour(D, "gleich", 20, 3, 0)
    t2 = [perm.index(c) for c in t0]
    a = run_search(D, t0, 2000, ALLE, "rr", BlockSplitMix64(4))
    b = run_search(D2, t2, 2000, ALLE, "rr", BlockSplitMix64(4))
    assert b["best"] == pytest.approx(a["best"], rel=1e-9) and [perm[c] for c in b["tour"]] == a["tour"]


def test_zufallsmischung_waehlt_gleichverteilt_ueber_die_zugarten():
    D, t0 = _instanz()
    r = run_search(D, t0, 60000, ALLE, "ob", BlockSplitMix64(11))
    schritte = r["steps"]
    for h in range(C.K):
        p = r["apps"][h] / schritte
        assert abs(p - 1 / 8) < 4.5 * (1 / 8 * 7 / 8 / schritte) ** 0.5
    # gleichverteilt über Anwendungen heißt nicht gleichverteilt über Auswertungen: 2opt_b5 bekommt 5 / 12 = 41,7 %
    assert r["evals"][7] / r["used"] == pytest.approx(5 / 12, abs=0.01)


def test_selector_haken_ersetzt_die_gleichverteilung():
    class NurZweiOpt:
        def __init__(self):
            self.gemeldet = []

        def choose(self, rng):
            return 1                                    # Index in arms, nicht die Zugart

        def update(self, index, delta, kosten, angenommen):
            self.gemeldet.append((index, kosten, angenommen, delta < -C.EPS))

    D, t0 = _instanz()
    sel = NurZweiOpt()
    r = run_search(D, t0, 500, (0, 2, 7), "ob", BlockSplitMix64(5), selector=sel)
    assert r["apps"][2] == 500 and sum(r["apps"]) == 500 and len(sel.gemeldet) == 500
    assert all(i == 1 and k == 1 for i, k, _, _ in sel.gemeldet)
    assert sum(1 for _, _, ok, _ in sel.gemeldet if ok) == r["accd"][2] == sum(1 for *_, besser in sel.gemeldet if besser)
    # derselbe Strom ohne Auswahl-Ziehung: identisch zur Einzelheuristik 2opt
    assert run_search(D, t0, 500, (2,), "ob", BlockSplitMix64(5))["tour"] == r["tour"]


def test_worst_case_am_reglermaximum_laeuft_durch():
    """n = 60, 400 n = 24 000 Auswertungen, alle Akzeptanzen der App: fängt Hänger, keine Zeitmessung."""
    D, t0 = _instanz("cluster", 60, 29)
    for akz in C.AKZEPTANZEN:
        r = run_search(D, t0, 400 * 60, ALLE, akz, BlockSplitMix64(1), checkpoints=tuple(f * 60 for f in C.STUFEN), trace=True)
        assert r["used"] == 24000 and len(r["ck"]) == len(C.STUFEN)
