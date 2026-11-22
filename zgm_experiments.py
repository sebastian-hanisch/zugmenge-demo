"""Läufe mit den festen Zufalls-Seeds der Demo und die Live-Messungen der Experimente.

Dieselbe Funktion `run_set` rechnet die Live-Experimente der App und die eingefrorene Messung (tools/zgm_make_band.py). Startlösung und
Zufallsstrom hängen nur an (Familie, n, Instanz, Lauf), nicht an Zugmenge, Auswahlregel oder Akzeptanz: alle Varianten eines Laufs lesen
denselben Strom von vorn (gemeinsame Zufallszahlen)."""

import json
from functools import lru_cache
from pathlib import Path

import zgm_constants as C
import zgm_scenario as S
import zgm_select as SE
import zgm_stats as ST
from zgm_beitrag import Recorder
from zgm_moves import apply_move
from zgm_rngblock import BlockSplitMix64
from zgm_search import run_search

ORDNER = Path(__file__).resolve().parent


def normalize_set(menge) -> tuple[int, ...]:
    """Zugmenge als sortiertes Tupel ohne Doppelte; leer ist nicht erlaubt."""
    arms = tuple(sorted({int(h) for h in menge}))
    if not arms:
        raise ValueError("Die Zugmenge ist leer: mindestens eine Zugart wählen.")
    if arms[0] < 0 or arms[-1] >= C.K:
        raise ValueError(f"unbekannte Zugart in {arms}")
    return arms


def set_name(menge) -> str | None:
    """Name der Menge in der eingefrorenen Messung (eine der 12 benannten), sonst None."""
    arms = normalize_set(menge)
    for name, m in C.MENGEN.items():
        if tuple(m) == arms:
            return name
    return None


def set_label(menge) -> str:
    """Anzeigename: der Name der benannten Menge oder die Liste der Zugarten."""
    name = set_name(menge)
    return C.MENGEN_ANZEIGE[name] if name else "{" + ", ".join(C.HNAMEN[h] for h in normalize_set(menge)) + "}"


@lru_cache(maxsize=256)
def instance(familie: str, n: int, idx: int):
    return S.make_instance(familie, n, idx)


def run_set(familie, n, idx, lauf, menge, regel, akz, budget, checkpoints=(), trace=False, app_checkpoints=()):
    """Ein Lauf: Zugmenge `menge`, Auswahlregel `regel` (rand, cf, laut, q), Akzeptanz `akz`, `budget` Auswertungen.

    Rückgabe wie zgm_search.run_search, ergänzt um `start` (Länge der Starttour), `arms`, `gain_best`, `gain_brutto` (je Zugart, Länge 8),
    `ck_gain` (gain_best je Kontrollpunkt) und `app_best` (Bestwert nach den Anwendungszahlen in app_checkpoints)."""
    _, D = instance(familie, n, idx)
    t0 = S.start_tour(D, familie, n, idx, lauf)
    rng = BlockSplitMix64(S.run_seed(familie, n, idx, lauf))
    arms = normalize_set(menge)
    start = S.tour_cost(D, t0)
    rec = Recorder(SE.make_selector(regel, len(arms), start / n), arms, start, checkpoints, app_checkpoints)
    r = run_search(D, t0, budget, arms, akz, rng, checkpoints=checkpoints, trace=trace, selector=rec)
    rec.finish()
    r.update(start=start, arms=arms, gain_best=rec.gain_best, gain_brutto=rec.gain_brutto, ck_gain=rec.ck_gain, app_best=rec.app_best, t0=t0)
    return r


# ---------------------------------------------------------------- Referenzwerte
def load_json(name: str) -> dict:
    return json.loads((ORDNER / name).read_text(encoding="utf-8"))


def reference(refs: dict, familie: str, n: int, idx: int) -> float | None:
    """Bester bekannter Wert der Instanz aus zgm_refs.json; None, wenn keiner vorgerechnet ist."""
    werte = refs.get("refs", {}).get(familie, {}).get(str(n))
    if werte is None or not 0 <= idx < len(werte):
        return None
    return werte[idx]


def effective_reference(referenz: float | None, laengen) -> tuple[float, bool]:
    """Die Referenz eines Klicks: das Minimum aus dem gespeicherten Wert und allen Längen dieses Klicks. Rückgabe (Referenz, unterboten)."""
    kleinste = min(laengen)
    if referenz is None:
        return kleinste, False
    if kleinste < referenz - 1e-9:
        return kleinste, True
    return referenz, False


# ---------------------------------------------------------------- Live-Messung
def instance_indices(seed: int, m: int) -> list[int]:
    """Instanzen des Zufalls-Seeds s der App: 8 s bis 8 s + m - 1."""
    return [C.INSTANZEN_JE_SEED * seed + j for j in range(m)]


def checkpoints_for(n: int, stufen) -> tuple[int, ...]:
    return tuple(f * n for f in stufen)


