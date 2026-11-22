"""Auswahlregeln: je Regel ein Schritt von Hand, dazu Verteilung, Grenzen und der Anschluss an die Suche."""

import pytest

import zgm_constants as C
import zgm_scenario as S
import zgm_select as SE
from zgm_rngblock import BlockSplitMix64
from zgm_search import run_search


class Feste:
    """Zufallsstrom mit vorgegebenen Werten (für Handrechnungen)."""

    def __init__(self, werte):
        self.werte = list(werte)
        self.gezogen = 0

    def random(self):
        self.gezogen += 1
        return self.werte.pop(0)


def test_standardbelohnung_von_hand():
    # Verbesserung 6 bei Kosten 1 und mittlerer Kante 10: 6 / 10; bei Kosten 5: 6 / 50; mehr als eine Kante je Auswertung wird auf 1 gekappt
    assert SE.reward_standard(-6.0, 1, 10.0) == pytest.approx(6 / 10)
    assert SE.reward_standard(-6.0, 5, 10.0) == pytest.approx(6 / 50)
    assert SE.reward_standard(-25.0, 1, 10.0) == 1.0
    assert SE.reward_standard(0.0, 1, 10.0) == 0.0 and SE.reward_standard(3.0, 1, 10.0) == 0.0 and SE.reward_standard(-1e-10, 1, 10.0) == 0.0
    f = SE.standard_reward(10.0)
    for delta, kosten in ((-6.0, 1), (-6.0, 5), (-25.0, 1), (0.0, 1), (4.0, 3)):
        assert f(delta, kosten, True) == SE.reward_standard(delta, kosten, 10.0)


def test_zufallsauswahl_zieht_wie_die_eingebaute_auswahl():
    z = SE.new_rand(5)
    assert SE.choose_rand(z, Feste([0.0])) == 0 and SE.choose_rand(z, Feste([0.39])) == 1 and SE.choose_rand(z, Feste([0.999])) == 4
    einer = Feste([])
    assert SE.choose_rand(SE.new_rand(1), einer) == 0 and einer.gezogen == 0      # eine einzige Zugart: keine Zufallszahl
    SE.update_rand(z, 2, 1.0)
    assert z == {"m": 5}


def test_choice_function_ein_schritt_von_hand():
    z = SE.new_cf(3)
    assert z["phi"] == 0.5 and z["prev"] == -1
    # Anfang: alle Werte 0, nur das Rauschen u * 1e-9 entscheidet: der Arm mit dem größten u gewinnt, je Arm eine Zufallszahl
    rng = Feste([0.2, 0.9, 0.5])
    assert SE.choose_cf(z, rng) == 1 and rng.gezogen == 3
    SE.update_cf(z, 1, 0.4)                       # Erfolg: f1[1] = 0,4 + 0,9 * 0 = 0,4; phi = 0,99; Vorgänger = 1; Schritt 1
    assert z["f1"] == [0.0, 0.4, 0.0] and z["phi"] == 0.99 and z["prev"] == 1 and z["step"] == 1 and z["last"] == [0, 1, 0]
    assert z["f2"] == [[0.0] * 3 for _ in range(3)]                                # beim ersten Schritt gibt es keinen Vorgänger
    # zweiter Schritt: Arm 1: 0,99 * (0,4 / 0,4 + 0) + 0,01 * 0 / 50 = 0,99; Arme 0 und 2: 0,99 * 0 + 0,01 * 1 / 50 = 0,0002
    assert SE.choose_cf(z, Feste([0.9, 0.0, 0.9])) == 1
    SE.update_cf(z, 1, 0.0)                       # kein Erfolg: f1[1] = 0 + 0,9 * 0,4 = 0,36; f2[1][1] = 0; phi = 0,98
    assert z["f1"][1] == pytest.approx(0.36) and z["f2"][1][1] == 0.0 and z["phi"] == pytest.approx(0.98) and z["step"] == 2
    SE.update_cf(z, 2, 0.5)                       # f2[Vorgänger 1][2] = 0,5
    assert z["f2"][1][2] == 0.5 and z["prev"] == 2 and z["last"] == [0, 2, 3]


def test_choice_function_phi_faellt_nicht_unter_die_grenze_und_wartezeit_ist_gekappt():
    z = SE.new_cf(2)
    for _ in range(200):
        SE.update_cf(z, 0, 0.0)
    assert z["phi"] == pytest.approx(C.CF_PHI_MIN)
    # Arm 1 wartet 200 Schritte, gekappt auf 50: Wert (1 - 0,01) * 50 / 50 = 0,99 gegen 0 für Arm 0
    assert SE.choose_cf(z, Feste([0.5, 0.5])) == 1


