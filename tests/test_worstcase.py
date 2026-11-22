"""Worst-Case am Reglermaximum: die teuerste Live-Rechnung je Kernfrage bleibt unter der Rechengrenze und endet (Timeout als Netz, keine Zeit-Assertion)."""

import threading

import zgm_constants as C
import zgm_evaluation as EV
import zgm_exact as X
import zgm_experiments as E

REFS = {"refs": {}}
TIMEOUT_S = 240


def _mit_timeout(fn):
    ergebnis = {}
    t = threading.Thread(target=lambda: ergebnis.update(wert=fn()), daemon=True)
    t.start()
    t.join(TIMEOUT_S)
    assert not t.is_alive(), "Rechnung am Reglermaximum hängt"
    return ergebnis["wert"]


def test_teuerster_vergleich_mit_lernregeln_am_reglermaximum():
    """n = 60, groß (400·n), Late Acceptance, vier Auswahlregeln: plan_runs kürzt auf 5 Instanzen und 1 Lauf (480 000 Auswertungen)."""
    plan = EV.plan_runs(60, 400, 4, C.INSTANZEN_MAX, C.LAEUFE_MAX)
    assert plan["kosten"] == 480000 <= C.RECHENGRENZE and plan["instanzen"] >= C.MIN_INSTANZEN
    live = _mit_timeout(lambda: E.measure(REFS, "cluster", 60, C.SEED_MAX, plan["instanzen"], plan["laeufe"], "la",
                                           {r: (C.ALLE_ZUGARTEN, r) for r in C.REGELN}, (400,)))
    assert live["kosten"] == plan["kosten"] and len(live["gaps"]["cf"]) == plan["instanzen"]


def test_neun_mengen_am_reglermaximum():
    plan = EV.plan_runs(60, 400, 9, C.INSTANZEN_MAX, C.LAEUFE_MAX)
    assert plan["kosten"] <= C.RECHENGRENZE
    varianten = {"voll": (C.ALLE_ZUGARTEN, "cf")}
    varianten.update({C.HNAMEN[h]: (tuple(x for x in range(C.K) if x != h), "cf") for h in range(C.K)})
    live = _mit_timeout(lambda: E.measure(REFS, "gitter", 60, 0, plan["instanzen"], plan["laeufe"], "rr", varianten, (400,)))
    assert live["kosten"] == plan["kosten"]


def test_exakte_zustandsansicht_bei_sechzig_staedten():
    r = E.run_set("gleich", 60, 0, 0, C.ALLE_ZUGARTEN, "rand", "rr", 3000)
    _, D = E.instance("gleich", 60, 0)
    p = _mit_timeout(lambda: X.improve_probs(r["tour"], D, exakt=False))
    assert len(p) == 8 and all(0.0 <= x <= 1.0 for x in p)
    assert sum(len(X.move_draws(h, 60)) for h in range(7)) == 54790          # so viele Ziehungen zählt die Ansicht je Zustand durch
