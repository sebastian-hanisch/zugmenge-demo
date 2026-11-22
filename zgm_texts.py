"""Texte der App: Einleitung, einfache Worte, Erklärtabellen, Hilfetexte der Beispiele, Annahmen, Formelblock.

Zahlen der eingefrorenen Messung stehen nicht als Text hier, sondern werden aus zgm_band gelesen (preset_help, band_satz): so kann kein
Hilfetext von der Messung abweichen. ASSUMPTIONS_MARKDOWN steht wortgleich in der README (Test)."""

import zgm_band as B
import zgm_constants as C
from zgm_evaluation import de, de_v

TITEL = "🧰 Die Zugmenge entscheidet: Was die Suche zur Auswahl hat"

INTRO = """Eine Suche, die zwischen mehreren **Zugarten** auswählt, kann nur finden, was die **Zugmenge** hergibt, die man ihr mitgibt.
Diese Demo nimmt acht Zugarten für die Rundtour (Tausch, Einfügen, zwei Arten 2-opt, zwei Arten Or-opt, Doppelbrücke, 2-opt mit fünf Stichproben)
und lässt sie weg, einzeln oder in Gruppen: *Was ändert sich, wenn eine Zugart fehlt, und wie viel davon kann Lernen wettmachen?*
Gezählt wird in **Auswertungen** (bewertete Kandidaten) auf erzeugten Rundtouren mit 30 oder 60 Städten. Die Akzeptanz ist hier in der Voreinstellung
**Rekord-zu-Rekord** und damit eine andere als in der Wurzel-Demo der Reihe („nur besser“); wie Akzeptanz und Auswahl zusammenwirken, zeigt die Demo
„Akzeptanz mal Auswahl“. Die Kernfragen stehen unten, danach **„🔧 Alle Mengen im Vergleich (eingefroren)“**, **„🧮 Handbeispiel“**,
**„🚧 Wo die Annahmen enden“** und **„📐 Mathematische Formulierung“**."""

EINFACH = """Stell dir vor, ein Handwerker hat einen Werkzeugkasten und greift bei jedem Schritt zufällig hinein. Wenn im Kasten ein gutes Werkzeug
fehlt, hilft ein Verfahren, das ihm sagt, wonach er greifen soll, nur wenig (auf Mengen ohne 2-opt-Zugart brachten die drei hier geprüften Lernregeln in 4 von 54 Fällen einen belegten Gewinn). Das prüft diese Demo bei der Suche nach einer kurzen Rundreise:
Die Suche hat mehrere Arten, die Reihenfolge der Stopps zu ändern. Wir nehmen einzelne Arten heraus, nehmen ganze Gruppen heraus oder geben nur eine
feste Auswahl und vergleichen, wie kurz die Tour am Ende ist. Danach lassen wir die Suche aus ihren Erfolgen lernen, welche Art sie bevorzugen soll,
und fragen, ob das mehr bringt als die Wahl des Werkzeugkastens. Wichtig: Alles gilt nur für die hier gebauten Beispiele und diese acht Arten."""

SO_FUNKTIONIERT = """Die Suche startet mit einer Rundtour (Nächster Nachbar ab einer zufälligen Stadt) und wiederholt drei Schritte, bis das Budget an
**Auswertungen** verbraucht ist: (1) eine **Zugart** aus der **Zugmenge** wählen, (2) einen zufälligen Vorschlag dieser Zugart bewerten (eine Auswertung;
`2opt_b5` bewertet bis zu fünf), (3) nach der **Akzeptanzregel** entscheiden, ob der Vorschlag bleibt. Gemerkt wird die beste Tour.

Verändert wird in dieser Demo Schritt 1: **welche Zugarten überhaupt zur Wahl stehen** (die Kästchen in der Seitenleiste) und **wie gewählt wird**
(Zufallsauswahl oder eine von drei Regeln, die während des Laufs aus ihren Erfolgen lernen). Die **2-opt-Familie** sind die drei Zugarten, die ein
Stück der Tour umdrehen: `2opt`, `2opt_lokal`, `2opt_b5`. Die feste Teilmenge **T3** besteht genau aus diesen dreien. Das Maß ist der **Abstand**:
um wie viel Prozent die beste gefundene Tour länger ist als der beste bekannte Wert der Instanz."""

ZUGARTEN_TABELLE = """| Zugart | Was sie tut | Auswertungen je Anwendung |
|---|---|---|
| `swap` (Tausch) | zwei nicht benachbarte Städte tauschen die Plätze | 1 |
| `insert` (Einfügen) | eine Stadt an eine andere Stelle der Tour setzen | 1 |
| `2opt` | ein Stück der Tour umdrehen, Länge des Stücks beliebig | 1 |
| `2opt_lokal` | ein kurzes Stück umdrehen (2 bis 8 Städte) | 1 |
| `oropt2` (Or-opt 2) | ein Stück aus zwei Städten umsetzen, in der Hälfte der Fälle umgedreht | 1 |
| `oropt3` (Or-opt 3) | ein Stück aus drei Städten umsetzen, in der Hälfte der Fälle umgedreht | 1 |
| `dbridge` (Doppelbrücke) | die Tour an drei Stellen schneiden und die beiden mittleren Stücke tauschen | 1 |
| `2opt_b5` | fünf 2-opt-Vorschläge bewerten, den besten nehmen | bis 5 |"""

