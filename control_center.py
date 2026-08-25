"""
GazeAlert Modern Desktop Control Center & Dashboard.
Provides an elegant, dark-mode glassmorphic graphical UI with live gauges,
1-click action buttons, interactive sensitivity sliders, and report launcher.
Zero external dependencies (uses native Python Tkinter with custom styled widgets).
"""

import json
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, Optional


class ControlCenterGUI:
    def __init__(
        self,
        config: Dict[str, Any],
        on_calibrate_center: Optional[Callable[[], None]] = None,
        on_calibrate_9point: Optional[Callable[[], None]] = None,
        on_toggle_pomodoro: Optional[Callable[[], None]] = None,
        on_toggle_sound: Optional[Callable[[], bool]] = None,
        on_toggle_monk: Optional[Callable[[], bool]] = None,
        on_toggle_pill: Optional[Callable[[], bool]] = None,
        on_open_report: Optional[Callable[[], None]] = None,
        on_save_config: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.config = config
        self.on_calibrate_center = on_calibrate_center
        self.on_calibrate_9point = on_calibrate_9point
        self.on_toggle_pomodoro = on_toggle_pomodoro
        self.on_toggle_sound = on_toggle_sound
        self.on_toggle_monk = on_toggle_monk
        self.on_toggle_pill = on_toggle_pill
        self.on_open_report = on_open_report
        self.on_save_config = on_save_config

        self.root: Optional[tk.Toplevel] = None
        self.is_open = False

        # Live telemetry data
        self.focus_pct = 100
        self.status_label = "CONCENTRAT"
        self.pomo_str = "25:00 [STUDIU]"
        self.distance_cm = 55
        self.posture_str = "CORECTA"
        self.xp = 0
        self.level = 1
        self.needed_xp = 100
        self.sound_on = True
        self.monk_on = False

    def show(self, parent_root: Optional[tk.Tk] = None):
        """Display the modern Control Center window."""
        if self.root is not None and tk.Toplevel.winfo_exists(self.root):
            self.root.deiconify()
            self.root.lift()
            return

        if parent_root is not None:
            self.root = tk.Toplevel(parent_root)
        else:
            self.root = tk.Tk()

        self.root.title("GazeAlert Studio • Panou de Control")
        self.root.geometry("640x720")
        self.root.minsize(580, 650)
        self.root.configure(bg="#0b0f19")

        # Window styling
        try:
            icon_p = os.path.join(os.path.dirname(__file__), "app_icon.ico")
            if os.path.exists(icon_p):
                self.root.iconbitmap(icon_p)
        except Exception:
            pass

        self._build_ui()
        self.is_open = True
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.is_open = False
        if self.root:
            self.root.withdraw()

    def _build_ui(self):
        # 1. Header Banner
        header = tk.Frame(self.root, bg="#0f172a", height=70, padx=20, pady=12)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg="#0f172a")
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="⚡ GazeAlert Studio",
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff",
            bg="#0f172a"
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Medical-Grade AI Eye Tracking & Productivity Suite",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg="#0f172a"
        ).pack(anchor="w")

        self.status_badge = tk.Label(
            header,
            text="🟢 MOTOR ACTIV",
            font=("Segoe UI", 9, "bold"),
            fg="#00FF78",
            bg="#162e24",
            padx=12,
            pady=6,
            relief="flat"
        )
        self.status_badge.pack(side="right")

        # 2. Main Scrollable or Notebook Area
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=12)

        # Style Notebook tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TNotebook",
            background="#0b0f19",
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background="#1e293b",
            foreground="#cbd5e1",
            padding=[16, 8],
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#38bdf8")],
            foreground=[("selected", "#0b0f19")]
        )

        tab_live = tk.Frame(notebook, bg="#0b0f19", padx=12, pady=12)
        tab_settings = tk.Frame(notebook, bg="#0b0f19", padx=12, pady=12)

        notebook.add(tab_live, text="📊 Monitor Live")
        notebook.add(tab_settings, text="⚙️ Setări & Sensibilitate")

        self._build_live_tab(tab_live)
        self._build_settings_tab(tab_settings)

    def _build_live_tab(self, parent: tk.Frame):
        # Card 1: Focus & Pomodoro Gauge
        card_focus = tk.Frame(parent, bg="#131d31", padx=16, pady=14, relief="flat", highlightthickness=1, highlightbackground="#1e293b")
        card_focus.pack(fill="x", pady=6)

        tk.Label(card_focus, text="STARE DE CONCENTRARE", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w")

        row1 = tk.Frame(card_focus, bg="#131d31")
        row1.pack(fill="x", pady=8)

        self.lbl_focus_pct = tk.Label(row1, text="100%", font=("Segoe UI", 32, "bold"), fg="#00FF78", bg="#131d31")
        self.lbl_focus_pct.pack(side="left")

        info_box = tk.Frame(row1, bg="#131d31", padx=16)
        info_box.pack(side="left", fill="x", expand=True)

        self.lbl_state = tk.Label(info_box, text="Stare: CONCENTRAT", font=("Segoe UI", 11, "bold"), fg="#ffffff", bg="#131d31")
        self.lbl_state.pack(anchor="w")

        self.lbl_pomo = tk.Label(info_box, text="Pomodoro: 25:00 [STUDIU ACTIV]", font=("Segoe UI", 9), fg="#94a3b8", bg="#131d31")
        self.lbl_pomo.pack(anchor="w")

        self.lbl_posture = tk.Label(info_box, text="Distanță: 55 cm (Postură Corectă)", font=("Segoe UI", 9), fg="#38bdf8", bg="#131d31")
        self.lbl_posture.pack(anchor="w")

        # XP & Level Progress
        card_xp = tk.Frame(parent, bg="#131d31", padx=16, pady=12, highlightthickness=1, highlightbackground="#1e293b")
        card_xp.pack(fill="x", pady=6)

        row_xp = tk.Frame(card_xp, bg="#131d31")
        row_xp.pack(fill="x")

        self.lbl_level = tk.Label(row_xp, text="🏆 Nivel 1 (Novice)", font=("Segoe UI", 11, "bold"), fg="#fbbf24", bg="#131d31")
        self.lbl_level.pack(side="left")

        self.lbl_xp_txt = tk.Label(row_xp, text="0 / 100 XP", font=("Segoe UI", 10), fg="#94a3b8", bg="#131d31")
        self.lbl_xp_txt.pack(side="right")

        self.progress_xp = ttk.Progressbar(card_xp, orient="horizontal", length=400, mode="determinate")
        self.progress_xp.pack(fill="x", pady=6)

        # Action Buttons Hub
        tk.Label(parent, text="ACȚIUNI RAPIDE (1-CLICK)", font=("Segoe UI", 9, "bold"), fg="#64748b", bg="#0b0f19").pack(anchor="w", pady=(12, 4))

        btn_grid = tk.Frame(parent, bg="#0b0f19")
        btn_grid.pack(fill="x")

        def make_btn(text, cmd, color="#1e293b", hover="#334155", fg="#ffffff"):
            btn = tk.Button(
                btn_grid,
                text=text,
                command=cmd,
                font=("Segoe UI", 10, "bold"),
                bg=color,
                fg=fg,
                activebackground=hover,
                activeforeground="#ffffff",
                relief="flat",
                padx=12,
                pady=10,
                cursor="hand2"
            )
            return btn

        b1 = make_btn("🎯 Calibrează Centru (1s)", self._do_calib_center, color="#0284c7")
        b1.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

        b2 = make_btn("📐 Calibrare 9 Puncte", self._do_calib_9point, color="#4f46e5")
        b2.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")

        b3 = make_btn("⏱️ Start/Pauză Pomodoro", self._do_toggle_pomo, color="#059669")
        b3.grid(row=1, column=0, padx=4, pady=4, sticky="nsew")

        self.btn_monk = make_btn("🛡️ Monk Mode: OFF", self._do_toggle_monk, color="#1e293b")
        self.btn_monk.grid(row=1, column=1, padx=4, pady=4, sticky="nsew")

        self.btn_sound = make_btn("🔔 Sunet Alerte: ON", self._do_toggle_sound, color="#1e293b")
        self.btn_sound.grid(row=2, column=0, padx=4, pady=4, sticky="nsew")

        b6 = make_btn("📊 Vezi Raport & Heatmap", self._do_open_report, color="#d97706")
        b6.grid(row=2, column=1, padx=4, pady=4, sticky="nsew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

    def _build_settings_tab(self, parent: tk.Frame):
        # Settings Card
        card = tk.Frame(parent, bg="#131d31", padx=16, pady=16, highlightthickness=1, highlightbackground="#1e293b")
        card.pack(fill="both", expand=True)

        tk.Label(card, text="SENSIBILITATE ȘI PRAGURI ATENȚIE", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w", pady=(0, 12))

        # Slider 1: Unghi Lateral (Yaw)
        tk.Label(card, text="Unghi Limită Lateral (grade monitor):", font=("Segoe UI", 9), fg="#cbd5e1", bg="#131d31").pack(anchor="w")
        self.scale_yaw = tk.Scale(card, from_=12.0, to=35.0, resolution=1.0, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#0b0f19")
        self.scale_yaw.set(float(self.config.get("head_yaw_threshold", 18.0)))
        self.scale_yaw.pack(fill="x", pady=4)

        # Slider 2: Timp Alertă Distragere
        tk.Label(card, text="Timp Alertă Distragere (secunde privit în altă parte):", font=("Segoe UI", 9), fg="#cbd5e1", bg="#131d31").pack(anchor="w", pady=(8, 0))
        self.scale_delay = tk.Scale(card, from_=2.0, to=15.0, resolution=0.5, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#0b0f19")
        self.scale_delay.set(float(self.config.get("away_threshold_seconds", 5.0)))
        self.scale_delay.pack(fill="x", pady=4)

        # Slider 3: Durată Pomodoro Focus
        tk.Label(card, text="Durată Pomodoro Focus (minute):", font=("Segoe UI", 9), fg="#cbd5e1", bg="#131d31").pack(anchor="w", pady=(8, 0))
        self.scale_pomo = tk.Scale(card, from_=10.0, to=60.0, resolution=5.0, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#0b0f19")
        self.scale_pomo.set(float(self.config.get("pomodoro_focus_minutes", 25.0)))
        self.scale_pomo.pack(fill="x", pady=4)

        # Save Button
        btn_save = tk.Button(
            card,
            text="💾 Salvează Preferințele",
            command=self._do_save_settings,
            font=("Segoe UI", 10, "bold"),
            bg="#00FF78",
            fg="#0b0f19",
            activebackground="#00dcff",
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2"
        )
        btn_save.pack(fill="x", pady=16)

    def _do_calib_center(self):
        if self.on_calibrate_center:
            self.on_calibrate_center()

    def _do_calib_9point(self):
        if self.on_calibrate_9point:
            self.on_calibrate_9point()

    def _do_toggle_pomo(self):
        if self.on_toggle_pomodoro:
            self.on_toggle_pomodoro()

    def _do_toggle_monk(self):
        if self.on_toggle_monk:
            active = self.on_toggle_monk()
            self.monk_on = active
            self.btn_monk.configure(
                text=f"🛡️ Monk Mode: {'ON' if active else 'OFF'}",
                bg="#b91c1c" if active else "#1e293b"
            )

    def _do_toggle_sound(self):
        if self.on_toggle_sound:
            active = self.on_toggle_sound()
            self.sound_on = active
            self.btn_sound.configure(
                text=f"🔔 Sunet Alerte: {'ON' if active else 'OFF'}",
                bg="#059669" if active else "#1e293b"
            )

    def _do_open_report(self):
        if self.on_open_report:
            self.on_open_report()

    def _do_save_settings(self):
        self.config["head_yaw_threshold"] = float(self.scale_yaw.get())
        self.config["away_threshold_seconds"] = float(self.scale_delay.get())
        self.config["pomodoro_focus_minutes"] = float(self.scale_pomo.get())
        if self.on_save_config:
            self.on_save_config(self.config)
        messagebox.showinfo("GazeAlert", "Setarile au fost salvate cu succes!")

    def update_telemetry(
        self,
        focus_pct: int,
        status_label: str,
        pomo_str: str,
        distance_cm: int,
        posture_str: str,
        xp: int,
        level: int,
        needed_xp: int,
        level_ratio: float,
        is_focused: bool,
    ):
        """Update live telemetry values on GUI."""
        if not self.is_open or self.root is None:
            return

        try:
            col = "#00FF78" if is_focused else "#FF3250"
            self.lbl_focus_pct.configure(text=f"{focus_pct}%", fg=col)
            self.lbl_state.configure(text=f"Stare: {status_label}")
            self.lbl_pomo.configure(text=f"Pomodoro: {pomo_str}")
            self.lbl_posture.configure(text=f"Distanță: {distance_cm} cm ({posture_str})")
            self.lbl_level.configure(text=f"🏆 Nivel {level} • {xp} XP")
            self.lbl_xp_txt.configure(text=f"{xp % 100} / 100 XP")
            self.progress_xp["value"] = level_ratio * 100.0
            self.root.update_idletasks()
        except Exception:
            pass
