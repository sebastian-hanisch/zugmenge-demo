"""Erzeugt die eingefrorene Messung (zgm_band.json) mit den Zufallsströmen der App (SplitMix64).

Aufruf im Demo-Ordner (zgm_refs.json muss vorhanden sein: tools/zgm_make_refs.py):
    python tools/zgm_make_band.py --procs 2            # rechnet alles neu und schreibt zgm_band.json
    python tools/zgm_make_band.py --check              # rechnet eine Stichprobe neu und vergleicht sie als Band mit der Datei

Messung je Instanz (3 Familien x n = 30, 60 x Instanzen 0 bis 19 = 120 Instanzen), 3 Läufe (Zufalls-Seeds) je Instanz; alle Varianten
eines Laufs haben dieselbe Starttour und lesen denselben Zufallsstrom von vorn:
  Haupt        12 Zugmengen x 4 Auswahlregeln (rand, cf, laut, q) x 3 Akzeptanzen (ob, rr, la): ein Lauf bis 400 n, Bestwert und Beitrag
               je Zugart an den Kontrollpunkten 50 n, 150 n, 400 n; Zähler je Zugart am Ende
  Einzel       jede der acht Zugarten allein, 3 Akzeptanzen, ein Lauf bis 400 n mit denselben Kontrollpunkten
  Anwendungen  Zufallsauswahl auf „voll“ und „T3“, Budget in Anwendungen statt Auswertungen (50 n, 150 n, 400 n Anwendungen)
  Pool         „beste von 5“ für swap, insert, oropt2, oropt3 als Einzelzugart, ob und rr, Budget genau 50 n (Suche nach gleich starken Zugarten)
Referenz einer Instanz = Minimum aus zgm_refs.json und allen Läufen dieser Messung (bester bekannter Wert, kein Optimum)."""

import argparse
import json
import multiprocessing as mp
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import zgm_accept as AC  # noqa: E402
import zgm_constants as C  # noqa: E402
import zgm_experiments as E  # noqa: E402
import zgm_scenario as S  # noqa: E402
from zgm_moves import PROPOSE, apply_move  # noqa: E402
from zgm_rngblock import BlockSplitMix64  # noqa: E402

SEEDS = C.BAND_SEEDS
POOL_ZUGARTEN = (0, 1, 4, 5)                 # swap, insert, oropt2, oropt3: je eine Variante „beste von 5“
POOL_AKZ = ("ob", "rr")
REF_TOLERANZ = 1e-6                          # zgm_refs.json rundet auf 6 Nachkommastellen: erst darunter gilt eine Referenz als unterboten
ANW_BUDGET = {"voll": 700, "T3": 1100}       # Auswertungen (mal n), die für 400 n Anwendungen sicher reichen (mittlere Kosten 1,5 bzw. 2,33)


def run_best_of(D, t0, budget: int, h: int, stichproben: int, akz: str, rng) -> float:
    """Einzelzugart „beste von `stichproben`“ der Grundzugart h (Kosten = Zahl der Stichproben, am Budgetrand der Rest), Akzeptanz ob oder rr.
    Mit h = 2 und fünf Stichproben ist das genau 2opt_b5 (Test gegen zgm_search.run_search)."""
    n = len(t0)
    t = list(t0)
    cost = S.tour_cost(D, t)
    best = cost
    used = 0
    prop = PROPOSE[h]
    while used < budget:
        c = stichproben if stichproben <= budget - used else budget - used
        delta = 1e300
        mv = None
        for _ in range(c):
            d, m = prop(t, D, n, rng)
            if d < delta:
                delta, mv = d, m
        used += c
        neu = cost + delta
        ok = AC.accept_ob(delta) if akz == "ob" else AC.accept_rr(delta, neu, best)
        if ok:
            apply_move(t, h, mv)
            cost = neu
            if cost < best - 1e-12:
                best = cost
    return best


def _shares(ck_gain, start, ck):
    """Je Kontrollpunkt die Anteile der Zugarten an der Senkung des Bestwerts (None, wenn der Bestwert dort noch die Startlänge ist)."""
    out = []
    for gains, best in zip(ck_gain, ck):
        gesamt = start - best
        out.append([g / gesamt for g in gains] if gesamt > 1e-9 else None)
    return out