AKZEPTANZ_TABELLE = """| Akzeptanzregel | Ein Vorschlag bleibt, wenn … |
|---|---|
| nur besser | er die Tour streng verkürzt |
| Rekord-zu-Rekord (Dueck 1993) | er nicht verlängert oder die neue Länge höchstens 1 % über dem Bestwert liegt |
| Late Acceptance (Burke und Bykov), L = 50 | er nicht verlängert oder die neue Länge höchstens so groß ist wie die Länge vor 50 Anwendungen |"""

REGEL_TABELLE = """| Auswahlregel | Wie sie die nächste Zugart wählt | Was sie lernt |
|---|---|---|
| Zufallsauswahl | gleichverteilt über die Zugmenge | nichts |
| Choice Function (nach Cowling u. a. 2000, eigene vereinfachte Umsetzung) | die Zugart mit der höchsten Punktzahl aus eigener Leistung, Leistung nach dem Vorgänger und Wartezeit seit der letzten Anwendung | Leistung mit Vergessen (Faktor 0,9); das Gewicht der Leistung steigt nach einem Erfolg auf 0,99 und sinkt sonst je Anwendung um 0,01 |
| Lernautomat (linear reward-inaction) | zieht aus einer Wahrscheinlichkeitsverteilung über die Zugmenge | nach jedem Erfolg wandert ein Anteil 0,05 der Wahrscheinlichkeit zur erfolgreichen Zugart; Untergrenze 0,01 je Zugart |
| Q-Lernen mit einem Zustand | meist die Zugart mit dem höchsten Q-Wert, in 10 % der Anwendungen eine zufällige | Q-Wert der gewählten Zugart mit Lernrate 0,1 und Abzinsung 0,5 |

Belohnung für alle drei Lernregeln: Verbesserung des Vorschlags je Auswertung, gemessen in mittleren Kantenlängen der Starttour, auf den Bereich 0 bis 1
gekappt. Ein Erfolg ist ein Vorschlag, der die Tour streng verkürzt. Die Regeln lernen während des Laufs über die gewählte Zugmenge; ihre Parameter
sind fest und nicht abgestimmt. Warum eine Belohnung in die Irre führen kann, zeigt die Demo zu den Auswahlregeln."""

HAND_TEXT = """**Sechs Städte, ganzzahlige Fahrzeiten** (symmetrisch, kein Euklid):

| | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| **0** | 0 | 7 | 8 | 4 | 7 | 4 |
| **1** | 7 | 0 | 2 | 5 | 8 | 9 |
| **2** | 8 | 2 | 0 | 3 | 2 | 8 |
| **3** | 4 | 5 | 3 | 0 | 5 | 5 |
| **4** | 7 | 8 | 2 | 5 | 0 | 2 |
| **5** | 4 | 9 | 8 | 5 | 2 | 0 |

**Starttour** T0 = 0-1-2-3-4-5-0 mit Länge 7 + 2 + 3 + 5 + 2 + 4 = **23**. **Beste Tour** 0-3-1-2-4-5-0 mit 4 + 5 + 2 + 2 + 2 + 4 = **19**; sie ist
unter allen 60 Rundtouren die einzige mit dieser Länge (Aufzählung und Held-Karp).

**Wer kann T0 verbessern?** Von den zwölf möglichen 2-opt-Zügen verkürzt keiner die Tour (ihre Längenänderungen sind 0, 0, 2, 3, 3, 3, 5, 5, 7, 11, 11, 12);
dasselbe gilt für `2opt_lokal` und `2opt_b5`, die nur 2-opt-Züge ziehen, und für `swap`. Verbessern können: `insert` mit 2 von 24 Ziehungen
(Stadt 3 hinter Stadt 0 gibt 19, Stadt 3 ans Ende gibt 22), `oropt2` mit 2 von 30, `oropt3` mit 1 von 16, `dbridge` mit 1 von 10.
**Die 2-opt-Familie hält T0 für fertig, die anderen Zugarten nicht.**"""

HAND_K_TEXT = """**Einschritt-Kennzahl** K(S): erwartete Auswertungen bis zur ersten Verbesserung, wenn die Zufallsauswahl über die Menge S an T0 zieht
(Summe der Kosten geteilt durch Summe der Verbesserungswahrscheinlichkeiten). An diesem einen Zustand ist die Menge **ohne** die 2-opt-Familie die
schnellste der fünf Mengen der Tabelle, und die feste Teilmenge kommt gar nicht voran. Das ist eine Aussage über diesen Zustand, nicht über einen ganzen
Lauf: an 5 der 60 Touren ist umgekehrt die feste Teilmenge schneller (an 54 die Menge ohne die 2-opt-Familie), und bei 30 oder 60 Städten liegt die Menge ohne die 2-opt-Familie in der eingefrorenen Messung in allen neun
Zellen hinten."""

