"""Zugriff auf die eingefrorene Messung (zgm_band.json) und alle Zählungen, die README und App daraus nennen.

Die Datei erzeugt tools/zgm_make_band.py. Abstände in Prozent über dem besten bekannten Wert, je Instanz das Mittel über die Läufe;
Unterschiede sind gepaart über Instanzen, Intervalle 95-%-Bootstrap über Instanzen (zgm_stats.bootstrap_ci, SplitMix64).
Vorzeichen: „Menge gegen voll“ d = Abstand(voll) - Abstand(Menge), positiv = die Menge ist besser; „Gewinn der Lernregel“
g = Abstand(Zufallsauswahl) - Abstand(Regel) auf derselben Menge, positiv = die Regel ist besser."""

import itertools
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

import zgm_constants as C
import zgm_exact as X
import zgm_stats as ST

ORDNER = Path(__file__).resolve().parent
ZELLEN = tuple((akz, j) for akz in C.AKZEPTANZEN for j in range(len(C.STUFEN)))      # 9 Zellen: Akzeptanz x Budgetstufe
MENGEN_OHNE_VOLL = tuple(m for m in C.MENGEN if m != "voll")


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads((ORDNER / "zgm_band.json").read_text(encoding="utf-8"))


def gaps(akz: str, menge: str, regel: str, j: int) -> list[float]:
    """Abstände je Instanz an der Stufe j (0 = klein, 1 = mittel, 2 = groß)."""
    return [zeile[j] for zeile in load()["gap"][akz][menge][regel]]


def mean_gap(akz: str, menge: str, regel: str, j: int) -> float:
    return ST.mean(gaps(akz, menge, regel, j))


def _vergleich(a, b) -> dict:
    d = [x - y for x, y in zip(a, b, strict=True)]
    lo, hi = ST.bootstrap_ci(d, C.ZWECK_BOOT)
    return dict(d=ST.mean(d), lo=lo, hi=hi, m=len(d))


def klasse(d: float, lo: float, hi: float) -> str:
    """'plus' bei d >= 0,25 und Intervall über 0; 'minus' bei d <= -0,25 und Intervall unter 0; sonst 'rauschen'."""
    if d >= C.MARKE and lo > 0:
        return "plus"
    if d <= -C.MARKE and hi < 0:
        return "minus"
    return "rauschen"


@lru_cache(maxsize=None)
def set_vs_full(akz: str, menge: str, j: int, regel: str = "rand") -> dict:
    """Menge gegen die volle Menge unter derselben Auswahlregel: d = Abstand(voll) - Abstand(Menge), positiv = Menge besser."""
    r = _vergleich(gaps(akz, "voll", regel, j), gaps(akz, menge, regel, j))
    r["klasse"] = klasse(r["d"], r["lo"], r["hi"])
    return r


@lru_cache(maxsize=None)
def gain(akz: str, menge: str, regel: str, j: int) -> dict:
    """Gewinn der Lernregel auf der Menge: g = Abstand(Zufallsauswahl) - Abstand(Regel), positiv = Regel besser."""
    r = _vergleich(gaps(akz, menge, "rand", j), gaps(akz, menge, regel, j))
    r["klasse"] = klasse(r["d"], r["lo"], r["hi"])
    return r


@lru_cache(maxsize=None)
def t3_vs_rule(akz: str, regel: str, j: int) -> dict:
    """Feste Teilmenge T3 mit Zufallsauswahl gegen die Lernregel auf der vollen Menge: d = Abstand(Regel, voll) - Abstand(Zufall, T3)."""
    r = _vergleich(gaps(akz, "voll", regel, j), gaps(akz, "T3", "rand", j))
    r["klasse"] = klasse(r["d"], r["lo"], r["hi"])
    return r


# ---------------------------------------------------------------- Zählungen
def count_classes(rows) -> dict:
    out = {"plus": 0, "minus": 0, "rauschen": 0}
    for r in rows:
        out[r["klasse"]] += 1
    return out


def weak_rows(stufen=(0, 1, 2)) -> list[dict]:
    """Je eine der sechs Zugarten außer 2opt und 2opt_b5 weglassen: 6 Mengen x 3 Akzeptanzen x Stufen."""
    return [dict(set_vs_full(akz, m, j), akz=akz, menge=m, j=j) for akz in C.AKZEPTANZEN for j in stufen for m in C.SCHWACHE_EINZELN]


