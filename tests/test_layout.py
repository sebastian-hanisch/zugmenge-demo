"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Beispiel hervorgehoben.

Die Hervorhebung ist zustandslos (`aktives_preset` vergleicht jeden Regler aus SETTING_SPECS mit dem Beispiel). Der Test unten stellt
sicher, dass wirklich JEDER Regler der Seitenleiste dort steht: sonst bliebe das Beispiel trotz Änderung markiert."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import zgm_constants as C
import zgm_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio", "toggle", "checkbox", "text_input")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    """Button-Typ je Beispiel-Name (die Schnellstart-Buttons der Seitenleiste)."""
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in C.PRESETS}


def _regler(at, key):
    for art in REGLER_ARTEN:
        try:
            return getattr(at.sidebar, art)(key=key)
        except KeyError:
            continue
    raise AssertionError(f"Regler {key} steht nicht in der Seitenleiste")


def _anderer_wert(spec, wert):
    if spec.options is not None:
        return next(o for o in spec.options if o != wert)
    return spec.hi if wert != spec.hi else spec.lo


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button][: len(C.PRESETS)] == list(C.PRESETS)  # die ersten Buttons der Seitenleiste
    assert not [b for b in at.main.button if b.label in C.PRESETS]


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))  # das Stylesheet setzt an der Klasse des Containers an
    assert at.title[0].value.startswith("🧰 Die Zugmenge entscheidet")
    for wort in ("Konfiguration", "Parameterwahl", "Verfahrenswahl", "Wahlregeln"):
        assert wort not in at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    typen = _typen(_app())
    assert [name for name, typ in typen.items() if typ == "primary"] == [next(iter(C.PRESETS))]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]
    at.run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]


def test_jeder_regler_der_seitenleiste_steht_in_setting_specs():
    at = _app()
    schluessel = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
    assert schluessel == set(P.SETTING_SPECS)


def test_jeder_regler_der_app_hat_einen_schluessel_und_die_grenzen_aus_dem_presets_modul():
    at = _app()
    bekannt = set(P.SETTING_SPECS) | {"schritt_slider"}
    for art in REGLER_ARTEN:
        for w in getattr(at, art):
            assert w.key in bekannt, (art, w.label)
    for key in ("instanzen_slider", "laeufe_slider"):
        regler = at.sidebar.slider(key=key)
        assert (regler.min, regler.max, regler.value) == (*P.bounds(key), P.SETTING_SPECS[key].default)
    seed = at.sidebar.number_input(key="seed_input")
    assert (seed.min, seed.max) == (0, C.SEED_MAX)
    for key in ("familie_select", "n_select", "akz_select", "budget_select", "regel_select"):
        assert tuple(at.sidebar.selectbox(key=key).options) == tuple(str(o) if not isinstance(o, str) else o for o in P.options(key)) or \
            len(at.sidebar.selectbox(key=key).options) == len(P.options(key))


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(state_key):
    at = _app()
    spec = P.SETTING_SPECS[state_key]
    regler = _regler(at, state_key)
    regler.set_value(_anderer_wert(spec, regler.value)).run()
    assert not at.exception
    name = next(iter(C.PRESETS))
    typen = _typen(at)
    assert typen[name] != "primary"                                  # das Standard-Beispiel ist nicht mehr markiert
    assert list(typen.values()).count("primary") <= 1                # höchstens ein anderes, das genau diese Einstellung ist (z. B. andere Akzeptanz)
    # erneutes Anklicken markiert wieder
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert _typen(at)[name] == "primary"


def test_expander_in_der_vorgesehenen_reihenfolge():
    at = _app()
    titel = [e.label for e in at.expander]
    for name in ("💬 In einfachen Worten", "So funktioniert die Suche über eine Zugmenge", "🔧 Alle Mengen im Vergleich (eingefroren)", "🧮 Handbeispiel",
                 "📐 Mathematische Formulierung"):
        assert name in titel
    assert titel.index("💬 In einfachen Worten") == 0 and titel[-1] == "📐 Mathematische Formulierung"
    assert titel.index("🔧 Alle Mengen im Vergleich (eingefroren)") < titel.index("🧮 Handbeispiel")
    kopf = [s.value for s in at.subheader]
    assert [k[:15] for k in kopf[:4]] == [f"🔬 Kernfrage {i}: "[:15] for i in (1, 2, 3, 4)] and kopf[-1] == "🚧 Wo die Annahmen enden"
