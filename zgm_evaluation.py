"""Verdikte als reine Funktionen und die Rechengrenze je Klick.

Jede Verdikt-Funktion bekommt Zahlen und gibt `dict(kind, level, text)` zurück: `kind` ist der geprüfte Fall, `level` die Farbe der
Meldung (success, info, warning), `text` der Satz. Die Marken (0,25 Prozentpunkte mit Intervall ohne 0, mindestens 4 Instanzen,
Anteile 70 % und 40 %) stehen in zgm_constants und sind gesetzt, nicht abgeleitet."""

import zgm_constants as C


def de(x: float, stellen: int = 2) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{stellen}f}".replace(".", ",")


def de_v(x: float, stellen: int = 2) -> str:
    """Zahl mit Vorzeichen und Dezimalkomma (Minuszeichen als echtes Minus)."""
    text = f"{x:+.{stellen}f}"
    if float(text) == 0.0:                       # weder "+0,00" noch "−0,00"
        text = text[1:]
    return text.replace(".", ",").replace("-", "−")


def tausender(x: int) -> str:
    return f"{int(x):,}".replace(",", " ")


def prozent(x: float, stellen: int = 0) -> str:
    """Anteil 0..1 als Prozentzahl mit Dezimalkomma."""
    return de(100.0 * x, stellen) + " %"


def kontext(m: int, laeufe: int, akz: str, f: int, n: int) -> str:
    """Voraussetzung eines Live-Befunds in einem Satzteil: Instanzen, Läufe, Akzeptanz, Budget in Auswertungen."""
    return (f"{m} Instanzen mit {n} Städten, {laeufe} {'Lauf' if laeufe == 1 else 'Läufe'} je Instanz, Akzeptanz „{C.AKZ_ANZEIGE[akz]}“, "
            f"{f}·n = {tausender(f * n)} Auswertungen je Lauf")


# ---------------------------------------------------------------- Rechengrenze
def plan_runs(n: int, f: int, varianten: int, instanzen: int, laeufe: int, grenze: int = C.RECHENGRENZE) -> dict:
    """Kürzt erst die Läufe je Instanz, dann die Instanzen, bis varianten x instanzen x laeufe x f x n <= grenze (mindestens je 1)."""
    je = varianten * f * n
    m, s = instanzen, laeufe
    while s > 1 and je * m * s > grenze:
        s -= 1
    while m > 1 and je * m * s > grenze:
        m -= 1
    gekuerzt = (m, s) != (instanzen, laeufe)
    kosten = je * m * s
    text = f"Rechenaufwand: {varianten * m * s} Läufe zu je {tausender(f * n)} Auswertungen = {tausender(kosten)} Auswertungen"
    if gekuerzt:
        teile = []
        if s != laeufe:
            teile.append(f"Läufe je Instanz von {laeufe} auf {s}")
        if m != instanzen:
            teile.append(f"Instanzen von {instanzen} auf {m}")
        text += f" ({' und '.join(teile)} gekürzt, Grenze {tausender(grenze)} Auswertungen je Vergleich)"
    return dict(instanzen=m, laeufe=s, gekuerzt=gekuerzt, kosten=kosten, text=text + ".")


def _zu_wenig(n_inst: int, band_instanzen: int) -> dict:
    return dict(kind="zu_wenig", level="info",
                text=f"Mit {n_inst} Instanzen ist kein Urteil möglich (mindestens {C.MIN_INSTANZEN}); der eingefrorene Vergleich hat {band_instanzen} Instanzen.")


def _klasse(d, lo, hi) -> str:
    if lo is None or hi is None:
        return "rauschen"
    if d >= C.MARKE and lo > 0:
        return "plus"
    if d <= -C.MARKE and hi < 0:
        return "minus"
    return "rauschen"


def _intervall(lo, hi) -> str:
    if lo is None or hi is None:
        return "ohne Intervall"
    return f"Intervall {de_v(lo)} bis {de_v(hi)}"


