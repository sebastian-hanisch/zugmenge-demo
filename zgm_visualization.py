"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import zgm_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_progress(start: float, punkte, budget: int, schritt_used: int | None = None):
    """Verlauf des Bestwerts eines Laufs über den Auswertungen; jeder neue Bestwert ist ein Punkt in der Farbe seiner Zugart."""
    fig = go.Figure()
    xs, ys = [0], [start]
    for used, best, _ in punkte:
        xs.append(used)
        ys.append(best)
    xs.append(budget)
    ys.append(ys[-1])
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_GRAU, shape="hv", width=2), name="Bestwert", hoverinfo="skip"))
    for h in range(C.K):
        hx = [u for u, _, z in punkte if z == h]
        if hx:
            fig.add_trace(go.Scatter(x=hx, y=[b for _, b, z in punkte if z == h], mode="markers", marker=dict(color=C.FARBE_ZUGART[h], size=8),
                                     name=C.HNAMEN[h], hovertemplate="%{x} Auswertungen<br>Bestwert %{y:.1f}<extra>" + C.HNAMEN[h] + "</extra>"))
    if schritt_used is not None:
        fig.add_trace(go.Scatter(x=[schritt_used, schritt_used], y=[min(ys), max(ys)], mode="lines", line=dict(color="#444", dash="dot", width=1),
                                 name="gewählter Schritt", hoverinfo="skip"))
    fig.update_xaxes(title_text="Auswertungen", range=[0, budget * 1.02])
    fig.update_yaxes(title_text="Länge der besten Tour")
    return _base(fig)


def build_contribution(e, a, menge):
    """Je Zugart der Menge zwei Balken: Anteil am Beitrag zum Bestwert und Anteil an den Auswertungen (in Prozent)."""
    namen = [C.HNAMEN[h] for h in menge]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=namen, y=[100.0 * e[h] for h in menge], name="Beitrag zum Bestwert", marker_color=C.COLOR_MENGE,
                         hovertemplate="%{x}: %{y:.1f} %<extra>Beitrag</extra>"))
    fig.add_trace(go.Bar(x=namen, y=[100.0 * a[h] for h in menge], name="Anteil an den Auswertungen", marker_color=C.COLOR_GRAU,
                         hovertemplate="%{x}: %{y:.1f} %<extra>Auswertungen</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Anteil in Prozent", range=[0, 100])
    return _base(fig)


def build_state(p, menge):
    """Je Zugart der Menge: Anteil der Ziehungen, die die Tour am gewählten Zustand streng verkürzen (in Prozent)."""
    namen = [C.HNAMEN[h] for h in menge]
    werte = [100.0 * float(p[h]) for h in menge]
    fig = go.Figure(go.Bar(x=namen, y=werte, marker_color=[C.FARBE_ZUGART[h] for h in menge], hovertemplate="%{x}: %{y:.2f} %<extra></extra>"))
    fig.update_yaxes(title_text="verbessernde Ziehungen in Prozent", range=[0, max(werte + [1.0]) * 1.15])
    return _base(fig, height=300)


def build_pair(namen, mittel, intervalle, farben, y_titel="Abstand in Prozent"):
    """Balken mit Bootstrap-Intervallen (None: ohne Intervall)."""
    fig = go.Figure()
    plus = [(hi - m) if (lo is not None) else 0.0 for m, (lo, hi) in zip(mittel, intervalle)]
    minus = [(m - lo) if (lo is not None) else 0.0 for m, (lo, hi) in zip(mittel, intervalle)]
    fig.add_trace(go.Bar(x=namen, y=mittel, marker_color=farben, error_y=dict(type="data", symmetric=False, array=plus, arrayminus=minus, color="#444"),
                         hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
    oben = max([m + p for m, p in zip(mittel, plus)] + [0.5])
    unten = min([m - q for m, q in zip(mittel, minus)] + [0.0])
    fig.update_yaxes(title_text=y_titel, range=[unten * 1.15 if unten < 0 else 0, oben * 1.15])
    fig.update_layout(showlegend=False)
    return _base(fig, height=320)


def build_curves(x, kurven, marken):
    """Verlaufskurven mit Band. kurven: Liste (Name, Mittel, lo, hi, Farbe, Bandfarbe); marken: Auswertungszahlen der Budgetstufen."""
    fig = go.Figure()
    oben = 0.0
    for name, mittel, lo, hi, farbe, band in kurven:
        if lo is not None:
            fig.add_trace(go.Scatter(x=list(x) + list(x)[::-1], y=list(hi) + list(lo)[::-1], fill="toself", fillcolor=band, line=dict(width=0),
                                     hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=list(x), y=list(mittel), mode="lines+markers", line=dict(color=farbe, width=2), marker=dict(size=4), name=name,
                                 hovertemplate="%{x} Auswertungen<br>%{y:.2f} %<extra>" + name + "</extra>"))
        oben = max(oben, max(hi if hi is not None else mittel))
    for m in marken:
        fig.add_trace(go.Scatter(x=[m, m], y=[0, oben * 1.05], mode="lines", line=dict(color="#888", dash="dot", width=1), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(title_text="Auswertungen", range=[0, max(x) * 1.02])
    fig.update_yaxes(title_text="mittlerer Abstand des Bestwerts in Prozent", range=[0, oben * 1.08])
    return _base(fig, height=380)
