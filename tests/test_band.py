"""Die eingefrorene Messung (zgm_band.json, zgm_refs.json): Aufbau, Konsistenz, Neu-Rechnen eines Ausschnitts als Band, Hilfsfunktionen."""

import sys
from pathlib import Path

import pytest

import zgm_band as B
import zgm_constants as C
import zgm_experiments as E
import zgm_scenario as S
from zgm_rngblock import BlockSplitMix64
from zgm_search import run_search

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import zgm_make_band as MB  # noqa: E402

BAND = B.load()
NI = BAND["meta"]["instanzen"]


def test_kopf_und_instanzen():
    meta = BAND["meta"]
    assert NI == 3 * 2 * C.BAND_INSTANZEN == 120 and meta["seeds"] == C.BAND_SEEDS == 3
    assert meta["stufen"] == list(C.STUFEN) and meta["akzeptanzen"] == list(C.AKZEPTANZEN) and meta["regeln"] == list(C.REGELN)
    assert {k: tuple(v) for k, v in meta["mengen"].items()} == C.MENGEN and len(meta["mengen"]) == 12
    assert BAND["instanzen"] == [[fam, n, idx] for fam in C.FAMILIEN for n in C.N_GEMESSEN for idx in range(C.BAND_INSTANZEN)]
    assert meta["python"] and meta["rechner"] and meta["auswertungen_gesamt"] > 10 ** 9
    assert len(BAND["ref"]) == NI and all(r > 0 for r in BAND["ref"])


def test_auswertungen_gesamt_ist_die_summe_der_teile():
    je_n = {30: 0, 60: 0}
    for n in je_n:
        haupt = 3 * 12 * 4 * 3 * 400 * n
        einzel = 3 * 8 * 3 * 400 * n
        anwendungen = 3 * 3 * (700 + 1100) * n
        pool = 2 * 4 * 3 * 50 * n
        je_n[n] = haupt + einzel + anwendungen + pool
    assert BAND["meta"]["auswertungen_gesamt"] == 60 * (je_n[30] + je_n[60])


def test_abstaende_sind_vollstaendig_nichtnegativ_und_monoton():
    for akz in C.AKZEPTANZEN:
        for menge in C.MENGEN:
            for regel in C.REGELN:
                zeilen = BAND["gap"][akz][menge][regel]
                assert len(zeilen) == NI
                for z in zeilen:
                    assert len(z) == 3 and z[0] >= z[1] >= z[2] >= 0.0
        for h in C.HNAMEN:
            assert len(BAND["einzel"][akz][h]) == NI and all(z[0] >= z[1] >= z[2] >= 0.0 for z in BAND["einzel"][akz][h])
        for menge in ("voll", "T3"):
            assert len(BAND["anwendungen"][akz][menge]) == NI and all(z[0] >= z[1] >= z[2] >= 0.0 for z in BAND["anwendungen"][akz][menge])
    assert set(BAND["pool"]) == {"ob", "rr"} and all(len(v) == NI for d in BAND["pool"].values() for v in d.values())


def test_referenz_ist_hoechstens_der_gespeicherte_wert():
    refs = E.load_json("zgm_refs.json")
    assert refs["meta"]["instanzen_je_zelle"] == C.INSTANZEN_REF == 200 and refs["meta"]["budget_faktor"] == 1000 and len(refs["meta"]["laeufe"]) == 5
    for fam in C.FAMILIEN:
        for n in C.N_GEMESSEN:
            assert len(refs["refs"][fam][str(n)]) == 200 and all(x > 0 for x in refs["refs"][fam][str(n)])
    tiefer = sum(1 for (fam, n, idx), r in zip(BAND["instanzen"], BAND["ref"]) if r < E.reference(refs, fam, n, idx) - 1e-6)
    assert all(r <= E.reference(refs, fam, n, idx) + 1e-6 for (fam, n, idx), r in zip(BAND["instanzen"], BAND["ref"]))
    assert tiefer == BAND["unterboten"]


def test_zaehler_und_beitraege():
    gesamt = 60 * 3 * 400 * 30 + 60 * 3 * 400 * 60          # Auswertungen je Zelle (Akzeptanz, Menge, Regel): 6 480 000
    for akz in C.AKZEPTANZEN:
        for menge, arms in C.MENGEN.items():
            for regel in C.REGELN:
                z = BAND["zaehler"][akz][menge][regel]
                assert sum(z["evals"]) == gesamt == 6480000
                assert all((z["apps"][h] > 0) == (h in arms) for h in range(C.K))
                assert all(z["succ"][h] <= z["apps"][h] for h in range(C.K))
                b = BAND["beitrag"][akz][menge][regel]
                for anteile, laeufe in zip(b["anteile"], b["laeufe"]):
                    assert 0 < laeufe <= NI * 3 and sum(anteile) == pytest.approx(1.0, abs=1e-3)
                    assert all(anteile[h] == 0 for h in range(C.K) if h not in arms)
                assert b["laeufe"][0] <= b["laeufe"][1] <= b["laeufe"][2]


def test_zufallsauswahl_verteilt_anwendungen_gleich_und_auswertungen_nach_kosten():
    for akz in C.AKZEPTANZEN:
        apps = B.app_share(akz, "voll", "rand")
        assert all(abs(a - 1 / 8) < 0.002 for a in apps)                                  # jede Zugart ein Achtel der Anwendungen
        assert B.eval_share(akz, "voll", "rand")[7] == pytest.approx(5 / 12, abs=0.003)   # 2opt_b5: 5 von 12 Kosteneinheiten
        fam = sum(B.eval_share(akz, "voll", "rand")[h] for h in C.FAMILIE_2OPT)
        assert fam == pytest.approx(B.family_share("voll"), abs=0.003) == pytest.approx(7 / 12, abs=0.003)


