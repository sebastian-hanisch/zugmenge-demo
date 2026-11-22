"""Auswahlregeln über eine Zugmenge: Zufallsauswahl, Choice Function, Lernautomat, Q-Lernen (Quelle für die Folge-Demos der Linie).

Jede Regel besteht aus drei reinen Funktionen über einem ausdrücklich übergebenen Zustand (dict):
    new_<regel>(m) -> state                 Anfangszustand für m Zugarten (Arme 0 bis m - 1 = Positionen in der sortierten Zugmenge)
    choose_<regel>(state, rng) -> arm       wählt einen Arm; Zufall nur über rng.random()
    update_<regel>(state, arm, reward)      lernt aus der Belohnung in [0, 1] der gerade ausgeführten Anwendung

`Selector` verbindet eine Regel mit einer Belohnungsfunktion und passt sie an den Haken der Suche an
(zgm_search.run_search: `selector.choose(rng)`, `selector.update(index, delta, kosten, angenommen)`).
Standardbelohnung: Verbesserung des Vorschlags je Auswertung, in mittleren Kantenlängen der Starttour, auf [0, 1] gekappt.

Die Regeln lernen online über die übergebene Zugmenge, mit festen, nicht abgestimmten Parametern (zgm_constants)."""

import zgm_constants as C

EPS = C.EPS


# ---------------------------------------------------------------- Belohnung
def reward_standard(delta: float, kosten: int, kante: float) -> float:
    """min(1, max(0, -delta) / (kosten * kante)): strenge Verbesserung des Vorschlags je Auswertung, in mittleren Kantenlängen."""
    if delta >= -EPS:
        return 0.0
    r = -delta / (kosten * kante)
    return 1.0 if r > 1.0 else r


def standard_reward(kante: float):
    """Belohnungsfunktion für `Selector`: (delta, kosten, angenommen) -> Belohnung; `kante` = Länge der Starttour / n."""
    def belohnung(delta, kosten, angenommen):
        if delta >= -EPS:
            return 0.0
        r = -delta / (kosten * kante)
        return 1.0 if r > 1.0 else r
    return belohnung


# ---------------------------------------------------------------- Zufallsauswahl
def new_rand(m: int) -> dict:
    return {"m": m}


def choose_rand(state: dict, rng) -> int:
    """Gleichverteilt über die m Arme: int(u * m); bei einem einzigen Arm ohne Zufallszahl (wie die eingebaute Auswahl der Suche)."""
    m = state["m"]
    return 0 if m == 1 else int(rng.random() * m)


def update_rand(state: dict, arm: int, reward: float) -> None:
    """Die Zufallsauswahl lernt nichts."""


# ---------------------------------------------------------------- Choice Function
def new_cf(m: int) -> dict:
    """f1: Leistung je Arm; f2: Leistung des Arms nach dem Vorgänger; last: Schritt der letzten Anwendung; phi: Gewicht der Leistung."""
    return {"m": m, "f1": [0.0] * m, "f2": [[0.0] * m for _ in range(m)], "last": [0] * m, "phi": C.CF_PHI0, "prev": -1, "step": 0}


def choose_cf(state: dict, rng) -> int:
    """Arm mit dem größten Wert phi * (f1 / max f1 + f2[Vorgänger] / max f2[Vorgänger]) + (1 - phi) * min(Wartezeit, 50) / 50.

    Je Arm kommt ein Rauschen u * 1e-9 dazu (löst Gleichstände, zieht je Arm eine Zufallszahl); bei gleichem Wert gewinnt der kleinere Index."""
    m = state["m"]
    f1 = state["f1"]
    last = state["last"]
    phi = state["phi"]
    prev = state["prev"]
    step = state["step"]
    rnd = rng.random
    m1 = max(f1) + 1e-12
    if prev >= 0:
        row2 = state["f2"][prev]
        m2 = max(row2) + 1e-12
    fenster = C.CF_ZEITFENSTER
    best = -1e300
    arm = 0
    for j in range(m):
        s = phi * (f1[j] / m1 + (row2[j] / m2 if prev >= 0 else 0.0))
        dt = step - last[j]
        s += (1.0 - phi) * (dt if dt < fenster else fenster) / fenster
        s += rnd() * C.CF_RAUSCHEN
        if s > best:
            best = s
            arm = j
    return arm


