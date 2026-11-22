"""Je Beispiel die Verdikt-Zeile, die die App mit den festen Zufalls-Seeds zeigt (8 oder 4 Instanzen, ein Lauf): festgehalten, nicht ausgesucht.

Die Hilfetexte der Beispiele nennen die Erwartung aus der eingefrorenen Messung (120 Instanzen); mit 8 Instanzen kommt oft „kein belegter
Unterschied“ heraus. Dieser Test hält fest, was die App tatsächlich meldet, und prüft, dass kein Beispiel dem eingefrorenen Befund im
Vorzeichen widerspricht, wo es ein Urteil fällt."""

import pytest

import zgm_band as B
import zgm_constants as C
import zgm_evaluation as EV
import zgm_experiments as E
import zgm_texts  # noqa: F401  (füllt C.PRESET_HELP aus der eingefrorenen Messung; ohne den Import ist es allein gestartet leer)

REFS = E.load_json("zgm_refs.json")
K = "Voraussetzung"


def _einstellung(name):
    p = C.PRESETS[name]
    return p, tuple(h for h in range(C.K) if p[f"z{h}"])


def _menge_gegen_voll(name):
    p, menge = _einstellung(name)
    live = E.measure(REFS, p["familie"], p["n"], p["seed"], p["instanzen"], p["laeufe"], p["akz"], {"voll": (C.ALLE_ZUGARTEN, "rand"), "S": (menge, "rand")}, (p["budget"],))
    r = E.diff_ci(E.level(live, "voll"), E.level(live, "S"))
    return r, EV.verdict_menge(r["d"], r["lo"], r["hi"], r["m"], E.set_label(menge), K)


@pytest.mark.parametrize("name,menge,kind,d", [
    ("Die stärkste Zugart fehlt", "ohne_2opt_b5", "rauschen", -0.86),
    ("Eine schwache Zugart fehlt", "ohne_dbridge", "rauschen", 0.18),
    ("Ohne die 2-opt-Familie", "ohne_2opt_Familie", "schadet", -3.69),
    ("Nur schwache Zugarten", "nur_schwache", "schadet", -7.34),
])
def test_beispiele_zur_menge(name, menge, kind, d):
    r, v = _menge_gegen_voll(name)
    assert v["kind"] == kind and r["d"] == pytest.approx(d, abs=0.006) and r["m"] == 8
    eingefroren = B.set_vs_full("rr", menge, 0)
    if kind != "rauschen":                                           # wo das Beispiel urteilt, urteilt die eingefrorene Messung gleich
        assert eingefroren["klasse"] == "minus"
    assert name in C.PRESET_HELP and EV.de_v(eingefroren["d"]) in C.PRESET_HELP[name]


def test_beispiel_alle_acht_zeigt_den_beitrag_der_familie():
    p, menge = _einstellung("Alle acht Zugarten")
    live = E.measure(REFS, p["familie"], p["n"], p["seed"], p["instanzen"], p["laeufe"], p["akz"], {"S": (menge, "rand")}, (p["budget"],))
    sh = E.family_shares(live["zaehler"]["S"])
    v = EV.verdict_beitrag(sh["e"], sh["a"], menge, sh["laeufe"], K)
    assert v["kind"] == "fam_liefert" and sh["e_fam"] == pytest.approx(0.82, abs=0.006) and sh["a_fam"] == pytest.approx(7 / 12, abs=0.005) and sh["laeufe"] == 8
    assert B.contribution("rr", "voll", "rand", 0)["e_fam"] >= C.BEITRAG_VIEL          # die eingefrorene Messung fällt dasselbe Urteil


@pytest.mark.parametrize("name,arten,klein", [
    ("Feste Teilmenge, kleines Budget", ["gleich", "gleich", "gleich"], 1.77),
    ("Feste Teilmenge, großes Budget", ["t3_vorn", "gleich", "gleich"], 4.09),
])
def test_beispiele_zur_festen_teilmenge(name, arten, klein):
    p, menge = _einstellung(name)
    live = E.measure(REFS, p["familie"], p["n"], p["seed"], p["instanzen"], p["laeufe"], p["akz"], {"S": (menge, "rand"), "T3": (C.T3, "rand")}, C.STUFEN)
    stufen = []
    for j in range(3):
        r = E.diff_ci(E.level(live, "S", j), E.level(live, "T3", j))
        stufen.append((r["d"], r["lo"], r["hi"]))
    v = EV.verdict_teilmenge(stufen, p["instanzen"], "alle acht", K)
    assert v["kind"] == "gemischt" and v["je_stufe"] == arten and stufen[0][0] == pytest.approx(klein, abs=0.006)
    assert B.set_vs_full("ob", "T3", 0)["klasse"] == "plus" and B.set_vs_full("ob", "T3", 2)["klasse"] == "minus"   # eingefroren: Kreuzung unter „nur besser“


@pytest.mark.parametrize("name,regel,kind,g", [
    ("Lernen unter Late Acceptance", "cf", "rauschen", -1.08),
    ("Lernen unter Late Acceptance", "laut", "rauschen", -0.48),
    ("Lernen unter Late Acceptance", "q", "rauschen", -1.20),
    ("Lernen ohne 2opt_b5", "cf", "rauschen", 0.01),
    ("Lernen ohne 2opt_b5", "laut", "rauschen", 1.30),
    ("Lernen ohne 2opt_b5", "q", "rauschen", 0.78),
    ("Alle acht Zugarten", "q", "hilft", 2.26),
    ("Alle acht Zugarten", "cf", "rauschen", 0.13),
])
def test_beispiele_zum_lernen(name, regel, kind, g):
    p, menge = _einstellung(name)
    live = E.measure(REFS, p["familie"], p["n"], p["seed"], p["instanzen"], p["laeufe"], p["akz"], {r: (menge, r) for r in C.REGELN}, (p["budget"],))
    r = E.diff_ci(E.level(live, "rand"), E.level(live, regel))
    assert EV.verdict_lernregel(r["d"], r["lo"], r["hi"], r["m"], regel, K)["kind"] == kind and r["d"] == pytest.approx(g, abs=0.006)


def test_handbeispiel_rechnet_wie_das_erste_beispiel():
    a, b = dict(C.PRESETS["Handbeispiel: sechs Städte"]), dict(C.PRESETS["Alle acht Zugarten"])
    assert a.pop("hand") is True and b.pop("hand") is False and a == b
