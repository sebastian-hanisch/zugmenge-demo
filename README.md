# Die Zugmenge entscheidet – Streamlit-Demo

Zweite Demo der Reihe **„Hyperheuristiken erklärt“** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie steht auf dem Ast **Auswählen** und folgt auf die Wurzel-Demo „Heuristiken auswählen statt Lösungen“ (`hyperheuristik-demo`). Die Wurzel nimmt die Menge der acht Zugarten als gegeben und vergleicht die Zufallsauswahl mit jeder einzelnen Zugart; dass die Menge selbst der Hebel ist, bleibt dort unsichtbar. Diese Demo hebt genau diese Annahme auf: dieselbe Suche, dieselben acht Zugarten, aber die **Zugmenge** wird verändert, und danach wird gefragt, wie viel Lernen auf welcher Menge ändert.

Das Fahrzeug ist wie in der Wurzel eine erzeugte Rundtour (Städte in der Ebene, kürzeste geschlossene Tour gesucht). Instanzen, Zugarten, Akzeptanzregeln, Suche und Zufallsströme sind aus der Wurzel-Demo kopiert (Kopier-Tests); neu sind die Auswahlregeln, die Mengen, der Beitrag je Zugart und die exakte Rechnung am Zustand. **Die Akzeptanz ist hier in der Voreinstellung Rekord-zu-Rekord, in der Wurzel-Demo „nur besser“.** Verwandte Demos des Portfolios mit anderem Maß und anderer Zähleinheit (nicht mit den Abständen hier vergleichbar): [simulated-annealing-demo](https://sebastianhanisch-simulated-annealing-demo.streamlit.app/) (Nachbarschaften als Regler, Abstand zu einer Schranke, Zähleinheit Vorschläge), [alns-demo](https://sebastianhanisch-alns-demo.streamlit.app/) (adaptive Auswahl von Operatoren für die Tourenplanung; deren README nennt 8,89 % gegen 8,87 % Verbesserung für adaptiv gegen gleichverteilt, also praktisch keinen Unterschied), `vrp-nachbarschaften-demo`, `bandit-demo`. Keine Neuheit behauptet; die Einordnung folgt Burke u. a. (2013).

## Kernfrage

Was kostet es, eine Zugart zu streichen, und was bringt Lernen auf der Menge?

**Befund, mit seinen Voraussetzungen** (eigene Umsetzung, acht selbst gewählte Zugarten, 120 erzeugte Instanzen mit 30 oder 60 Städten aus drei Familien, 3 Läufe je Instanz, Budget 50·n, 150·n und 400·n **Auswertungen**, drei Akzeptanzregeln, Abstand zum besten bekannten Wert): Dieselbe Zufallsauswahl liegt bei 50·n Auswertungen unter Rekord-zu-Rekord je nach Zugmenge zwischen 6,12 und 13,27 % über dem besten bekannten Wert (unter „nur besser“ zwischen 5,33 und 11,94 %, unter Late Acceptance zwischen 9,48 und 13,25 %). Die beste der drei Lernregeln gewinnt auf keiner der 12 Mengen und in keiner der 9 Zellen aus Akzeptanz und Budget mehr als 1,67 Prozentpunkte. Wer die ganze 2-opt-Familie (2opt, 2opt_lokal, 2opt_b5) streicht, verliert bei 50·n je nach Akzeptanz 2,64 bis 4,81 Punkte; wer eine einzelne der sechs Zugarten außer 2opt und 2opt_b5 streicht, verändert den Abstand bei 50·n um höchstens 0,66 Punkte, belegt in 5 von 18 Fällen (je nach Bootstrap-Ziehung 5 bis 7, ohne Korrektur für Mehrfachvergleiche), und in allen belegten ist die Menge **ohne** die Zugart besser. Kein Urteil über HyFlex, irace, fertige Löser oder die Praxis in Logistik, Lager und Fertigung.

## Befunde und Korrekturen gegenüber der Vormessung

Die Planung stützte sich auf eine Vormessung mit dem Zufallsgenerator von numpy, 60 Instanzen und anderen Referenzwerten. Der Bau hat mit den Zufallsströmen der App (SplitMix64) und **120 Instanzen** (Instanzen 0 bis 19 je Familie und n, 3 Läufe) neu gemessen: 1 182 600 000 Auswertungen. Die absoluten Abstände sind nicht vergleichbar (andere Instanzen, andere Referenz); verglichen werden die gepaarten Unterschiede und die Zählungen.

| Aussage der Planung (Vormessung) | Neumessung |
|---|---|
| 13 Mengen, 351 Intervalle | 12 Mengen, 324 Intervalle (12 Mengen × 3 Lernregeln × 9 Zellen) |
| größter Gewinn einer Lernregel +1,22 (Rekord-zu-Rekord, klein, Lernautomat, ohne 2opt_b5) | **+1,67** [+1,27; +2,07], dieselbe Zelle, Regel und Menge |
| 25 von 324 Intervallen mit belegtem Gewinn, 84 ganz unter 0 | **46** mit belegtem Gewinn, 93 mit belegtem Verlust, 95 ganz unter 0 |
| größter Verlust −3,33 (Late Acceptance, mittel, Choice Function, ohne 2opt) | **−2,89** [−3,34; −2,44] (Late Acceptance, mittel, Choice Function, ohne swap) |
| Late Acceptance, klein, alle acht: Choice Function −1,87, Lernautomat −1,40, Q-Lernen −1,80 | −1,57, −1,18, −1,36 (alle drei belegt) |
| dieselbe Zelle ohne 2opt_b5: +0,40, +0,87, +0,14, nur der Lernautomat belegt | +0,30, **+1,08**, −0,09, nur der Lernautomat belegt (bestätigt) |
| „Lernregeln gewinnen kaum“ ohne Einschränkung der Akzeptanz | **unter Rekord-zu-Rekord bei 50·n gewinnen alle drei Lernregeln auf allen acht Zugarten belegt** (+1,15, +0,84, +0,88); unter Late Acceptance verlieren sie dort |
| eine der sechs übrigen Zugarten weglassen, 50·n: höchstens 0,76 Punkte, 2 von 18 belegt | höchstens **0,66**, **5 von 18** belegt (alle: ohne ist besser) |
| über alle 54 Fälle: 3 besser, 6 schlechter, 45 ohne belegten Unterschied | **7** besser, **4** schlechter, **43** ohne belegten Unterschied |
| ohne 2opt_b5, 50·n: −0,90 (nur besser), −1,50 (Rekord-zu-Rekord), +0,13 (Late Acceptance) | −1,13, −1,62, +0,19 (bestätigt) |
| ohne 2opt, 50·n: +0,17, −0,20, +0,43 (Late Acceptance belegt) | +0,08, +0,27, +0,14: **in keiner der 9 Zellen belegt** |
| ohne 2-opt-Familie, 50·n: −4,32, −5,25, −2,15 (nur besser, Rekord-zu-Rekord, Late Acceptance) | −4,81, −4,68, −2,64; belegt schlechter in 9 von 9 Zellen (bestätigt) |
| nur schwache, 50·n: −5,85, −5,83, −3,39 | −5,93, −5,59, −3,44; 9 von 9 (bestätigt) |
| feste Teilmenge T3 gegen alle acht: vorn in 2, hinten in 5, offen in 2 von 9 Zellen | vorn in **3** (auch Rekord-zu-Rekord bei 150·n), hinten in 5, offen in **1** |
| T3 unter „nur besser“: +0,73 bei 50·n, −2,56 bei 400·n (4,97 gegen 2,41 %) | +0,68 und **−1,84** (4,15 gegen 2,31 %); die Kreuzung ist bestätigt, der Rückstand kleiner |
| Spannweite der Zufallsauswahl mindestens das Doppelte des größten Gewinns: 9 von 9 Zellen | 9 von 9 über alle 12 Mengen (bestätigt) |
| Rangkorrelation Budgetanteil der 2-opt-Familie gegen Abstand: −0,90, −0,96, −0,86 (nur besser klein, Rekord-zu-Rekord klein und mittel) | −0,92, −0,95, −0,80 (bestätigt) |
| 2opt und 2opt_b5 allein gleich stark | gilt unter „nur besser“ und Rekord-zu-Rekord (Unterschied höchstens 0,09 Punkte), **nicht unter Late Acceptance** (1,04 bis 3,32 Punkte) |
| Anteil der Anwendungen auf 2opt_b5 unter Late Acceptance, alle acht: 41,2 / 80,8 / 23,1 % | 37,9 / 79,9 / 23,5 % (Choice Function, Lernautomat, Q-Lernen) |
| auf Mengen ohne starke Zugart setzt der Lernautomat 33 bis 37 % auf oropt2 | auf „nur schwache“ 35,3 % auf oropt2; auf „ohne 2-opt-Familie“ setzt er **51,8 % auf insert** |
| Zahl der Ziehungen von 2opt_lokal bei 60 Städten: 385 | **392** (59 + 58 + … + 53); zusammen 54 790 Ziehungen je Zustand |
| „K der Mischung liegt zwischen dem kleinsten und größten K der Zugarten“ | gilt nur nach unten; eine Zugart ohne Erfolg hat kein endliches K, dann kann die Mischung über dem größten endlichen Wert liegen |

Was die Neumessung an der Kernaussage ändert: „Die Menge bewegt mehr als die Lernregel“ gilt über alle 12 Mengen weiter in 9 von 9 Zellen, über die zehn Mengen mit 2-opt-Zugart nicht (siehe „Menge oder Lernen“ unten). Die Aussage „Lernen bringt wenig“ gilt so nicht: unter Rekord-zu-Rekord bei kleinem Budget ist der Gewinn in 21 von 36 Intervallen (12 Mengen × 3 Lernregeln) belegt (bis 1,67 Punkte), unter Late Acceptance bei kleinem Budget ist in 27 von 36 Intervallen der Verlust belegt (bis 2,08 Punkte). Das Vorzeichen hängt an der Akzeptanz; warum, ist Gegenstand der Demos zu den Auswahlregeln und zu Akzeptanz mal Auswahl.

**Zur Wurzel-Demo:** Sie misst auf 180 Instanzen mit 6 Läufen, dass die bessere der beiden Zugarten 2opt und 2opt_b5 bei 50·n unter Rekord-zu-Rekord und Late Acceptance vor der Zufallsauswahl über alle acht liegt und unter „nur besser“ kein gesicherter Unterschied besteht. Die Einzelläufe hier (120 Instanzen, 3 Läufe) passen dazu: 6,82 gegen 7,68 % unter Rekord-zu-Rekord, 8,33 gegen 9,81 % unter Late Acceptance, 6,17 gegen 6,01 % unter „nur besser“. Den Vergleich selbst führt die Wurzel-Demo.

## Modell

Vollständig im Expander „📐 Mathematische Formulierung“ der App. Kurz:

* **Instanz:** n = 30 oder 60 Städte, euklidische Abstände, drei erzeugte Familien (gleichverteilt im Quadrat 1000 × 1000; fünf Gruppen mit Streuung 40; Gitter mit Rauschen). Starttour: Nächster Nachbar ab einer zufälligen Stadt.
* **Acht Zugarten** (Index 0 bis 7): `swap`, `insert`, `2opt`, `2opt_lokal`, `oropt2`, `oropt3`, `dbridge`, `2opt_b5`. Jede Anwendung kostet 1 Auswertung, `2opt_b5` bis zu 5 (der beste von fünf 2-opt-Vorschlägen). Die **2-opt-Familie** sind `2opt`, `2opt_lokal`, `2opt_b5`.
* **Zwölf benannte Zugmengen:** alle acht; acht Mengen „ohne eine Zugart“; ohne die 2-opt-Familie ({swap, insert, oropt2, oropt3, dbridge}); nur schwache ({swap, oropt2, oropt3, dbridge}); die feste Teilmenge T3 = {2opt, 2opt_lokal, 2opt_b5}.
* **Auswahlregeln:** Zufallsauswahl (gleichverteilt über die Menge), Choice Function (Vergessen 0,9), Lernautomat (Schritt 0,05, Untergrenze 0,01), Q-Lernen mit einem Zustand (ε = 0,1, Lernrate 0,1, Abzinsung 0,5). Belohnung: Verbesserung des Vorschlags je Auswertung in mittleren Kantenlängen der Starttour, auf 0 bis 1 gekappt. Die Regeln lernen während des Laufs; ihre Parameter sind nicht abgestimmt.
* **Akzeptanz:** nur besser; Rekord-zu-Rekord (höchstens 1 % über dem Bestwert); Late Acceptance mit Liste 50.
* **Maß:** Abstand = 100 · (beste Länge − bester bekannter Wert) / bester bekannter Wert. Unterschiede zweier Varianten sind gepaart über Instanzen, mit 95-%-Bootstrap-Intervall (4000 Ziehungen).
* **Am Zustand:** p_h = Anteil der Ziehungen einer Zugart, die die Tour streng verkürzen (exakt durch Aufzählung); K(S) = Summe der Kosten / Summe der p_h = erwartete Auswertungen bis zur nächsten Verbesserung unter Zufallsauswahl und „nur besser“.

## Methodik

* **Gemeinsame Zufallszahlen:** Starttour und Zufallsstrom hängen nur an (Familie, n, Instanz, Lauf). Alle Mengen, Auswahlregeln und Akzeptanzregeln eines Laufs starten gleich und lesen denselben Strom von vorn.
* **Eingefrorene Messung** (`zgm_band.json`, erzeugt von `tools/zgm_make_band.py`): 120 Instanzen × 3 Läufe; 12 Mengen × 4 Auswahlregeln × 3 Akzeptanzregeln, je ein Lauf bis 400·n mit Kontrollpunkten bei 50·n und 150·n. Ein Kontrollpunkt ist der Bestwert nach der ersten Anwendung, mit der die verbrauchten Auswertungen die Marke erreichen (`2opt_b5` kann sie um bis zu 4 überschreiten). Dazu: jede Zugart allein; die Zufallsauswahl auf „alle acht“ und T3 mit dem Budget in Anwendungen; vier weitere Zugarten „beste von 5“ allein bei 50·n.
* **Referenz** (`zgm_refs.json`, erzeugt von `tools/zgm_make_refs.py`): je Instanz der kleinste Wert aus drei Läufen mit Annealing-Akzeptanz und zwei mit Late Acceptance, je 1000·n Auswertungen, für die Instanzen 0 bis 199 je Familie und n. In der eingefrorenen Messung gilt das Minimum aus diesem Wert und allen Messläufen (in 44 von 120 Instanzen unterbot ein Messlauf die fünf langen Läufe). Die App nimmt je Rechnung das Minimum aus Referenz und den Läufen der Rechnung.
* **Urteil:** „belegt“ heißt mindestens 0,25 Prozentpunkte Unterschied und ein Intervall ohne 0; live zusätzlich mindestens 4 Instanzen. Die Marken sind gesetzt, nicht abgeleitet. Die 324 Intervalle sind nicht für Mehrfachvergleiche korrigiert.
* **Live:** je Vergleich höchstens 500 000 Auswertungen; darüber kürzt die App erst die Läufe je Instanz, dann die Instanzen, und sagt es.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen dieses Abschnitts stammen aus der eingefrorenen Messung: 120 Instanzen (3 Familien × n = 30 und 60 × 20), 3 Läufe je Instanz, je Instanz das Mittel der Läufe, Abstand in Prozent über dem besten bekannten Wert, Unterschiede in Prozentpunkten mit 95-%-Bootstrap-Intervall über die Instanzen, Zähleinheit Auswertungen. „Klein“, „mittel“, „groß“ sind 50·n, 150·n, 400·n. Die neun Zellen sind die drei Akzeptanzregeln mal die drei Budgets.

**Abstand der Zufallsauswahl je Menge** (klein / mittel / groß):

| Menge | nur besser | Rekord-zu-Rekord | Late Acceptance |
|---|---|---|---|
| alle acht | 6,01 / 3,45 / 2,31 | 7,68 / 3,82 / 1,98 | 9,81 / 3,89 / 2,08 |
| ohne 2opt | 5,93 / 3,42 / 2,25 | 7,41 / 3,64 / 1,89 | 9,66 / 3,89 / 2,10 |
| ohne 2opt_b5 | 7,14 / 3,58 / 2,12 | 9,30 / 4,51 / 2,18 | 9,61 / 3,92 / 1,98 |
| ohne 2-opt-Familie | 10,82 / 6,31 / 4,07 | 12,37 / 7,96 / 4,54 | 12,44 / 6,98 / 4,11 |
| nur schwache | 11,94 / 7,85 / 5,39 | 13,27 / 9,23 / 5,74 | 13,25 / 8,54 / 5,53 |
| feste Teilmenge T3 | 5,33 / 4,28 / 4,15 | 6,12 / 3,34 / 2,36 | 10,25 / 4,11 / 2,66 |

| Frage | Befund | Test |
|---|---|---|
| Wer liefert die Verbesserung? | Mit allen acht Zugarten und Zufallsauswahl wird der 2-opt-Familie bei 50·n im Mittel über 360 Läufe 84 % (nur besser), 84 % (Rekord-zu-Rekord) und 85 % (Late Acceptance) der Senkung des Bestwerts zugerechnet, bei 58,3 % der Auswertungen (7 von 12 Kosteneinheiten). 2opt_b5 allein werden unter Rekord-zu-Rekord 57 % zugerechnet. Ohne 2opt_b5 werden 2opt und 2opt_lokal 64 bis 66 % zugerechnet, bei 28,6 % der Auswertungen. Das ist eine Zurechnung (die Zugart, die den Bestwert gesenkt hat, bekommt die Senkung), keine Wirkung; die Wirkung zeigen erst die Auslassungen unten. | `test_claims.py` |
| Was ändert sich, wenn eine der sechs Zugarten außer 2opt und 2opt_b5 fehlt? | In 43 von 54 Fällen (6 Zugarten × 9 Zellen) kein belegter Unterschied, in 7 ist die Menge ohne die Zugart besser, in 4 schlechter (dreimal ohne insert, einmal ohne oropt2, bei mittlerem oder großem Budget). Bei kleinem Budget höchstens 0,66 Punkte; belegt sind dort 5 von 18 (je nach Bootstrap-Ziehung 5 bis 7), alle zugunsten des Weglassens (ohne swap unter „nur besser“ und Rekord-zu-Rekord; ohne oropt2, oropt3 und dbridge unter Rekord-zu-Rekord). | `test_claims.py` |
| Und wenn 2opt oder 2opt_b5 fehlt? | Ohne 2opt: in keiner der 9 Zellen ein belegter Unterschied (höchstens 0,27 Punkte), solange 2opt_b5 und 2opt_lokal bleiben. Ohne 2opt_b5: belegt schlechter in 3 von 9 Zellen (nur besser klein −1,13; Rekord-zu-Rekord klein −1,62 und mittel −0,69), sonst kein belegter Unterschied. | `test_claims.py` |
| Und wenn die ganze 2-opt-Familie fehlt? | Belegt schlechter in 9 von 9 Zellen, um 1,76 bis 4,81 Punkte. Nur schwache Zugarten: 9 von 9, um 3,08 bis 5,93 Punkte. | `test_claims.py` |
| Hängt der Mengeneffekt am Budgetanteil der 2-opt-Familie? | Rangkorrelation über die 12 Mengen zwischen dem Anteil der Auswertungen der Familie unter Zufallsauswahl und dem Abstand: −0,92 (nur besser, klein), −0,95 (Rekord-zu-Rekord, klein), −0,80 (Rekord-zu-Rekord, mittel); in den übrigen sechs Zellen zwischen −0,51 und +0,02. Zwölf Punkte, neun Korrelationen ohne Korrektur: eine Größenordnung, kein Test, und keine belegte Ursache. | `test_claims.py` |
| Reicht eine feste Teilmenge? | T3 gegen alle acht (Zufallsauswahl): vorn in 3 Zellen (nur besser klein +0,68; Rekord-zu-Rekord klein +1,56 und mittel +0,48), hinten in 5, kein belegter Unterschied in 1 (Late Acceptance, mittel). Unter „nur besser“ kreuzt es: +0,68 bei klein, −0,83 bei mittel, −1,84 bei groß. Unter Late Acceptance liegt T3 bei klein und groß hinten (−0,44, −0,58). | `test_claims.py` |
| Feste Teilmenge gegen Lernregel auf allen acht? | Bei kleinem Budget liegt T3 mit Zufallsauswahl in 8 von 9 Vergleichen (3 Akzeptanzregeln × 3 Lernregeln) belegt vor der Lernregel auf allen acht (+0,32 bis +1,13; Ausnahme Q-Lernen unter „nur besser“, +0,17 ohne Beleg). Bei großem Budget liegt T3 in 7 von 9 belegt dahinter (bis −1,95 unter „nur besser“). | `test_claims.py` |
| Was bringt Lernen? | Von 324 Intervallen haben 46 einen belegten Gewinn und 93 einen belegten Verlust. Größter Gewinn +1,67 (Lernautomat, Rekord-zu-Rekord, klein, ohne 2opt_b5), größter Verlust −2,89 (Choice Function, Late Acceptance, mittel, ohne swap). Auf allen acht bei kleinem Budget: unter Rekord-zu-Rekord gewinnen alle drei (+1,15, +0,84, +0,88), unter Late Acceptance verlieren alle drei (−1,57, −1,18, −1,36). | `test_claims.py` |
| Hängt der Gewinn an der Menge? | Unter Late Acceptance bei kleinem Budget: auf allen acht verliert der Lernautomat 1,18 Punkte, ohne 2opt_b5 gewinnt er 1,08 [+0,74; +1,40]; Choice Function (+0,30) und Q-Lernen (−0,09) haben dort keinen belegten Unterschied. Auf den Mengen ohne 2-opt-Zugart (ohne 2-opt-Familie, nur schwache) gibt es in 54 Intervallen 4 belegte Gewinne, der größte +0,64. | `test_claims.py` |
| Menge oder Lernen: was bewegt mehr? | Die Spannweite der Zufallsauswahl über die 12 Mengen liegt je Zelle zwischen 3,27 und 7,15 Punkten, der größte Gewinn einer Lernregel je Zelle zwischen 0,14 und 1,67. Über alle 12 Mengen ist die Spannweite in 9 von 9 Zellen mindestens das Doppelte des größten Gewinns; sie entsteht vor allem durch die zwei Mengen ohne 2-opt-Zugart. Über die zehn Mengen mit 2-opt-Zugart liegt sie je Zelle zwischen 0,52 und 3,18 Punkten (unter Late Acceptance zwischen 0,68 und 0,77) und unter Late Acceptance bei kleinem Budget (0,77) unter dem größten Gewinn einer Lernregel (1,08); dort bewegt die Menge nicht mehr als die Lernregel. Für Verluste gilt das nicht: unter Late Acceptance bei mittlerem Budget steht ein Verlust von 2,89 neben einer Spannweite von 5,10. | `test_claims.py` |
| Worauf legen sich die Lernregeln fest? | Anteil der Anwendungen auf 2opt_b5 unter Late Acceptance (alle Läufe bis 400·n), alle acht: Choice Function 37,9 %, Lernautomat 79,9 %, Q-Lernen 23,5 % (Zufallsauswahl: 12,5 %); auf T3: 58,4 %, 89,0 %, 41,6 % (Zufallsauswahl: 33,3 %). | `test_claims.py` |
| Ändert die Zähleinheit das Urteil? | Ja. Bei gleicher Zahl **Anwendungen** statt Auswertungen und kleinem Budget liegt T3 unter allen drei Akzeptanzregeln belegt vor allen acht (+0,54, +2,35, +1,89 für nur besser, Rekord-zu-Rekord, Late Acceptance), unter Late Acceptance also mit umgekehrtem Vorzeichen (−0,44 bei gleichen Auswertungen). Ohne 2opt_b5 ist bei gleichen Anwendungen in allen drei belegt schlechter (−2,24, −3,21, −2,35). Eine Menge mit 2opt_b5 bekommt je Anwendung mehr Auswertungen. | `test_claims.py` |
| Gibt es eine Menge ohne klaren Sieger? | Nicht unter den geprüften 12 Zugarten (die acht und vier Varianten „beste von 5“, gemessen unter nur besser und Rekord-zu-Rekord). Jede Zugart außer 2opt und 2opt_b5 liegt allein bei 50·n unter nur besser und Rekord-zu-Rekord mindestens 4,63 Punkte hinter der besten (unter Late Acceptance, nur für die acht Zugarten gemessen: mindestens 3,55); die Varianten „beste von 5“ unterscheiden sich von ihrer Grundzugart um höchstens 0,18 Punkte. Nach der vorab festgelegten Regel gibt es keine Kandidatenmenge; das fünfte Experiment der Planung entfällt. | `test_claims.py` |
| Handbeispiel | Sechs Städte, 60 Touren, Start 23, eindeutiges Optimum 19. An der Starttour verbessert keine Zugart der 2-opt-Familie; K(S) ist 38,4 für alle acht, 22,4 ohne 2opt_b5, 16 ohne die 2-opt-Familie, 17,45 für nur schwache, für T3 nicht endlich. Lokale Optima je Zugart: 6, 1, 2, 2, 2, 2, 6, 2; die Menge aller acht hat eines, T3 zwei. Erwartete beste Länge nach 20 / 80 Auswertungen: 21,637 / 19,611 (alle acht), 20,702 / 19,132 (ohne 2-opt-Familie), 23 / 23 (T3). | `test_exact.py`, `test_oracle_zugmenge.py` |

**Jede Zugart allein** (Abstand bei 50·n; Reihenfolge swap, insert, 2opt, 2opt_lokal, oropt2, oropt3, dbridge, 2opt_b5): nur besser 15,95 / 10,88 / 6,21 / 11,84 / 12,16 / 13,00 / 17,19 / 6,17; Rekord-zu-Rekord 16,02 / 12,38 / 6,90 / 11,45 / 13,17 / 13,90 / 17,88 / 6,82; Late Acceptance 16,15 / 12,44 / 8,33 / 11,88 / 13,14 / 13,86 / 17,51 / 11,65. Die bessere von 2opt und 2opt_b5 liegt in jeder der neun Zellen 2,52 bis 4,82 Punkte vor der besten der übrigen sechs.

**Die Beispiele der App** rechnen 8 Instanzen (gleichverteilt, n = 30, Zufalls-Seed 0, ein Lauf), das Beispiel „Feste Teilmenge, großes Budget“ 4. Mit so wenigen Instanzen fällt die App oft kein Urteil, wo die eingefrorene Messung eines fällt: „Die stärkste Zugart fehlt“ zeigt −0,86 Punkte ohne Beleg (eingefroren −1,62, belegt), „Eine schwache Zugart fehlt“ +0,18 ohne Beleg (eingefroren +0,44, belegt), „Ohne die 2-opt-Familie“ −3,69 und „Nur schwache Zugarten“ −7,34 (beide belegt, wie eingefroren), „Lernen unter Late Acceptance“ −1,08 für die Choice Function ohne Beleg (eingefroren −1,57, belegt), „Lernen ohne 2opt_b5“ +1,30 für den Lernautomaten ohne Beleg (eingefroren +1,08, belegt). Die Zahlen sind festgehalten, nicht ausgesucht (`test_preset_verdicts.py`).

### Zahl → Test

| Zahl | Test | Art |
|---|---|---|
| Handbeispiel: 23, 19, p_h, K(S), lokale Optima, Zahl der Ziehungen, Sätze 1 bis 3 über 255 Mengen | `tests/test_exact.py` | exakt (Brüche) |
| erwartete beste Länge nach 20 / 80 Auswertungen | `tests/test_exact.py` exakt; `tests/test_oracle_zugmenge.py` gegen 4 000 Läufe der Suche | exakt und Band (4,5 Standardfehler) |
| Tabelle „Abstand der Zufallsauswahl je Menge“, Einzelzugarten | `tests/test_claims.py` gegen `zgm_band.json` | auf 0,006 genau (Rundung) |
| Unterschiede, Intervalle, Zählungen (43 / 7 / 4, 5 von 18, 9 von 9, 3 / 5 / 1, 46 / 93 / 95, 8 und 7 von 9) | `tests/test_claims.py` | Zählung exakt, Intervalle ±0,02 |
| Rangkorrelationen | `tests/test_claims.py`; Funktion gegen scipy in `tests/test_band.py` | auf 0,006 genau |
| Beiträge und Anteile der Anwendungen | `tests/test_claims.py` | auf 0,006 bzw. 0,06 Prozentpunkte |
| `zgm_band.json` selbst | `tests/test_band.py`: 4 Instanzen × 2 Mengen × 3 Läufe neu gerechnet, dazu je ein Fall mit Lernregel, Einzelzugart und „beste von 5“ | Band 0,001 Punkte |
| Beispiele der App | `tests/test_preset_verdicts.py` | Urteil exakt, Zahl auf 0,006 |
| Zahlen der Tabelle „Befunde und Korrekturen“, linke Spalte | Planung; die Zählungen der Vormessung rechnet `tests/test_verdicts.py` aus deren Rohausgabe nach, falls sie vorliegt | nicht Teil dieser Messung |
| Testzahl | `tests/test_claims.py` (übersprungen, wenn nur ein Teil der Suite läuft) | exakt |

Nicht im Test, sondern Angabe dieser README: die Gesamtzahl der Auswertungen der Referenzläufe (270 000 000 = 1 200 Instanzen × 5 Läufe × 1000·n, nur als Produkt nachgerechnet) und die beiden Zahlen aus der README der `alns-demo` (dort gemessen, hier nicht).

## Ehrliche Grenzen

Derselbe Text steht in der App unter „🚧 Wo die Annahmen enden“.

| Annahme oder Grenze | Was das heißt | Stand |
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
| **Wenige Instanzen live** | Ein Live-Vergleich rechnet 2 bis 8 Instanzen; die eingefrorene Messung hat 120. Ein Urteil aus 8 Instanzen kann von der eingefrorenen Messung abweichen, auch im Vorzeichen. | so gebaut |

## Befunde und Korrekturen gegenüber dem Plan

* **120 statt 60 Instanzen** in der eingefrorenen Messung (Instanzen 0 bis 19 je Familie und n): die Intervalle der Vormessung waren für mehrere Aussagen zu breit.
* **Kernfrage 2 vergleicht die in der Seitenleiste gewählte Menge mit allen acht Zugarten.** Die Planung sah ein eigenes Auswahlfeld „Zugart weglassen“ vor; die Kästchen der Zugmenge leisten dasselbe ohne einen zweiten Regler, und die Beispiele „ohne 2-opt-Familie“ und „nur schwache“ lassen sich so direkt laden. Ein Knopf rechnet alle acht Einzelabläufe.
* **Kernfrage 4 zeigt immer alle drei Lernregeln** neben der Zufallsauswahl (statt eines Auswahlfelds).
* **Die Rechengrenze kürzt erst die Läufe je Instanz, dann die Instanzen** (die Planung nannte nur die Instanzen): so bleiben eher mindestens 4 Instanzen für ein Urteil.
* **4000 Bootstrap-Ziehungen** wie in der Wurzel-Demo (die Planung nannte 2000).
* **Das fünfte Experiment („Menge ohne klaren Sieger“) entfällt**, weil die vorab festgelegte Suche keine Kandidatenmenge fand; der Befund steht im eingefrorenen Vergleich und unter den Grenzen.
* **Die Zustandsansicht meldet einen vierten Fall** („einige Zugarten der Menge finden nichts mehr“): die Planung hätte ihn als „alle aktiv“ bezeichnet.
* **Kein `pandas`, kein `scipy` zur Laufzeit**; `scipy` nur in den Tests (Gegenprobe der Rangkorrelation).
* **Ausblendbare Regler gibt es nicht**, deshalb auch keinen Test dafür.

## Bewusst nicht enthalten

Eine Auswahlregel, die sich je Zustand ändert; die Erklärung, warum eine Belohnung eine Lernregel fehlleitet (Demo zu den Auswahlregeln); das Zusammenspiel von Akzeptanz und Auswahl als eigener Befund (Demo „Akzeptanz mal Auswahl“; hier ist die Akzeptanz ein Schalter); vorab auf Trainingsinstanzen gelernte Mischungen und ihre Kosten (Demo zu den Kosten der Meta-Ebene); weitere Zugarten (Or-opt variabler Länge, 3-opt); Tourenplanung mit Kapazitäten, Bin Packing; „alle Züge annehmen“ und „besser oder gleich“ als Schalter; UCB und andere Bandit-Regeln; Mehrfachvergleichskorrektur; PDF-Export.

## Quellen

Mit dem, was gelesen wurde. Burke, Gendreau, Hyde, Kendall, Ochoa, Özcan, Qu (2013), „Hyper-heuristics: a survey of the state of the art“, Journal of the Operational Research Society 64(12), S. 1695 bis 1724 (Volltext gelesen): Einteilung; die Menge der Heuristiken ist dort von Menschen gewählt. Sobotka, Kletzander, Musliu, Rudová (2025), „Key Principles in Cross-Domain Hyper-Heuristic Performance“, arXiv 2509.02782 (Vorabdruck ohne Begutachtung; Hauptteil gelesen, Anhänge nicht): Eingriffe in die Menge der Niedrigebenen-Heuristiken bei gleichverteilter Zufallsauswahl. Branke, Nguyen, Pickardt, Zhang (2016), „Automated design of production scheduling heuristics: a review“, IEEE Transactions on Evolutionary Computation 20(1), S. 110 bis 124 (angenommene Fassung gelesen): der Vergleich bei gleicher Auswertungszahl ist nur begrenzt gültig. Dueck (1993), Journal of Computational Physics 104(1), S. 86 bis 92 (nur die Kurzfassung gelesen): Rekord-zu-Rekord. Burke und Bykov (2017), European Journal of Operational Research 258(1), S. 70 bis 78 (nur die Kurzfassung gelesen): Late Acceptance. Cowling, Kendall, Soubeiga (2000/2001), Choice Function (nicht selbst gelesen); die Formel folgt Drake, Özcan, Burke (2012), „An improved choice function heuristic selection for cross domain heuristic search“ (Volltext gelesen), in eigener vereinfachter Umsetzung ohne die adaptive Gewichtung des Originals. Ropke und Pisinger (2006), Transportation Science 40(4), S. 455 bis 472 (nur die Kurzfassung gelesen): Einsatz konkurrierender Teilheuristiken nach bisheriger Leistung. Zahlen aus der Literatur zu Auswahl-Hyperheuristiken sind nicht auf diese Aufgabe übertragbar; Literaturreferenzwerte für die Zahlen dieser Demo gibt es nicht.

## Verifikation

- **Kern in kleinen Einheiten:** jede Zugart, jede Akzeptanzregel, die Suche und die Statistik sind Kopien aus der Wurzel-Demo mit deren Tests (`tests/test_moves.py`, `test_accept.py`, `test_search.py`, `test_scenario.py`, `test_stats.py`, `test_rng.py`) und Kopier-Tests (`tests/test_copies.py`). Jede Auswahlregel hat einen von Hand gerechneten Schritt (`tests/test_select.py`), der Mitschreiber der Beiträge ebenso (`tests/test_eigenschaften_zugmenge.py`).
- **Orakel** (`tests/test_oracle_zugmenge.py`, unabhängige Rechenwege): Längenänderung gegen volle Neubewertung in jedem angenommenen Zug, auch mit Lernregeln; Held-Karp gegen Aufzählung, die Suche unterbietet das Optimum bei 11 Städten nie; die Ziehung der App gegen die exakte Verteilung; die ganze Suche gegen eine Markov-Kette über die 60 Touren des Handbeispiels; K(S) gegen die gemessene Wartezeit.
- **Eigenschaften:** Budget exakt, nur Zugarten der Menge, Reihenfolge der Mengenangabe ohne Wirkung, gleicher Zufalls-Seed gleiches Ergebnis, Bestwert monoton, Beiträge ergänzen sich exakt, jede Zugart und jede Auswahlregel ändert auf mindestens einer Instanz das Ergebnis, Verschieben und Strecken der Instanz.
- **Verdikte:** jede Schwelle und jeder Fall (`tests/test_verdicts.py`), die Rechengrenze an jedem Reglerwert, Worst-Case am Reglermaximum (`tests/test_worstcase.py`).
- **App:** jedes Beispiel, Schritt-Regler, leere Menge, einzelne Zugart, Permalink, Regler am Maximum (`tests/test_app.py`, `test_app_demo.py`, `test_layout.py`).
- **Nicht geprüft:** Lauf unter Linux (die Suche benutzt nur Grundrechenarten und `math.sqrt`; Bootstrap-Intervalle sind deshalb mit Band getestet); ein unabhängiger Leser der Texte und des Formelblocks.

## Tests

574 Tests (`pytest --collect-only -q tests`), Laufzeit mit zwei Prozessen (`pytest tests -q -n 2`) rund drei Minuten auf dem Entwicklungsrechner unter Last anderer Rechnungen (kein Befund).

Zusammensetzung: Kern aus der Wurzel-Demo 301 (Suche 201, Zugarten 65, Szenario 14, Zufall 9, Akzeptanz 8, Statistik 4), Kopier-Tests 9, Auswahlregeln 16, Läufe und Mitschreiber 26, Handbeispiel exakt 14, Orakel 45, eingefrorene Messung 12, Aussagen 20, Verdikte 40, Beispiele 22, Worst-Case 3, Layout 33, App 23 (allgemeiner Rauchtest 3, demo-eigen 20), Footer, Laufzeit-Importe und Neuladen 10.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Seitengerüst: fester Kopf, Einleitung, Erklärtabellen, vier Kernfragen, eingefrorener Vergleich, Handbeispiel, Grenzen, Formeln |
| `zgm_constants.py` | Zugarten, Familien, Budgetstufen, die 12 Mengen, Parameter der Auswahlregeln, Marken, Regler-Grenzen, Beispiele |
| `zgm_rng.py`, `zgm_rngblock.py` | SplitMix64 (unveränderte Vorlage) und der bitgleiche Blockstrom |
| `zgm_scenario.py`, `zgm_moves.py`, `zgm_accept.py`, `zgm_search.py`, `zgm_stats.py` | Kopien aus der Wurzel-Demo: Instanzen, Zugarten, Akzeptanz, Suche, Statistik |
| `zgm_select.py` | Auswahlregeln: Zufallsauswahl, Choice Function, Lernautomat, Q-Lernen; Adapter für die Suche |
| `zgm_beitrag.py` | Mitschreiber: Beitrag je Zugart zum Bestwert, Kontrollpunkte, Zählung in Anwendungen |
| `zgm_exact.py` | Ziehungen mit Wahrscheinlichkeiten, p_h, K(S), lokale Optima, Held-Karp, Markov-Kette des Handbeispiels |
| `zgm_experiments.py` | Läufe mit festen Zufalls-Seeds, Live-Messung, Referenz |
| `zgm_band.py` | Zugriff auf die eingefrorene Messung und alle Zählungen |
| `zgm_evaluation.py` | Verdikte als reine Funktionen, Rechengrenze |
| `zgm_presets.py`, `zgm_layout.py`, `zgm_visualization.py`, `zgm_texts.py` | Permalink und Beispiele; fester Kopf; Plotly; Texte, Formelblock, Annahmen |
| `zgm_band.json`, `zgm_refs.json` | eingefrorene Messung, Referenzwerte |
| `tools/zgm_make_refs.py`, `tools/zgm_make_band.py` | erzeugen die beiden Dateien; `zgm_make_band.py --check` rechnet einen Ausschnitt neu |
| `modul_frisch.py` | lädt geänderte Hilfsmodule nach einem Update neu |
| `tests/` | siehe Verifikation |

## Lokal ausführen

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html).