FORMELN = r"""**Lesehilfe.** Gegeben sind eine Instanz (n Städte mit Abständen), eine Zugmenge S, eine Auswahlregel, eine Akzeptanzregel und ein Budget B an
Auswertungen. Gesucht ist die Länge der besten Tour, die die Suche findet, als Abstand zum besten bekannten Wert. Die Formeln beschreiben die ganze
Suchschleife und alle Kennzahlen der Experimente; die Rechenschritte der drei Lernregeln stehen als Text unter der Tabelle.

| Symbol | Bedeutung |
|---|---|
| $n$, $D$ | Zahl der Städte, symmetrische Abstandsmatrix |
| $t$, $L(t)$ | Tour (Reihenfolge der Städte), ihre Länge |
| $h$, $S$ | Zugart (0 bis 7), Zugmenge (nichtleere Teilmenge der acht Zugarten) |
| $c_h$ | Kosten einer Anwendung der Zugart $h$ in Auswertungen |
| $p_h(t)$ | Wahrscheinlichkeit, dass eine Anwendung von $h$ die Tour $t$ streng verkürzt |
| $B$ | Budget in Auswertungen |
| $\Delta$ | Längenänderung eines Vorschlags (neue minus alte Länge) |
| $g$, $d$ | Abstand in Prozent, gepaarter Unterschied zweier Varianten in Prozentpunkten |
| $G_h$, $a_h$ | Beitrag der Zugart $h$ zum Bestwert, ihr Anteil an den Auswertungen |
| $K_h$, $K_t(S)$ | Auswertungen je Verbesserung im Lauf, Einschritt-Kennzahl am Zustand $t$ |

**Instanz und Tour.** Die Städte liegen in der Ebene, der Abstand ist euklidisch, die Tour ist geschlossen:

$$D_{ij} = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}$$

$$L(t) = \sum_{k=1}^{n} D_{t_{k-1},\,t_k}, \qquad t_0 := t_n$$

Drei erzeugte Familien: gleichverteilt im Quadrat 1000 × 1000; fünf Gruppen mit Streuung 40 um Mittelpunkte in [100, 900]²; Gitter mit n besetzten
Zellen aus g × g, g = ⌈√(1,5 n)⌉, und Rauschen von 0,1 Gitterabständen. Starttour: Nächster Nachbar ab einer gleichverteilt gezogenen Stadt.

**Zugarten.** Jede Zugart zieht einen Zug gleichverteilt aus ihrem Vorrat und berechnet $\Delta$ aus den entfernten und den neuen Kanten.
`swap`: zwei Positionen im Abstand 2 bis n − 2 tauschen. `insert`: die Stadt an Position i hinter die Stadt an einer anderen Position setzen.
`2opt`: Start i gleichverteilt in 0 bis n − 2, Länge des umgedrehten Stücks gleichverteilt in 2 bis min(n − i, n − 2). `2opt_lokal`: Länge gleichverteilt
in 2 bis min(8, n − 2), danach der Start gleichverteilt. `oropt2`, `oropt3`: ein Stück aus 2 oder 3 Städten hinter eine andere Stadt setzen, mit
Wahrscheinlichkeit 1/2 umgedreht. `dbridge`: drei verschiedene Schnittstellen, die beiden mittleren Stücke tauschen. `2opt_b5`: der beste von bis zu
fünf unabhängigen 2-opt-Vorschlägen, bei Gleichstand der frühere. Kosten:

$$c_h = 1 \ (h \ne \texttt{2opt\_b5}), \qquad c_{\texttt{2opt\_b5}} = \min(5,\ B - \text{verbraucht})$$

**Auswahl.** Die Zufallsauswahl zieht $h$ gleichverteilt aus $S$. Die Lernregeln bekommen nach jeder Anwendung die Belohnung

$$r = \min\!\left(1,\ \frac{\max(0, -\Delta)}{c_h \cdot \bar e}\right), \qquad \bar e = \frac{L(t_{\text{Start}})}{n}$$

**Akzeptanz** (mit ε = 10⁻⁹; eine strenge Verbesserung bleibt unter jeder der drei Regeln):

$$\text{nur besser:}\quad \Delta < -\varepsilon$$

$$\text{Rekord-zu-Rekord:}\quad \Delta \le \varepsilon \ \ \text{oder}\ \ L(t') \le 1{,}01 \cdot L_{\text{best}}$$

$$\text{Late Acceptance:}\quad \Delta \le \varepsilon \ \ \text{oder}\ \ L(t') \le L_{k-50}$$

Dabei ist $t'$ die vorgeschlagene Tour und $L_{k-50}$ die Länge der aktuellen Tour vor 50 Anwendungen (zu Beginn die Startlänge).

**Schleife und Maß.** Die Schleife läuft, solange die verbrauchten Auswertungen kleiner als $B$ sind. Der Abstand zum besten bekannten Wert $L_{\text{ref}}$:

$$g = 100 \cdot \frac{L_{\text{best}} - L_{\text{ref}}}{L_{\text{ref}}}$$

Der gepaarte Unterschied zweier Varianten A und B über m Instanzen (je Instanz das Mittel über die Läufe), mit 95-%-Bootstrap-Intervall über die
Instanzen (4000 Ziehungen):

$$d = \frac{1}{m} \sum_{i=1}^{m} \bigl(g_i(A) - g_i(B)\bigr)$$

**Kennzahlen im Lauf.** $G_h$ ist die Summe aller Senkungen des Bestwerts durch Anwendungen der Zugart $h$; die Beiträge ergänzen sich exakt:

$$\sum_{h \in S} G_h = L(t_{\text{Start}}) - L_{\text{best}}$$

$$a_h = \frac{\text{Auswertungen}_h}{\sum_{k \in S} \text{Auswertungen}_k}, \qquad K_h = \frac{\text{Auswertungen}_h}{\text{Erfolge}_h}$$

**Einschritt-Kennzahl am Zustand.** $p_h(t)$ wird durch Aufzählung aller Ziehungen gezählt, für `2opt_b5` gilt $p = 1 - (1 - p_{\texttt{2opt}})^5$.

$$K_t(S) = \frac{\sum_{h \in S} c_h}{\sum_{h \in S} p_h(t)}$$

*Satz 1 (Mediant).* $K_t(S) \ge \min_{h \in S} c_h / p_h$: die Mischung ist an einem Zustand nie schneller als ihre beste Zugart allein
(ein Quotient von Summen liegt zwischen dem kleinsten und dem größten Einzelquotienten).
*Satz 2 (Weglassen).* $K_t(S \setminus \{h\}) < K_t(S)$ genau dann, wenn $c_h / p_h > K_t(S)$ (bei $p_h = 0$ ist das wahr, solange eine andere Zugart verbessern kann).
*Satz 3 (lokale Optima).* $t$ ist genau dann lokales Optimum von $S$, wenn es lokales Optimum jeder Zugart in $S$ ist; `2opt_b5` hat dieselben lokalen
Optima wie `2opt`.
*Satz 4 (Wartezeit).* Bei Zufallsauswahl über $S$, Akzeptanz „nur besser“ und unverändertem Zustand ist die erwartete Zahl der Auswertungen bis zur
ersten Verbesserung gleich $K_t(S)$: die Zahl $N$ der Anwendungen ist geometrisch verteilt mit Erfolgswahrscheinlichkeit $\bar p = \frac{1}{|S|}\sum p_h$,
und nach der Gleichung von Wald ist die erwartete Summe der Kosten $E[N] \cdot \bar c$. Die Sätze gelten am Zustand, nicht über den Lauf (die $p_h$ ändern
sich mit jeder angenommenen Änderung), und Satz 4 nicht unter Rekord-zu-Rekord oder Late Acceptance. Für das Handbeispiel sind die Sätze 1 bis 3 über alle
255 Mengen und alle 60 Touren nachgerechnet.

**Was die Formeln nicht enthalten:** die Rechenschritte der Choice Function, des Lernautomaten und des Q-Lernens. Sie stehen mit ihren Parametern in der
Tabelle der Auswahlregeln oben und im Modul `zgm_select.py` des Repositorys.

**Quellen** (mit dem, was gelesen wurde). Burke, Gendreau, Hyde, Kendall, Ochoa, Özcan, Qu (2013), „Hyper-heuristics: a survey of the state of the art“,
Journal of the Operational Research Society 64(12), S. 1695 bis 1724 (Volltext gelesen): Einteilung; die Menge der Heuristiken ist dort von Menschen gewählt,
so auch hier. Sobotka, Kletzander, Musliu, Rudová (2025), arXiv 2509.02782 (Vorabdruck ohne Begutachtung; Hauptteil gelesen): Eingriffe in die Menge der
Niedrigebenen-Heuristiken bei gleichverteilter Zufallsauswahl. Branke, Nguyen, Pickardt, Zhang (2016), IEEE Transactions on Evolutionary Computation 20(1)
(angenommene Fassung gelesen): der Vergleich bei gleicher Auswertungszahl ist nur begrenzt gültig. Dueck (1993), Rekord-zu-Rekord, und Burke und Bykov (2017),
Late Acceptance (jeweils nur die Kurzfassung gelesen). Cowling, Kendall, Soubeiga (2000/2001), Choice Function (nicht selbst gelesen; die Formel folgt
Drake, Özcan, Burke 2012, Volltext gelesen). Ropke und Pisinger (2006), Einsatz konkurrierender Teilheuristiken nach bisheriger Leistung (nur die Kurzfassung
gelesen). Keine Neuheit behauptet."""


