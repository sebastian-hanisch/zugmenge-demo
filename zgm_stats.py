"""Statistik des Vergleichs: Abstand zum besten bekannten Wert, gepaarte Differenz V, Bootstrap-Intervall über Instanzen, Klassen.

V = Abstand(Einzelheuristik) - Abstand(Zufallsmischung), je Instanz gepaart; positiv heißt: die Zufallsmischung ist besser."""

from functools import lru_cache

import numpy as np

import zgm_constants as C
from zgm_rngblock import uniform_block


def gap(laenge: float, referenz: float) -> float:
    """Abstand in Prozent über dem Referenzwert."""
    return 100.0 * (laenge - referenz) / referenz


def mean(werte) -> float:
    werte = list(werte)
    return sum(werte) / len(werte)


def paired_diff(einzel, mischung) -> list[float]:
    """V je Instanz: Abstand der Einzelheuristik minus Abstand der Mischung."""
    return [e - m for e, m in zip(einzel, mischung, strict=True)]


@lru_cache(maxsize=4)
def _boot_index(seed: int, m: int, ziehungen: int) -> np.ndarray:
    """Die gezogenen Instanz-Indizes (ziehungen x m); für gleiche Größe wiederverwendet, damit viele Vergleiche schnell bleiben."""
    return (uniform_block(seed, 0, ziehungen * m) * m).astype(np.int32).reshape(ziehungen, m)


def bootstrap_ci(werte, seed: int, ziehungen: int = C.BOOTSTRAP_ZIEHUNGEN) -> tuple[float, float] | None:
    """95-%-Intervall des Mittels (Perzentile 2,5 und 97,5 von `ziehungen` Ziehungen mit Zurücklegen über die Instanzen); None bei weniger als zwei Werten."""
    x = np.asarray(list(werte), dtype=np.float64)
    m = len(x)
    if m < 2:
        return None
    mittel = x[_boot_index(seed, m, ziehungen)].mean(axis=1)
    return float(np.percentile(mittel, 2.5)), float(np.percentile(mittel, 97.5))


def klasse(v: float, lo: float, hi: float) -> str:
    """'klar' bei |v| >= 0,25 und Intervall ohne 0; 'gleich' bei |v| < 0,10 oder Intervall mit 0; sonst 'klein'."""
    ohne_null = lo > 0 or hi < 0
    if abs(v) >= C.MARKE_KLAR and ohne_null:
        return "klar"
    if abs(v) < C.MARKE_GLEICH or not ohne_null:
        return "gleich"
    return "klein"


def count_better(v_je_instanz) -> int:
    """Zahl der Instanzen, in denen die Zufallsmischung besser ist (V > 0)."""
    return sum(1 for v in v_je_instanz if v > 0)


def compare(einzel, mischung, seed: int = C.ZWECK_BOOT) -> dict:
    """Vergleich einer Einzelheuristik mit der Mischung über Instanzen: V, Intervall, Klasse, Zählung."""
    v = paired_diff(einzel, mischung)
    m = len(v)
    vm = mean(v) if m else 0.0
    ci = bootstrap_ci(v, seed)
    if ci is None:
        return dict(v=vm, lo=None, hi=None, klasse=None, besser=count_better(v), m=m)
    return dict(v=vm, lo=ci[0], hi=ci[1], klasse=klasse(vm, ci[0], ci[1]), besser=count_better(v), m=m)
