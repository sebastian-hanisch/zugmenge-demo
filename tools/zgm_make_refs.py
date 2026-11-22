"""Erzeugt die Referenzwerte (zgm_refs.json): je Instanz der kleinste Bestwert aus fünf langen Läufen der Zufallsauswahl über alle acht Zugarten.

Aufruf im Demo-Ordner:
    python tools/zgm_make_refs.py --procs 2

Je Familie (gleich, cluster, gitter), n (30, 60) und Instanz 0 bis 199 (die Instanzen der Zufalls-Seeds 0 bis 24 der App): drei Läufe mit
Annealing-Akzeptanz (Temperatur geometrisch von 0,3 auf 0,003 mittlere Kantenlängen) und zwei Läufe mit Late Acceptance (L = 50), je
1000·n Auswertungen. Annealing kommt nur hier vor, nicht in der App. Die Werte sind beste bekannte Werte, keine Optima: ein Lauf der App
kann sie unterbieten; die App nimmt dann je Klick das Minimum."""

import argparse
import json
import multiprocessing as mp
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import zgm_constants as C  # noqa: E402
import zgm_experiments as E  # noqa: E402
import zgm_scenario as S  # noqa: E402
from zgm_rng import SplitMix64  # noqa: E402
from zgm_rngblock import BlockSplitMix64  # noqa: E402
from zgm_search import run_search  # noqa: E402

REF_LAEUFE = (("sa", 0), ("sa", 1), ("sa", 2), ("la", 0), ("la", 1))
REF_F = 1000


def ref_runs(familie: str, n: int, idx: int) -> float:
    """Kleinster Bestwert der fünf Referenzläufe einer Instanz."""
    _, D = E.instance(familie, n, idx)
    fi = C.FAMILIEN.index(familie)
    werte = []
    for akz, lauf in REF_LAEUFE:
        t0 = S.nn_start(D, SplitMix64(S.derive(C.ZWECK_REFSTART, fi, n, idx, lauf, 0 if akz == "sa" else 1)))
        rng = BlockSplitMix64(S.derive(C.ZWECK_REF, fi, n, idx, lauf, 0 if akz == "sa" else 1))
        werte.append(run_search(D, t0, REF_F * n, C.ALLE_ZUGARTEN, akz, rng)["best"])
    return min(werte)


def _job(args):
    return args, ref_runs(*args)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--instanzen", type=int, default=C.INSTANZEN_REF)
    a = ap.parse_args()
    jobs = [(fam, n, idx) for fam in C.FAMILIEN for n in C.N_GEMESSEN for idx in range(a.instanzen)]
    refs = {fam: {str(n): [None] * a.instanzen for n in C.N_GEMESSEN} for fam in C.FAMILIEN}
    t0 = time.time()
    with mp.Pool(a.procs) as pool:
        for i, ((fam, n, idx), wert) in enumerate(pool.imap_unordered(_job, jobs, chunksize=4)):
            refs[fam][str(n)][idx] = round(wert, 6)
            if (i + 1) % 100 == 0:
                print(f"{i + 1}/{len(jobs)} Instanzen, {time.time() - t0:.0f} s", flush=True)
    auswertungen = sum(len(REF_LAEUFE) * REF_F * n for _, n, _ in jobs)
    out = dict(meta=dict(instanzen_je_zelle=a.instanzen, laeufe=[list(x) for x in REF_LAEUFE], budget_faktor=REF_F, auswertungen_gesamt=auswertungen,
                         python=platform.python_version(), rechner=platform.system()), refs=refs)
    (ROOT / "zgm_refs.json").write_text(json.dumps(out, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"fertig: {len(jobs)} Instanzen, {auswertungen} Auswertungen, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