def stufen_name(f: int) -> str:
    return C.STUFEN_ANZEIGE[f]


def band_satz(akz: str, menge: str, j: int) -> str:
    """Zeile der eingefrorenen Messung zu „Menge gegen alle acht“ für eine Zelle."""
    r = B.set_vs_full(akz, menge, j)
    wort = {"plus": "die Menge ist besser", "minus": "die Menge ist schlechter", "rauschen": "kein belegter Unterschied"}[r["klasse"]]
    return (f"Eingefrorene Messung ({r['m']} Instanzen, {C.BAND_SEEDS} Läufe je Instanz, „{C.AKZ_ANZEIGE[akz]}“, {stufen_name(C.STUFEN[j])}): "
            f"{de_v(r['d'])} Prozentpunkte, Intervall {de_v(r['lo'])} bis {de_v(r['hi'])} ({wort}).")


def gain_satz(akz: str, menge: str, regel: str, j: int) -> str:
    r = B.gain(akz, menge, regel, j)
    wort = {"plus": "die Regel gewinnt", "minus": "die Regel verliert", "rauschen": "kein belegter Unterschied"}[r["klasse"]]
    return f"{C.REGEL_ANZEIGE[regel]} {de_v(r['d'])} [{de_v(r['lo'])}; {de_v(r['hi'])}] ({wort})"