def set_rows(menge: str) -> list[dict]:
    """Eine Menge gegen die volle in allen 9 Zellen."""
    return [dict(set_vs_full(akz, menge, j), akz=akz, j=j) for akz, j in ZELLEN]


def gain_rows() -> list[dict]:
    """Alle 324 Gewinn-Intervalle: 12 Mengen x 3 Lernregeln x 9 Zellen."""
    return [dict(gain(akz, m, regel, j), akz=akz, j=j, menge=m, regel=regel) for akz, j in ZELLEN for m in C.MENGEN for regel in C.LERNREGELN]


def gain_summary() -> dict:
    rows = gain_rows()
    groesster = max(rows, key=lambda r: r["d"])
    kleinster = min(rows, key=lambda r: r["d"])
    return dict(n=len(rows), marke=sum(1 for r in rows if r["klasse"] == "plus"), unter_null=sum(1 for r in rows if r["hi"] < 0),
                verlust_marke=sum(1 for r in rows if r["klasse"] == "minus"), groesster=groesster, kleinster=kleinster)


OHNE_2OPT_ZUGART = ("ohne_2opt_Familie", "nur_schwache")      # die zwei Mengen ohne jede Zugart der 2-opt-Familie


@lru_cache(maxsize=None)
def cell_summary(akz: str, j: int) -> dict:
    """Je Zelle: Spannweite der Zufallsauswahl über die 12 Mengen, größter und kleinster Gewinn einer Lernregel über Mengen und Regeln."""
    mittel = {m: mean_gap(akz, m, "rand", j) for m in C.MENGEN}
    g = [dict(gain(akz, m, regel, j), menge=m, regel=regel) for m in C.MENGEN for regel in C.LERNREGELN]
    gp = max(g, key=lambda r: r["d"])
    gm = min(g, key=lambda r: r["d"])
    spann = max(mittel.values()) - min(mittel.values())
    mit2opt = [v for m, v in mittel.items() if m not in OHNE_2OPT_ZUGART]
    spann_mit_2opt = max(mit2opt) - min(mit2opt)
    return dict(spann=spann, spann_mit_2opt=spann_mit_2opt, beste=min(mittel, key=mittel.get), schlechteste=max(mittel, key=mittel.get), lo_gap=min(mittel.values()),
                hi_gap=max(mittel.values()), gplus=gp["d"], gplus_wo=(gp["menge"], gp["regel"]), gmin=gm["d"], gmin_wo=(gm["menge"], gm["regel"]),
                menge_mehr=spann >= C.SPANN_FAKTOR * max(gp["d"], C.MARKE))


# ---------------------------------------------------------------- Rangkorrelation Budgetanteil der Familie gegen Abstand
def ranks(werte) -> np.ndarray:
    """Ränge 1..n, Gleichstände bekommen den mittleren Rang."""
    x = np.asarray(werte, dtype=float)
    ordnung = np.argsort(x, kind="mergesort")
    r = np.empty(len(x))
    i = 0
    while i < len(x):
        k = i
        while k + 1 < len(x) and x[ordnung[k + 1]] == x[ordnung[i]]:
            k += 1
        r[ordnung[i:k + 1]] = (i + k) / 2.0 + 1.0
        i = k + 1
    return r


def spearman(a, b) -> float:
    """Rangkorrelation nach Spearman (Pearson-Korrelation der Ränge); 0.0, wenn eine Seite keine Streuung hat."""
    ra, rb = ranks(a), ranks(b)
    sa, sb = ra.std(), rb.std()
    if sa == 0 or sb == 0:
        return 0.0
    return float(((ra - ra.mean()) * (rb - rb.mean())).mean() / (sa * sb))


def family_share(menge: str) -> float:
    return float(X.share_of_family(C.MENGEN[menge]))


def spearman_cell(akz: str, j: int) -> float:
    """Über die 12 Mengen: Anteil der Auswertungen der 2-opt-Familie unter Zufallsauswahl gegen den mittleren Abstand der Zufallsauswahl."""
    namen = list(C.MENGEN)
    return spearman([family_share(m) for m in namen], [mean_gap(akz, m, "rand", j) for m in namen])


