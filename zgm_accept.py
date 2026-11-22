"""Akzeptanzregeln als reine Funktionen: jede entscheidet aus der Längenänderung und einem ausdrücklich übergebenen Zustand, ob der Zug bleibt.

In der App wählbar: nur besser (`accept_ob`), Rekord-zu-Rekord (`accept_rr`), Late Acceptance (`accept_la` mit `update_hist`). Sintflut
(`accept_gd`) und Annealing (`accept_sa`) brauchen das Gesamtbudget und stehen nur in der eingefrorenen Messung."""

import math

import zgm_constants as C

EPS = C.EPS

# Name der Einstellung -> (Regel, Länge der Historie); die Länge zählt nur für Late Acceptance
REGELN = {"ob": ("ob", 0), "rr": ("rr", 0), "la": ("la", C.LA_LEN), "la10": ("la", C.LA_LEN_KURZ), "gd": ("gd", 0), "sa": ("sa", 0)}
BUDGETFREI = ("ob", "rr", "la", "la10")     # das Ergebnis bis zu einer Auswertungszahl hängt nicht am Gesamtbudget


def accept_ob(delta: float) -> bool:
    """Nur besser: der Zug bleibt genau dann, wenn er die Tour streng verkürzt."""
    return delta < -EPS


def accept_rr(delta: float, neu: float, best: float, rho: float = C.RHO) -> bool:
    """Rekord-zu-Rekord: der Zug bleibt, wenn er nicht verlängert oder die neue Länge höchstens (1 + rho) mal der Bestwert ist."""
    return delta <= EPS or neu <= (1.0 + rho) * best


def new_hist(kosten0: float, laenge: int) -> list[float]:
    """Historie von Late Acceptance: anfangs `laenge` Einträge mit der Länge der Starttour."""
    return [kosten0] * laenge


def accept_la(delta: float, neu: float, hist: list[float], step: int) -> bool:
    """Late Acceptance: der Zug bleibt, wenn er nicht verlängert oder die neue Länge höchstens der Eintrag vor len(hist) Schritten ist."""
    return delta <= EPS or neu <= hist[step % len(hist)]


def update_hist(hist: list[float], step: int, kosten: float) -> None:
    """Nach jedem Schritt (auch nach einem abgelehnten) überschreibt die aktuelle Länge den ältesten Eintrag."""
    hist[step % len(hist)] = kosten


def accept_gd(delta: float, neu: float, kosten0: float, used: int, budget: int, gd_end: float = C.GD_END) -> bool:
    """Sintflut: der Pegel fällt linear in den verbrauchten Auswertungen von der Startlänge auf gd_end mal die Startlänge."""
    return delta <= EPS or neu <= kosten0 * (1.0 - (1.0 - gd_end) * used / budget)


def sa_temperature(used: int, budget: int, kante: float, t0: float = C.SA_T0, t1: float = C.SA_T1) -> float:
    """Annealing: Temperatur fällt geometrisch von t0 auf t1 (in Einheiten der mittleren Kantenlänge `kante` der Starttour)."""
    return t0 * kante * (t1 / t0) ** (used / budget)


def accept_sa(delta: float, temperatur: float, u: float) -> bool:
    """Annealing (Metropolis): ein verlängernder Zug bleibt mit Wahrscheinlichkeit exp(-delta / Temperatur); u ist die Gleichverteilte."""
    return delta <= EPS or u < math.exp(-delta / temperatur)