def _erwartung_menge(akz, menge, j=0):
    r = B.set_vs_full(akz, menge, j)
    return f"{de_v(r['d'])} Prozentpunkte gegenüber allen acht (Intervall {de_v(r['lo'])} bis {de_v(r['hi'])})"


def preset_help() -> dict:
    """Hilfetexte der Beispiele; die Erwartungen stammen aus der eingefrorenen Messung (120 Instanzen), ein Beispiel rechnet nur 8 oder 4 Instanzen."""
    m = B.load()["meta"]["instanzen"]
    zusatz = f" Erwartung aus der eingefrorenen Messung mit {m} Instanzen; das Beispiel rechnet weniger Instanzen, dort kann auch „kein belegter Unterschied“ herauskommen."
    t3k, t3g = B.set_vs_full("ob", "T3", 0), B.set_vs_full("ob", "T3", 2)
    return {
        "Alle acht Zugarten": "Gleichverteilte Städte, n = 30, Rekord-zu-Rekord, 50·n Auswertungen, Zufallsauswahl über alle acht Zugarten: der Ausgangspunkt. "
                              "Experiment 1 zeigt, welche Zugart die Verbesserung liefert.",
        "Die stärkste Zugart fehlt": f"Ohne 2opt_b5, die Zugart mit dem größten Beitrag zum Bestwert ({round(100 * B.contribution('rr', 'voll', 'rand', 0)['e'][7])} % mit allen acht "
                                     "unter Rekord-zu-Rekord bei 50·n): " + _erwartung_menge("rr", "ohne_2opt_b5") + "." + zusatz,
        "Eine schwache Zugart fehlt": "Ohne dbridge: " + _erwartung_menge("rr", "ohne_dbridge") + "." + zusatz,
        "Ohne die 2-opt-Familie": "Ohne 2opt, 2opt_lokal und 2opt_b5: " + _erwartung_menge("rr", "ohne_2opt_Familie") + "." + zusatz,
        "Nur schwache Zugarten": "Nur swap, oropt2, oropt3 und dbridge: " + _erwartung_menge("rr", "nur_schwache") + "." + zusatz,
        "Feste Teilmenge, kleines Budget": f"Akzeptanz „nur besser“, 50·n: Experiment 3 vergleicht alle acht mit der festen Teilmenge aus 2opt, 2opt_lokal und 2opt_b5. "
                                           f"Unterschied bei kleinem Budget: {de_v(t3k['d'])} Prozentpunkte (positiv: die feste Teilmenge ist besser)." + zusatz,
        "Feste Teilmenge, großes Budget": f"Akzeptanz „nur besser“, 400·n, 4 Instanzen: bei großem Budget liegt die feste Teilmenge "
                                          f"{de(-t3g['d'])} Prozentpunkte hinter allen acht." + zusatz,
        "Lernen unter Late Acceptance": "Alle acht, Late Acceptance, 50·n: Experiment 4 zeigt die drei Lernregeln gegen die Zufallsauswahl. "
                                        + gain_satz("la", "voll", "cf", 0) + "." + zusatz,
        "Lernen ohne 2opt_b5": "Ohne 2opt_b5, Late Acceptance, 50·n: " + gain_satz("la", "ohne_2opt_b5", "laut", 0) + "; auf allen acht: "
                               + gain_satz("la", "voll", "laut", 0) + "." + zusatz,
        "Handbeispiel: sechs Städte": "Klappt das Handbeispiel auf: sechs Städte, 60 Touren, alles exakt gerechnet. Die Experimente darüber laufen mit den "
                                      "Einstellungen des ersten Beispiels weiter.",
    }


C.PRESET_HELP.update(preset_help())


# ---------------------------------------------------------------- Texte aus der eingefrorenen Messung (alle Zahlen gerechnet, keine abgeschrieben)
def gain_kurz(akz: str, menge: str, regel: str, j: int) -> str:
    """Tabellenzelle: Gewinn [Intervall] mit Marke (★ Gewinn, ▼ Verlust)."""
    r = B.gain(akz, menge, regel, j)
    marke = {"plus": " ★", "minus": " ▼", "rauschen": ""}[r["klasse"]]
    return f"{de_v(r['d'])} [{de_v(r['lo'])}; {de_v(r['hi'])}]{marke}"


