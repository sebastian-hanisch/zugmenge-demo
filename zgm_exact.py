"""Exakte Rechnungen am Zustand: alle Ziehungen einer Zugart mit ihren Wahrscheinlichkeiten, Verbesserungswahrscheinlichkeiten,
die Einschritt-Kennzahl K(S), lokale Optima, Held-Karp und die ganze Suche des Handbeispiels als Markov-Kette.

Kein Zufallsstrom. `outcomes` setzt die neue Tour aus der Beschreibung des Zugs neu zusammen (anderer Rechenweg als zgm_moves.apply_move);
`move_delta` rechnet die Längenänderung aus den Kanten. Handbeispiel: sechs Städte mit ganzzahliger Fahrzeitmatrix."""

import itertools
from fractions import Fraction
from functools import lru_cache

import numpy as np

import zgm_constants as C
from zgm_scenario import tour_cost

# Handbeispiel: Fahrzeitmatrix (symmetrisch, ganzzahlig), Starttour T0 mit Länge 23, eindeutiges Optimum mit Länge 19
HAND_D = (
    (0, 7, 8, 4, 7, 4),
    (7, 0, 2, 5, 8, 9),
    (8, 2, 0, 3, 2, 8),
    (4, 5, 3, 0, 5, 5),
    (7, 8, 2, 5, 0, 2),
    (4, 9, 8, 5, 2, 0),
)
HAND_T0 = (0, 1, 2, 3, 4, 5)
HAND_OPT_TOUR = (0, 3, 1, 2, 4, 5)
HAND_MENGEN = ("voll", "ohne_2opt_b5", "ohne_2opt_Familie", "nur_schwache", "T3")


def hand_matrix() -> list[list[float]]:
    """Die Fahrzeitmatrix des Handbeispiels als Liste von Listen (wie die Suche sie erwartet)."""
    return [[float(x) for x in zeile] for zeile in HAND_D]


def canon(t) -> tuple:
    """Kanonische Form einer Rundtour: Start bei Stadt 0, der kleinere Nachbar von 0 zuerst."""
    t = list(t)
    k = t.index(0)
    t = t[k:] + t[:k]
    if t[1] > t[-1]:
        t = [t[0]] + t[1:][::-1]
    return tuple(t)


def all_tours(n: int) -> list[tuple]:
    """Alle (n - 1)! / 2 Rundtouren in kanonischer Form."""
    return [(0,) + p for p in itertools.permutations(range(1, n)) if p[0] < p[-1]]


# ---------------------------------------------------------------- Ziehungen
@lru_cache(maxsize=32)
def move_draws(h: int, n: int) -> tuple:
    """Alle Ziehungen der Zugart h (0 bis 6) bei n Städten: Tupel (Wahrscheinlichkeit als Bruch, Zug im Format von zgm_moves.apply_move)."""
    out = []
    if h == 0:                                   # swap: i gleichverteilt, j = i + 2 + k (mod n), k in 0..n-4
        for i in range(n):
            for k in range(n - 3):
                out.append((Fraction(1, n * (n - 3)), (i, (i + 2 + k) % n)))
    elif h == 1:                                 # insert: Stadt an Position i hinter die Stadt an Position j = i + 1 + k (mod n), k in 0..n-3
        for i in range(n):
            for k in range(n - 2):
                out.append((Fraction(1, n * (n - 2)), (i, (i + 1 + k) % n)))
    elif h == 2:                                 # 2opt: i in 0..n-2, Länge gleichverteilt in 2..min(n - i, n - 2)
        for i in range(n - 1):
            maxl = min(n - i, n - 2)
            for laenge in range(2, maxl + 1):
                out.append((Fraction(1, (n - 1) * (maxl - 1)), (i, i + laenge - 1)))
    elif h == 3:                                 # 2opt_lokal: Länge in 2..min(8, n - 2), dann der Start gleichverteilt
        lmax = min(C.LOKAL_LMAX, n - 2)
        for laenge in range(2, lmax + 1):
            for i in range(n - laenge + 1):
                out.append((Fraction(1, (lmax - 1) * (n - laenge + 1)), (i, i + laenge - 1)))
    elif h in (4, 5):                            # oropt: Stück aus m Städten ab i hinter die Stadt an Position j, halb umgedreht
        m = 2 if h == 4 else 3
        for i in range(n - m + 1):
            for k in range(n - m - 1):
                for rev in (False, True):
                    out.append((Fraction(1, (n - m + 1) * (n - m - 1) * 2), (i, (i + m + k) % n, m, rev)))
    elif h == 6:                                 # dbridge: drei verschiedene Schnitte aus 1..n-1, alle Tripel gleich wahrscheinlich
        tripel = list(itertools.combinations(range(1, n), 3))
        for c in tripel:
            out.append((Fraction(1, len(tripel)), c))
    else:
        raise ValueError(f"keine Aufzählung für Zugart {h}")
    return tuple(out)


