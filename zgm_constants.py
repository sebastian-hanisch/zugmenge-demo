"""Konstanten: Zugarten, Familien, Budgetstufen, benannte Zugmengen, Marken der Verdikte, Parameter der Auswahlregeln, Regler-Grenzen, Farben, Presets.

Der obere Teil (Zugarten, Instanzen, Zwecke der Zufalls-Seeds, Akzeptanz, Marken) führt dieselben Namen und Werte wie die Wurzel-Demo der
Linie (hyperheuristik-demo): die kopierten Module (zgm_scenario, zgm_moves, zgm_accept, zgm_search, zgm_stats) lesen sie hier."""

# ---------------------------------------------------------------- Zugarten (Reihenfolge und Index sind Schnittstelle der Linie)
HNAMEN = ("swap", "insert", "2opt", "2opt_lokal", "oropt2", "oropt3", "dbridge", "2opt_b5")
K = 8
KOSTEN = (1, 1, 1, 1, 1, 1, 1, 5)          # Auswertungen je Anwendung; 2opt_b5 am Budgetrand weniger (zgm_moves.cost_of)
H_2OPT, H_2OPT_B5 = 2, 7
ALLE_ZUGARTEN = tuple(range(K))
B5_STICHPROBEN = 5
LOKAL_LMAX = 8                              # 2opt_lokal: Segmentlänge höchstens min(8, n - 2)
FAMILIE_2OPT = (2, 3, 7)                    # die 2-opt-Familie: 2opt, 2opt_lokal, 2opt_b5
HNAMEN_ANZEIGE = {
    "swap": "Tausch", "insert": "Einfügen", "2opt": "2-opt", "2opt_lokal": "2-opt lokal", "oropt2": "Or-opt 2", "oropt3": "Or-opt 3",
    "dbridge": "Doppelbrücke", "2opt_b5": "2-opt, beste von 5",
}

# ---------------------------------------------------------------- Instanzen
FAMILIEN = ("gleich", "cluster", "gitter")  # Index = Schlüssel der Zufalls-Seeds
FAMILIE_HAND = "hand"
FAMILIEN_ANZEIGE = {"gleich": "gleichverteilt", "cluster": "Gruppen", "gitter": "Gitter"}
N_GEMESSEN = (30, 60)                       # nur dort liegt die eingefrorene Messung vor; die App bietet nur diese beiden
SEITE = 1000.0                              # Quadrat 1000 x 1000 (Einheiten, keine Kilometer)
CLUSTER_ZAHL, CLUSTER_SIGMA = 5, 40.0
GITTER_FAKTOR, GITTER_RAUSCHEN = 1.5, 0.1
INSTANZEN_JE_SEED = 8                       # Zufalls-Seed s der App: Instanzen 8 s bis 8 s + 7
SEED_MAX = 24                               # Zufalls-Seeds 0 bis 24: Instanzen 0 bis 199 je Familie und n (Referenzwerte vorgerechnet)
INSTANZEN_REF = INSTANZEN_JE_SEED * (SEED_MAX + 1)
BAND_INSTANZEN = 20                         # eingefrorene Messung: Instanzen 0 bis 19 je Familie und n (120 Instanzen)
BAND_SEEDS = 3                              # Läufe (Zufalls-Seeds) je Instanz in der eingefrorenen Messung

# Zwecke der Zufalls-Seeds (zgm_scenario.derive): je Zweck ein eigener Strom
ZWECK_INSTANZ, ZWECK_START, ZWECK_LAUF, ZWECK_REF, ZWECK_REFSTART, ZWECK_BOOT, ZWECK_PROBE = 11, 33, 24, 25, 34, 7, 41

# ---------------------------------------------------------------- Budget (in Vielfachen von n) und Rechengrenze
STUFEN = (50, 150, 400)                     # klein, mittel, groß: Auswertungen = Faktor mal n
STUFEN_NAMEN = ("klein", "mittel", "groß")
STUFEN_ANZEIGE = {50: "klein (50·n)", 150: "mittel (150·n)", 400: "groß (400·n)"}
KURVE_PUNKTE = 25                           # Kontrollpunkte der Verlaufskurve in Experiment 3
RECHENGRENZE = 500_000                      # Auswertungen je Live-Vergleich: Mengen x Instanzen x Läufe x Budget (Python-Schleife, O(Produkt))
MIN_INSTANZEN = 4                           # darunter gibt es kein Urteil

# ---------------------------------------------------------------- Akzeptanz
EPS = 1e-9
RHO = 0.01                                  # Rekord-zu-Rekord: Kandidat <= (1 + RHO) * Bestwert
LA_LEN, LA_LEN_KURZ = 50, 10                # Late Acceptance: Länge der Historie in Anwendungen
GD_END = 0.80                               # Sintflut (hier nicht benutzt; Name wird von zgm_accept gelesen)
SA_T0, SA_T1 = 0.3, 0.003                   # Annealing: nur in den Referenzläufen (tools/zgm_make_refs.py)
AKZEPTANZEN = ("ob", "rr", "la")            # in der App wählbar und eingefroren
AKZ_ANZEIGE = {"ob": "nur besser", "rr": "Rekord-zu-Rekord", "la": "Late Acceptance (L = 50)"}