def band_kopf() -> str:
    meta = B.load()["meta"]
    je_zelle = meta["instanzen"] // (len(C.FAMILIEN) * len(C.N_GEMESSEN))
    return (f"**Eingefrorene Messung:** {meta['instanzen']} Instanzen (3 Familien × n = 30 und 60 × {je_zelle} Instanzen), {meta['seeds']} Läufe je Instanz, "
            f"12 Zugmengen × 4 Auswahlregeln × 3 Akzeptanzregeln, je ein Lauf bis 400·n mit Kontrollpunkten bei 50·n und 150·n. Dazu jede Zugart allein, "
            f"die Zählung in Anwendungen und vier weitere Zugarten für die Suche nach gleich starken Zugarten; zusammen "
            f"{de(meta['auswertungen_gesamt'] / 1e9)} Milliarden Auswertungen. "
            "Abstand = Prozent über dem besten bekannten Wert; je Instanz zählt das Mittel der Läufe; Intervalle sind 95-%-Bootstrap-Intervalle über die Instanzen, "
            "ohne Korrektur für die vielen Vergleiche: belastbar sind zusammenhängende Muster, nicht ein einzelnes Intervall.")


def _spanne(rows) -> str:
    werte = [abs(r["d"]) for r in rows]
    return f"{de(min(werte))} bis {de(max(werte))}"


def band_zaehlungen() -> str:
    """Die Zählungen über alle neun Zellen (3 Akzeptanzregeln × 3 Budgets), Zufallsauswahl, als Liste."""
    w54, w18 = B.count_classes(B.weak_rows()), B.weak_rows((0,))
    k18 = B.count_classes(w18)
    fam, schwach, t3 = B.set_rows("ohne_2opt_Familie"), B.set_rows("nur_schwache"), B.set_rows("T3")
    kf, ks, kt = B.count_classes(fam), B.count_classes(schwach), B.count_classes(t3)
    b5, o2 = B.count_classes(B.set_rows("ohne_2opt_b5")), B.count_classes(B.set_rows("ohne_2opt"))
    gs = B.gain_summary()
    g, v = gs["groesster"], gs["kleinster"]
    mehr = sum(1 for a, j in B.ZELLEN if B.cell_summary(a, j)["menge_mehr"])
    spann = [B.cell_summary(a, j)["spann"] for a, j in B.ZELLEN]
    spann10 = [B.cell_summary(a, j)["spann_mit_2opt"] for a, j in B.ZELLEN]
    spann10_la0, gplus_la0 = B.cell_summary("la", 0)["spann_mit_2opt"], B.cell_summary("la", 0)["gplus"]

    def wo(r):
        return f"„{C.AKZ_ANZEIGE[r['akz']]}“, {C.STUFEN_NAMEN[r['j']]}, {C.REGEL_ANZEIGE[r['regel']]}, Menge „{C.MENGEN_ANZEIGE[r['menge']]}“"

    return "\n".join([
        "**Zählungen über alle neun Zellen** (3 Akzeptanzregeln × 3 Budgets; „belegt“ heißt mindestens 0,25 Punkte mit Intervall ohne 0):",
        "",
        f"* **Eine der sechs Zugarten außer 2opt und 2opt_b5 weglassen** (6 × 9 = 54 Fälle): {w54['rauschen']} ohne belegten Unterschied, "
        f"{w54['plus']} mit „ohne ist besser“, {w54['minus']} mit „ohne ist schlechter“. Bei kleinem Budget (18 Fälle) ist der größte Betrag "
        f"{de(max(abs(r['d']) for r in w18))} Punkte; belegt sind dort {k18['plus'] + k18['minus']} von 18 (je nach Bootstrap-Ziehung 5 bis 7).",
        f"* **2opt weglassen:** {o2['minus']} von 9 Zellen belegt schlechter, {o2['plus']} belegt besser. **2opt_b5 weglassen:** {b5['minus']} von 9 belegt schlechter, "
        f"{b5['plus']} belegt besser.",
        f"* **Die ganze 2-opt-Familie weglassen:** belegt schlechter in {kf['minus']} von 9 Zellen, um {_spanne(fam)} Punkte. **Nur schwache Zugarten:** "
        f"belegt schlechter in {ks['minus']} von 9, um {_spanne(schwach)} Punkte.",
        f"* **Feste Teilmenge T3 gegen alle acht:** vorn in {kt['plus']}, hinten in {kt['minus']}, ohne belegten Unterschied in {kt['rauschen']} von 9 Zellen.",
        f"* **Gewinn der Lernregeln** (12 Mengen × 3 Regeln × 9 Zellen = {gs['n']} Intervalle): {gs['marke']} mit belegtem Gewinn, {gs['verlust_marke']} mit belegtem "
        f"Verlust, {gs['unter_null']} Intervalle ganz unter 0. Größter Gewinn {de_v(g['d'])} ({wo(g)}), größter Verlust {de_v(v['d'])} ({wo(v)}).",
        f"* **Menge gegen Lernen:** die Spannweite der Zufallsauswahl über die zwölf Mengen liegt je Zelle zwischen {de(min(spann))} und {de(max(spann))} Punkten; "
        f"in {mehr} von 9 Zellen ist sie mindestens das Doppelte des größten Gewinns einer Lernregel (und mindestens 0,5 Punkte). Sie entsteht vor allem durch die zwei Mengen "
        f"ohne 2-opt-Zugart; über die zehn Mengen mit 2-opt-Zugart liegt sie je Zelle zwischen {de(min(spann10))} und {de(max(spann10))} Punkten, unter Late Acceptance bei kleinem Budget "
        f"({de(spann10_la0)}) unter dem größten Gewinn einer Lernregel ({de(gplus_la0)}).",
    ])


