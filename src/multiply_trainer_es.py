"""
Entrenamiento Matemáticas — Versión en español.

A competitive mental arithmetic training application (Spanish UI).

Features:
    - Five modes: addition (+), subtraction (−), multiplication (×), division (÷), random (🎲)
    - Five difficulty levels: 1-digit, 2-digit, 3-digit, 4-digit, and random
    - Configurable time limit (2–30s per problem) and question count (0 = infinite)
    - Light/dark theme toggle with full live-switching
    - Per-game and per-problem timing for competitive stats
    - Persistent game log with daily/all-time high scores
    - Stats dashboard: daily high, all-time high, vs last game, fastest/slowest game, fastest solve

Architecture:
    Single-file tkinter application. All UI, logic, and theming in one class (MathTrainer).
    Data persistence via JSON at ~/.config/MathTrainer/data.json.

    Layout:
        ┌──────────────────────────────────────┐
        │ Mode: + − × ÷ 🎲        ☀️/🌙      │  ← mode_row
        │ Digits: 1  2  3  4  🎲               │  ← digits_row
        │ Time: [10] Count: [0](0=∞)   [🚀]  │  ← settings_row
        ├──────────────────────────────────────┤
        │                                      │
        │              8 × 7                   │  ← problem_label (or stats on finish)
        │             [____]                   │  ← answer_entry
        │        ⏱ 8s        ✓ ¡Correcto!     │  ← timer + feedback
        ├──────────────────────────────────────┤
        │ Puntos: 5/8   Mejor: 82%  [⏸]       │  ← bottom bar
        └──────────────────────────────────────┘

    Game flow:
        start_game() → next_problem() → [user answers] → check_answer()
                                                              ↓
                              timeout() ← tick() ← timer expires
                                  ↓
                              next_problem() (or finish_game() if count reached)

    Data schema (~/.config/MathTrainer/data.json):
        {
          "settings": {
            "time_limit": 10,      // seconds per problem
            "count_limit": 0,      // 0 = infinite
            "mode": "×",           // "+", "-", "×", "÷", "random"
            "digits": 1,           // 1, 2, 3, 4, or 0 (random)
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
              "completed_by": "count",     // "count" or "time"
              "problem_times": [2.1, 1.5, ...]  // seconds per correct answer
            }
          ]
        }

    Adding a new operation:
        1. Add the operator symbol to the THEMES radio buttons list in _build_ui()
        2. Add an elif branch in next_problem() to generate the problem and set self.current_answer
        3. Ensure the branch respects the digits setting for operand ranges
        4. If using random mode, add the symbol to the random.choice list in next_problem()

    Adding a new theme:
        1. Add a new entry to the THEMES dict with all required keys
        2. Keys needed: bg, card, input_bg, input_fg, fg, accent, accent_hover,
           correct, wrong, score, gold, muted, border, btn_disabled

    Adding a new stat:
        1. Compute it in _compute_stats() and add to the returned dict
        2. Display it in finish_game() by appending to the lines list

    Digit-aware problem generation:
        The _digit_range() helper returns (lo, hi) for an n-digit number.
        Each operation uses this to set operand bounds:
          +  : a,b from digit range
          −  : a from upper half of range, b smaller (ensures positive result)
          ×  : a,b from digit range
          ÷  : answer from digit range, divisor from digit range, dividend = answer * divisor
        When digits=0 (random), the actual digit count is picked per-problem from 1–4.
"""

import os
import json
import time
import random
import datetime
import tkinter as tk
from tkinter import ttk

# ── Theme definitions ────────────────────────────────────────────────
# Each theme defines colors for every UI element.
# To add a theme: copy "dark" or "light" and adjust values.
# All keys are required for apply_theme() to work.

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

# ── Font definitions ─────────────────────────────────────────────────
# Centralized so all text sizing is in one place.
# FONT_PROBLEM is not defined here because it scales with digit count.

FONT = ("Arial", 12)
FONT_SM = ("Arial", 9)
FONT_LG = ("Arial", 16, "bold")
FONT_BTN = ("Arial", 11, "bold")
FONT_TIMER = ("Arial", 22, "bold")
FONT_FEEDBACK = ("Arial", 20, "bold")
FONT_STATS = ("Consolas", 12)
FONT_THEME = ("Arial", 13)

