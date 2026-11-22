"""App-Tests der Demo (zusätzlich zum allgemeinen Rauchtest in test_app.py): jedes Beispiel, der Schritt-Regler, die Einzelabläufe auf Klick,
Permalink, leere Zugmenge, eine einzelne Zugart, alle Regler am Maximum."""

import os
import re

import pytest
from streamlit.testing.v1 import AppTest

import zgm_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _meldungen(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning)]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_beispiel_laedt_ohne_fehler_und_zeigt_alle_vier_kernfragen(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, (name, [str(e) for e in at.exception])
    assert len([s for s in at.subheader if s.value.startswith("🔬 Kernfrage")]) == 4
    assert len(at.get("plotly_chart")) >= 5
    texte = _meldungen(at)
    assert any("Lernregeln" in t or "Lernregel" in t for t in texte)                 # das eingefrorene Verdikt der Zelle steht immer da
    hand = next(e for e in at.expander if e.label == "🧮 Handbeispiel")
    assert hand.proto.expanded == bool(C.PRESETS[name]["hand"])


def test_schritt_regler_zeigt_start_und_spaetere_zustaende():
    at = _fresh_app()
    regler = at.slider(key="schritt_slider")
    assert regler.value == 0 and regler.max > 0
    regler.set_value(regler.max).run(timeout=TIMEOUT)
    assert not at.exception
    # anderes Budget und andere Menge: der Regler wird auf die neue Zahl der Züge begrenzt, kein Fehler
    at.sidebar.button(key="preset_Nur schwache Zugarten").click().run(timeout=TIMEOUT)
    assert not at.exception and at.slider(key="schritt_slider").value <= at.slider(key="schritt_slider").max


def test_einzelablaeufe_auf_klick_und_verschwinden_bei_neuer_einstellung():
    at = _fresh_app()
    vorher = len(at.dataframe)
    at.button(key="einzeln_knopf").click().run(timeout=TIMEOUT)
    assert not at.exception and len(at.dataframe) == vorher + 1
    assert any("Positiv: ohne die Zugart ist der Abstand kleiner" in c.value for c in at.caption)
    at.sidebar.selectbox(key="akz_select").set_value("ob").run(timeout=TIMEOUT)
    assert not at.exception and len(at.dataframe) == vorher                           # kein Ergebnis einer anderen Einstellung


def test_alle_acht_zeigt_hinweis_statt_vergleich_und_eine_abgewaehlte_zugart_den_vergleich():
    at = _fresh_app()
    assert any("es fehlt nichts" in t for t in _meldungen(at))
    at.sidebar.checkbox(key="z7_check").set_value(False).run(timeout=TIMEOUT)
    assert not at.exception and not any("es fehlt nichts" in t for t in _meldungen(at))
    assert any("Mit der Menge „ohne 2opt_b5“" in t for t in _meldungen(at))
    assert any(c.value.startswith("Eingefrorene Messung (120 Instanzen") for c in at.caption)


def test_leere_zugmenge_gibt_eine_meldung_und_keinen_fehler():
    at = _fresh_app()
    for h in range(C.K):
        at.sidebar.checkbox(key=f"z{h}_check").set_value(False)
    at.run(timeout=TIMEOUT)
    assert not at.exception and any("Die Zugmenge ist leer" in t for t in _meldungen(at))


def test_eine_einzelne_zugart_und_eine_unbenannte_menge():
    at = _fresh_app()
    for h in range(C.K):
        at.sidebar.checkbox(key=f"z{h}_check").set_value(h == 6)
    at.run(timeout=TIMEOUT)
    assert not at.exception and any("nur eine Zugart" in t for t in _meldungen(at))
    at.sidebar.checkbox(key="z1_check").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception and any("keine eingefrorene Messung" in c.value for c in at.caption)


def test_feste_teilmenge_als_gewaehlte_menge_vergleicht_mit_allen_acht():
    at = _fresh_app()
    for h in range(C.K):
        at.sidebar.checkbox(key=f"z{h}_check").set_value(h in C.T3)
    at.run(timeout=TIMEOUT)
    assert not at.exception and any("die gewählte Menge ist die feste Teilmenge selbst" in c.value for c in at.caption)


def test_alle_regler_am_maximum_bleiben_unter_der_rechengrenze_und_melden_die_kuerzung():
    at = _fresh_app()
    at.sidebar.selectbox(key="n_select").set_value(60)
    at.sidebar.selectbox(key="budget_select").set_value(400)
    at.sidebar.slider(key="laeufe_slider").set_value(C.LAEUFE_MAX)
    at.sidebar.selectbox(key="akz_select").set_value("la")
    at.sidebar.selectbox(key="regel_select").set_value("cf")
    at.sidebar.checkbox(key="z0_check").set_value(False)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("gekürzt, Grenze 500 000 Auswertungen" in c.value for c in at.caption)


def test_wenige_instanzen_geben_kein_urteil():
    at = _fresh_app()
    at.sidebar.checkbox(key="z7_check").set_value(False)
    at.sidebar.slider(key="instanzen_slider").set_value(2)
    at.run(timeout=TIMEOUT)
    assert not at.exception and sum("kein Urteil möglich (mindestens 4)" in t for t in _meldungen(at)) >= 3


def test_permalink_wird_begrenzt_uebernommen():
    at = AppTest.from_file(APP_PATH)
    for key, wert in (("n", "47"), ("akz", "la"), ("budget", "9999"), ("seed", "-3"), ("familie", "gitter"), ("z7", "0"), ("instanzen", "99"), ("regel", "xx")):
        at.query_params[key] = wert
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.selectbox(key="n_select").value == 60 and at.sidebar.selectbox(key="akz_select").value == "la"
    assert at.sidebar.selectbox(key="budget_select").value == 400 and at.sidebar.number_input(key="seed_input").value == 0
    assert at.sidebar.selectbox(key="familie_select").value == "gitter" and at.sidebar.checkbox(key="z7_check").value is False
    assert at.sidebar.slider(key="instanzen_slider").value == C.INSTANZEN_MAX and at.sidebar.selectbox(key="regel_select").value == "rand"


def test_texte_ohne_planungswoerter():
    at = _fresh_app()
    texte = " ".join([m.value for m in at.markdown] + [c.value for c in at.caption] + _meldungen(at))
    for wort in ("Preset", "Hook", "Kante der Linie", "Saatwert", "trägt", "tragen", "Schwanz", "läuft lokal"):
        assert wort not in texte, wort
    assert not re.search(r"Stück \d", texte)                         # keine Nummern aus der Planung („Stück 3“)