def band_zusatz() -> str:
    """Drei Zusatzmessungen: jede Zugart allein, Zählung in Anwendungen, Suche nach gleich starken Zugarten."""
    m = B.load()["meta"]["instanzen"]
    kopf = "| Akzeptanz, Budget | " + " | ".join(C.HNAMEN) + " |\n|---|" + "---|" * C.K
    zeilen = []
    for akz in C.AKZEPTANZEN:
        for j in (0, 2):
            d = B.dominance(akz, j)
            zeilen.append(f"| {C.AKZ_ANZEIGE[akz].split(' (')[0]}, {C.STUFEN_NAMEN[j]} | " + " | ".join(de(x) for x in d["werte"]) + " |")
    dom = [B.dominance(a, j) for a, j in B.ZELLEN]
    zw_obrr = max(B.dominance(a, j)["zwilling"] for a, j in B.ZELLEN if a != "la")
    zw_la = [B.dominance("la", j)["zwilling"] for j in range(3)]
    anw = ["| Menge | Akzeptanz | gleiche Auswertungen | gleiche Anwendungen |", "|---|---|---|---|"]
    for menge in C.MENGEN_ANWENDUNGEN[1:]:
        for akz in C.AKZEPTANZEN:
            a, b = B.set_vs_full(akz, menge, 0), B.applications_row(akz, menge, 0)
            anw.append(f"| {C.MENGEN_ANZEIGE[menge]} | {C.AKZ_ANZEIGE[akz].split(' (')[0]} | {de_v(a['d'])} [{de_v(a['lo'])}; {de_v(a['hi'])}] | "
                       f"{de_v(b['d'])} [{de_v(b['lo'])}; {de_v(b['hi'])}] |")
    pool = B.pool_means()
    kandidaten = B.pool_candidates()
    naechste = B.pool_closest()
    pool_zeilen = ["| Zugart allein | nur besser | Rekord-zu-Rekord |", "|---|---|---|"]
    for name in sorted(pool["ob"], key=pool["ob"].get):
        pool_zeilen.append(f"| {name} | {de(pool['ob'][name])} | {de(pool['rr'][name])} |")
    if kandidaten:
        pool_satz = f"Nach der vorab festgelegten Regel gibt es {len(kandidaten)} Kandidatenmengen; gemessen wurde auf ihnen noch nichts."
    else:
        pool_satz = ("**Eine Menge mit mehreren gleich starken, verschiedenen Zugarten wurde mit den 12 geprüften Zugarten nicht gefunden:** außer 2opt und 2opt_b5 "
                     f"liegt jede bei 50·n unter nur besser und Rekord-zu-Rekord mindestens {de(min(naechste[a]['spann3'] for a in naechste))} Punkte hinter der besten. Ob Lernen bei mehreren gleich starken, "
                     "verschiedenen Zugarten mehr bringt, ist damit nicht gemessen.")
    return "\n".join([
        f"**Jede Zugart allein** (Abstand in Prozent, {m} Instanzen × {C.BAND_SEEDS} Läufe; die Wurzel-Demo der Reihe führt diesen Vergleich ausführlich):",
        "", kopf, *zeilen, "",
        f"Die bessere der beiden Zugarten 2opt und 2opt_b5 liegt in jeder der neun Zellen {de(min(d['vorsprung'] for d in dom))} bis "
        f"{de(max(d['vorsprung'] for d in dom))} Punkte vor der besten der übrigen sechs. Unter „nur besser“ und Rekord-zu-Rekord sind 2opt und 2opt_b5 allein "
        f"fast gleich stark (Unterschied höchstens {de(zw_obrr)} Punkte), unter Late Acceptance nicht ({de(min(zw_la))} bis {de(max(zw_la))} Punkte).",
        "",
        "**Gleiche Zahl Anwendungen statt gleiche Zahl Auswertungen** (kleines Budget, Zufallsauswahl, Unterschied zu allen acht in Punkten, positiv: Menge besser). "
        "Eine Anwendung von 2opt_b5 kostet bis zu 5 Auswertungen; zählt man Anwendungen, bekommt eine Menge mit 2opt_b5 mehr Auswertungen:",
        "", *anw, "",
        "**Suche nach gleich starken Zugarten.** Vorab festgelegte Regel: eine Menge aus mindestens drei Zugarten, die allein unter „nur besser“ und unter "
        "Rekord-zu-Rekord bei 50·n höchstens 1,0 Punkte auseinanderliegen und höchstens 1,0 Punkte hinter der besten 2-opt-Zugart. Geprüft: die acht Zugarten und "
        "vier weitere (`swap_b5`, `insert_b5`, `oropt2_b5`, `oropt3_b5`: der beste von fünf Vorschlägen der Grundzugart, Kosten fünf Auswertungen).",
        "", *pool_zeilen, "", pool_satz,
    ])