# Problem font scales inversely with digit count to fit the window width.
# The problem text grows as: "8 × 7" (3 chars) → "12 × 34" (7 chars) → "1234 × 5678" (13 chars).
FONT_PROBLEM = {1: ("Arial", 52, "bold"), 2: ("Arial", 44, "bold"), 3: ("Arial", 38, "bold"), 4: ("Arial", 34, "bold")}


# ── Data persistence helpers ─────────────────────────────────────────

def get_data_dir():
    """Return ~/.config/MathTrainer/, creating it if needed."""
    d = os.path.join(os.path.expanduser("~"), ".config", "MathTrainer")
    os.makedirs(d, exist_ok=True)
    return d


def load_data(path):
    """Load JSON data from path. Returns default structure on any error."""
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"settings": {}, "games": []}


def save_data(path, data):
    """Write data as pretty-printed JSON, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── Main application ─────────────────────────────────────────────────

class MathTrainer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Entrenamiento Matemáticas")
        self.root.geometry("540x680")
        self.root.resizable(False, False)

        # ── Game state ──
        self.time_limit = tk.IntVar(value=10)    # seconds per problem
        self.count_limit = tk.IntVar(value=0)     # 0 = infinite
        self.mode = tk.StringVar(value="×")       # +, -, ×, ÷, random
        self.digits = tk.IntVar(value=1)          # 1, 2, 3, 4 digits per operand, or 0 for random
        self.score = self.total = self.remaining = self.target_count = 0
        self.timer_id = self.current_answer = None
        self.waiting_for_next = self.paused = False

        # ── Data persistence ──
        self.data_path = os.path.join(get_data_dir(), "data.json")
        self.data = load_data(self.data_path)
        self.game_start_time = self.problem_start_time = None
        self.current_problem_times = []  # per-problem solve times in seconds

        # ── Restore saved settings ──
        s = self.data.get("settings", {})
        self.time_limit.set(s.get("time_limit", 10))
        self.count_limit.set(s.get("count_limit", 0))
        self.mode.set(s.get("mode", "×"))
        self.digits.set(s.get("digits", 1))
        self.dark_mode = s.get("dark_mode", True)
        self.t = THEMES["dark" if self.dark_mode else "light"]

        # ── ttk style setup ──
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self._build_ui()
        self.apply_theme()
        self.root.mainloop()

    # ── UI construction ──────────────────────────────────────────────
    # Widget hierarchy:
    #   root
    #     main (padding wrapper)
    #       top
    #         mode_row     — operation radios + theme toggle
    #         digits_row   — digit count radios
    #         settings_row — time/count spinboxes + start button
    #       problem_frame  — question, answer input, timer, feedback
    #       bottom         — score, best, pause button

    def _build_ui(self):
        self.main = tk.Frame(self.root)
        self.main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.top = tk.Frame(self.main)
        self.top.pack(fill=tk.X, pady=(0, 15))

        # ── Mode selection row ──
        self.mode_row = tk.Frame(self.top)
        self.mode_row.pack(fill=tk.X, pady=(0, 5))

        self.mode_label = tk.Label(self.mode_row, text="Modo:", font=FONT)
        self.mode_label.pack(side=tk.LEFT)

        # To add a new operation: append ("symbol", " display ") to this list
        for val, txt in [("+", " + "), ("-", " − "), ("×", " × "), ("÷", " ÷ "), ("random", " 🎲 ")]:
            ttk.Radiobutton(self.mode_row, text=txt, variable=self.mode, value=val,
                            style="Mode.TRadiobutton").pack(side=tk.LEFT, padx=(2, 0))

        self.theme_btn = tk.Button(self.mode_row, text="☀️", command=self.toggle_theme,
                                   font=FONT_THEME, bd=0, padx=6, pady=0, cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT)

        # ── Digits selection row ──
        # Controls operand size: 1 (1–9), 2 (10–99), 3 (100–999), 4 (1000–9999), random (mixed).
        # Using radio buttons for clean discrete selection.
        self.digits_row = tk.Frame(self.top)
        self.digits_row.pack(fill=tk.X, pady=(0, 5))

        self.digits_label = tk.Label(self.digits_row, text="Dígitos:", font=FONT)
        self.digits_label.pack(side=tk.LEFT)

        for val, txt in [(1, " 1 "), (2, " 2 "), (3, " 3 "), (4, " 4 "), (0, " 🎲 ")]:
            ttk.Radiobutton(self.digits_row, text=txt, variable=self.digits, value=val,
                            style="Mode.TRadiobutton").pack(side=tk.LEFT, padx=(2, 0))

        # ── Settings row ──
        self.settings_row = tk.Frame(self.top)
        self.settings_row.pack(fill=tk.X)

        self.time_label = tk.Label(self.settings_row, text="Tiempo:", font=FONT)
        self.time_label.pack(side=tk.LEFT)
        self.spin = tk.Spinbox(self.settings_row, from_=2, to=30, textvariable=self.time_limit,
                               width=4, font=("Arial", 12, "bold"), bd=0, highlightthickness=0, justify="center")
        self.spin.pack(side=tk.LEFT, padx=(4, 0))

        self.count_label = tk.Label(self.settings_row, text="Cantidad:", font=FONT)
        self.count_label.pack(side=tk.LEFT, padx=(10, 0))
        self.count_spin = tk.Spinbox(self.settings_row, from_=0, to=99, textvariable=self.count_limit,
                                     width=4, font=("Arial", 12, "bold"), bd=0, highlightthickness=0, justify="center")
        self.count_spin.pack(side=tk.LEFT, padx=(4, 0))
        self.inf_label = tk.Label(self.settings_row, text="(0=∞)", font=FONT_SM)
        self.inf_label.pack(side=tk.LEFT, padx=(2, 0))

        self.start_btn = ttk.Button(self.settings_row, text="🚀 Start", command=self.start_game, style="Start.TButton")
        self.start_btn.pack(side=tk.RIGHT)

        self.pause_btn = tk.Button(self.settings_row, text="⏸ Pausa", command=self.toggle_pause,
                                   font=FONT_BTN, bd=0, padx=12, pady=4, state="disabled")
        self.pause_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # ── Problem area ──
        self.problem_frame = tk.Frame(self.main, highlightthickness=4, bd=0)
        self.problem_frame.pack(expand=True, fill=tk.BOTH)

        self.problem_label = ttk.Label(self.problem_frame, text="", style="Problem.TLabel")
        self.problem_label.pack(expand=True, pady=(30, 5))

        # Entry width is set dynamically in next_problem() based on digit count
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

        # ── Bottom bar ──
        self.bottom = tk.Frame(self.main)
        self.bottom.pack(fill=tk.X, pady=(10, 0))

        self.score_label = ttk.Label(self.bottom, text="Puntos: 0 / 0", style="Score.TLabel")
        self.score_label.pack(side=tk.LEFT)

        best = self._all_time_best()
        self.best_label = ttk.Label(self.bottom, text=f"Mejor: {best:.0f}%", style="Best.TLabel")
        self.best_label.pack(side=tk.LEFT, padx=(15, 0))

        self.watermark = tk.Label(self.bottom, text="by PacifistPanda", font=FONT_SM)
        self.watermark.pack(side=tk.RIGHT, padx=(0, 10))

    # ── Theming ──────────────────────────────────────────────────────
    # apply_theme() reads self.t (current theme dict) and applies colors
    # to every widget. Called on init and on toggle_theme().
    #
    # To add a new themed widget: add its configure() call here.

    def apply_theme(self):
        t = self.t
        self.root.configure(bg=t["bg"])

        # Background frames
        for w in [self.main, self.top, self.mode_row, self.digits_row, self.settings_row, self.bottom]:
            w.configure(bg=t["bg"])
        self.timer_feedback.configure(bg=t["card"])

        # Labels
        for w in [self.mode_label, self.digits_label, self.time_label, self.count_label, self.inf_label]:
            w.configure(bg=t["bg"], fg=t["fg"])
        self.watermark.configure(bg=t["bg"], fg=t["muted"])
        self.theme_btn.configure(bg=t["bg"], fg=t["fg"], activebackground=t["bg"], activeforeground=t["accent"])

        # Input widgets
        for w in [self.spin, self.count_spin]:
            w.configure(bg=t["input_bg"], fg=t["input_fg"], buttonbackground=t["accent"], insertbackground=t["input_fg"])

        # Problem area
        self.problem_frame.configure(bg=t["card"], highlightbackground=t["card"])
        self.answer_entry.configure(bg=t["input_bg"], fg=t["input_fg"], insertbackground=t["input_fg"],
                                    highlightbackground=t["accent"], highlightcolor=t["accent"])

        # ttk styles — these control colors for all widgets using each style
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

        # Widgets that need per-instance color overrides
        self.timer_label.configure(background=t["card"])
        self.feedback_label.configure(background=t["card"])
        self.score_label.configure(background=t["bg"], foreground=t["score"])
        self.best_label.configure(background=t["bg"], foreground=t["muted"])

        # Pause button: red when game active, grey when disabled
        if str(self.pause_btn["state"]) == "normal":
            self.pause_btn.configure(bg=t["wrong"], activebackground=t["wrong"], fg=t["bg"])
        else:
            self.pause_btn.configure(bg=t["btn_disabled"], activebackground=t["btn_disabled"], fg=t["muted"])

    def toggle_theme(self):
        """Switch between dark and light mode, save preference, refresh all colors."""
        self.dark_mode = not self.dark_mode
        self.t = THEMES["dark" if self.dark_mode else "light"]
        self.theme_btn.configure(text="☀️" if self.dark_mode else "🌙")
        self.apply_theme()
        self.data.setdefault("settings", {})["dark_mode"] = self.dark_mode
        save_data(self.data_path, self.data)

    # ── Data helpers ─────────────────────────────────────────────────

    def _all_time_best(self):
        """Return the highest accuracy (%) across all games, or 0 if none."""
        games = self.data.get("games", [])
        return max((g["accuracy"] for g in games), default=0)

    def _save_settings(self):
        """Persist current UI settings to the data file."""
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
        """Return (lo, hi) inclusive bounds for a d-digit number.
        1-digit: (1, 9), 2-digit: (10, 99), 3-digit: (100, 999), 4-digit: (1000, 9999)."""
        if d == 1:
            return (1, 9)
        lo = 10 ** (d - 1)
        hi = 10 ** d - 1
        return (lo, hi)

    def _compute_stats(self):
        """
        Compute all competitive statistics from the game log.

        Returns a dict with:
            daily_high       — best accuracy today (%)
            all_time_high    — best accuracy ever (%)
            vs_last          — accuracy of the previous game (for comparison)
            fastest_game     — shortest game time (count-based games only)
            slowest_game     — longest game time (count-based games only)
            fastest_solve_today — fastest single-problem solve today
            fastest_solve_all   — fastest single-problem solve ever
            today_count      — number of games played today

        Note: Time-based stats (fastest_game, fastest_solve) compare across
        all digit settings. A 1-digit game's time is not directly comparable
        to a 4-digit game's time. For per-digit records, filter games by
        g.get("digits", 1) before computing.
        """
        games = self.data.get("games", [])
        today = datetime.date.today().isoformat()
        today_games = [g for g in games if g["timestamp"][:10] == today]

        # Flatten all per-problem solve times from a list of games
        solve_times = lambda gl: [t for g in gl for t in g.get("problem_times", [])]

        # Only count-based games have meaningful elapsed time
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
        """Format seconds as 'Xmin Xs' or 'Xs'."""
        m, s = divmod(int(secs), 60)
        return f"{m}min {s}s" if m else f"{s}s"

    # ── Game logic ───────────────────────────────────────────────────
    # The game loop is driven by tkinter's after() timer mechanism.
    # Each problem gets a countdown. When it expires or the user answers,
    # we either show the next problem or finish the game.

    def start_game(self):
        """Reset state and begin a new game."""
        self.score = self.total = 0
        self.target_count = self.count_limit.get()
        self.waiting_for_next = self.paused = False
        self.current_problem_times = []
        self.game_start_time = time.time()
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="⏸ Pausa", bg=self.t["wrong"],
                              activebackground=self.t["wrong"], fg=self.t["bg"])
        self._save_settings()
        d = self.digits.get() or 1  # 0 (random) → use 1-digit font as placeholder
        self.problem_label.config(text="", font=FONT_PROBLEM[d], anchor="center", justify="center")
        self.next_problem()

    def next_problem(self):
        """
        Generate and display the next problem.

        For random mode, picks an operation randomly each time.
        Problem generation respects the digits setting via _digit_range().
        Adjusts the answer entry width to accommodate the largest possible answer.
        Calls finish_game() if the target count has been reached.

        To add a new operation:
            1. Add an elif branch below
            2. Set self.current_answer to the correct answer
            3. Set the problem_label text to the display string
            4. Use _digit_range(self.digits.get()) for operand bounds
        """
        if self.target_count > 0 and self.total >= self.target_count:
            self.finish_game()
            return
        self.total += 1

        # Resolve digit count: 0 = random (1–4), otherwise use setting directly
        d = self.digits.get()
        if d == 0:
            d = random.randint(1, 4)
        lo, hi = self._digit_range(d)
        op = self.mode.get()
        if op == "random":
            op = random.choice(["+", "-", "×", "÷"])

        # Generate problem based on operation and digit count
        if op == "+":
            a = random.randint(lo, hi)
            b = random.randint(lo, hi)
            self.current_answer = a + b
            self.problem_label.config(text=f"{a} + {b}")
        elif op == "-":
            # a is in the upper half of the range to ensure a − b > 0
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
            # Generate answer first, then compute dividend for clean division
            answer = random.randint(lo, hi)
            divisor = random.randint(lo, hi)
            self.current_answer = answer
            self.problem_label.config(text=f"{answer * divisor} ÷ {divisor}")
        else:
            # Fallback: should not reach here with valid mode values
            self.current_answer = 0
            self.problem_label.config(text="?")

        # Adjust entry width and problem font for digit count
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
        """Called every second. Decrements timer and triggers timeout at zero."""
        self.remaining -= 1
        if self.remaining <= 0:
            self._update_timer()
            self._timeout()
            return
        self._update_timer()
        self.timer_id = self.root.after(1000, self._tick)

    def _update_timer(self):
        """Update the timer label with color gradient (green → red)."""
        total = self.time_limit.get()
        ratio = self.remaining / total if total > 0 else 0
        r = int(255 * (1 - ratio))
        g = int(255 * ratio)
        self.timer_label.config(text=f"⏱ {self.remaining}s", foreground=f"#{r:02x}{g:02x}00")

    def toggle_pause(self):
        """Pause/resume the current game timer."""
        if self.waiting_for_next:
            return
        if self.paused:
            self.paused = False
            self.pause_btn.config(text="⏸ Pausa", bg=self.t["wrong"], activebackground=self.t["wrong"])
            self.answer_entry.config(state="normal")
            self.answer_entry.focus()
            self.timer_id = self.root.after(1000, self._tick)
        else:
            self.paused = True
            self.pause_btn.config(text="▶ Reanudar", bg=self.t["wrong"], activebackground=self.t["wrong"])
            self.answer_entry.config(state="disabled")
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None

    def _flash(self, color, text=None):
        """
        Flash the problem frame border with a color (correct/wrong)
        and optionally show feedback text. Updates the score label.
        """
        self.problem_frame.config(highlightbackground=color, highlightcolor=color, highlightthickness=4)
        self.root.after(800, lambda: self.problem_frame.config(highlightthickness=0, highlightbackground=self.t["card"]))
        if text:
            self.feedback_label.config(text=text, foreground=color)
        if self.target_count > 0:
            self.score_label.config(text=f"{self.total}/{self.target_count} — {self.score}/{self.total}")
        else:
            self.score_label.config(text=f"Puntos: {self.score} / {self.total}")

    def check_answer(self, event=None):
        """Validate the user's answer, record solve time, and show feedback."""
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
            self._flash(self.t["correct"], "✓ ¡Correcto!")
        else:
            self._flash(self.t["wrong"], f"✗ {self.current_answer}")
        self.waiting_for_next = True
        self.answer_entry.config(state="disabled")
        self.root.after(1500, self.next_problem)

    def _timeout(self):
        """Handle problem timeout — show correct answer and move on."""
        self.timer_id = None
        self._flash(self.t["wrong"], f"✗ ¡Tiempo! Respuesta: {self.current_answer}")
        self.waiting_for_next = True
        self.answer_entry.config(state="disabled")
        self.root.after(2000, self.next_problem)

    def finish_game(self):
        """
        End the current game: save the record, compute stats, display dashboard.

        Steps:
        1. Record snapshot of highs before saving (for "new best" detection)
        2. Append game record to data['games'] (includes digits setting)
        3. Compute all stats
        4. Build and display the stats dashboard in problem_label
        5. Update score label with new-best indicator
        6. Re-enable start button, disable pause
        """
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        elapsed = time.time() - self.game_start_time if self.game_start_time else 0
        accuracy = (self.score / self.total * 100) if self.total > 0 else 0
        t = self.t

        # snapshot highs before saving current game
        today_str = datetime.date.today().isoformat()
        today_before = [g for g in self.data.get("games", []) if g["timestamp"][:10] == today_str]
        old_daily = max((g["accuracy"] for g in today_before), default=None)
        old_alltime = max((g["accuracy"] for g in self.data.get("games", [])), default=None)

        # save game record
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

        # ── Build stats dashboard text ──
        # Each line is formatted as "Label:<padding>Value" for alignment.
        L = 17  # label column width
        d_label = {0: "aleatorio", 1: "1 dígito", 2: "2 dígitos", 3: "3 dígitos", 4: "4 dígitos"}[self.digits.get()]
        lines = [f"  ¡Listo! {self.score}/{self.total} ({accuracy:.0f}%)  [{d_label}]", ""]

        dh = f"{stats['daily_high']:.0f}%" if stats["daily_high"] is not None else "---"
        if stats["today_count"] and stats["today_count"] > 1:
            dh += f"  ({stats['today_count']} partidas hoy)"
        lines.append(f"{'Récord del día:':<{L}}{dh}")

        ah = f"{stats['all_time_high']:.0f}%" if stats["all_time_high"] is not None else "---"
        lines.append(f"{'Récord histórico:':<{L}}{ah}")

        if stats["vs_last"] is not None:
            d = accuracy - stats["vs_last"]
            vs = f"↑ +{d:.0f}% ¡mejor!" if d > 0 else (f"↓ {d:.0f}% peor" if d < 0 else "Igual")
        else:
            vs = "¡Primera partida!"
        lines.append(f"{'vs Partida anterior:':<{L}}{vs}")

        fg = self._fmt_time(stats["fastest_game"]) if stats["fastest_game"] is not None else "---"
        lines.append(f"{'Partida más rápida:':<{L}}{fg}")

        sl = self._fmt_time(stats["slowest_game"]) if stats["slowest_game"] is not None else "---"
        lines.append(f"{'Partida más lenta:':<{L}}{sl}")

        parts = []
        if stats["fastest_solve_today"] is not None:
            parts.append(f"{stats['fastest_solve_today']:.1f}s hoy")
        if stats["fastest_solve_all"] is not None:
            parts.append(f"{stats['fastest_solve_all']:.1f}s total")
        lines.append(f"{'Resolución más rápida:':<{L}}{' | '.join(parts) if parts else '---'}")

        self.problem_label.config(text="\n".join(lines), font=FONT_STATS,
                                  foreground=t["fg"], background=t["card"], anchor="w", justify="left")
        self.answer_entry.config(state="disabled")
        self.feedback_label.config(text="")
        self.timer_label.config(text="")

        # ── Score bar with conditional fire emoji ──
        if new_alltime:
            self.score_label.config(text=f"🔥 ¡NUEVO RÉCORD HISTÓRICO! {self.score}/{self.total} ({accuracy:.0f}%) 🔥", foreground=t["gold"])
        elif new_daily:
            self.score_label.config(text=f"🔥 ¡NUEVO RÉCORD DEL DÍA! {self.score}/{self.total} ({accuracy:.0f}%) 🔥", foreground=t["correct"])
        else:
            self.score_label.config(text=f"Puntos: {self.score} / {self.total} ({accuracy:.0f}%)", foreground=t["score"])

        self.best_label.config(text=f"Mejor: {self._all_time_best():.0f}%")
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸ Pausa", bg=self.t["btn_disabled"],
                              activebackground=self.t["btn_disabled"], fg=self.t["muted"])


if __name__ == "__main__":
    MathTrainer()