def test_neu_rechnen_eines_ausschnitts_als_band():
    """4 Instanzen x 2 Mengen (voll, T3), Zufallsauswahl, Rekord-zu-Rekord, alle drei Stufen: neu gerechnet gegen die Datei."""
    werte = MB.check_values(BAND)
    assert len(werte) == 8
    for fall, menge, neu, alt in werte:
        assert neu == pytest.approx(alt, abs=MB.CHECK_TOLERANZ), (fall, menge)


def test_neu_rechnen_mit_lernregel_und_einzelzugart():
    werte = MB.check_values(BAND, faelle=(("gitter", 30, 2),), mengen=("ohne_2opt_b5",), akz="la", regel="laut")
    assert werte[0][2] == pytest.approx(werte[0][3], abs=MB.CHECK_TOLERANZ)
    i = BAND["instanzen"].index(["cluster", 30, 4])
    v = [E.run_set("cluster", 30, 4, lauf, (1,), "rand", "ob", 400 * 30, checkpoints=(1500, 4500, 12000))["ck"] for lauf in range(3)]
    assert MB._gaps(v, BAND["ref"][i]) == pytest.approx(BAND["einzel"]["ob"]["insert"][i], abs=MB.CHECK_TOLERANZ)


def test_beste_von_fuenf_ist_fuer_2opt_genau_2opt_b5():
    for fam, n, idx in (("gleich", 30, 0), ("gitter", 60, 3)):
        _, D = E.instance(fam, n, idx)
        t0 = S.start_tour(D, fam, n, idx, 0)
        for akz in ("ob", "rr"):
            a = MB.run_best_of(D, t0, 50 * n + 3, 2, 5, akz, BlockSplitMix64(11))
            b = run_search(D, t0, 50 * n + 3, (7,), akz, BlockSplitMix64(11))["best"]
            assert a == b
    i = BAND["instanzen"].index(["gleich", 30, 0])
    _, D = E.instance("gleich", 30, 0)
    v = [MB.run_best_of(D, S.start_tour(D, "gleich", 30, 0, lauf), 1500, 1, 5, "rr", BlockSplitMix64(S.run_seed("gleich", 30, 0, lauf))) for lauf in range(3)]
    assert sum(100.0 * (x - BAND["ref"][i]) / BAND["ref"][i] for x in v) / 3 == pytest.approx(BAND["pool"]["rr"]["insert_b5"][i], abs=MB.CHECK_TOLERANZ)


def test_klasse_und_vergleich_von_hand():
    assert B.klasse(0.25, 0.01, 0.6) == "plus" and B.klasse(0.24, 0.01, 0.6) == "rauschen" and B.klasse(0.9, 0.0, 1.5) == "rauschen"
    assert B.klasse(-0.25, -0.6, -0.01) == "minus" and B.klasse(-0.9, -1.5, 0.0) == "rauschen"
    r = B.set_vs_full("rr", "T3", 0)
    d = [a - b for a, b in zip(B.gaps("rr", "voll", "rand", 0), B.gaps("rr", "T3", "rand", 0))]
    assert r["d"] == pytest.approx(sum(d) / NI) and r["lo"] <= r["d"] <= r["hi"] and r["m"] == NI
    g = B.gain("la", "voll", "cf", 0)
    assert g["d"] == pytest.approx(B.mean_gap("la", "voll", "rand", 0) - B.mean_gap("la", "voll", "cf", 0))
    assert len(B.gain_rows()) == 324 and len(B.weak_rows()) == 54 and len(B.weak_rows((0,))) == 18 and len(B.set_rows("T3")) == 9


def test_rangkorrelation_gegen_scipy_und_von_hand():
    from scipy.stats import spearmanr

    assert B.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0) and B.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert list(B.ranks([10, 20, 20, 5])) == [2.0, 3.5, 3.5, 1.0]                       # Gleichstand: mittlerer Rang
    assert B.spearman([1, 1, 1], [1, 2, 3]) == 0.0                                     # keine Streuung: 0 statt Division durch 0
    for akz, j in B.ZELLEN:
        namen = list(C.MENGEN)
        a = [B.family_share(m) for m in namen]
        b = [B.mean_gap(akz, m, "rand", j) for m in namen]
        assert B.spearman_cell(akz, j) == pytest.approx(float(spearmanr(a, b).statistic), abs=1e-9)


def test_regel_fuer_gleich_starke_zugarten(monkeypatch):
    """Die vorab festgelegte Regel an erfundenen Werten: drei Zugarten innerhalb von 1,0 Punkt und höchstens 1,0 hinter der besten 2-opt-Zugart."""
    werte = {"ob": {"2opt": 6.0, "2opt_b5": 6.2, "a": 6.5, "b": 6.9, "c": 9.0}, "rr": {"2opt": 7.0, "2opt_b5": 7.1, "a": 7.6, "b": 7.9, "c": 7.5}}
    monkeypatch.setattr(B, "pool_means", lambda: werte)
    kand = B.pool_candidates()
    assert ("2opt", "2opt_b5", "a") in kand and ("2opt", "2opt_b5", "a", "b") in kand and all("c" not in k for k in kand)
    werte["ob"]["b"] = 7.3                                                              # b fällt in einer Akzeptanz heraus
    assert ("2opt", "2opt_b5", "a", "b") not in B.pool_candidates() and ("2opt", "2opt_b5", "a") in B.pool_candidates()
    werte["rr"]["a"] = 8.2
    assert B.pool_candidates() == []
