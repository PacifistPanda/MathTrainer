"""
Math-Trainer (Deutsch) — Wettbewerbsorientierte Kopfrechen-Trainingsanwendung.

Funktionen:
    - Fünf Modi: Addition (+), Subtraktion (−), Multiplikation (×), Division (÷), Zufall (🎲)
    - Fünf Schwierigkeitsstufen: 1-stellig, 2-stellig, 3-stellig, 4-stellig und zufällig
    - Konfigurierbare Zeitbegrenzung (2–30s pro Aufgabe) und Aufgabenanzahl (0 = unendlich)
    - Heller/dunkler Farbschema-Umschalter mit sofortiger Live-Umschaltung
    - Spiel- und aufgabenbezogene Zeitmessung für Wettbewerbsstatistiken
    - Persistentes Spielprotokoll mit Tages-/Allzeitbestwerten
    - Statistik-Dashboard: Tagesbester, Allzeitbester, Vergleich mit letztem Spiel, schnellstes/langsamstes Spiel, schnellste Lösung

Architektur:
    Einzelne Datei-Anwendung mit tkinter. Oberfläche, Logik und Farbschema in einer Klasse (MathTrainer).
    Datenspeicherung via JSON unter ~/.config/MathTrainer/data.json.

    Anordnung:
        ┌──────────────────────────────────────┐
        │ Modus: + − × ÷ 🎲        ☀️/🌙      │  ← mode_row
        │ Ziffern: 1  2  3  4  🎲              │  ← digits_row
        │ Zeit: [10] Anzahl: [0](0=∞)   [🚀]  │  ← settings_row
        ├──────────────────────────────────────┤
        │                                      │
        │              8 × 7                   │  ← problem_label (oder Statistiken bei Ende)
        │             [____]                   │  ← answer_entry
        │        ⏱ 8s        ✓ Richtig!       │  ← timer + feedback
        ├──────────────────────────────────────┤
        │ Punkte: 5/8   Beste: 82%  [⏸]       │  ← bottom bar
        └──────────────────────────────────────┘

    Spielablauf:
        start_game() → next_problem() → [Benutzer antwortet] → check_answer()
                                                                  ↓
                              timeout() ← tick() ← Timer läuft ab
                                  ↓
                              next_problem() (oder finish_game() wenn Anzahl erreicht)

    Datenschema (~/.config/MathTrainer/data.json):
        {
          "settings": {
            "time_limit": 10,      # Sekunden pro Aufgabe
            "count_limit": 0,      # 0 = unendlich
            "mode": "×",           # "+", "-", "×", "÷", "random"
            "digits": 1,           # 1, 2, 3, 4 oder 0 (zufällig)
            "dark_mode": true
          },
          "games": [
            {
              "id": 1,
              "timestamp": "2025-07-18T14:30:00",
              "mode": "×",
              "digits": 1,
              "time_limit": 10,
              "count_limit": 10,
              "score": 8,
              "total": 10,
              "accuracy": 80.0,
              "elapsed_seconds": 95.3,
              "completed_by": "count",     # "count" oder "time"
              "problem_times": [2.1, 1.5, ...]  // Sekunden pro richtiger Antwort
            }
          ]
        }

    Eine neue Operation hinzufügen:
        1. Fügen Sie das Operatorsymbol zur THEMES-Radio-Buttons-Liste in _build_ui() hinzu
        2. Fügen Sie einen elif-Zweig in next_problem() hinzu, um die Aufgabe zu generieren und self.current_answer zu setzen
        3. Stellen Sie sicher, dass der Zweig die Zifferneinstellung für den Zahlenbereich der Operanden berücksichtigt
        4. Bei Zufallsmodus: Fügen Sie das Symbol zur random.choice-Liste in next_problem() hinzu

    Ein neues Farbschema hinzufügen:
        1. Fügen Sie einen neuen Eintrag zum THEMES-Dictionary mit allen erforderlichen Schlüsseln hinzu
        2. Benötigte Schlüssel: bg, card, input_bg, input_fg, fg, accent, accent_hover,
           correct, wrong, score, gold, muted, border, btn_disabled

    Eine neue Statistik hinzufügen:
        1. Berechnen Sie sie in _compute_stats() und fügen Sie sie zum Rückgabewörterbuch hinzu
        2. Zeigen Sie sie in finish_game() an, indem Sie sie zur Zeilenliste hinzufügen

    Ziffernbewusste Aufgabengenerierung:
        Die Hilfsfunktion _digit_range() gibt (lo, hi) für eine n-stellige Zahl zurück.
        Jede Operation verwendet dies für die Operandenbereiche:
          +  : a,b aus dem Ziffernbereich
          −  : a aus der oberen Hälfte des Bereichs, b kleiner (ergibt positives Ergebnis)
          ×  : a,b aus dem Ziffernbereich
          ÷  : Antwort aus dem Ziffernbereich, Divisor aus dem Ziffernbereich, Dividend = Antwort × Divisor
        Bei digits=0 (zufällig) wird die tatsächliche Ziffernanzahl pro Aufgabe aus 1–4 gewählt.
"""

