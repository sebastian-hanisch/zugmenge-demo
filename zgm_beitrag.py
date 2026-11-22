"""Mitschreiber am Haken der Suche: zählt je Zugart, was sie zum Bestwert beiträgt, und hält Zwischenstände fest.

`Recorder` umhüllt eine Auswahlregel (zgm_select.Selector), reicht `choose` und `update` unverändert durch und rechnet aus den Meldungen
der Suche (delta, kosten, angenommen) die Länge der aktuellen Tour und den Bestwert nach, mit derselben Arithmetik wie die Suche. Daraus:

    gain_best[h]    Summe der Senkungen des Bestwerts durch Anwendungen der Zugart h (Summe über h = Startlänge - Bestwert, exakt)
    gain_brutto[h]  Summe aller angenommenen strengen Verbesserungen der Zugart h (auch solcher, die nur frühere Verschlechterungen aufholen)
    ck_gain[i]      gain_best beim Erreichen des Auswertungs-Kontrollpunkts i (wie `ck` der Suche)
    app_best[i]     Bestwert nach genau app_checkpoints[i] Anwendungen (Zähleinheit Anwendungen statt Auswertungen)"""

import zgm_constants as C


class Recorder:
    def __init__(self, inner, arms, cost0: float, checkpoints=(), app_checkpoints=()):
        self.inner = inner
        self.arms = tuple(arms)
        self.cost = cost0
        self.best = cost0
        self.used = 0
        self.apps = 0
        self.gain_best = [0.0] * C.K
        self.gain_brutto = [0.0] * C.K
        self._ck = sorted(checkpoints)
        self._cki = 0
        self.ck_gain = []
        self._ack = sorted(app_checkpoints)
        self._acki = 0
        self.app_best = []

    def choose(self, rng) -> int:
        return self.inner.choose(rng)

    def update(self, index: int, delta: float, kosten: int, angenommen: bool) -> None:
        self.inner.update(index, delta, kosten, angenommen)
        self.used += kosten
        self.apps += 1
        if angenommen:
            h = self.arms[index]
            self.cost = self.cost + delta
            if delta < -C.EPS:
                self.gain_brutto[h] -= delta
            if self.cost < self.best - 1e-12:
                self.gain_best[h] += self.best - self.cost
                self.best = self.cost
        while self._cki < len(self._ck) and self.used >= self._ck[self._cki]:
            self.ck_gain.append(list(self.gain_best))
            self._cki += 1
        while self._acki < len(self._ack) and self.apps >= self._ack[self._acki]:
            self.app_best.append(self.best)
            self._acki += 1

    def finish(self) -> None:
        """Füllt Kontrollpunkte auf, die das Budget nicht erreicht hat (wie die Suche)."""
        while self._cki < len(self._ck):
            self.ck_gain.append(list(self.gain_best))
            self._cki += 1
        while self._acki < len(self._ack):
            self.app_best.append(self.best)
            self._acki += 1
