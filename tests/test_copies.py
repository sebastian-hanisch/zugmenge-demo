"""Kopier-Tests: die Rundtour-Module sind wörtliche Kopien aus der Wurzel-Demo der Linie (hyperheuristik-demo), bis auf das Präfix.

Fehlt der Nachbarordner (CI), werden die Tests übersprungen. Eine Korrektur gehört in die Quelle und wird neu kopiert, nicht in die Kopie."""

from pathlib import Path

import pytest

import zgm_constants as C

ROOT = Path(__file__).resolve().parent.parent
QUELLE = ROOT.parent / "hyperheuristik-demo"
KOPIEN = ("rng", "rngblock", "scenario", "moves", "accept", "search", "stats")
GLEICHE_KONSTANTEN = (
    "HNAMEN", "K", "KOSTEN", "H_2OPT", "H_2OPT_B5", "ALLE_ZUGARTEN", "B5_STICHPROBEN", "LOKAL_LMAX", "FAMILIEN", "FAMILIE_HAND", "SEITE",
    "CLUSTER_ZAHL", "CLUSTER_SIGMA", "GITTER_FAKTOR", "GITTER_RAUSCHEN", "ZWECK_INSTANZ", "ZWECK_START", "ZWECK_LAUF", "ZWECK_BOOT", "EPS",
    "RHO", "LA_LEN", "LA_LEN_KURZ", "GD_END", "SA_T0", "SA_T1", "MARKE_KLAR", "MARKE_GLEICH", "BOOTSTRAP_ZIEHUNGEN",
)


def _text(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("suffix", KOPIEN)
def test_kopie_stimmt_mit_der_quelle_ueberein_falls_vorhanden(suffix):
    quelle = QUELLE / f"hhw_{suffix}.py"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    assert _text(ROOT / f"zgm_{suffix}.py") == _text(quelle).replace("hhw_", "zgm_")


def test_konstanten_der_kopien_haben_die_werte_der_quelle_falls_vorhanden():
    quelle = QUELLE / "hhw_constants.py"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    namen: dict = {}
    exec(compile(_text(quelle), str(quelle), "exec"), namen)   # nur Zuweisungen von Konstanten
    for name in GLEICHE_KONSTANTEN:
        assert getattr(C, name) == namen[name], name


def test_die_zwoelf_benannten_mengen():
    assert len(C.MENGEN) == 12
    assert C.MENGEN["voll"] == tuple(range(8)) and C.MENGEN["T3"] == (2, 3, 7)
    assert C.MENGEN["ohne_2opt_Familie"] == (0, 1, 4, 5, 6) and C.MENGEN["nur_schwache"] == (0, 4, 5, 6)
    for h, name in enumerate(C.HNAMEN):
        assert C.MENGEN["ohne_" + name] == tuple(x for x in range(8) if x != h)
    assert len(set(C.MENGEN.values())) == 12 and set(C.MENGEN) == set(C.MENGEN_ANZEIGE)
    assert 12 * 3 * 9 == 324                                        # Mengen x Lernregeln x (Akzeptanz x Stufe): Zahl der Gewinn-Intervalle
    assert len(C.SCHWACHE_EINZELN) * len(C.AKZEPTANZEN) * len(C.STUFEN) == 54