# ---------------------------------------------------------------- Auswahlregeln (zgm_select)
REGELN = ("rand", "cf", "laut", "q")
LERNREGELN = ("cf", "laut", "q")
REGEL_ANZEIGE = {"rand": "Zufallsauswahl", "cf": "Choice Function", "laut": "Lernautomat", "q": "Q-Lernen"}
CF_ALPHA, CF_PHI0, CF_PHI_ERFOLG, CF_PHI_SCHRITT, CF_PHI_MIN, CF_ZEITFENSTER, CF_RAUSCHEN = 0.9, 0.5, 0.99, 0.01, 0.01, 50, 1e-9
LAUT_A, LAUT_BODEN = 0.05, 0.01
Q_EPS, Q_ALPHA, Q_GAMMA = 0.1, 0.1, 0.5

# ---------------------------------------------------------------- benannte Zugmengen (die 12 der eingefrorenen Messung)
MENGEN = {"voll": ALLE_ZUGARTEN}
for _h in range(K):
    MENGEN["ohne_" + HNAMEN[_h]] = tuple(x for x in ALLE_ZUGARTEN if x != _h)
MENGEN["ohne_2opt_Familie"] = (0, 1, 4, 5, 6)
MENGEN["nur_schwache"] = (0, 4, 5, 6)
MENGEN["T3"] = FAMILIE_2OPT
T3 = MENGEN["T3"]
SCHWACHE_EINZELN = ("ohne_swap", "ohne_insert", "ohne_2opt_lokal", "ohne_oropt2", "ohne_oropt3", "ohne_dbridge")   # je eine der sechs Zugarten außer 2opt und 2opt_b5
MENGEN_ANZEIGE = {"voll": "alle acht", "ohne_2opt_Familie": "ohne 2-opt-Familie", "nur_schwache": "nur schwache", "T3": "feste Teilmenge T3"}
for _h in range(K):
    MENGEN_ANZEIGE["ohne_" + HNAMEN[_h]] = "ohne " + HNAMEN[_h]
MENGEN_ANWENDUNGEN = ("voll", "ohne_2opt_b5", "T3", "ohne_2opt_Familie")   # Zusatzmessung „gleiche Zahl Anwendungen“

# ---------------------------------------------------------------- Verdikte (gesetzt, nicht abgeleitet)
MARKE_KLAR, MARKE_GLEICH = 0.25, 0.10       # Prozentpunkte
MARKE = MARKE_KLAR
BEITRAG_VIEL, BEITRAG_TEILS = 0.70, 0.40    # Anteil der 2-opt-Familie an der Verbesserung des Bestwerts
SPANN_FAKTOR = 2.0                          # „Menge bewegt mehr“: Spannweite >= 2 * max(größter Gewinn, MARKE)
BOOTSTRAP_ZIEHUNGEN = 4000
POOL_MARKE = 1.0                            # Suche nach gleich starken Zugarten: Spannweite und Rückstand höchstens 1,0 Punkte

# ---------------------------------------------------------------- Regler
DEFAULT_FAMILIE, DEFAULT_N, DEFAULT_SEED, DEFAULT_AKZ, DEFAULT_BUDGET, DEFAULT_REGEL = "gleich", 30, 0, "rr", 50, "rand"
INSTANZEN_MIN, INSTANZEN_MAX, DEFAULT_INSTANZEN = 2, 8, 8
LAEUFE_MIN, LAEUFE_MAX, DEFAULT_LAEUFE = 1, 3, 1

# ---------------------------------------------------------------- Farben
FARBE_ZUGART = ("#9d755d", "#f58518", "#4c78a8", "#72b7b2", "#b279a2", "#ff9da6", "#bab0ac", "#e45756")
COLOR_MENGE = "#2F6B65"
COLOR_OHNE = "#e45756"
COLOR_T3 = "#4c78a8"
COLOR_LERN = "#f58518"
COLOR_BAND = "rgba(47,107,101,0.18)"
COLOR_BAND_T3 = "rgba(76,120,168,0.18)"
COLOR_GRAU = "rgba(150,150,150,0.75)"

# ---------------------------------------------------------------- Presets (jedes legt alle Regler fest)
_BASIS = {"familie": "gleich", "n": 30, "instanzen": 8, "laeufe": 1, "akz": "rr", "budget": 50, "regel": "rand", "seed": 0, "hand": False}
for _h in range(K):
    _BASIS["z" + str(_h)] = True


def _preset(**kw):
    p = dict(_BASIS)
    menge = kw.pop("menge", None)
    if menge is not None:
        for h in range(K):
            p["z" + str(h)] = h in menge
    p.update(kw)
    return p


PRESETS = {
    "Alle acht Zugarten": _preset(),
    "Die stärkste Zugart fehlt": _preset(menge=MENGEN["ohne_2opt_b5"]),
    "Eine schwache Zugart fehlt": _preset(menge=MENGEN["ohne_dbridge"]),
    "Ohne die 2-opt-Familie": _preset(menge=MENGEN["ohne_2opt_Familie"]),
    "Nur schwache Zugarten": _preset(menge=MENGEN["nur_schwache"]),
    "Feste Teilmenge, kleines Budget": _preset(akz="ob"),
    "Feste Teilmenge, großes Budget": _preset(akz="ob", budget=400, instanzen=4),
    "Lernen unter Late Acceptance": _preset(akz="la"),
    "Lernen ohne 2opt_b5": _preset(akz="la", menge=MENGEN["ohne_2opt_b5"]),
    "Handbeispiel: sechs Städte": _preset(hand=True),
}
PRESET_HELP: dict[str, str] = {}             # wird in zgm_texts gefüllt (die Texte nennen Zahlen der eingefrorenen Messung)