def test_lernautomat_ein_schritt_von_hand():
    z = SE.new_laut(4)
    assert z["p"] == [0.25] * 4
    assert SE.choose_laut(z, Feste([0.10])) == 0 and SE.choose_laut(z, Feste([0.60])) == 2 and SE.choose_laut(z, Feste([0.9999])) == 3
    SE.update_laut(z, 2, 0.0)                     # kein Erfolg: nichts ändert sich (reward-inaction)
    assert z["p"] == [0.25] * 4
    SE.update_laut(z, 2, 0.3)                     # Erfolg: 0,25 * 0,95 = 0,2375; Arm 2: 0,2375 + 0,05 = 0,2875; Summe 1
    assert z["p"] == pytest.approx([0.2375, 0.2375, 0.2875, 0.2375]) and sum(z["p"]) == pytest.approx(1.0)


def test_lernautomat_untergrenze():
    z = SE.new_laut(3)
    for _ in range(500):
        SE.update_laut(z, 0, 1.0)
    assert min(z["p"]) >= C.LAUT_BODEN / 1.02 and sum(z["p"]) == pytest.approx(1.0) and z["p"][0] > 0.95


def test_q_lernen_ein_schritt_von_hand():
    z = SE.new_q(3)
    SE.update_q(z, 1, 0.8)                        # Q[1] = 0 + 0,1 * (0,8 + 0,5 * 0 - 0) = 0,08
    assert z["q"] == pytest.approx([0.0, 0.08, 0.0])
    SE.update_q(z, 1, 0.0)                        # Q[1] = 0,08 + 0,1 * (0 + 0,5 * 0,08 - 0,08) = 0,076
    assert z["q"][1] == pytest.approx(0.076)
    rng = Feste([0.5])                            # u >= eps: gierig, eindeutiger bester Arm, keine weitere Zufallszahl
    assert SE.choose_q(z, rng) == 1 and rng.gezogen == 1
    assert SE.choose_q(z, Feste([0.05, 0.7])) == 2                                 # u < eps = 0,1: gleichverteilt, int(0,7 * 3) = 2
    frisch = SE.new_q(4)
    assert SE.choose_q(frisch, Feste([0.5, 0.26])) == 1                            # Gleichstand aller vier: gleichverteilt unter den besten


@pytest.mark.parametrize("regel", C.REGELN)
def test_regel_waehlt_nur_arme_der_menge_und_ist_reproduzierbar(regel):
    def lauf(seed):
        sel = SE.make_selector(regel, 5, 10.0)
        rng = BlockSplitMix64(seed)
        arme = []
        for k in range(400):
            a = sel.choose(rng)
            arme.append(a)
            sel.update(a, -3.0 if (a == 2 and k % 3 == 0) else 1.0, 1, False)
        return arme
    a = lauf(1)
    assert set(a) <= set(range(5)) and a == lauf(1) and a != lauf(2)


@pytest.mark.parametrize("regel", C.LERNREGELN)
def test_lernregel_bevorzugt_den_arm_der_belohnt_wird(regel):
    sel = SE.make_selector(regel, 4, 10.0)
    rng = BlockSplitMix64(5)
    zahl = [0] * 4
    for _ in range(3000):
        a = sel.choose(rng)
        zahl[a] += 1
        sel.update(a, -8.0 if a == 3 else 2.0, 1, a == 3)
    assert zahl[3] == max(zahl) and zahl[3] > 0.5 * sum(zahl)


def test_selector_mit_zufallsauswahl_ist_bitgleich_zur_eingebauten_auswahl(hand):
    D, t0 = hand
    for arms in (C.ALLE_ZUGARTEN, (2, 3, 7), (6,)):
        a = run_search(D, t0, 300, arms, "rr", BlockSplitMix64(3), trace=True)
        b = run_search(D, t0, 300, arms, "rr", BlockSplitMix64(3), trace=True, selector=SE.make_selector("rand", len(arms), S.tour_cost(D, t0) / 6))
        assert a["trace"] == b["trace"] and a["best"] == b["best"] and a["apps"] == b["apps"]


def test_tabelle_der_regeln_ist_vollstaendig_und_erweiterbar():
    assert tuple(SE.REGEL_FUNKTIONEN) == C.REGELN and set(C.REGEL_ANZEIGE) == set(C.REGELN)
    eigene = dict(SE.REGEL_FUNKTIONEN, immer0=(SE.new_rand, lambda state, rng: 0, SE.update_rand))
    sel = SE.Selector("immer0", 3, SE.standard_reward(1.0), funktionen=eigene)
    assert sel.choose(None) == 0
