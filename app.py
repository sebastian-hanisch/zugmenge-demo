"""Die Zugmenge entscheidet - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Dieselbe Suche über acht Zugarten der Rundtour, aber die Zugmenge wird verändert: einzelne Zugarten oder Gruppen weglassen, eine feste
Teilmenge, dazu drei Regeln, die während des Laufs lernen. Vier Kernfragen mit Live-Rechnung und der eingefrorenen Messung daneben.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import zgm_band as B
import zgm_constants as C
import zgm_evaluation as EV
import zgm_exact as X
import zgm_experiments as E
import zgm_layout as L
import zgm_presets as P
import zgm_stats as ST
import zgm_texts as T
import zgm_visualization as V

import modul_frisch

modul_frisch.aktualisieren(__file__)

st.set_page_config(page_title="Die Zugmenge entscheidet – Sebastian Hanisch", layout="wide")

KURVE = tuple(sorted({16 * k for k in range(1, C.KURVE_PUNKTE + 1)} | set(C.STUFEN)))     # Budgetfaktoren der Verlaufskurve (bis 400·n)


@st.cache_data(show_spinner=False)
def _refs():
    return E.load_json("zgm_refs.json")


@st.cache_data(show_spinner=False)
def _measure(familie, n, seed, m, laeufe, akz, varianten, stufen):
    """varianten: Tupel (Schlüssel, Zugmenge, Auswahlregel)."""
    return E.measure(_refs(), familie, n, seed, m, laeufe, akz, {key: (menge, regel) for key, menge, regel in varianten}, stufen)


@st.cache_data(show_spinner=False)
def _trace(familie, n, idx, menge, regel, akz, budget):
    r = E.run_set(familie, n, idx, 0, menge, regel, akz, budget, trace=True)
    return dict(start=r["start"], best=r["best"], spur=r["trace"], t0=r["t0"], punkte=E.best_points(r["start"], r["trace"]))


@st.cache_data(show_spinner=False)
def _zustand(familie, n, idx, menge, regel, akz, budget, k):
    lauf = _trace(familie, n, idx, menge, regel, akz, budget)
    _, D = E.instance(familie, n, idx)
    tour = E.replay(lauf["t0"], lauf["spur"], k)
    return X.improve_probs(tour, D, exakt=False)


@st.cache_data(show_spinner=False)
def _hand():
    D = X.hand_matrix()
    p = X.improve_probs(X.HAND_T0, D)
    zeilen = []
    for name in X.HAND_MENGEN:
        menge = C.MENGEN[name]
        zeilen.append(dict(name=name, kosten=sum(C.KOSTEN[h] for h in menge), k=X.k_of_set(menge, p), e20=X.hand_expected_best(menge, 20),
                           e80=X.hand_expected_best(menge, 80), optima=sum(1 for t in X.all_tours(6) if X.is_local_optimum(t, D, menge))))
    return dict(p=p, zeilen=zeilen, optima=[sum(1 for t in X.all_tours(6) if X.is_local_optimum(t, D, (h,))) for h in range(C.K)])


def _knopf(schluessel: str, text: str, parameter: tuple) -> bool:
    """Live-Rechnung auf Klick; das Ergebnis bleibt, solange die Einstellung dieselbe ist."""
    if st.button(text, key=f"{schluessel}_knopf"):
        st.session_state[f"{schluessel}_parameter"] = parameter
    return st.session_state.get(f"{schluessel}_parameter") == parameter


def _referenz_hinweis(unterboten: int):
    if unterboten:
        st.caption(f"In {unterboten} Instanz(en) hat ein Lauf dieser Rechnung den gespeicherten besten bekannten Wert unterboten; dort gilt der neue kleinste Wert als Referenz.")


def _ci(werte):
    ci = ST.bootstrap_ci(werte, C.ZWECK_BOOT)
    return (None, None) if ci is None else ci


# --- Kopf, Einleitung, Erklärung ---------------------------------------------------------------------------------------------------------------
st.html(L.kopf_css(L.dunkles_design()))
with st.container(key="kopf"):
    st.title(T.TITEL)
st.markdown(T.INTRO)

with st.expander("💬 In einfachen Worten"):
    st.markdown(T.EINFACH)

with st.expander("So funktioniert die Suche über eine Zugmenge", expanded=True):
    st.markdown(T.SO_FUNKTIONIERT)
    st.markdown("**Die acht Zugarten**")
    st.markdown(T.ZUGARTEN_TABELLE)
    st.markdown("**Die Akzeptanzregeln**")
    st.markdown(T.AKZEPTANZ_TABELLE)
    st.markdown("**Die Auswahlregeln**")
    st.markdown(T.REGEL_TABELLE)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

P.load_permalink_settings()
P.init_session_state_defaults()

with st.sidebar:
    P.sidebar_presets()  # Schnellstart oben, das aktive Beispiel ist hervorgehoben
    st.header("⚙️ Instanz")
    familie = st.selectbox("Familie der Instanzen", P.options("familie_select"), format_func=C.FAMILIEN_ANZEIGE.get, key="familie_select",
                           help="Gleichverteilte Städte, fünf Gruppen oder ein Gitter mit Rauschen.")
    n = int(st.selectbox("Städte n", P.options("n_select"), key="n_select", help="Nur 30 oder 60: nur dort liegt die eingefrorene Messung vor."))
    m_wunsch = int(st.slider("Instanzen je Vergleich", *P.bounds("instanzen_slider"), key="instanzen_slider",
                             help="So viele Instanzen rechnet jeder Live-Vergleich. Unter 4 Instanzen gibt es kein Urteil."))
    laeufe_wunsch = int(st.slider("Läufe je Instanz", *P.bounds("laeufe_slider"), key="laeufe_slider",
                                  help="Läufe mit verschiedenen Zufalls-Seeds der Suche; je Instanz zählt das Mittel."))
    st.header("🔍 Suche")
    akz = st.selectbox("Akzeptanzregel", P.options("akz_select"), format_func=C.AKZ_ANZEIGE.get, key="akz_select",
                       help="Entscheidet, ob ein Vorschlag bleibt; die Regeln stehen oben in der Tabelle.")
    f = int(st.selectbox("Budget", P.options("budget_select"), format_func=C.STUFEN_ANZEIGE.get, key="budget_select",
                         help="Auswertungen je Lauf als Vielfaches der Städtezahl n."))
    regel = st.selectbox("Auswahlregel", P.options("regel_select"), format_func=C.REGEL_ANZEIGE.get, key="regel_select",
                         help="Gilt für die Kernfragen 1 bis 3. Kernfrage 4 vergleicht immer die Zufallsauswahl mit allen drei Lernregeln.")
    st.header("🧰 Zugmenge")
    st.caption("Mindestens eine Zugart ankreuzen.")
    for h in range(C.K):
        st.checkbox(f"{C.HNAMEN[h]} ({C.HNAMEN_ANZEIGE[C.HNAMEN[h]]})", key=f"z{h}_check")
    st.header("🎲 Zufall")
    seed = int(st.number_input("Zufalls-Seed", *P.bounds("seed_input"), key="seed_input", step=1,
                               help="Der Zufalls-Seed s wählt die Instanzen 8·s bis 8·s + 7 der Familie."))
    hand = st.toggle("Handbeispiel aufklappen", key="hand_toggle", help="Klappt unten das Handbeispiel mit sechs Städten auf.")
    st.button("🎲 Neue Instanzen generieren", width="stretch", on_click=P.randomize_seed)

menge = P.selected_set(st.session_state)
if not menge:
    st.warning("Die Zugmenge ist leer. Gerechnet wird mit allen acht Zugarten, bis mindestens eine Zugart angekreuzt ist.")
    menge = C.ALLE_ZUGARTEN
voll = C.ALLE_ZUGARTEN
name_menge = E.set_name(menge)
label = E.set_label(menge)
j_stufe = C.STUFEN.index(f)
band = B.load()
band_m = band["meta"]["instanzen"]
akz_name = C.AKZ_ANZEIGE[akz]
regel_name = C.REGEL_ANZEIGE[regel]
st.markdown(f"**Gewählte Zugmenge:** {label} ({len(menge)} von 8 Zugarten: {', '.join(C.HNAMEN[h] for h in menge)}). "
            f"Jeder Vergleich unten nutzt für alle Varianten dieselben Instanzen, dieselben Starttouren und dieselben Zufallszahlen.")

# --- Kernfrage 1 --------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔬 Kernfrage 1: Wer liefert die Verbesserung, und wer kann es noch?")
plan1 = EV.plan_runs(n, f, 1, m_wunsch, laeufe_wunsch)
with st.spinner(f"Rechne {EV.tausender(plan1['kosten'])} Auswertungen …"):
    live1 = _measure(familie, n, seed, plan1["instanzen"], plan1["laeufe"], akz, (("S", menge, regel),), (f,))
z1 = live1["zaehler"]["S"]
anteile1 = E.family_shares(z1)
ktx1 = EV.kontext(plan1["instanzen"], plan1["laeufe"], akz, f, n) + f", {regel_name}, Zufalls-Seed {seed}"
st.caption(f"{regel_name} über die gewählte Zugmenge. Der **Beitrag zum Bestwert** einer Zugart ist die Summe aller Senkungen des Bestwerts durch ihre Anwendungen; "
           f"die Beiträge aller Zugarten ergänzen sich zu Startlänge minus beste Länge. {plan1['text']}")
c1, c2 = st.columns([3, 2])
with c1:
    st.plotly_chart(V.build_contribution(anteile1["e"], anteile1["a"], menge), width="stretch", key="beitrag")
with c2:
    kh = E.k_per_improvement(z1)
    st.dataframe({
        "Zugart": [C.HNAMEN[h] for h in menge],
        "Anwendungen": [z1["apps"][h] for h in menge],
        "Erfolge": [z1["succ"][h] for h in menge],
        "Auswertungen": [z1["evals"][h] for h in menge],
        "Auswertungen je Verbesserung": [None if kh["kh"][h] is None else round(kh["kh"][h], 1) for h in menge],
        "Beitrag zum Bestwert (%)": [round(100.0 * anteile1["e"][h], 1) for h in menge],
    }, hide_index=True, width="stretch", column_config={"Beitrag zum Bestwert (%)": st.column_config.NumberColumn(format="%.1f %%")})
    if kh["k"] is not None:
        st.caption(f"Erfolg = Vorschlag, der die Tour streng verkürzt. Über alle Zugarten der Menge: {EV.de(kh['k'], 1)} Auswertungen je Verbesserung.")
EV.show(st, EV.verdict_beitrag(anteile1["e"], anteile1["a"], menge, anteile1["laeufe"], ktx1))
anteil_fam = X.share_of_family(menge)
st.caption(f"Unter Zufallsauswahl bekommt die 2-opt-Familie in dieser Menge im Mittel diesen Anteil der Auswertungen: Kosten der Familie durch Kosten der Menge = "
           f"{anteil_fam.numerator}/{anteil_fam.denominator} = {EV.prozent(float(anteil_fam), 1)}. "
           + (f"Eingefrorene Messung für diese Zelle ({band_m} Instanzen × {C.BAND_SEEDS} Läufe): Anteil der 2-opt-Familie am Beitrag zum Bestwert "
              f"{EV.prozent(B.contribution(akz, name_menge, regel, j_stufe)['e_fam'])}." if name_menge else "Für diese Menge gibt es keine eingefrorene Messung."))

st.markdown("**Ein einzelner Lauf, Schritt für Schritt** (erste Instanz des Vergleichs, Lauf 0)")
idx0 = E.instance_indices(seed, 1)[0]
lauf1 = _trace(familie, n, idx0, menge, regel, akz, f * n)
zuege = len(lauf1["spur"])
if zuege == 0:
    k_schritt = 0
    st.info("In diesem Lauf wurde kein Zug angenommen; der Zustand ist die Starttour.")
else:
    st.session_state["schritt_slider"] = min(int(st.session_state.get("schritt_slider", 0)), zuege)
    k_schritt = int(st.slider("Zustand nach k angenommenen Zügen", 0, zuege, key="schritt_slider",
                              help="0 ist die Starttour. Für die Tour an dieser Stelle zählt die Ansicht rechts alle Ziehungen jeder Zugart durch."))
used_k = lauf1["spur"][k_schritt - 1][0] if k_schritt > 0 else 0
p_zustand = _zustand(familie, n, idx0, menge, regel, akz, f * n, k_schritt)
d1, d2 = st.columns(2)
with d1:
    st.plotly_chart(V.build_progress(lauf1["start"], lauf1["punkte"], f * n, used_k), width="stretch", key=f"verlauf_{k_schritt}")
    st.caption(f"Bestwert über den Auswertungen; jeder Punkt ist ein neuer Bestwert in der Farbe seiner Zugart. {zuege} angenommene Züge, "
               f"Startlänge {EV.de(lauf1['start'], 1)}, beste Länge {EV.de(lauf1['best'], 1)}.")
with d2:
    st.plotly_chart(V.build_state(p_zustand, menge), width="stretch", key=f"zustand_{k_schritt}")
    kt = X.k_of_set(menge, p_zustand)
    st.caption("Exakt am gewählten Zustand: Anteil der Ziehungen je Zugart, die die Tour streng verkürzen (alle Ziehungen aufgezählt, keine Stichprobe). "
               + ("Einschritt-Kennzahl: keine Verbesserung möglich." if kt is None else
                  f"Einschritt-Kennzahl K = {EV.de(kt, 1)} Auswertungen bis zur nächsten Verbesserung (Zufallsauswahl, nur besser, Zustand unverändert)."))
EV.show(st, EV.verdict_zustand(p_zustand, menge))

# --- Kernfrage 2 --------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔬 Kernfrage 2: Was ändert sich, wenn eine Zugart fehlt?")
if menge == voll:
    st.info("Gewählt sind alle acht Zugarten: es fehlt nichts. In der Seitenleiste Zugarten abwählen oder ein Beispiel laden, dann vergleicht dieser Abschnitt "
            "die gewählte Menge mit allen acht. Die Tabelle zeigt die eingefrorene Messung für die gewählte Akzeptanz und das gewählte Budget.")
else:
    plan2 = EV.plan_runs(n, f, 2, m_wunsch, laeufe_wunsch)
    with st.spinner(f"Rechne {EV.tausender(plan2['kosten'])} Auswertungen …"):
        live2 = _measure(familie, n, seed, plan2["instanzen"], plan2["laeufe"], akz, (("voll", voll, regel), ("S", menge, regel)), (f,))
    g_voll, g_s = E.level(live2, "voll"), E.level(live2, "S")
    diff2 = E.diff_ci(g_voll, g_s)
    ktx2 = EV.kontext(plan2["instanzen"], plan2["laeufe"], akz, f, n) + f", {regel_name}, Zufalls-Seed {seed}"
    st.caption(f"Abstand zum besten bekannten Wert mit allen acht Zugarten und mit der gewählten Menge, in **Auswertungen** gleich. {plan2['text']}")
    st.plotly_chart(V.build_pair(["alle acht", label], [ST.mean(g_voll), ST.mean(g_s)], [_ci(g_voll), _ci(g_s)], [C.COLOR_MENGE, C.COLOR_OHNE]),
                    width="stretch", key="paar2")
    EV.show(st, EV.verdict_menge(diff2["d"], diff2["lo"], diff2["hi"], diff2["m"], label, ktx2, band_m))
    _referenz_hinweis(live2["unterboten"])
    if name_menge:
        st.caption(T.band_satz(akz, name_menge, j_stufe) + (" (Zufallsauswahl.)" if regel == "rand" else
                                                             f" (Zufallsauswahl; unter {regel_name}: {EV.de_v(B.set_vs_full(akz, name_menge, j_stufe, regel)['d'])}.)"))
    else:
        st.caption("Für diese Menge gibt es keine eingefrorene Messung; sie liegt nur für die zwölf benannten Mengen vor.")

zeilen2 = [dict(B.set_vs_full(akz, mname, j_stufe), menge=mname) for mname in B.MENGEN_OHNE_VOLL]
wort2 = {"plus": "Menge besser", "minus": "Menge schlechter", "rauschen": "kein belegter Unterschied"}
st.markdown(f"**Eingefroren: jede der elf anderen Mengen gegen alle acht** („{akz_name}“, {C.STUFEN_ANZEIGE[f]}, Zufallsauswahl, {band_m} Instanzen × {C.BAND_SEEDS} Läufe)")
st.dataframe({
    "Menge": [C.MENGEN_ANZEIGE[r["menge"]] for r in zeilen2],
    "Abstand (%)": [round(B.mean_gap(akz, r["menge"], "rand", j_stufe), 2) for r in zeilen2],
    "Unterschied zu allen acht (Punkte)": [round(r["d"], 2) for r in zeilen2],
    "Intervall von": [round(r["lo"], 2) for r in zeilen2],
    "Intervall bis": [round(r["hi"], 2) for r in zeilen2],
    "Anteil der 2-opt-Familie an den Auswertungen (%)": [round(100.0 * B.family_share(r["menge"]), 1) for r in zeilen2],
    "Urteil": [wort2[r["klasse"]] for r in zeilen2],
}, hide_index=True, width="stretch")
st.caption(f"Positiver Unterschied: die Menge ist besser als alle acht (Abstand mit allen acht: {EV.de(B.mean_gap(akz, 'voll', 'rand', j_stufe))} %). "
           f"Urteil nur bei mindestens 0,25 Punkten und einem Intervall ohne 0. Rangkorrelation zwischen dem Anteil der 2-opt-Familie an den Auswertungen und dem "
           f"Abstand über die zwölf Mengen in dieser Zelle: {EV.de_v(B.spearman_cell(akz, j_stufe))} (zwölf Punkte, eine Größenordnung, kein Test). "
           "Gleiche Zahl von Auswertungen heißt nicht gleiche Rechenzeit (Branke u. a. 2016 nennen diesen Vergleich nur begrenzt gültig); "
           "eine Anwendung von 2opt_b5 kostet bis zu 5 Auswertungen.")

st.markdown("**Live: jede der acht Zugarten einzeln weglassen** (neun Mengen auf denselben Instanzen)")
plan2b = EV.plan_runs(n, f, 9, m_wunsch, laeufe_wunsch)
st.caption(plan2b["text"])
if _knopf("einzeln", "Alle acht Einzelabläufe rechnen", (familie, n, seed, akz, f, regel, plan2b["instanzen"], plan2b["laeufe"])):
    varianten = (("voll", voll, regel),) + tuple((C.HNAMEN[h], tuple(x for x in voll if x != h), regel) for h in range(C.K))
    with st.spinner(f"Rechne {EV.tausender(plan2b['kosten'])} Auswertungen (einige Sekunden) …"):
        live2b = _measure(familie, n, seed, plan2b["instanzen"], plan2b["laeufe"], akz, varianten, (f,))
    basis = E.level(live2b, "voll")
    zeilen = []
    for h in range(C.K):
        r = E.diff_ci(basis, E.level(live2b, C.HNAMEN[h]))
        v = EV.verdict_menge(r["d"], r["lo"], r["hi"], r["m"], "ohne " + C.HNAMEN[h], "", band_m)
        zeilen.append((C.HNAMEN[h], r, {"hilft": "ohne ist besser", "schadet": "wird gebraucht", "rauschen": "kein belegter Unterschied", "zu_wenig": "zu wenige Instanzen"}[v["kind"]]))
    st.dataframe({
        "weggelassen": [z[0] for z in zeilen],
        "Unterschied zu allen acht (Punkte)": [round(z[1]["d"], 2) for z in zeilen],
        "Intervall von": [None if z[1]["lo"] is None else round(z[1]["lo"], 2) for z in zeilen],
        "Intervall bis": [None if z[1]["hi"] is None else round(z[1]["hi"], 2) for z in zeilen],
        "Urteil": [z[2] for z in zeilen],
    }, hide_index=True, width="stretch")
    st.caption(f"Live: {EV.kontext(plan2b['instanzen'], plan2b['laeufe'], akz, f, n)}, {regel_name}, Zufalls-Seed {seed}. Positiv: ohne die Zugart ist der Abstand kleiner.")
    _referenz_hinweis(live2b["unterboten"])

# --- Kernfrage 3 --------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔬 Kernfrage 3: Reicht eine feste Teilmenge, und bis zu welchem Budget?")
menge3 = voll if menge == C.T3 else menge
label3 = E.set_label(menge3)
name3 = E.set_name(menge3)
plan3 = EV.plan_runs(n, C.STUFEN[-1], 2, m_wunsch, laeufe_wunsch)
with st.spinner(f"Rechne {EV.tausender(plan3['kosten'])} Auswertungen …"):
    live3 = _measure(familie, n, seed, plan3["instanzen"], plan3["laeufe"], akz, (("S", menge3, regel), ("T3", C.T3, regel)), KURVE)
st.caption("Die feste Teilmenge T3 = {2opt, 2opt_lokal, 2opt_b5} gegen "
           + ("alle acht Zugarten (die gewählte Menge ist die feste Teilmenge selbst)" if menge == C.T3 else f"die gewählte Menge „{label3}“")
           + f", ohne Lernen der Menge. Ein Lauf bis 400·n je Menge; die gepunkteten Linien sind die drei Budgetstufen. {plan3['text']}")
kurven3 = []
for key, name, farbe, bandfarbe in (("S", label3, C.COLOR_MENGE, C.COLOR_BAND), ("T3", "feste Teilmenge T3", C.COLOR_T3, C.COLOR_BAND_T3)):
    spalten = [E.level(live3, key, j) for j in range(len(KURVE))]
    grenzen = [_ci(s) for s in spalten]
    hat = grenzen[0][0] is not None
    kurven3.append((name, [ST.mean(s) for s in spalten], [g[0] for g in grenzen] if hat else None, [g[1] for g in grenzen] if hat else None, farbe, bandfarbe))
st.plotly_chart(V.build_curves([k * n for k in KURVE], kurven3, [s * n for s in C.STUFEN]), width="stretch", key="kurve3")
stufen3 = []
for s in C.STUFEN:
    r = E.diff_ci(E.level(live3, "S", KURVE.index(s)), E.level(live3, "T3", KURVE.index(s)))
    stufen3.append((r["d"], r["lo"] if r["lo"] is not None else r["d"], r["hi"] if r["hi"] is not None else r["d"]))
ktx3 = (f"{plan3['instanzen']} Instanzen mit {n} Städten, {plan3['laeufe']} {'Lauf' if plan3['laeufe'] == 1 else 'Läufe'} je Instanz, Akzeptanz „{akz_name}“, "
        f"{regel_name}, Zufalls-Seed {seed}, Unterschied in Prozentpunkten, positiv: die feste Teilmenge ist besser")
EV.show(st, EV.verdict_teilmenge(stufen3, plan3["instanzen"], label3, ktx3, band_m))
_referenz_hinweis(live3["unterboten"])
if name3:
    teile = []
    for j, s in enumerate(C.STUFEN):
        if name3 == "voll":
            r = B.set_vs_full(akz, "T3", j)
            d, lo, hi = r["d"], r["lo"], r["hi"]
        else:
            lo, hi = ST.bootstrap_ci([a - b for a, b in zip(B.gaps(akz, name3, "rand", j), B.gaps(akz, "T3", "rand", j))], C.ZWECK_BOOT)
            d = B.mean_gap(akz, name3, "rand", j) - B.mean_gap(akz, "T3", "rand", j)
        teile.append(f"{C.STUFEN_ANZEIGE[s]} {EV.de_v(d)} [{EV.de_v(lo)}; {EV.de_v(hi)}]")
    st.caption(f"Eingefrorene Messung ({band_m} Instanzen × {C.BAND_SEEDS} Läufe, „{akz_name}“, Zufallsauswahl), Abstand „{label3}“ minus Abstand T3: " + ", ".join(teile)
               + ". Warum die feste Teilmenge bei großem Budget zurückfallen kann, zeigt das Handbeispiel als Mechanismus (die 2-opt-Familie hält eine Tour für fertig, "
                 "die andere Zugarten noch verbessern); wie oft das in den Läufen hier geschieht, ist nicht gemessen.")

# --- Kernfrage 4 --------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔬 Kernfrage 4: Was bringt Lernen auf dieser Menge?")
plan4 = EV.plan_runs(n, f, 4, m_wunsch, laeufe_wunsch)
with st.spinner(f"Rechne {EV.tausender(plan4['kosten'])} Auswertungen …"):
    live4 = _measure(familie, n, seed, plan4["instanzen"], plan4["laeufe"], akz, tuple((r, menge, r) for r in C.REGELN), (f,))
st.caption(f"Zufallsauswahl und die drei Lernregeln über dieselbe Menge „{label}“; die Regeln lernen während des Laufs (Standardbelohnung, feste Parameter). {plan4['text']}")
g4 = {r: E.level(live4, r) for r in C.REGELN}
st.plotly_chart(V.build_pair([C.REGEL_ANZEIGE[r] for r in C.REGELN], [ST.mean(g4[r]) for r in C.REGELN], [_ci(g4[r]) for r in C.REGELN],
                             [C.COLOR_MENGE, C.COLOR_LERN, C.COLOR_LERN, C.COLOR_LERN]), width="stretch", key="paar4")
ktx4 = EV.kontext(plan4["instanzen"], plan4["laeufe"], akz, f, n) + f", Menge „{label}“, Zufalls-Seed {seed}"
if len(menge) == 1:
    st.info("Die Menge hat nur eine Zugart: es gibt nichts auszuwählen, alle vier Regeln wenden dieselbe Zugart an (die Läufe unterscheiden sich nur durch die "
            "Zufallszahlen, die eine Regel für ihre Auswahl verbraucht).")
for r in C.LERNREGELN:
    d4 = E.diff_ci(g4["rand"], g4[r])
    EV.show(st, EV.verdict_lernregel(d4["d"], d4["lo"], d4["hi"], d4["m"], r, ktx4, band_m))
_referenz_hinweis(live4["unterboten"])
st.dataframe({
    "Auswahlregel": [C.REGEL_ANZEIGE[r] for r in C.REGELN],
    **{C.HNAMEN[h]: [round(100.0 * live4["zaehler"][r]["apps"][h] / max(sum(live4["zaehler"][r]["apps"]), 1), 1) for r in C.REGELN] for h in menge},
}, hide_index=True, width="stretch", column_config={C.HNAMEN[h]: st.column_config.NumberColumn(format="%.1f %%") for h in menge})
st.caption("Anteil der Anwendungen je Zugart in diesen Läufen. Warum eine Lernregel sich auf eine Zugart festlegt und was die Belohnung damit zu tun hat, "
           "zeigt die Demo zu den Auswahlregeln.")
if name_menge:
    st.caption(f"Eingefrorene Messung ({band_m} Instanzen × {C.BAND_SEEDS} Läufe, „{akz_name}“, {C.STUFEN_ANZEIGE[f]}, Menge „{label}“), Gewinn gegen die Zufallsauswahl "
               "in Prozentpunkten mit Intervall: " + "; ".join(T.gain_satz(akz, name_menge, r, j_stufe) for r in C.LERNREGELN) + ".")
zelle = B.cell_summary(akz, j_stufe)
EV.show(st, EV.verdict_menge_vs_lernen(zelle["spann"], zelle["gplus"], zelle["gmin"], len(C.MENGEN),
                                       f"eingefrorene Messung, {band_m} Instanzen × {C.BAND_SEEDS} Läufe, „{akz_name}“, {C.STUFEN_ANZEIGE[f]}, Auswertungen"))

# --- Eingefrorener Vergleich --------------------------------------------------------------------------------------------------------------------
st.markdown("---")
with st.expander("🔧 Alle Mengen im Vergleich (eingefroren)"):
    st.markdown(T.band_kopf())
    st.dataframe({
        "Menge": [C.MENGEN_ANZEIGE[mname] for mname in C.MENGEN],
        **{f"{C.AKZ_ANZEIGE[a].split(' (')[0]}, {C.STUFEN_NAMEN[j]}": [round(B.mean_gap(a, mname, "rand", j), 2) for mname in C.MENGEN] for a, j in B.ZELLEN},
    }, hide_index=True, width="stretch")
    st.caption("Mittlerer Abstand der Zufallsauswahl in Prozent je Menge (Zeile) und je Zelle aus Akzeptanz und Budget (Spalte).")
    st.markdown(T.band_zaehlungen())
    st.markdown(f"**Gewinn der Lernregeln je Menge** („{akz_name}“, {C.STUFEN_ANZEIGE[f]}; Prozentpunkte gegen die Zufallsauswahl auf derselben Menge)")
    st.dataframe({
        "Menge": [C.MENGEN_ANZEIGE[mname] for mname in C.MENGEN],
        "Zufallsauswahl: Abstand (%)": [round(B.mean_gap(akz, mname, "rand", j_stufe), 2) for mname in C.MENGEN],
        **{C.REGEL_ANZEIGE[r]: [T.gain_kurz(akz, mname, r, j_stufe) for mname in C.MENGEN] for r in C.LERNREGELN},
    }, hide_index=True, width="stretch")
    st.caption("Je Zelle: Gewinn [Intervall]; ★ heißt mindestens 0,25 Punkte mit Intervall über 0, ▼ heißt mindestens 0,25 Punkte Verlust mit Intervall unter 0.")
    st.markdown(T.band_zusatz())

with st.expander("🧮 Handbeispiel", expanded=bool(hand)):
    hb = _hand()
    st.markdown(T.HAND_TEXT)
    st.dataframe({
        "Zugart": list(C.HNAMEN),
        "Kosten": list(C.KOSTEN),
        "verbessernde Ziehungen an T0": [str(x) for x in hb["p"]],
        "Kosten je Verbesserung": ["keine Verbesserung" if x == 0 else str(C.KOSTEN[h] / x) for h, x in enumerate(hb["p"])],
        "lokale Optima (von 60 Touren)": hb["optima"],
    }, hide_index=True, width="stretch")
    st.markdown(T.HAND_K_TEXT)
    st.dataframe({
        "Menge": [C.MENGEN_ANZEIGE[z["name"]] for z in hb["zeilen"]],
        "Summe der Kosten": [z["kosten"] for z in hb["zeilen"]],
        "K(S) an T0": ["keine Verbesserung möglich" if z["k"] is None else EV.de(float(z["k"]), 2) for z in hb["zeilen"]],
        "erwartete beste Länge nach 20 Auswertungen": [round(z["e20"], 3) for z in hb["zeilen"]],
        "nach 80 Auswertungen": [round(z["e80"], 3) for z in hb["zeilen"]],
        "lokale Optima der Menge": [z["optima"] for z in hb["zeilen"]],
    }, hide_index=True, width="stretch")
    k_wahl = X.k_of_set(menge, hb["p"])
    st.caption("Erwartete beste Länge: exakt aus der Verteilung über die 60 Touren (Zufallsauswahl, nur besser, Start in T0), keine Simulation. "
               f"Für die in der Seitenleiste gewählte Menge „{label}“ ist K(S) an T0 "
               + ("nicht endlich: keine ihrer Zugarten verbessert T0." if k_wahl is None else f"gleich {EV.de(float(k_wahl), 2)} Auswertungen.")
               + " Bei sechs Städten gibt es keinen Vorsprung der festen Teilmenge bei kleinem Budget; den zeigt erst die Messung mit 30 und 60 Städten, und dort nur unter nur besser und Rekord-zu-Rekord.")

st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(T.ASSUMPTIONS_MARKDOWN)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    st.markdown(T.FORMELN)

P.sync_query_params({key: st.session_state[key] for key in P.SETTING_SPECS})

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html)."
)
