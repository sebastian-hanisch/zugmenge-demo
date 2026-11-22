"""Die acht Zugarten der Rundtour: je Zugart ein zufälliger Vorschlag mit Längenänderung nach der Kantenformel, dazu Anwenden und Kosten.

Jede Funktion `propose_<h>(t, D, n, rng)` zieht einen Vorschlag aus dem Zufallsstrom `rng` (nur `rng.random()`), ändert die Tour nicht und
gibt `(delta, move)` zurück: delta = Länge(neue Tour) - Länge(alte Tour), berechnet aus den entfernten und neuen Kanten. `apply_move`
führt den Zug aus. Eine Auswertung = ein bewerteter Vorschlag; `2opt_b5` bewertet bis zu fünf 2-opt-Vorschläge und kostet so viele."""

import zgm_constants as C


def propose_swap(t, D, n, rng):
    """Zwei nicht benachbarte Orte tauschen: Position i gleichverteilt, die zweite im Abstand 2 bis n - 2."""
    r = rng.random
    i = int(r() * n)
    j = (i + 2 + int(r() * (n - 3))) % n
    a = t[i]
    b = t[j]
    p = t[i - 1]
    s = t[i + 1] if i + 1 < n else t[0]
    pj = t[j - 1]
    q = t[j + 1] if j + 1 < n else t[0]
    Da = D[a]
    Db = D[b]
    return D[p][b] + Db[s] + D[pj][a] + Da[q] - D[p][a] - Da[s] - D[pj][b] - Db[q], (i, j)


def propose_insert(t, D, n, rng):
    """Einen Ort umsetzen: den Ort an Position i hinter den Ort an Position j (Abstand 1 bis n - 2)."""
    r = rng.random
    i = int(r() * n)
    j = (i + 1 + int(r() * (n - 2))) % n
    a = t[i]
    p = t[i - 1]
    s = t[i + 1] if i + 1 < n else t[0]
    u = t[j]
    v = t[j + 1] if j + 1 < n else t[0]
    Da = D[a]
    return D[p][s] + D[u][a] + Da[v] - D[p][a] - Da[s] - D[u][v], (i, j)


def propose_2opt(t, D, n, rng):
    """Ein Stück umdrehen: Start i gleichverteilt in 0 bis n - 2, Länge gleichverteilt in 2 bis min(n - i, n - 2)."""
    r = rng.random
    i = int(r() * (n - 1))
    maxl = n - i if n - i < n - 2 else n - 2
    j = i + 1 + int(r() * (maxl - 1))
    p = t[i - 1]
    a = t[i]
    b = t[j]
    q = t[j + 1] if j + 1 < n else t[0]
    return D[p][b] + D[a][q] - D[p][a] - D[b][q], (i, j)


def propose_2opt_lokal(t, D, n, rng):
    """Ein kurzes Stück umdrehen: Länge gleichverteilt in 2 bis min(8, n - 2), danach der Start gleichverteilt."""
    r = rng.random
    lmax = C.LOKAL_LMAX if n - 2 > C.LOKAL_LMAX else n - 2
    laenge = 2 + int(r() * (lmax - 1))
    i = int(r() * (n - laenge + 1))
    j = i + laenge - 1
    p = t[i - 1]
    a = t[i]
    b = t[j]
    q = t[j + 1] if j + 1 < n else t[0]
    return D[p][b] + D[a][q] - D[p][a] - D[b][q], (i, j)


def _propose_oropt(t, D, n, rng, m):
    r = rng.random
    i = int(r() * (n - m + 1))
    j = (i + m + int(r() * (n - m - 1))) % n
    rev = r() < 0.5
    a = t[i]
    z = t[i + m - 1]
    p = t[i - 1]
    s = t[i + m] if i + m < n else t[0]
    u = t[j]
    v = t[j + 1] if j + 1 < n else t[0]
    delta = D[p][s] - D[p][a] - D[z][s] - D[u][v]
    if rev:
        delta += D[u][z] + D[a][v]
    else:
        delta += D[u][a] + D[z][v]
    return delta, (i, j, m, rev)


def propose_oropt2(t, D, n, rng):
    """Ein Stück aus zwei Orten umsetzen (hinter den Ort an Position j), mit Wahrscheinlichkeit 1/2 umgedreht."""
    return _propose_oropt(t, D, n, rng, 2)


def propose_oropt3(t, D, n, rng):
    """Ein Stück aus drei Orten umsetzen (hinter den Ort an Position j), mit Wahrscheinlichkeit 1/2 umgedreht."""
    return _propose_oropt(t, D, n, rng, 3)


def propose_dbridge(t, D, n, rng):
    """Doppelbrücke: drei verschiedene Schnitte aus 1 bis n - 1 (gleichverteilt, sortiert), die beiden mittleren Stücke tauschen."""
    r = rng.random
    while True:
        x = int(r() * (n - 1)) + 1
        y = int(r() * (n - 1)) + 1
        w = int(r() * (n - 1)) + 1
        if x != y and y != w and x != w:
            break
    c1, c2, c3 = sorted((x, y, w))
    p = t[c1 - 1]
    b1 = t[c1]
    b2 = t[c2 - 1]
    e1 = t[c2]
    e2 = t[c3 - 1]
    q = t[c3] if c3 < n else t[0]
    return D[p][e1] + D[e2][b1] + D[b2][q] - D[p][b1] - D[b2][e1] - D[e2][q], (c1, c2, c3)


def propose_2opt_b5(t, D, n, rng, stichproben=C.B5_STICHPROBEN):
    """Der beste von `stichproben` unabhängigen 2-opt-Vorschlägen (kleinstes delta; bei Gleichstand der frühere)."""
    delta = 1e300
    move = None
    for _ in range(stichproben):
        d, mv = propose_2opt(t, D, n, rng)
        if d < delta:
            delta = d
            move = mv
    return delta, move


PROPOSE = (propose_swap, propose_insert, propose_2opt, propose_2opt_lokal, propose_oropt2, propose_oropt3, propose_dbridge, propose_2opt_b5)


def cost_of(h: int, rest: int) -> int:
    """Auswertungen, die die nächste Anwendung der Zugart h kostet, wenn noch `rest` Auswertungen übrig sind (2opt_b5: höchstens der Rest)."""
    k = C.KOSTEN[h]
    return k if k <= rest else rest


def apply_move(t, h: int, move) -> None:
    """Führt den Zug der Zugart h auf der Tour t aus (die Liste wird geändert)."""
    if h == 0:
        i, j = move
        t[i], t[j] = t[j], t[i]
    elif h == 1:
        i, j = move
        x = t.pop(i)
        t.insert((j if j < i else j - 1) + 1, x)
    elif h == 4 or h == 5:
        i, j, m, rev = move
        seg = t[i:i + m]
        if rev:
            seg.reverse()
        del t[i:i + m]
        ju = j if j < i else j - m
        t[ju + 1:ju + 1] = seg
    elif h == 6:
        c1, c2, c3 = move
        t[c1:c3] = t[c2:c3] + t[c1:c2]
    else:
        i, j = move
        seg = t[i:j + 1]
        seg.reverse()
        t[i:j + 1] = seg