ASSUMPTIONS_MARKDOWN = """| Annahme oder Grenze | Was das heißt | Stand |
|---|---|---|
| **Eigene Umsetzung, acht selbst gewählte Zugarten** | Die Zugmenge ist von Menschen gewählt (so auch in der Literatur: Burke u. a. 2013). Andere Zugarten (Or-opt mit variabler Länge, 3-opt) können das Bild ändern. Kein Urteil über HyFlex, irace oder fertige Löser. | nicht gemessen |
| **Erzeugte Rundtouren mit 30 oder 60 Städten**, drei Familien | Die Befunde gelten für diese Instanzen; größere Instanzen und echte Straßennetze sind nicht geprüft. Nutzen in Logistik, Lager oder Fertigung ist nicht belegt. | nicht gemessen |
| **Abstand zum besten bekannten Wert** | Die Referenz ist kein Optimum, die Abstände sind Untergrenzen. In der eingefrorenen Messung haben Läufe die Referenz aus fünf langen Läufen in 44 von 120 Instanzen unterboten; die App nimmt je Rechnung den kleinsten Wert. Absolute Abstände hängen an der Referenz, gepaarte Unterschiede auf denselben Instanzen viel weniger. | so gebaut |
| **Budget höchstens 400·n Auswertungen** | Das sind 12 000 Auswertungen bei 30 und 24 000 bei 60 Städten. Ob die Reihenfolge der Mengen bei viel größeren Budgets gleich bleibt, zeigt diese Demo nicht. | nicht gemessen |
| **Gleiche Zahl von Auswertungen** als Maß | Gleiche Auswertungszahl ist nicht gleiche Rechenzeit (Branke u. a. 2016 nennen diesen Vergleich nur begrenzt gültig). Zählt man Anwendungen statt Auswertungen, ändern sich Urteile: siehe die Zusatzmessung im eingefrorenen Vergleich. Sekunden weist die App nicht als Befund aus. | Zusatzmessung |
| **Drei Akzeptanzregeln** | Annealing und Sintflut sind hier nicht gemessen. „Alle Züge annehmen“ und „besser oder gleich“ sind nicht wählbar: in der Vormessung blieb der Bestwert unter der ersten Regel nahe der Starttour, und die zweite verhielt sich wie „nur besser“. | nicht gemessen |
| **Drei Lernregeln mit festen Parametern** | Choice Function, Lernautomat und Q-Lernen lernen während des Laufs, mit einer Belohnung und nicht abgestimmten Parametern. Die Befunde gelten für diese drei Regeln in dieser Einstellung, nicht für „Lernen“ allgemein. Die Choice Function misst hier Auswertungen statt Zeit und ist eine vereinfachte eigene Umsetzung. | Demo zu den Auswahlregeln |
| **324 Intervalle ohne Korrektur** | Bei so vielen Vergleichen fallen einige Intervalle zufällig auf eine Seite der 0. Belastbar sind zusammenhängende Muster (alle neun Zellen, alle drei Regeln), nicht ein einzelnes Intervall. | so gebaut |
| **Keine Menge mit gleich starken, verschiedenen Zugarten** | In jeder der zehn gemessenen Mengen mit 2-opt-Zugarten wird diesen unter Zufallsauswahl in allen neun Zellen mehr als 60 % der Verbesserung zugerechnet; in den Mengen ohne sie fehlt eine gute Zugart. Die Suche unter 12 Zugarten fand keine Menge mit mehreren gleich starken, verschiedenen Zugarten. Ob Lernen dort mehr bringt, ist offen. | nicht gemessen |
| **Die Einschritt-Kennzahl gilt am Zustand** | K(S) beschreibt eine Tour, nicht den Lauf; die Verbesserungswahrscheinlichkeiten ändern sich mit jedem angenommenen Zug. Wie oft die 2-opt-Familie in den Läufen festhängt, ist nicht gezählt; das Handbeispiel zeigt nur den Mechanismus. | nicht gemessen |
| **Eine Auswahl, die sich je Zustand ändert** | Die Zustandsansicht zeigt, dass an einer Tour andere Zugarten verbessern können als im Mittel des Laufs. Eine Auswahlregel, die das nutzt, ist nicht gebaut. | nicht gebaut |
| **Wenige Instanzen live** | Ein Live-Vergleich rechnet 2 bis 8 Instanzen; die eingefrorene Messung hat 120. Ein Urteil aus 8 Instanzen kann von der eingefrorenen Messung abweichen, auch im Vorzeichen. | so gebaut |"""
