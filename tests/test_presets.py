"""Beispiele (Presets): Vollständigkeit, gültige Werte, Standard-Beispiel = Standardeinstellungen, Namen passen zu den Werten, Rechenlast."""

import zgm_constants as C
import zgm_evaluation as EV
import zgm_presets as P
import zgm_texts  # noqa: F401  (füllt C.PRESET_HELP aus der eingefrorenen Messung)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 10
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid_for_their_widgets():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.options is not None:
                assert preset[key] in spec.options, (name, key)
            else:
                assert spec.lo <= preset[key] <= spec.hi, (name, key)
        assert any(preset[f"z{h}"] for h in range(C.K)), name            # keine leere Zugmenge


def test_default_preset_equals_the_default_settings():
    erstes = next(iter(C.PRESETS))
    assert erstes == "Alle acht Zugarten"
    assert C.PRESETS[erstes] == {key: P.SETTING_SPECS[state_key].default for key, state_key in P.PRESET_KEYS.items()}
    assert C.PRESETS[erstes]["akz"] == "rr"                                # Standard-Akzeptanz dieser Demo: Rekord-zu-Rekord


def test_setting_specs_cover_every_preset_key_and_presets_are_distinct():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)   # sonst wären zwei zugleich hervorgehoben


def _menge(preset):
    return tuple(h for h in range(C.K) if preset[f"z{h}"])


def test_preset_namen_passen_zu_den_werten():
    """Vertauschte Beschriftungen: die Menge im Namen ist die Menge des Beispiels, Akzeptanz und Budget ebenso."""
    p = C.PRESETS
    assert _menge(p["Alle acht Zugarten"]) == C.ALLE_ZUGARTEN
    assert _menge(p["Die stärkste Zugart fehlt"]) == C.MENGEN["ohne_2opt_b5"]
    assert _menge(p["Eine schwache Zugart fehlt"]) == C.MENGEN["ohne_dbridge"]
    assert _menge(p["Ohne die 2-opt-Familie"]) == C.MENGEN["ohne_2opt_Familie"] == (0, 1, 4, 5, 6)
    assert _menge(p["Nur schwache Zugarten"]) == C.MENGEN["nur_schwache"] == (0, 4, 5, 6)
    assert (p["Feste Teilmenge, kleines Budget"]["akz"], p["Feste Teilmenge, kleines Budget"]["budget"]) == ("ob", 50)
    assert (p["Feste Teilmenge, großes Budget"]["akz"], p["Feste Teilmenge, großes Budget"]["budget"], p["Feste Teilmenge, großes Budget"]["instanzen"]) == ("ob", 400, 4)
    assert p["Lernen unter Late Acceptance"]["akz"] == "la" and _menge(p["Lernen unter Late Acceptance"]) == C.ALLE_ZUGARTEN
    assert p["Lernen ohne 2opt_b5"]["akz"] == "la" and _menge(p["Lernen ohne 2opt_b5"]) == C.MENGEN["ohne_2opt_b5"]
    assert p["Handbeispiel: sechs Städte"]["hand"] is True and sum(1 for x in p.values() if x["hand"]) == 1
    for preset in p.values():
        assert preset["seed"] == 0 and preset["laeufe"] == 1 and preset["regel"] == "rand" and preset["n"] == 30


def test_presets_bleiben_unter_der_rechengrenze_und_ueber_der_mindestzahl():
    """Je Beispiel die vier Vergleiche (1, 2, 2 bis 400·n, 4 Varianten): keiner wird gekürzt, jeder hat mindestens 4 Instanzen."""
    for name, preset in C.PRESETS.items():
        for varianten, f in ((1, preset["budget"]), (2, preset["budget"]), (2, C.STUFEN[-1]), (4, preset["budget"])):
            plan = EV.plan_runs(preset["n"], f, varianten, preset["instanzen"], preset["laeufe"])
            assert not plan["gekuerzt"] and plan["instanzen"] >= C.MIN_INSTANZEN and plan["kosten"] <= C.RECHENGRENZE, (name, varianten, f)