def job(args):
    """Alle Läufe einer Instanz; Rückgabe (Schlüssel, Rohwerte, Auswertungen)."""
    fam, n, idx = args
    st = E.checkpoints_for(n, C.STUFEN)
    haupt, zaehler, beitrag, einzel, anw, pool = {}, {}, {}, {}, {}, {}
    kosten = 0
    for akz in C.AKZEPTANZEN:
        for sname, arms in C.MENGEN.items():
            for regel in C.REGELN:
                v = []
                z = dict(apps=[0] * C.K, evals=[0] * C.K, succ=[0] * C.K)
                sh = [[] for _ in st]
                for lauf in range(SEEDS):
                    r = E.run_set(fam, n, idx, lauf, arms, regel, akz, st[-1], checkpoints=st)
                    kosten += r["used"]
                    v.append(r["ck"])
                    for name in z:
                        z[name] = [a + b for a, b in zip(z[name], r[name])]
                    for j, anteile in enumerate(_shares(r["ck_gain"], r["start"], r["ck"])):
                        if anteile is not None:
                            sh[j].append(anteile)
                haupt[(akz, sname, regel)] = v
                zaehler[(akz, sname, regel)] = z
                beitrag[(akz, sname, regel)] = sh
        for h in range(C.K):
            v = []
            for lauf in range(SEEDS):
                r = E.run_set(fam, n, idx, lauf, (h,), "rand", akz, st[-1], checkpoints=st)
                kosten += r["used"]
                v.append(r["ck"])
            einzel[(akz, h)] = v
        for sname, faktor in ANW_BUDGET.items():
            v = []
            for lauf in range(SEEDS):
                r = E.run_set(fam, n, idx, lauf, C.MENGEN[sname], "rand", akz, faktor * n, app_checkpoints=st)
                assert r["steps"] >= st[-1], "Budget der Anwendungs-Messung zu klein"
                kosten += r["used"]
                v.append(r["app_best"])
            anw[(akz, sname)] = v
    _, D = E.instance(fam, n, idx)
    for akz in POOL_AKZ:
        for h in POOL_ZUGARTEN:
            v = []
            for lauf in range(SEEDS):
                t0 = S.start_tour(D, fam, n, idx, lauf)
                v.append(run_best_of(D, t0, st[0], h, C.B5_STICHPROBEN, akz, BlockSplitMix64(S.run_seed(fam, n, idx, lauf))))
                kosten += st[0]
            pool[(akz, h)] = v
    return args, dict(haupt=haupt, zaehler=zaehler, beitrag=beitrag, einzel=einzel, anw=anw, pool=pool), kosten


def _minimum(roh) -> float:
    werte = [x for teil in ("haupt", "einzel", "anw") for v in roh[teil].values() for zeile in v for x in zeile]
    werte += [x for v in roh["pool"].values() for x in v]
    return min(werte)


def _gaps(v, ref):
    """Je Stufe das Mittel der Abstände über die Läufe (4 Nachkommastellen)."""
    return [round(sum(100.0 * (zeile[j] - ref) / ref for zeile in v) / len(v), 4) for j in range(len(v[0]))]