def move_delta(t, D, h: int, move) -> float:
    """Längenänderung des Zugs aus den entfernten und neuen Kanten (ohne die Tour zu ändern)."""
    n = len(t)
    if h == 0:
        i, j = move
        a, b = t[i], t[j]
        p, s = t[i - 1], (t[i + 1] if i + 1 < n else t[0])
        pj, q = t[j - 1], (t[j + 1] if j + 1 < n else t[0])
        return D[p][b] + D[b][s] + D[pj][a] + D[a][q] - D[p][a] - D[a][s] - D[pj][b] - D[b][q]
    if h == 1:
        i, j = move
        a = t[i]
        p, s = t[i - 1], (t[i + 1] if i + 1 < n else t[0])
        u, v = t[j], (t[j + 1] if j + 1 < n else t[0])
        return D[p][s] + D[u][a] + D[a][v] - D[p][a] - D[a][s] - D[u][v]
    if h in (2, 3, 7):
        i, j = move
        p, a, b, q = t[i - 1], t[i], t[j], (t[j + 1] if j + 1 < n else t[0])
        return D[p][b] + D[a][q] - D[p][a] - D[b][q]
    if h in (4, 5):
        i, j, m, rev = move
        a, z = t[i], t[i + m - 1]
        p, s = t[i - 1], (t[i + m] if i + m < n else t[0])
        u, v = t[j], (t[j + 1] if j + 1 < n else t[0])
        d = D[p][s] - D[p][a] - D[z][s] - D[u][v]
        return d + (D[u][z] + D[a][v] if rev else D[u][a] + D[z][v])
    c1, c2, c3 = move
    p, b1, b2, e1, e2, q = t[c1 - 1], t[c1], t[c2 - 1], t[c2], t[c3 - 1], (t[c3] if c3 < n else t[0])
    return D[p][e1] + D[e2][b1] + D[b2][q] - D[p][b1] - D[b2][e1] - D[e2][q]


def outcomes(h: int, t) -> list[tuple]:
    """Alle Ausgänge der Ziehung der Zugart h (0 bis 6) auf der Tour t: Liste (Wahrscheinlichkeit, neue Tour); die Tour wird aus der
    Beschreibung des Zugs neu zusammengesetzt (ohne zgm_moves.apply_move), in derselben Reihenfolge wie `move_draws`."""
    t = list(t)
    n = len(t)
    out = []
    for w, mv in move_draws(h, n):
        if h == 0:
            i, j = mv
            neu = list(t)
            neu[i], neu[j] = neu[j], neu[i]
        elif h == 1:
            i, j = mv
            rest = [c for c in t if c != t[i]]
            pos = rest.index(t[j]) + 1
            neu = rest[:pos] + [t[i]] + rest[pos:]
        elif h in (2, 3):
            i, j = mv
            neu = t[:i] + t[i:j + 1][::-1] + t[j + 1:]
        elif h in (4, 5):
            i, j, m, rev = mv
            seg = t[i:i + m]
            rest = [c for c in t if c not in seg]
            pos = rest.index(t[j]) + 1
            neu = rest[:pos] + (seg[::-1] if rev else seg) + rest[pos:]
        else:
            c1, c2, c3 = mv
            neu = t[:c1] + t[c2:c3] + t[c1:c2] + t[c3:]
        out.append((w, neu))
    return out


# ---------------------------------------------------------------- Verbesserungswahrscheinlichkeit und Einschritt-Kennzahl
def improve_probs(t, D, exakt: bool = True, eps: float = C.EPS) -> list:
    """p_h je Zugart h = 0..7: Wahrscheinlichkeit, dass EINE Anwendung die Tour streng verkürzt (Aufzählung aller Ziehungen).
    2opt_b5: 1 - (1 - p_2opt)^5. exakt=True rechnet in Brüchen, sonst in Gleitkommazahlen (für n = 30 und 60)."""
    n = len(t)
    p = []
    for h in range(7):
        if exakt:
            p.append(sum((w for w, mv in move_draws(h, n) if move_delta(t, D, h, mv) < -eps), Fraction(0)))
        else:
            p.append(float(sum(float(w) for w, mv in move_draws(h, n) if move_delta(t, D, h, mv) < -eps)))
    p.append(1 - (1 - p[C.H_2OPT]) ** C.B5_STICHPROBEN)
    return p


def k_of_set(menge, p, kosten=C.KOSTEN):
    """Einschritt-Kennzahl K(S) = Summe der Kosten / Summe der p_h über die Menge: erwartete Auswertungen bis zur ersten Verbesserung
    bei Zufallsauswahl, Akzeptanz „nur besser“ und unverändertem Zustand. None, wenn keine Zugart der Menge verbessern kann."""
    sp = sum(p[h] for h in menge)
    if sp <= 0:
        return None
    sc = sum(kosten[h] for h in menge)
    return Fraction(sc) / sp if isinstance(sp, Fraction) else sc / sp