def measure(refs: dict, familie: str, n: int, seed: int, m: int, laeufe: int, akz: str, varianten: dict, stufen) -> dict:
    """Live-Vergleich mehrerer Varianten auf denselben Instanzen, Starttouren und Zufallsströmen.

    varianten: {Schlüssel: (Zugmenge, Auswahlregel)}; stufen: aufsteigende Budgetfaktoren, ein Lauf bis zur größten mit Kontrollpunkten.
    Rückgabe: gaps[Schlüssel] = je Instanz die Abstände je Stufe (Mittel über die Läufe, gegen die Referenz des Klicks), dazu je Schlüssel
    die Zähler (apps, succ, evals, gain_best, gain_brutto als Summen; anteile = je Lauf die Anteile der Zugarten am Beitrag zum Bestwert),
    `unterboten` (Zahl der Instanzen, deren gespeicherte Referenz ein Lauf unterbot) und `kosten` (Auswertungen)."""
    ck = checkpoints_for(n, stufen)
    gaps = {key: [] for key in varianten}
    zaehler = {key: dict(apps=[0] * C.K, succ=[0] * C.K, evals=[0] * C.K, gain_best=[0.0] * C.K, gain_brutto=[0.0] * C.K, anteile=[], start=0.0, best=0.0)
               for key in varianten}
    unterboten = 0
    kosten = 0
    for idx in instance_indices(seed, m):
        laengen = {}
        for key, (menge, regel) in varianten.items():
            zeilen = []
            z = zaehler[key]
            for lauf in range(laeufe):
                r = run_set(familie, n, idx, lauf, menge, regel, akz, ck[-1], checkpoints=ck)
                zeilen.append(r["ck"])
                kosten += r["used"]
                for name in ("apps", "succ", "evals", "gain_best", "gain_brutto"):
                    z[name] = [a + b for a, b in zip(z[name], r[name])]
                z["start"] += r["start"]
                z["best"] += r["best"]
                gesamt = r["start"] - r["best"]
                if gesamt > 1e-9:
                    z["anteile"].append([g / gesamt for g in r["gain_best"]])
            laengen[key] = zeilen
        ref, u = effective_reference(reference(refs, familie, n, idx), [x for zeilen in laengen.values() for zeile in zeilen for x in zeile])
        unterboten += u
        for key, zeilen in laengen.items():
            gaps[key].append([ST.mean(ST.gap(zeile[j], ref) for zeile in zeilen) for j in range(len(ck))])
    return dict(gaps=gaps, zaehler=zaehler, unterboten=unterboten, kosten=kosten, stufen=tuple(stufen), m=m, laeufe=laeufe)


def level(live: dict, key: str, j: int = -1) -> list[float]:
    """Abstände einer Variante je Instanz an der Stufe j (Standard: die letzte)."""
    return [zeile[j] for zeile in live["gaps"][key]]


def diff_ci(a, b, seed: int = C.ZWECK_BOOT) -> dict:
    """Gepaarter Unterschied a - b je Instanz: Mittel, Bootstrap-Intervall über Instanzen (None bei weniger als zwei), Zahl der Instanzen."""
    d = [x - y for x, y in zip(a, b, strict=True)]
    ci = ST.bootstrap_ci(d, seed)
    return dict(d=ST.mean(d), lo=None if ci is None else ci[0], hi=None if ci is None else ci[1], m=len(d))


def family_shares(z: dict) -> dict:
    """Aus den Zählern einer Variante: Anteil je Zugart am Beitrag zum Bestwert (Mittel der Anteile je Lauf) und an den Auswertungen."""
    laeufe = len(z["anteile"])
    e = [ST.mean(a[h] for a in z["anteile"]) for h in range(C.K)] if laeufe else [0.0] * C.K
    ev = sum(z["evals"])
    a = [x / ev for x in z["evals"]] if ev else [0.0] * C.K
    return dict(e=e, a=a, e_fam=sum(e[h] for h in C.FAMILIE_2OPT), a_fam=sum(a[h] for h in C.FAMILIE_2OPT), laeufe=laeufe)


# ---------------------------------------------------------------- Einzellauf mit Spur (Experiment 1)
def replay(t0, spur, k: int) -> list[int]:
    """Tour nach den ersten k angenommenen Zügen der Spur."""
    t = list(t0)
    for _, h, move, _, _, _ in spur[:k]:
        apply_move(t, h, move)
    return t


def best_points(start: float, spur) -> list[tuple[int, float, int]]:
    """Punkte (Auswertungen, Bestwert, Zugart) je neuem Bestwert der Spur."""
    punkte = []
    best = start
    for used, h, _, _, _, b in spur:
        if b < best - 1e-12:
            best = b
            punkte.append((used, b, h))
    return punkte


def k_per_improvement(z: dict) -> dict:
    """Auswertungen je Verbesserung K_h je Zugart (None ohne Erfolg) und K der Mischung = alle Auswertungen / alle Erfolge."""
    kh = [(e / s if s else None) for e, s in zip(z["evals"], z["succ"])]
    alle = sum(z["succ"])
    return dict(kh=kh, k=(sum(z["evals"]) / alle if alle else None))
