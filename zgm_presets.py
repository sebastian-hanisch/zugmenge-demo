"""Permalink (Begrenzen, Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

SETTING_SPECS: alle Regler der Seitenleiste; sie stehen im Permalink und entscheiden, welches Beispiel hervorgehoben ist."""

import random
from dataclasses import dataclass

import streamlit as st

import zgm_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None       # Auswahlregler: erlaubte Werte


def _bool(text) -> bool:
    return str(text).strip().lower() in ("1", "true", "ja")


SETTING_SPECS = {
    "familie_select": SettingSpec("familie", str, C.DEFAULT_FAMILIE, options=C.FAMILIEN),
    "n_select": SettingSpec("n", int, C.DEFAULT_N, options=C.N_GEMESSEN),
    "instanzen_slider": SettingSpec("instanzen", int, C.DEFAULT_INSTANZEN, C.INSTANZEN_MIN, C.INSTANZEN_MAX),
    "laeufe_slider": SettingSpec("laeufe", int, C.DEFAULT_LAEUFE, C.LAEUFE_MIN, C.LAEUFE_MAX),
    "akz_select": SettingSpec("akz", str, C.DEFAULT_AKZ, options=C.AKZEPTANZEN),
    "budget_select": SettingSpec("budget", int, C.DEFAULT_BUDGET, options=C.STUFEN),
    "regel_select": SettingSpec("regel", str, C.DEFAULT_REGEL, options=C.REGELN),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "hand_toggle": SettingSpec("hand", _bool, False, options=(False, True)),
}
for _h in range(C.K):
    SETTING_SPECS[f"z{_h}_check"] = SettingSpec(f"z{_h}", _bool, True, options=(False, True))
PRESET_KEYS = {"familie": "familie_select", "n": "n_select", "instanzen": "instanzen_slider", "laeufe": "laeufe_slider", "akz": "akz_select",
               "budget": "budget_select", "regel": "regel_select", "seed": "seed_input", "hand": "hand_toggle"}
PRESET_KEYS.update({f"z{_h}": f"z{_h}_check" for _h in range(C.K)})
ZUGART_KEYS = tuple(f"z{_h}_check" for _h in range(C.K))


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    """(Minimum, Maximum) eines Zahlenreglers."""
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def options(state_key) -> tuple:
    """Erlaubte Werte eines Auswahlreglers."""
    return SETTING_SPECS[state_key].options


def clamp(spec: SettingSpec, value):
    """Wert aus der Adresszeile auf den Regler abbilden: Zahlen begrenzen, Auswahlwerte einrasten (Zahl: nächster Wert; Text: nur gültige)."""
    if spec.options is not None:
        if value in spec.options:
            return value
        if spec.caster is int:
            return min(spec.options, key=lambda o: (abs(o - value), o))
        return None
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            value = clamp(spec, value)
            if value is not None:
                st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration (Schalter als 1 oder 0)."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(int(value)) if isinstance(value, bool) else str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Beispiel ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispiel laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)


def selected_set(state) -> tuple[int, ...]:
    """Die angekreuzten Zugarten als sortiertes Tupel (leer, wenn keine angekreuzt ist)."""
    return tuple(h for h in range(C.K) if state.get(f"z{h}_check", True))