import os
import json
import time
import random
import datetime
import tkinter as tk
from tkinter import ttk

# ── Farbschema-Definitionen ────────────────────────────────────────────
# Jedes Farbschema definiert Farben für jedes Oberflächenelement.
# Um ein Farbschema hinzuzufügen: kopieren Sie "dark" oder "light" und passen Sie die Werte an.
# Alle Schlüssel sind erforderlich, damit apply_theme() funktioniert.

THEMES = {
    "dark": {
        "bg": "#212121", "card": "#252525", "input_bg": "#303030", "input_fg": "#e0e0e0",
        "fg": "#e0e0e0", "accent": "#fab283", "accent_hover": "#f5a742",
        "correct": "#7fd88f", "wrong": "#e06c75", "score": "#e5c07b", "gold": "#fab283",
        "muted": "#6a6a6a", "border": "#4b4c5c", "btn_disabled": "#3a3a3a",
    },
    "light": {
        "bg": "#f5f5f5", "card": "#ffffff", "input_bg": "#eaeaea", "input_fg": "#1a1a1a",
        "fg": "#1a1a1a", "accent": "#3b7dd8", "accent_hover": "#2a6bc5",
        "correct": "#2e7d32", "wrong": "#c62828", "score": "#8d6e0f", "gold": "#bf6a10",
        "muted": "#666666", "border": "#d0d0d0", "btn_disabled": "#c0c0c0",
    },
}

# ── Schriftart-Definitionen ─────────────────────────────────────────────
# Zentralisiert, damit alle Textgrößen an einem Ort sind.
# FONT_PROBLEM wird hier nicht definiert, da es sich mit der Ziffernanzahl skaliert.

FONT = ("Arial", 12)
FONT_SM = ("Arial", 9)
FONT_LG = ("Arial", 16, "bold")
FONT_BTN = ("Arial", 11, "bold")
FONT_TIMER = ("Arial", 22, "bold")
FONT_FEEDBACK = ("Arial", 20, "bold")
FONT_STATS = ("Consolas", 12)
FONT_THEME = ("Arial", 13)

# Die Aufgabenschrift skaliert umgekehrt zur Ziffernanzahl, um in die Fensterbreite zu passen.
# Der Aufgabentext wächst wie: "8 × 7" (3 Zeichen) → "12 × 34" (7 Zeichen) → "1234 × 5678" (13 Zeichen).
FONT_PROBLEM = {1: ("Arial", 52, "bold"), 2: ("Arial", 44, "bold"), 3: ("Arial", 38, "bold"), 4: ("Arial", 34, "bold")}


# ── Hilfsfunktionen zur Datenspeicherung ─────────────────────────────────

def get_data_dir():
    """Gibt ~/.config/MathTrainer/ zurück und erstellt es bei Bedarf."""
    d = os.path.join(os.path.expanduser("~"), ".config", "MathTrainer")
    os.makedirs(d, exist_ok=True)
    return d


def load_data(path):
    """Lädt JSON-Daten von einem Pfad. Gibt Standardstruktur bei jedem Fehler zurück."""
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"settings": {}, "games": []}


