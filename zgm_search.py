"""Die Suche: in jeder Anwendung eine Zugart wählen, einen Vorschlag bewerten, über die Annahme entscheiden, Auswertungen zählen.

`run_search` ist nur Komposition: Auswahl (gleichverteilt über `arms` oder ein übergebener `selector`), Vorschlag (zgm_moves), Akzeptanz
(zgm_accept), Zählung. `arms` ist die Menge der erlaubten Zugarten: alle acht für die Zufallsmischung, `(h,)` für eine Einzelheuristik."""

import zgm_accept as AC
import zgm_constants as C
from zgm_moves import PROPOSE, apply_move, cost_of, propose_2opt_b5
from zgm_scenario import tour_cost

_OB, _RR, _LA, _GD, _SA = 0, 1, 2, 3, 4
_KIND = {"ob": _OB, "rr": _RR, "la": _LA, "gd": _GD, "sa": _SA}


def check_feasible(t, n: int) -> bool:
    """Unabhängiger Prüfer: t ist eine Permutation der Orte 0 bis n - 1."""
    return len(t) == n and sorted(t) == list(range(n))


def run_search(D, t0, budget, arms, accept, rng, checkpoints=(), trace=False, selector=None, check=False):
    """Eine Suche mit `budget` Auswertungen ab der Starttour t0.

    arms: Tupel der erlaubten Zugarten (Indizes aus zgm_constants.HNAMEN); ohne `selector` wird je Anwendung gleichverteilt daraus gewählt
        (bei einer einzigen Zugart ohne Zufallszahl).
    accept: Name aus zgm_accept.REGELN ("ob", "rr", "la", "la10", "gd", "sa").
    rng: Zufallsstrom mit `random()`; Reihenfolge je Anwendung: Auswahl, Vorschlag, bei Annealing die Annahme.
    checkpoints: Auswertungszahlen; `ck[i]` ist der Bestwert nach der ersten Anwendung, mit der die verbrauchten Auswertungen
        checkpoints[i] erreichen (2opt_b5 kann den Punkt um bis zu 4 überschreiten).
    trace: Spur der angenommenen Züge als Liste (Auswertungen danach, Zugart, Zug, delta, Länge danach, Bestwert danach).
    selector: Haken für gelernte Auswahlregeln (Folge-Demos): `selector.choose(rng)` gibt den Index in `arms`,
        `selector.update(index, delta, kosten, angenommen)` wird nach jeder Anwendung gerufen.
    check: prüft nach jedem angenommenen Zug Permutation und Länge gegen die volle Neubewertung (nur Tests).

    Rückgabe: dict mit best, final, used, steps, apps / succ / accd / evals (je Zugart: Anwendungen, strenge Verbesserungen des Vorschlags,
    angenommene Züge, Auswertungen), ck, trace, best_used (Auswertungen beim letzten neuen Bestwert)."""
    n = len(t0)
    t = list(t0)
    cost = tour_cost(D, t)
    cost0 = cost
    best = cost
    best_used = 0
    regel, laenge = AC.REGELN[accept]
    ak = _KIND[regel]
    hist = AC.new_hist(cost0, laenge) if ak == _LA else None
    kante = cost0 / n
    rnd = rng.random
    na = len(arms)
    eps = C.EPS
    apps = [0] * C.K
    succ = [0] * C.K
    accd = [0] * C.K
    evals = [0] * C.K
    used = 0
    step = 0
    ck_list = sorted(checkpoints)
    nck = len(ck_list)
    ck_i = 0
    ck_out = []
    spur = [] if trace else None
    pos = 0

    while used < budget:
        # Auswahl der Zugart
        if selector is not None:
            pos = selector.choose(rng)
            h = arms[pos]
        elif na == 1:
            h = arms[0]
        else:
            pos = int(rnd() * na)
            h = arms[pos]
        # Vorschlag und Zählung
        if h == 7:
            c = cost_of(7, budget - used)
            delta, mv = propose_2opt_b5(t, D, n, rng, c)
        else:
            c = 1
            delta, mv = PROPOSE[h](t, D, n, rng)
        used += c
        neu = cost + delta
        # Akzeptanz
        if ak == _OB:
            ok = AC.accept_ob(delta)
        elif ak == _RR:
            ok = AC.accept_rr(delta, neu, best)
        elif ak == _LA:
            ok = AC.accept_la(delta, neu, hist, step)
        elif ak == _GD:
            ok = AC.accept_gd(delta, neu, cost0, used, budget)
        else:
            ok = delta <= eps or AC.accept_sa(delta, AC.sa_temperature(used, budget, kante), rnd())
        if ok:
            apply_move(t, h, mv)
            cost = neu
            accd[h] += 1
            if cost < best - 1e-12:
                best = cost
                best_used = used
            if trace:
                spur.append((used, h, mv, delta, cost, best))
            if check:
                assert check_feasible(t, n), ("keine Permutation", h, mv)
                assert abs(tour_cost(D, t) - cost) < 1e-6, ("delta falsch", h, mv)
        if ak == _LA:
            AC.update_hist(hist, step, cost)
        step += 1
        # Statistik je Zugart
        apps[h] += 1
        evals[h] += c
        if delta < -eps:
            succ[h] += 1
        if selector is not None:
            selector.update(pos, delta, c, ok)
        if nck:
            while ck_i < nck and used >= ck_list[ck_i]:
                ck_out.append(best)
                ck_i += 1
    while ck_i < nck:
        ck_out.append(best)
        ck_i += 1
    return dict(best=best, final=cost, used=used, steps=step, apps=apps, succ=succ, accd=accd, evals=evals, ck=ck_out, trace=spur,
                best_used=best_used, tour=t)