# ---------------------------------------------------------------- Experiment 1
def verdict_beitrag(e, a, menge, laeufe: int, ktx: str) -> dict:
    """Wer liefert die Verbesserung des Bestwerts? e, a: Anteile je Zugart (Länge 8) am Beitrag zum Bestwert und an den Auswertungen."""
    if laeufe == 0:
        return dict(kind="keine_verbesserung", level="info", text=f"Kein Lauf hat die Starttour verbessert ({ktx}); es gibt keinen Beitrag zu verteilen.")
    top = max(menge, key=lambda h: (e[h], -h))
    fam = [h for h in menge if h in C.FAMILIE_2OPT]
    if not fam:
        return dict(kind="fam_fehlt", level="info",
                    text=f"Die Menge enthält keine Zugart der 2-opt-Familie; bekommt {C.HNAMEN[top]} den größten Beitrag zum Bestwert zugerechnet "
                         f"({prozent(e[top])}; {laeufe} Läufe mit Verbesserung, {ktx}).")
    e_fam = sum(e[h] for h in fam)
    a_fam = sum(a[h] for h in fam)
    rest = sorted((h for h in menge if h not in fam), key=lambda h: -e[h])
    if e_fam >= C.BEITRAG_VIEL:
        return dict(kind="fam_liefert", level="success",
                    text=f"Der 2-opt-Familie werden {prozent(e_fam)} der Verbesserung des Bestwerts zugerechnet; sie bekommt dafür {prozent(a_fam)} der Auswertungen "
                         f"({laeufe} Läufe mit Verbesserung, {ktx}).")
    if e_fam >= C.BEITRAG_TEILS:
        andere = ", ".join(f"{C.HNAMEN[h]} {prozent(e[h])}" for h in rest[:3])
        return dict(kind="fam_teils", level="info",
                    text=f"Der 2-opt-Familie werden nur {prozent(e_fam)} der Verbesserung des Bestwerts zugerechnet, bei {prozent(a_fam)} der Auswertungen; "
                         f"der Rest verteilt sich auf {andere} ({laeufe} Läufe mit Verbesserung, {ktx}).")
    return dict(kind="fam_wenig", level="warning",
                text=f"Der 2-opt-Familie werden nur {prozent(e_fam)} der Verbesserung des Bestwerts zugerechnet, bei {prozent(a_fam)} der Auswertungen "
                     f"({laeufe} Läufe mit Verbesserung, {ktx}).")


def verdict_zustand(p, menge) -> dict:
    """Wer kann an diesem Zustand noch verbessern? p: Verbesserungswahrscheinlichkeit je Zugart (Länge 8)."""
    aktiv = [h for h in menge if p[h] > 0]
    fertig = [h for h in menge if p[h] <= 0]
    fam = [h for h in menge if h in C.FAMILIE_2OPT]
    namen = lambda hs: ", ".join(C.HNAMEN[h] for h in hs)   # noqa: E731
    if not aktiv:
        return dict(kind="optimum", level="warning",
                    text="Die Tour ist ein lokales Optimum dieser Menge: keine Zugart der Menge hat hier einen Zug, der die Tour verkürzt.")
    if fam and all(p[h] <= 0 for h in fam):
        return dict(kind="fam_fertig", level="info", text=f"Die 2-opt-Familie hat an dieser Tour keinen verbessernden Zug mehr; verbessern können noch {namen(aktiv)}.")
    if not fertig:
        return dict(kind="alle_aktiv", level="success", text="Jede Zugart der Menge hat an dieser Tour noch mindestens einen verbessernden Zug.")
    return dict(kind="teils", level="info",
                text=f"An dieser Tour gibt es keinen verbessernden Zug mehr für {namen(fertig)}; verbessern können noch {namen(aktiv)}.")


# ---------------------------------------------------------------- Experiment 2
def verdict_menge(d, lo, hi, n_inst: int, label: str, ktx: str, band_instanzen: int = 0) -> dict:
    """Gewählte Menge gegen alle acht: d = Abstand(alle acht) - Abstand(Menge), positiv = die Menge ist besser."""
    if n_inst < C.MIN_INSTANZEN:
        return _zu_wenig(n_inst, band_instanzen)
    kl = _klasse(d, lo, hi)
    if kl == "plus":
        return dict(kind="hilft", level="success",
                    text=f"Mit der Menge „{label}“ ist der Abstand im Mittel {de(d)} Prozentpunkte kleiner als mit allen acht Zugarten "
                         f"({_intervall(lo, hi)}; {ktx}): was hier fehlt, hilft in dieser Einstellung nicht.")
    if kl == "minus":
        return dict(kind="schadet", level="warning",
                    text=f"Mit der Menge „{label}“ ist der Abstand im Mittel {de(-d)} Prozentpunkte größer als mit allen acht Zugarten "
                         f"({_intervall(lo, hi)}; {ktx}): was hier fehlt, wird in dieser Einstellung gebraucht.")
    return dict(kind="rauschen", level="info",
                text=f"Mit der Menge „{label}“ ändert sich der Abstand um {de_v(d)} Prozentpunkte gegenüber allen acht Zugarten "
                     f"({_intervall(lo, hi)}; {ktx}): kein belegter Unterschied.")