def build(procs: int, instanzen: int) -> dict:
    refs = E.load_json("zgm_refs.json")
    jobs = [(fam, n, idx) for fam in C.FAMILIEN for n in C.N_GEMESSEN for idx in range(instanzen)]
    roh = {}
    kosten = 0
    t0 = time.time()
    with mp.Pool(procs) as pool:
        for i, (key, wert, k) in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            roh[key] = wert
            kosten += k
            if (i + 1) % 10 == 0 or i + 1 == len(jobs):
                print(f"{i + 1}/{len(jobs)} Instanzen, {kosten} Auswertungen, {time.time() - t0:.0f} s", flush=True)
    out = dict(
        meta=dict(instanzen=len(jobs), seeds=SEEDS, stufen=list(C.STUFEN), akzeptanzen=list(C.AKZEPTANZEN), regeln=list(C.REGELN),
                  mengen={k: list(v) for k, v in C.MENGEN.items()}, auswertungen_gesamt=kosten, python=platform.python_version(),
                  rechner=platform.system(), pool_zugarten=[C.HNAMEN[h] + "_b5" for h in POOL_ZUGARTEN], anwendungen_budget=ANW_BUDGET),
        instanzen=[list(j) for j in jobs], ref=[], unterboten=0,
        gap={a: {s: {r: [] for r in C.REGELN} for s in C.MENGEN} for a in C.AKZEPTANZEN},
        zaehler={a: {s: {r: dict(apps=[0] * C.K, evals=[0] * C.K, succ=[0] * C.K) for r in C.REGELN} for s in C.MENGEN} for a in C.AKZEPTANZEN},
        beitrag={a: {s: {} for s in C.MENGEN} for a in C.AKZEPTANZEN},
        einzel={a: {C.HNAMEN[h]: [] for h in range(C.K)} for a in C.AKZEPTANZEN},
        anwendungen={a: {s: [] for s in ANW_BUDGET} for a in C.AKZEPTANZEN},
        pool={a: {C.HNAMEN[h] + "_b5": [] for h in POOL_ZUGARTEN} for a in POOL_AKZ},
    )
    summen = {}
    for fam, n, idx in jobs:
        r = roh[(fam, n, idx)]
        gespeichert = E.reference(refs, fam, n, idx)
        kleinste = _minimum(r)
        ref = min(gespeichert, kleinste) if gespeichert is not None else kleinste
        out["unterboten"] += int(gespeichert is not None and round(kleinste, 6) < gespeichert - REF_TOLERANZ)
        out["ref"].append(round(ref, 6))
        for (akz, sname, regel), v in r["haupt"].items():
            out["gap"][akz][sname][regel].append(_gaps(v, ref))
            z = out["zaehler"][akz][sname][regel]
            for name in z:
                z[name] = [a + b for a, b in zip(z[name], r["zaehler"][(akz, sname, regel)][name])]
            s = summen.setdefault((akz, sname, regel), [[[0.0] * C.K, 0] for _ in C.STUFEN])
            for j, laeufe in enumerate(r["beitrag"][(akz, sname, regel)]):
                for anteile in laeufe:
                    s[j][0] = [a + b for a, b in zip(s[j][0], anteile)]
                    s[j][1] += 1
        for (akz, h), v in r["einzel"].items():
            out["einzel"][akz][C.HNAMEN[h]].append(_gaps(v, ref))
        for (akz, sname), v in r["anw"].items():
            out["anwendungen"][akz][sname].append(_gaps(v, ref))
        for (akz, h), v in r["pool"].items():
            out["pool"][akz][C.HNAMEN[h] + "_b5"].append(round(sum(100.0 * (x - ref) / ref for x in v) / len(v), 4))
    for (akz, sname, regel), s in summen.items():
        out["beitrag"][akz][sname][regel] = dict(anteile=[[round(x / max(k, 1), 5) for x in summe] for summe, k in s], laeufe=[k for _, k in s])
    return out


CHECK = (("gleich", 30, 0), ("cluster", 60, 3), ("gitter", 30, 7), ("gleich", 60, 9))
CHECK_MENGEN = ("voll", "T3")
CHECK_TOLERANZ = 1e-3                          # Prozentpunkte: die Datei rundet auf 4 Nachkommastellen


def check_values(band: dict, faelle=CHECK, mengen=CHECK_MENGEN, akz: str = "rr", regel: str = "rand") -> list[tuple]:
    """Rechnet für die Fälle die Abstände der Zufallsauswahl neu: Liste (Fall, Menge, neu gerechnet, Datei)."""
    out = []
    index = {tuple(x): i for i, x in enumerate(band["instanzen"])}
    for fam, n, idx in faelle:
        i = index[(fam, n, idx)]
        st = E.checkpoints_for(n, C.STUFEN)
        for sname in mengen:
            v = [E.run_set(fam, n, idx, lauf, C.MENGEN[sname], regel, akz, st[-1], checkpoints=st)["ck"] for lauf in range(band["meta"]["seeds"])]
            out.append(((fam, n, idx), sname, _gaps(v, band["ref"][i]), band["gap"][akz][sname][regel][i]))
    return out


def check() -> int:
    band = E.load_json("zgm_band.json")
    fehler = 0
    werte = check_values(band)
    for fall, sname, neu, alt in werte:
        for a, b in zip(neu, alt):
            if abs(a - b) > CHECK_TOLERANZ:
                fehler += 1
                print("ABWEICHUNG", fall, sname, neu, alt)
    print(f"{3 * len(werte)} Vergleiche, {fehler} Abweichungen")
    return 1 if fehler else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--instanzen", type=int, default=C.BAND_INSTANZEN)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        sys.exit(check())
    t0 = time.time()
    out = build(a.procs, a.instanzen)
    (ROOT / "zgm_band.json").write_text(json.dumps(out, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"fertig: {out['meta']['auswertungen_gesamt']} Auswertungen, {time.time() - t0:.0f} s, Referenz unterboten in {out['unterboten']} Instanzen")


if __name__ == "__main__":
    main()