def save_data(path, data):
    """Speichert Daten als schön formatiertes JSON und erstellt bei Bedarf übergeordnete Verzeichnisse."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── Hauptanwendung ─────────────────────────────────────────────────────

class MathTrainer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Math-Trainer")
        self.root.geometry("540x680")
        self.root.resizable(False, False)

        # ── Spielstatus ──
        self.time_limit = tk.IntVar(value=10)    # Sekunden pro Aufgabe
        self.count_limit = tk.IntVar(value=0)     # 0 = unendlich
        self.mode = tk.StringVar(value="×")       # +, -, ×, ÷, Zufall
        self.digits = tk.IntVar(value=1)          # 1, 2, 3, 4 Ziffern pro Operand, oder 0 für zufällig
        self.score = self.total = self.remaining = self.target_count = 0
        self.timer_id = self.current_answer = None
        self.waiting_for_next = self.paused = False

        # ── Datenspeicherung ──
        self.data_path = os.path.join(get_data_dir(), "data.json")
        self.data = load_data(self.data_path)
        self.game_start_time = self.problem_start_time = None
        self.current_problem_times = []  # Aufgabenbezogene Lösungszeiten in Sekunden

        # ── Gespeicherte Einstellungen wiederherstellen ──
        s = self.data.get("settings", {})
        self.time_limit.set(s.get("time_limit", 10))
        self.count_limit.set(s.get("count_limit", 0))
        self.mode.set(s.get("mode", "×"))
        self.digits.set(s.get("digits", 1))
        self.dark_mode = s.get("dark_mode", True)
        self.t = THEMES["dark" if self.dark_mode else "light"]

        # ── ttk-Stil-Einrichtung ──
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self._build_ui()
        self.apply_theme()
        self.root.mainloop()

    # ── Oberflächenerstellung ──────────────────────────────────────────
    # Widget-Hierarchie:
    #   root
    #     main (Einrahmung mit Innenabstand)
    #       top
    #         mode_row     — Operator-Radios + Farbschema-Umschalter
    #         digits_row   — Ziffernanzahl-Radios
    #         settings_row — Zeit-/Anzahl-Spinboxen + Start-Button
    #       problem_frame  — Frage, Antworteingabe, Timer, Feedback
    #         bottom       — Punkte, Bester, Pause-Button

    def _build_ui(self):
        self.main = tk.Frame(self.root)
        self.main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.top = tk.Frame(self.main)
        self.top.pack(fill=tk.X, pady=(0, 15))

        # ── Modusauswahl-Zeile ──
        self.mode_row = tk.Frame(self.top)
        self.mode_row.pack(fill=tk.X, pady=(0, 5))

        self.mode_label = tk.Label(self.mode_row, text="Modus:", font=FONT)
        self.mode_label.pack(side=tk.LEFT)

        # Um eine neue Operation hinzuzufügen: ("Symbol", " Anzeige ") an diese Liste anhängen
        for val, txt in [("+", " + "), ("-", " − "), ("×", " × "), ("÷", " ÷ "), ("random", " 🎲 ")]:
            ttk.Radiobutton(self.mode_row, text=txt, variable=self.mode, value=val,
                            style="Mode.TRadiobutton").pack(side=tk.LEFT, padx=(2, 0))

        self.theme_btn = tk.Button(self.mode_row, text="☀️", command=self.toggle_theme,
                                   font=FONT_THEME, bd=0, padx=6, pady=0, cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT)

        # ── Ziffernanzahl-Auswahl-Zeile ──
        # Steuert die Größe der Operanden: 1 (1–9), 2 (10–99), 3 (100–999), 4 (1000–9999), zufällig (gemischt).
        # Radio-Buttons für saubere diskrete Auswahl.
        self.digits_row = tk.Frame(self.top)
        self.digits_row.pack(fill=tk.X, pady=(0, 5))

        self.digits_label = tk.Label(self.digits_row, text="Ziffern:", font=FONT)
        self.digits_label.pack(side=tk.LEFT)

        for val, txt in [(1, " 1 "), (2, " 2 "), (3, " 3 "), (4, " 4 "), (0, " 🎲 ")]:
            ttk.Radiobutton(self.digits_row, text=txt, variable=self.digits, value=val,
                            style="Mode.TRadiobutton").pack(side=tk.LEFT, padx=(2, 0))

        # ── Einstellungs-Zeile ──
        self.settings_row = tk.Frame(self.top)
        self.settings_row.pack(fill=tk.X)

        self.time_label = tk.Label(self.settings_row, text="Zeit:", font=FONT)
        self.time_label.pack(side=tk.LEFT)
        self.spin = tk.Spinbox(self.settings_row, from_=2, to=30, textvariable=self.time_limit,
                               width=4, font=("Arial", 12, "bold"), bd=0, highlightthickness=0, justify="center")
        self.spin.pack(side=tk.LEFT, padx=(4, 0))

        self.count_label = tk.Label(self.settings_row, text="Anzahl:", font=FONT)
        self.count_label.pack(side=tk.LEFT, padx=(10, 0))
        self.count_spin = tk.Spinbox(self.settings_row, from_=0, to=99, textvariable=self.count_limit,
                                     width=4, font=("Arial", 12, "bold"), bd=0, highlightthickness=0, justify="center")
        self.count_spin.pack(side=tk.LEFT, padx=(4, 0))
        self.inf_label = tk.Label(self.settings_row, text="(0=∞)", font=FONT_SM)
        self.inf_label.pack(side=tk.LEFT, padx=(2, 0))

        self.start_btn = ttk.Button(self.settings_row, text="🚀 Start", command=self.start_game, style="Start.TButton")
        self.start_btn.pack(side=tk.RIGHT)

        self.pause_btn = tk.Button(self.settings_row, text="⏸ Pause", command=self.toggle_pause,
                                   font=FONT_BTN, bd=0, padx=12, pady=4, state="disabled")
        self.pause_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # ── Aufgabenbereich ──
        self.problem_frame = tk.Frame(self.main, highlightthickness=4, bd=0)
        self.problem_frame.pack(expand=True, fill=tk.BOTH)

        self.problem_label = ttk.Label(self.problem_frame, text="", style="Problem.TLabel")
        self.problem_label.pack(expand=True, pady=(30, 5))

        # Die Eingabebreite wird dynamisch in next_problem() basierend auf der Ziffernanzahl gesetzt
        self.answer_entry = tk.Entry(self.problem_frame, font=("Arial", 28), width=10, justify="center",
                                     bd=0, highlightthickness=2)
        self.answer_entry.pack(pady=(0, 5))
        self.answer_entry.bind("<Return>", self.check_answer)
        self.answer_entry.config(state="disabled")

        self.timer_feedback = tk.Frame(self.problem_frame)
        self.timer_feedback.pack(pady=(5, 10))

        self.timer_label = ttk.Label(self.timer_feedback, text="", style="Timer.TLabel")
        self.timer_label.pack(side=tk.LEFT, padx=(0, 20))

        self.feedback_label = ttk.Label(self.timer_feedback, text="", style="Feedback.TLabel")
        self.feedback_label.pack(side=tk.LEFT)

        # ── untere Leiste ──
        self.bottom = tk.Frame(self.main)
        self.bottom.pack(fill=tk.X, pady=(10, 0))

        self.score_label = ttk.Label(self.bottom, text="Punkte: 0 / 0", style="Score.TLabel")
        self.score_label.pack(side=tk.LEFT)

        best = self._all_time_best()
        self.best_label = ttk.Label(self.bottom, text=f"Beste: {best:.0f}%", style="Best.TLabel")
        self.best_label.pack(side=tk.LEFT, padx=(15, 0))

        self.watermark = tk.Label(self.bottom, text="by PacifistPanda", font=FONT_SM)
        self.watermark.pack(side=tk.RIGHT, padx=(0, 10))

    # ── Farbschema ──────────────────────────────────────────────────────
    # apply_theme() liest self.t (aktuelles Farbschema-Dictionary) und wendet Farben
    # auf jedes Widget an. Wird beim Start und bei toggle_theme() aufgerufen.
    #
    # Um ein neues Widget mit Farbschema zu versehen: Fügen Sie hier seinen configure()-Aufruf hinzu.

    def apply_theme(self):
        t = self.t
        self.root.configure(bg=t["bg"])

        # Hintergrundrahmen
        for w in [self.main, self.top, self.mode_row, self.digits_row, self.settings_row, self.bottom]:
            w.configure(bg=t["bg"])
        self.timer_feedback.configure(bg=t["card"])

        # Beschriftungen
        for w in [self.mode_label, self.digits_label, self.time_label, self.count_label, self.inf_label]:
            w.configure(bg=t["bg"], fg=t["fg"])
        self.watermark.configure(bg=t["bg"], fg=t["muted"])
        self.theme_btn.configure(bg=t["bg"], fg=t["fg"], activebackground=t["bg"], activeforeground=t["accent"])

        # Eingabe-Widgets
        for w in [self.spin, self.count_spin]:
            w.configure(bg=t["input_bg"], fg=t["input_fg"], buttonbackground=t["accent"], insertbackground=t["input_fg"])

        # Aufgabenbereich
        self.problem_frame.configure(bg=t["card"], highlightbackground=t["card"])
        self.answer_entry.configure(bg=t["input_bg"], fg=t["input_fg"], insertbackground=t["input_fg"],
                                    highlightbackground=t["accent"], highlightcolor=t["accent"])

        # ttk-Stile — steuern Farben für alle Widgets, die diesen Stil verwenden
        s = self.style
        s.configure(".", background=t["bg"], foreground=t["fg"], fieldbackground=t["card"])
        s.configure("TFrame", background=t["bg"])
        s.configure("TLabel", background=t["bg"], foreground=t["fg"])
        s.configure("TButton", background=t["accent"], foreground=t["bg"], borderwidth=0,
                    focusthickness=0, font=FONT_BTN)
        s.map("TButton", background=[("active", t["accent_hover"]), ("disabled", t["btn_disabled"])])
        s.configure("Start.TButton", background=t["correct"], font=FONT_BTN)
        s.map("Start.TButton", background=[("active", t["correct"]), ("disabled", t["btn_disabled"])])
        s.configure("Timer.TLabel", background=t["card"], foreground=t["fg"], font=FONT_TIMER)
        s.configure("Feedback.TLabel", background=t["card"], foreground=t["fg"], font=FONT_FEEDBACK)
        s.configure("Problem.TLabel", background=t["card"], foreground=t["fg"],
                    font=FONT_PROBLEM[self.digits.get() or 1])
        s.configure("Mode.TRadiobutton", background=t["bg"], foreground=t["fg"], font=FONT_LG)
        s.map("Mode.TRadiobutton", foreground=[("selected", t["accent"])])
        s.configure("Score.TLabel", background=t["bg"], foreground=t["score"], font=FONT_LG)
        s.configure("Best.TLabel", background=t["bg"], foreground=t["muted"], font=("Arial", 10))

        # Widgets, die individuelle Farbüberschreibungen benötigen
        self.timer_label.configure(background=t["card"])
        self.feedback_label.configure(background=t["card"])
        self.score_label.configure(background=t["bg"], foreground=t["score"])
        self.best_label.configure(background=t["bg"], foreground=t["muted"])

        # Pause-Button: rot bei aktivem Spiel, grau bei deaktiviert
        if str(self.pause_btn["state"]) == "normal":
            self.pause_btn.configure(bg=t["wrong"], activebackground=t["wrong"], fg=t["bg"])
        else:
            self.pause_btn.configure(bg=t["btn_disabled"], activebackground=t["btn_disabled"], fg=t["muted"])

    def toggle_theme(self):
        """Wechselt zwischen dunklem und hellem Modus, speichert die Einstellung und aktualisiert alle Farben."""
        self.dark_mode = not self.dark_mode
        self.t = THEMES["dark" if self.dark_mode else "light"]
        self.theme_btn.configure(text="☀️" if self.dark_mode else "🌙")
        self.apply_theme()
        self.data.setdefault("settings", {})["dark_mode"] = self.dark_mode
        save_data(self.data_path, self.data)

    # ── Datenhilfsfunktionen ─────────────────────────────────────────

    def _all_time_best(self):
        """Gibt die höchste Genauigkeit (%) über alle Spiele zurück, oder 0 wenn keine vorhanden."""
        games = self.data.get("games", [])
        return max((g["accuracy"] for g in games), default=0)

    def _save_settings(self):
        """Speichert die aktuellen Benutzeroberflächeneinstellungen in der Datendatei."""
        self.data["settings"] = {
            "time_limit": self.time_limit.get(),
            "count_limit": self.count_limit.get(),
            "mode": self.mode.get(),
            "digits": self.digits.get(),
            "dark_mode": self.dark_mode,
        }
        save_data(self.data_path, self.data)

    @staticmethod
    def _digit_range(d):
        """Gibt (lo, hi) einschließlich Grenzen für eine d-stellige Zahl zurück.
        1-stellig: (1, 9), 2-stellig: (10, 99), 3-stellig: (100, 999), 4-stellig: (1000, 9999)."""
        if d == 1:
            return (1, 9)
        lo = 10 ** (d - 1)
        hi = 10 ** d - 1
        return (lo, hi)

    def _compute_stats(self):
        """
        Berechnet alle Wettbewerbsstatistiken aus dem Spielprotokoll.

        Gibt ein Wörterbuch zurück mit:
            daily_high       — beste Genauigkeit heute (%)
            all_time_high    — beste Genauigkeit aller Zeiten (%)
            vs_last          — Genauigkeit des vorherigen Spiels (zum Vergleich)
            fastest_game     — kürzeste Spielzeit (nur bei anzahlbasierten Spielen)
            slowest_game     — längste Spielzeit (nur bei anzahlbasierten Spielen)
            fastest_solve_today — schnellste Einzelauflösung heute
            fastest_solve_all   — schnellste Einzelauflösung aller Zeiten
            today_count      — Anzahl der heute gespielten Spiele

        Hinweis: Zeitbasierte Statistiken (fastest_game, fastest_solve) vergleichen
        über alle Zifferneinstellungen hinweg. Die Zeit eines 1-stelligen Spiels ist nicht
        direkt vergleichbar mit der eines 4-stelligen Spiels. Für ziffernspezifische Rekorde,
        filtern Sie Spiele nach g.get("digits", 1) vor der Berechnung.
        """
        games = self.data.get("games", [])
        today = datetime.date.today().isoformat()
        today_games = [g for g in games if g["timestamp"][:10] == today]

        # Alle aufgabenbezogenen Lösungszeiten aus einer Spielliste flach klopfen
        solve_times = lambda gl: [t for g in gl for t in g.get("problem_times", [])]

        # Nur anzahlbasierte Spiele haben aussagekräftige vergangene Zeit
        count_games = [g for g in games if g.get("completed_by") == "count" and g.get("elapsed_seconds", 0) > 0]

        return {
            "daily_high": max((g["accuracy"] for g in today_games), default=None),
            "all_time_high": max((g["accuracy"] for g in games), default=None),
            "vs_last": games[-2]["accuracy"] if len(games) >= 2 else None,
            "fastest_game": min((g["elapsed_seconds"] for g in count_games), default=None),
            "slowest_game": max((g["elapsed_seconds"] for g in count_games), default=None),
            "fastest_solve_today": min(solve_times(today_games), default=None),
            "fastest_solve_all": min(solve_times(games), default=None),
            "today_count": len(today_games),
        }

    @staticmethod
    def _fmt_time(secs):
        """Formatiert Sekunden als 'XMin YSek' oder 'XSek'."""
        m, s = divmod(int(secs), 60)
        return f"{m}Min {s}Sek" if m else f"{s}Sek"

    # ── Spiellogik ───────────────────────────────────────────────────
    # Die Spielschleife wird durch den after()-Timer-Mechanismus von tkinter gesteuert.
    # Jede Aufgabe hat einen Countdown. Wenn dieser abläuft oder der Benutzer antwortet,
    # wird entweder die nächste Aufgabe angezeigt oder das Spiel beendet.

    def start_game(self):
        """Setzt den Status zurück und beginnt ein neues Spiel."""
        self.score = self.total = 0
        self.target_count = self.count_limit.get()
        self.waiting_for_next = self.paused = False
        self.current_problem_times = []
        self.game_start_time = time.time()
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="⏸ Pause", bg=self.t["wrong"],
                              activebackground=self.t["wrong"], fg=self.t["bg"])
        self._save_settings()
        d = self.digits.get() or 1  # 0 (zufällig) → 1-stellige Schriftart als Platzhalter verwenden
        self.problem_label.config(text="", font=FONT_PROBLEM[d], anchor="center", justify="center")
        self.next_problem()

    def next_problem(self):
        """
        Generiert und zeigt die nächste Aufgabe an.

        Im Zufallsmodus wird bei jedem Aufruf zufällig eine Operation ausgewählt.
        Die Aufgabengenerierung berücksichtigt die Zifferneinstellung über _digit_range().
        Passt die Eingabebreite an, um die größtmögliche Antwort unterzubringen.
        Ruft finish_game() auf, wenn die Zielanzahl erreicht wurde.

        Um eine neue Operation hinzuzufügen:
            1. Fügen Sie unten einen elif-Zweig hinzu
            2. Setzen Sie self.current_answer auf die richtige Antwort
            3. Setzen Sie den problem_label-Text auf die Anzeigezeichenfolge
            4. Verwenden Sie _digit_range(self.digits.get()) für die Operandenbereiche
        """
        if self.target_count > 0 and self.total >= self.target_count:
            self.finish_game()
            return
        self.total += 1

        # Ziffernanzahl auflösen: 0 = zufällig (1–4), sonst direkt verwenden
        d = self.digits.get()
        if d == 0:
            d = random.randint(1, 4)
        lo, hi = self._digit_range(d)
        op = self.mode.get()
        if op == "random":
            op = random.choice(["+", "-", "×", "÷"])

        # Aufgabe basierend auf Operation und Ziffernanzahl generieren
        if op == "+":
            a = random.randint(lo, hi)
            b = random.randint(lo, hi)
            self.current_answer = a + b
            self.problem_label.config(text=f"{a} + {b}")
        elif op == "-":
            # a liegt in der oberen Hälfte des Bereichs, um a − b > 0 zu gewährleisten
            mid = (lo + hi) // 2
            a = random.randint(mid, hi)
            b = random.randint(lo, a - 1)
            self.current_answer = a - b
            self.problem_label.config(text=f"{a} − {b}")
        elif op == "×":
            a = random.randint(lo, hi)
            b = random.randint(lo, hi)
            self.current_answer = a * b
            self.problem_label.config(text=f"{a} × {b}")
        elif op == "÷":
            # Zuerst Antwort generieren, dann Dividend für saubere Teilung berechnen
            answer = random.randint(lo, hi)
            divisor = random.randint(lo, hi)
            self.current_answer = answer
            self.problem_label.config(text=f"{answer * divisor} ÷ {divisor}")
        else:
            # Fallback: Sollte mit gültigen Moduswerten nicht erreicht werden
            self.current_answer = 0
            self.problem_label.config(text="?")

        # Eingabebreite und Aufgabenschrift für Ziffernanzahl anpassen
        self.answer_entry.config(state="normal")
        self.style.configure("Problem.TLabel", font=FONT_PROBLEM.get(d, FONT_PROBLEM[1]))
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.focus()
        self.feedback_label.config(text="")
        self.waiting_for_next = False
        self.problem_start_time = time.time()

        self.remaining = self.time_limit.get()
        self._update_timer()
        self.timer_id = self.root.after(1000, self._tick)

    def _tick(self):
        """Wird jede Sekunde aufgerufen. Verringert den Timer und löst bei Null einen Timeout aus."""
        self.remaining -= 1
        if self.remaining <= 0:
            self._update_timer()
            self._timeout()
            return
        self._update_timer()
        self.timer_id = self.root.after(1000, self._tick)

    def _update_timer(self):
        """Aktualisiert die Timer-Beschriftung mit Farbverlauf (grün → rot)."""
        total = self.time_limit.get()
        ratio = self.remaining / total if total > 0 else 0
        r = int(255 * (1 - ratio))
        g = int(255 * ratio)
        self.timer_label.config(text=f"⏱ {self.remaining}s", foreground=f"#{r:02x}{g:02x}00")

    def toggle_pause(self):
        """Pausiert/fortsetzt den aktuellen Spieltimer."""
        if self.waiting_for_next:
            return
        if self.paused:
            self.paused = False
            self.pause_btn.config(text="⏸ Pause", bg=self.t["wrong"], activebackground=self.t["wrong"])
            self.answer_entry.config(state="normal")
            self.answer_entry.focus()
            self.timer_id = self.root.after(1000, self._tick)
        else:
            self.paused = True
            self.pause_btn.config(text="▶ Weiter", bg=self.t["wrong"], activebackground=self.t["wrong"])
            self.answer_entry.config(state="disabled")
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None

    def _flash(self, color, text=None):
        """
        Lässt den Aufgabenrahmen mit einer Farbe (richtig/falsch) aufblinken
        und zeigt optional Feedback-Text an. Aktualisiert die Punktebeschriftung.
        """
        self.problem_frame.config(highlightbackground=color, highlightcolor=color, highlightthickness=4)
        self.root.after(800, lambda: self.problem_frame.config(highlightthickness=0, highlightbackground=self.t["card"]))
        if text:
            self.feedback_label.config(text=text, foreground=color)
        if self.target_count > 0:
            self.score_label.config(text=f"{self.total}/{self.target_count} — {self.score}/{self.total}")
        else:
            self.score_label.config(text=f"Punkte: {self.score} / {self.total}")

    def check_answer(self, event=None):
        """Validiert die Antwort des Benutzers, zeichnet die Lösungszeit auf und zeigt Feedback."""
        if self.waiting_for_next:
            return
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        try:
            user_answer = int(self.answer_entry.get())
        except ValueError:
            user_answer = None
        if user_answer == self.current_answer:
            self.current_problem_times.append(time.time() - self.problem_start_time)
            self.score += 1
            self._flash(self.t["correct"], "✓ Richtig!")
        else:
            self._flash(self.t["wrong"], f"✗ {self.current_answer}")
        self.waiting_for_next = True
        self.answer_entry.config(state="disabled")
        self.root.after(1500, self.next_problem)

    def _timeout(self):
        """Behandelt den Aufgaben-Timeout — zeigt die richtige Antwort an und fährt fort."""
        self.timer_id = None
        self._flash(self.t["wrong"], f"✗ Zeit ab! Antwort: {self.current_answer}")
        self.waiting_for_next = True
        self.answer_entry.config(state="disabled")
        self.root.after(2000, self.next_problem)

    def finish_game(self):
        """
        Beendet das aktuelle Spiel: Speichert den Datensatz, berechnet Statistiken, zeigt Dashboard an.

        Schritte:
        1. Schnappschuss der Bestwerte vor dem Speichern (zur Erkennung von "neuer Bestwert")
        2. Spieldatensatz an data['games'] anhängen (enthält auch die Zifferneinstellung)
        3. Alle Statistiken berechnen
        4. Statistik-Dashboard in problem_label aufbauen und anzeigen
        5. Punktebeschriftung mit "neuer Bestwert"-Indikator aktualisieren
        6. Start-Button wieder aktivieren, Pause deaktivieren
        """
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        elapsed = time.time() - self.game_start_time if self.game_start_time else 0
        accuracy = (self.score / self.total * 100) if self.total > 0 else 0
        t = self.t

        # Schnappschuss der Bestwerte vor dem Speichern des aktuellen Spiels
        today_str = datetime.date.today().isoformat()
        today_before = [g for g in self.data.get("games", []) if g["timestamp"][:10] == today_str]
        old_daily = max((g["accuracy"] for g in today_before), default=None)
        old_alltime = max((g["accuracy"] for g in self.data.get("games", [])), default=None)

        # Spieldatensatz speichern
        self.data.setdefault("games", []).append({
            "id": len(self.data.get("games", [])) + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": self.mode.get(),
            "digits": self.digits.get(),
            "time_limit": self.time_limit.get(),
            "count_limit": self.count_limit.get(),
            "score": self.score,
            "total": self.total,
            "accuracy": round(accuracy, 1),
            "elapsed_seconds": round(elapsed, 1),
            "completed_by": "count" if self.target_count > 0 else "time",
            "problem_times": [round(t2, 3) for t2 in self.current_problem_times],
        })
        save_data(self.data_path, self.data)

        new_daily = old_daily is None or accuracy > old_daily
        new_alltime = old_alltime is None or accuracy > old_alltime
        stats = self._compute_stats()

        # ── Statistik-Dashboard-Text aufbauen ──
        # Jede Zeile ist als "Bezeichner:<Auffüllung>Wert" formatiert für Ausrichtung.
        L = 17  # Spaltenbreite des Bezeichners
        d_label = {0: "zufällig", 1: "1-stellig", 2: "2-stellig", 3: "3-stellig", 4: "4-stellig"}[self.digits.get()]
        lines = [f"  Fertig! {self.score}/{self.total} ({accuracy:.0f}%)  [{d_label}]", ""]

        dh = f"{stats['daily_high']:.0f}%" if stats["daily_high"] is not None else "---"
        if stats["today_count"] and stats["today_count"] > 1:
            dh += f"  ({stats['today_count']} Spiele heute)"
        lines.append(f"{'Tagesbeste:':<{L}}{dh}")

        ah = f"{stats['all_time_high']:.0f}%" if stats["all_time_high"] is not None else "---"
        lines.append(f"{'Allzeitbeste:':<{L}}{ah}")

        if stats["vs_last"] is not None:
            d = accuracy - stats["vs_last"]
            vs = f"↑ +{d:.0f}% besser!" if d > 0 else (f"↓ {d:.0f}% schlechter" if d < 0 else "Gleich")
        else:
            vs = "Erstes Spiel!"
        lines.append(f"{'Vgl. Vorher:':<{L}}{vs}")

        fg = self._fmt_time(stats["fastest_game"]) if stats["fastest_game"] is not None else "---"
        lines.append(f"{'Schnellstes Spiel:':<{L}}{fg}")

        sl = self._fmt_time(stats["slowest_game"]) if stats["slowest_game"] is not None else "---"
        lines.append(f"{'Langsamstes Spiel:':<{L}}{sl}")

        parts = []
        if stats["fastest_solve_today"] is not None:
            parts.append(f"{stats['fastest_solve_today']:.1f}s heute")
        if stats["fastest_solve_all"] is not None:
            parts.append(f"{stats['fastest_solve_all']:.1f}s gesamt")
        lines.append(f"{'Schnellste Lösung:':<{L}}{' | '.join(parts) if parts else '---'}")

        self.problem_label.config(text="\n".join(lines), font=FONT_STATS,
                                  foreground=t["fg"], background=t["card"], anchor="w", justify="left")
        self.answer_entry.config(state="disabled")
        self.feedback_label.config(text="")
        self.timer_label.config(text="")

        # ── Punkteanzeige mit bedingtem Feuer-Emoji ──
        if new_alltime:
            self.score_label.config(text=f"🔥 NEUER ALLZEITREKORD! {self.score}/{self.total} ({accuracy:.0f}%) 🔥", foreground=t["gold"])
        elif new_daily:
            self.score_label.config(text=f"🔥 NEUER TAGESREKORD! {self.score}/{self.total} ({accuracy:.0f}%) 🔥", foreground=t["correct"])
        else:
            self.score_label.config(text=f"Punkte: {self.score} / {self.total} ({accuracy:.0f}%)", foreground=t["score"])

        self.best_label.config(text=f"Beste: {self._all_time_best():.0f}%")
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸ Pause", bg=self.t["btn_disabled"],
                              activebackground=self.t["btn_disabled"], fg=self.t["muted"])


if __name__ == "__main__":
    MathTrainer()