# ---------------------------------------------------------------- Experiment 3
def verdict_teilmenge(stufen, n_inst: int, label: str, ktx: str, band_instanzen: int = 0) -> dict:
    """Feste Teilmenge T3 gegen die Menge S über die drei Budgets. stufen: je Stufe (d, lo, hi), d = Abstand(S) - Abstand(T3)."""
    if n_inst < C.MIN_INSTANZEN:
        return dict(_zu_wenig(n_inst, band_instanzen), je_stufe=[])
    arten = [{"plus": "t3_vorn", "minus": "s_vorn", "rauschen": "gleich"}[_klasse(d, lo, hi)] for d, lo, hi in stufen]
    namen = [C.STUFEN_ANZEIGE[f] for f in C.STUFEN]
    worte = {"t3_vorn": "feste Teilmenge vorn", "s_vorn": f"„{label}“ vorn", "gleich": "kein belegter Unterschied"}
    liste = ", ".join(f"{nm}: {worte[a]} ({de_v(s[0])})" for nm, a, s in zip(namen, arten, stufen))
    if arten[0] == "t3_vorn" and arten[-1] == "s_vorn":
        k1 = max(i for i, a in enumerate(arten) if a == "t3_vorn" and all(x != "s_vorn" for x in arten[:i + 1]))
        k2 = min(i for i, a in enumerate(arten) if a == "s_vorn")
        return dict(kind="kreuzung", level="info", je_stufe=arten,
                    text=f"Die feste Teilmenge liegt bei kleinem Budget vorn und bei großem hinten (Kreuzung zwischen {C.STUFEN[k1]}·n und {C.STUFEN[k2]}·n). "
                         f"{liste} ({ktx}).")
    if all(a == "s_vorn" for a in arten):
        return dict(kind="s_immer", level="success", je_stufe=arten, text=f"Die Menge „{label}“ liegt bei jedem der drei Budgets vor der festen Teilmenge. {liste} ({ktx}).")
    if all(a == "t3_vorn" for a in arten):
        return dict(kind="t3_immer", level="warning", je_stufe=arten, text=f"Die feste Teilmenge liegt bei jedem der drei Budgets vor der Menge „{label}“. {liste} ({ktx}).")
    return dict(kind="gemischt", level="info", je_stufe=arten, text=f"Gemischt: {liste} ({ktx}).")


# ---------------------------------------------------------------- Experiment 4
def verdict_lernregel(g, lo, hi, n_inst: int, regel: str, ktx: str, band_instanzen: int = 0) -> dict:
    """Lernregel gegen Zufallsauswahl auf derselben Menge: g = Abstand(Zufall) - Abstand(Regel), positiv = die Regel ist besser."""
    if n_inst < C.MIN_INSTANZEN:
        return _zu_wenig(n_inst, band_instanzen)
    name = C.REGEL_ANZEIGE[regel]
    kl = _klasse(g, lo, hi)
    if kl == "plus":
        return dict(kind="hilft", level="success", text=f"{name} gewinnt {de(g)} Prozentpunkte gegen die Zufallsauswahl ({_intervall(lo, hi)}; {ktx}).")
    if kl == "minus":
        return dict(kind="schadet", level="warning", text=f"{name} verliert {de(-g)} Prozentpunkte gegen die Zufallsauswahl ({_intervall(lo, hi)}; {ktx}).")
    return dict(kind="rauschen", level="info", text=f"{name} liegt {de_v(g)} Prozentpunkte zur Zufallsauswahl ({_intervall(lo, hi)}; {ktx}): kein belegter Unterschied.")


def verdict_menge_vs_lernen(spann: float, gplus: float, gmin: float, mengen: int, ktx: str) -> dict:
    """Eingefrorener Vergleich je Zelle: Spannweite der Zufallsauswahl über die Mengen gegen den größten Gewinn einer Lernregel."""
    verlust = f"; sie verliert bis zu {de(-gmin)}" if gmin <= -C.MARKE else ""
    if spann >= C.SPANN_FAKTOR * max(gplus, C.MARKE):
        if gplus <= 0:
            return dict(kind="menge_mehr", level="success",
                        text=f"Die Menge bewegt die Zufallsauswahl um {de(spann)} Prozentpunkte; keine der drei Lernregeln gewinnt auf einer der {mengen} Mengen{verlust} ({ktx}).")
        return dict(kind="menge_mehr", level="success",
                    text=f"Die Menge bewegt die Zufallsauswahl um {de(spann)} Prozentpunkte; die beste der drei Lernregeln gewinnt auf keiner der {mengen} Mengen "
                         f"mehr als {de(gplus)}{verlust} ({ktx}).")
    if gplus > spann:
        return dict(kind="lernen_mehr", level="warning",
                    text=f"Der größte Gewinn einer Lernregel ({de(gplus)} Prozentpunkte) übersteigt die Spannweite über die Mengen ({de(spann)}){verlust} ({ktx}).")
    return dict(kind="gleich_gross", level="info",
                text=f"Spannweite über die Mengen {de(spann)} Prozentpunkte, größter Gewinn einer Lernregel {de(gplus)}: dieselbe Größenordnung{verlust} ({ktx}).")


def show(st, verdikt: dict) -> None:
    """Zeigt ein Verdikt in der Farbe seines Falls."""
    getattr(st, verdikt["level"])(verdikt["text"])
