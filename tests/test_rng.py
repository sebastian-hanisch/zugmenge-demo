"""Zufallsquelle: zgm_rng.py ist die unveränderte Vorlage, der Blockstrom ist bitgleich dazu, die Zufalls-Seeds je Zweck sind fest."""

from pathlib import Path

import pytest

import zgm_scenario as S
from zgm_rng import SplitMix64
from zgm_rngblock import BlockSplitMix64, uniform_block

ROOT = Path(__file__).resolve().parent.parent
VORLAGE = ROOT.parent / "sebastianhanisch-website" / "tools" / "templates" / "rng_splitmix64_exact.py"


def test_kopie_stimmt_mit_der_vorlage_ueberein_falls_vorhanden():
    if not VORLAGE.exists():
        pytest.skip("Vorlage nicht vorhanden (CI ohne Website-Repo)")
    assert (ROOT / "zgm_rng.py").read_bytes().replace(b"\r\n", b"\n") == VORLAGE.read_bytes().replace(b"\r\n", b"\n")


def test_splitmix64_bekannte_werte():
    """Referenzwerte von SplitMix64 mit Zufalls-Seed 0 (Vigna, splitmix64.c): die ersten drei Ausgaben."""
    r = SplitMix64(0)
    assert [r.next_u64() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]


@pytest.mark.parametrize("seed", [0, 1, 12345, (1 << 64) - 1, 0x9E3779B97F4A7C15])
def test_blockstrom_ist_bitgleich_zur_vorlage(seed):
    skalar = SplitMix64(seed)
    block = BlockSplitMix64(seed, block=64)       # kleine Blöcke: der Übergang zwischen Blöcken wird mitgeprüft
    assert [skalar.random() for _ in range(1000)] == [block.random() for _ in range(1000)]


def test_uniform_block_mit_versatz():
    skalar = SplitMix64(77)
    werte = [skalar.random() for _ in range(300)]
    assert uniform_block(77, 100, 200).tolist() == werte[100:300]
    assert all(0.0 <= u < 1.0 for u in werte)


def test_derive_ist_fest_und_trennt_zwecke_und_schluessel():
    a = S.derive(11, 0, 30, 0)
    assert a == S.derive(11, 0, 30, 0)
    andere = {S.derive(11, 0, 30, 1), S.derive(11, 1, 30, 0), S.derive(11, 0, 60, 0), S.derive(33, 0, 30, 0), S.derive(11, 0, 30, 0, 0)}
    assert a not in andere and len(andere) == 5