# ---------------------------------------------------------------- Einzelzugarten, Beiträge, Anwendungen, Pool
def single_mean(akz: str, h: int, j: int) -> float:
    return ST.mean(zeile[j] for zeile in load()["einzel"][akz][C.HNAMEN[h]])


def dominance(akz: str, j: int) -> dict:
    """Abstand der besseren der beiden 2-opt-Einzelzugarten (2opt, 2opt_b5) zur besten der übrigen sechs (positiv: 2-opt vorn)."""
    werte = [single_mean(akz, h, j) for h in range(C.K)]
    b2 = min(werte[C.H_2OPT], werte[C.H_2OPT_B5])
    rest = min(werte[h] for h in range(C.K) if h not in (C.H_2OPT, C.H_2OPT_B5))
    return dict(werte=werte, vorsprung=rest - b2, zwilling=abs(werte[C.H_2OPT] - werte[C.H_2OPT_B5]))


def contribution(akz: str, menge: str, regel: str, j: int) -> dict:
    """Anteile je Zugart am Beitrag zum Bestwert (Mittel der Anteile je Lauf) an der Stufe j und der Anteil der 2-opt-Familie."""
    b = load()["beitrag"][akz][menge][regel]
    e = b["anteile"][j]
    return dict(e=e, e_fam=sum(e[h] for h in C.FAMILIE_2OPT), laeufe=b["laeufe"][j])


def app_share(akz: str, menge: str, regel: str) -> list[float]:
    """Anteil der Anwendungen je Zugart (Summe über alle Läufe bis 400 n)."""
    a = load()["zaehler"][akz][menge][regel]["apps"]
    s = sum(a)
    return [x / s for x in a]


def eval_share(akz: str, menge: str, regel: str) -> list[float]:
    a = load()["zaehler"][akz][menge][regel]["evals"]
    s = sum(a)
    return [x / s for x in a]


@lru_cache(maxsize=None)
def applications_row(akz: str, menge: str, j: int) -> dict:
    """Zähleinheit Anwendungen: Menge gegen die volle Menge bei gleicher Zahl Anwendungen (Zufallsauswahl). Für Mengen ohne 2opt_b5
    ist eine Anwendung eine Auswertung: ihre Werte sind die der Hauptmessung."""
    data = load()["anwendungen"][akz]
    def werte(m):
        return [z[j] for z in data[m]] if m in data else gaps(akz, m, "rand", j)
    r = _vergleich(werte("voll"), werte(menge))
    r["klasse"] = klasse(r["d"], r["lo"], r["hi"])
    r["gap_voll"] = ST.mean(werte("voll"))
    r["gap_menge"] = ST.mean(werte(menge))
    return r


def pool_means() -> dict:
    """Mittlerer Abstand der 12 Einzelzugarten des erweiterten Pools bei 50 n unter ob und rr: {akz: {name: Abstand}}."""
    band = load()
    out = {}
    for akz in band["pool"]:
        d = {C.HNAMEN[h]: single_mean(akz, h, 0) for h in range(C.K)}
        d.update({name: ST.mean(v) for name, v in band["pool"][akz].items()})
        out[akz] = d
    return out


def pool_candidates(marke: float = C.POOL_MARKE) -> list[tuple]:
    """Teilmengen des erweiterten Pools mit mindestens 3 Zugarten, deren Einzelläufe sich in beiden Akzeptanzen um höchstens `marke`
    unterscheiden und deren beste um höchstens `marke` hinter der besten 2-opt-Einzelzugart liegt (vorab festgelegte Regel)."""
    mittel = pool_means()
    namen = list(next(iter(mittel.values())))
    out = []
    for r in range(3, len(namen) + 1):
        for teil in itertools.combinations(namen, r):
            ok = True
            for d in mittel.values():
                werte = [d[x] for x in teil]
                best2 = min(d["2opt"], d["2opt_b5"])
                if max(werte) - min(werte) > marke or min(werte) - best2 > marke:
                    ok = False
                    break
            if ok:
                out.append(teil)
    return out


def pool_closest() -> dict:
    """Je Akzeptanz: die drei besten Einzelzugarten des Pools und die Spannweite dieser drei (die engste denkbare Dreiermenge mit der besten)."""
    out = {}
    for akz, d in pool_means().items():
        rang = sorted(d, key=d.get)
        out[akz] = dict(rang=rang, spann3=d[rang[2]] - d[rang[0]], werte=d)
    return out