def update_cf(state: dict, arm: int, reward: float) -> None:
    """f1 und f2 mit Vergessen alpha fortschreiben; phi nach einem Erfolg (reward > 0) auf 0,99, sonst um 0,01 senken (mindestens 0,01)."""
    alpha = C.CF_ALPHA
    state["step"] += 1
    f1 = state["f1"]
    f1[arm] = reward + alpha * f1[arm]
    prev = state["prev"]
    if prev >= 0:
        row = state["f2"][prev]
        row[arm] = reward + alpha * row[arm]
    state["last"][arm] = state["step"]
    if reward > 0.0:
        state["phi"] = C.CF_PHI_ERFOLG
    else:
        phi = state["phi"] - C.CF_PHI_SCHRITT
        state["phi"] = phi if phi > C.CF_PHI_MIN else C.CF_PHI_MIN
    state["prev"] = arm


# ---------------------------------------------------------------- Lernautomat (linear reward-inaction)
def new_laut(m: int) -> dict:
    return {"m": m, "p": [1.0 / m] * m}


def choose_laut(state: dict, rng) -> int:
    """Zieht den Arm aus der Wahrscheinlichkeitsverteilung p (eine Zufallszahl, kumulierte Summe)."""
    u = rng.random()
    c = 0.0
    p = state["p"]
    for j, pj in enumerate(p):
        c += pj
        if u < c:
            return j
    return state["m"] - 1


def update_laut(state: dict, arm: int, reward: float) -> None:
    """Nur nach einem Erfolg (reward > 0): alle p mal (1 - a), der gewählte Arm plus a; danach Untergrenze 0,01 je Arm und neu normieren."""
    if reward <= 0.0:
        return
    a = C.LAUT_A
    boden = C.LAUT_BODEN
    p = state["p"]
    m = state["m"]
    for j in range(m):
        p[j] *= 1.0 - a
    p[arm] += a
    tot = 0.0
    for j in range(m):
        if p[j] < boden:
            p[j] = boden
        tot += p[j]
    for j in range(m):
        p[j] /= tot


# ---------------------------------------------------------------- Q-Lernen mit einem Zustand
def new_q(m: int) -> dict:
    return {"m": m, "q": [0.0] * m}


def choose_q(state: dict, rng) -> int:
    """Mit Wahrscheinlichkeit eps ein gleichverteilter Arm, sonst der Arm mit dem größten Q-Wert (Gleichstand innerhalb 1e-12: gleichverteilt unter den besten)."""
    rnd = rng.random
    m = state["m"]
    if rnd() < C.Q_EPS:
        return int(rnd() * m)
    q = state["q"]
    mq = max(q)
    cand = [j for j in range(m) if q[j] >= mq - 1e-12]
    return cand[int(rnd() * len(cand))] if len(cand) > 1 else cand[0]


def update_q(state: dict, arm: int, reward: float) -> None:
    """Q[arm] += alpha * (reward + gamma * max Q - Q[arm])."""
    q = state["q"]
    q[arm] += C.Q_ALPHA * (reward + C.Q_GAMMA * max(q) - q[arm])


# ---------------------------------------------------------------- Tabelle der Regeln und Adapter für die Suche
REGEL_FUNKTIONEN = {
    "rand": (new_rand, choose_rand, update_rand),
    "cf": (new_cf, choose_cf, update_cf),
    "laut": (new_laut, choose_laut, update_laut),
    "q": (new_q, choose_q, update_q),
}


class Selector:
    """Eine Auswahlregel am Haken der Suche: hält den Zustand der Regel und rechnet die Belohnung aus (delta, kosten, angenommen).

    regel: Name aus `funktionen` (Standard: REGEL_FUNKTIONEN); m: Zahl der Zugarten der Menge;
    belohnung: Funktion (delta, kosten, angenommen) -> Belohnung in [0, 1], z. B. `standard_reward(kante)`."""

    def __init__(self, regel: str, m: int, belohnung, funktionen=None):
        neu, self._choose, self._update = (funktionen or REGEL_FUNKTIONEN)[regel]
        self.regel = regel
        self.state = neu(m)
        self.belohnung = belohnung

    def choose(self, rng) -> int:
        return self._choose(self.state, rng)

    def update(self, index: int, delta: float, kosten: int, angenommen: bool) -> None:
        self._update(self.state, index, self.belohnung(delta, kosten, angenommen))


def make_selector(regel: str, m: int, kante: float) -> Selector:
    """Auswahlregel mit der Standardbelohnung; `kante` = Länge der Starttour / n (mittlere Kantenlänge)."""
    return Selector(regel, m, standard_reward(kante))