def neighbours(t, h: int) -> set:
    """Alle Touren (kanonisch), die die Zugart h von t aus in einer Anwendung erreichen kann; 2opt_b5 zieht nur 2opt-Züge."""
    if h == C.H_2OPT_B5:
        h = C.H_2OPT
    return {canon(neu) for _, neu in outcomes(h, t)}


def is_local_optimum(t, D, menge, eps: float = C.EPS) -> bool:
    """Kein Nachbar in der Vereinigung der Nachbarschaften der Menge ist streng kürzer (Rechenweg über die Nachbarn, nicht über p_h)."""
    alt = tour_cost(D, list(t))
    return all(tour_cost(D, list(x)) >= alt - eps for h in menge for x in neighbours(t, h))


def share_of_family(menge, kosten=C.KOSTEN, familie=C.FAMILIE_2OPT) -> Fraction:
    """Anteil der Auswertungen, den die Zufallsauswahl über die Menge der 2-opt-Familie zuteilt: Kosten der Familie / Kosten der Menge."""
    return Fraction(sum(kosten[h] for h in menge if h in familie), sum(kosten[h] for h in menge))


def held_karp(D) -> float:
    """Exakte Länge der kürzesten Rundtour (Teilmengen-Rekursion nach Held und Karp), für n bis etwa 13."""
    n = len(D)
    m = n - 1
    voll = 1 << m
    inf = 1e300
    dp = [[inf] * m for _ in range(voll)]
    for j in range(m):
        dp[1 << j][j] = D[0][j + 1]
    for mask in range(1, voll):
        row = dp[mask]
        for j in range(m):
            v = row[j]
            if v >= inf or not (mask >> j) & 1:
                continue
            Dj = D[j + 1]
            for k in range(m):
                if (mask >> k) & 1:
                    continue
                nv = v + Dj[k + 1]
                ziel = dp[mask | (1 << k)]
                if nv < ziel[k]:
                    ziel[k] = nv
    return min(dp[voll - 1][j] + D[j + 1][0] for j in range(m))


# ---------------------------------------------------------------- die ganze Suche des Handbeispiels als Markov-Kette
def _transition(t, h: int, D, stichproben: int) -> dict:
    """Verteilung der Folgetouren bei EINER Anwendung der Zugart h unter „nur besser“; der Rest der Masse bleibt auf t."""
    alt = tour_cost(D, list(t))
    res = {}
    if h != C.H_2OPT_B5:
        for w, neu in outcomes(h, t):
            if tour_cost(D, neu) < alt - C.EPS:
                k = canon(neu)
                res[k] = res.get(k, 0.0) + float(w)
        return res
    zuege = [(float(w), neu, tour_cost(D, neu) - alt) for w, neu in outcomes(C.H_2OPT, t)]
    for w, neu, dl in zuege:                     # bester von `stichproben` Zügen, bei Gleichstand der frühere
        if dl >= -C.EPS:
            continue
        q_gt = sum(p for p, _, d in zuege if d > dl)
        q_ge = sum(p for p, _, d in zuege if d >= dl)
        tot = sum(q_gt ** (k - 1) * w * q_ge ** (stichproben - k) for k in range(1, stichproben + 1))
        key = canon(neu)
        res[key] = res.get(key, 0.0) + tot
    return res


@lru_cache(maxsize=64)
def _hand_matrix_of(h: int, stichproben: int):
    D = hand_matrix()
    touren = all_tours(len(D))
    idx = {t: i for i, t in enumerate(touren)}
    M = np.zeros((len(touren), len(touren)))
    for t in touren:
        i = idx[t]
        s = 0.0
        for nt, pr in _transition(t, h, D, stichproben).items():
            M[i, idx[nt]] += pr
            s += pr
        M[i, i] += 1.0 - s
    return M


def hand_expected_best(menge, budget: int, start=HAND_T0) -> float:
    """Erwartete beste Länge im Handbeispiel nach `budget` Auswertungen: Zufallsauswahl über die Menge, Akzeptanz „nur besser“.
    Exakt über die Verteilung auf den 60 Touren (Zeitachse in Auswertungen; 2opt_b5 kostet min(5, Rest)). `start`: eine Tour oder
    None für den gleichverteilten Start über alle 60 Touren."""
    D = hand_matrix()
    touren = all_tours(len(D))
    idx = {t: i for i, t in enumerate(touren)}
    m = len(menge)
    masse = [np.zeros(len(touren)) for _ in range(budget + 6)]
    if start is None:
        masse[0][:] = 1.0 / len(touren)
    else:
        masse[0][idx[canon(start)]] = 1.0
    final = np.zeros(len(touren))
    for u in range(budget):
        if not masse[u].any():
            continue
        for h in menge:
            sm = min(C.B5_STICHPROBEN, budget - u) if h == C.H_2OPT_B5 else 1
            nxt = masse[u] @ _hand_matrix_of(h, sm) / m
            if u + sm >= budget:
                final += nxt
            else:
                masse[u + sm] += nxt
    return float(final @ np.array([tour_cost(D, list(t)) for t in touren]))
