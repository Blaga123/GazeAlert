"""
GazeAlert Unified Studio App • Peak Performance & Flicker-Free Edition.
Integrates Real-Time AI Camera Feed, Interactive Controls, Global Keyboard Shortcuts,
and Comprehensive Medical-Grade Eye, Pupil & Biometric Telemetry in a Single Seamless Window.
Zero flickering with hardware double-buffered centered video blitting.
"""

import json
import math
import os
import sys
import threading
import time
import webbrowser
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk

from gaze_detector import GazeDetector, GazeResult
from alert_manager import AlertManager
from screen_calibrator import ScreenCalibrator
from pro_face_tessellation import draw_pixel_perfect_mesh
from study_manager import StudyManager, ThreadedCamera
from session_logger import SessionLogger
from theme_manager import ThemeManager


class UnifiedGazeApp:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()

        # Core AI & Logic Engines
        self.detector = GazeDetector(
            head_yaw_thresh=float(self.config.get("head_yaw_threshold", 18.0)),
            head_pitch_thresh=float(self.config.get("head_pitch_threshold", 16.0)),
            ear_thresh=float(self.config.get("eye_open_ratio_threshold", 0.12)),
            enable_clahe=bool(self.config.get("enable_clahe_contrast", False)),
            auto_calibration_enabled=bool(self.config.get("auto_calibration_enabled", True)),
        )

        self.alert_mgr = AlertManager(
            enable_sound=bool(self.config.get("enable_sound_alert", True)),
            enable_popup=bool(self.config.get("enable_desktop_popup", True)),
            frequency=int(self.config.get("sound_frequency", 1200)),
            duration_ms=int(self.config.get("sound_duration_ms", 300)),
            repeat_interval_sec=float(self.config.get("sound_alert_interval_seconds", 3.0)),
            away_delay_sec=float(self.config.get("away_threshold_seconds", 5.0)),
            warn_delay_sec=float(self.config.get("warning_threshold_seconds", 2.5)),
        )

        self.study_mgr = StudyManager(
            pomodoro_focus_min=float(self.config.get("pomodoro_focus_minutes", 25.0)),
            pomodoro_break_min=float(self.config.get("pomodoro_break_minutes", 5.0)),
            eye_rest_interval_min=float(self.config.get("eye_rest_interval_minutes", 20.0)),
        )

        self.calibrator = ScreenCalibrator()
        self.session_logger = SessionLogger()
        self.theme_mgr = ThemeManager(self.config.get("theme", "cyber_dark"))

        # State Variables
        self.monk_mode_enabled = bool(self.config.get("monk_mode_enabled", False))
        self.show_mesh = bool(self.config.get("show_face_mesh", True))
        self.away_start_time: Optional[float] = None
        self.away_elapsed = 0.0
        self.fps = 30.0
        self._fps_counter = 0
        self._fps_time = time.time()
        self._last_ui_update = 0.0
        self.is_running = True

        # Cached canvas dimensions for zero-lag rendering
        self._target_w = 760
        self._target_h = 428

        # Camera
        webcam_id = int(self.config.get("webcam_id", 0))
        target_w = int(self.config.get("frame_width", 1280))
        target_h = int(self.config.get("frame_height", 720))
        use_mjpg = bool(self.config.get("use_mjpg_codec", True))

        self.camera = ThreadedCamera(
            src=webcam_id,
            width=target_w,
            height=target_h,
            fps=int(self.config.get("fps_target", 30)),
            use_mjpg=use_mjpg
        )

        # Build Single GUI Window & Bind Hotkeys
        self._init_window()

    def _load_config(self) -> Dict[str, Any]:
        defaults = {
            "webcam_id": 0,
            "frame_width": 1280,
            "frame_height": 720,
            "fps_target": 30,
            "use_mjpg_codec": True,
            "away_threshold_seconds": 5.0,
            "warning_threshold_seconds": 2.5,
            "head_yaw_threshold": 18.0,
            "head_pitch_threshold": 16.0,
            "pomodoro_focus_minutes": 25.0,
            "pomodoro_break_minutes": 5.0,
            "enable_sound_alert": True,
            "enable_desktop_popup": True,
            "theme": "cyber_dark",
            "monk_mode_enabled": False,
            "show_face_mesh": True,
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except Exception:
                pass
        return defaults

    def _save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _init_window(self):
        self.root = tk.Tk()
        self.root.title("GazeAlert Studio • AI Eye Tracking & Productivity Suite")
        self.root.geometry("1280x750")
        self.root.minsize(1080, 640)
        self.root.configure(bg="#070a0f")

        try:
            icon_p = os.path.join(os.path.dirname(__file__), "app_icon.ico")
            if os.path.exists(icon_p):
                self.root.iconbitmap(icon_p)
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Key>", self._on_key_press)

        # 1. Top Global Status Bar
        top_bar = tk.Frame(self.root, bg="#0d131f", height=46, padx=16, pady=6)
        top_bar.pack(fill="x", side="top")

        title_frame = tk.Frame(top_bar, bg="#0d131f")
        title_frame.pack(side="left")

        tk.Label(
            title_frame,
            text="⚡ GazeAlert Studio",
            font=("Segoe UI", 14, "bold"),
            fg="#ffffff",
            bg="#0d131f"
        ).pack(side="left")

        tk.Label(
            title_frame,
            text="  |  Medical-Grade Eye Tracking & Cognitive Suite",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg="#0d131f"
        ).pack(side="left")

        # Notification Toast Pill (in top bar)
        self.lbl_toast = tk.Label(
            top_bar,
            text="[Comenzi Rapide: C=Calibrare | P=Pomodoro | M=Monk | S=Sunet | F=Plasă]",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#0d131f",
            padx=10
        )
        self.lbl_toast.pack(side="left", padx=15)

        self.lbl_fps_badge = tk.Label(
            top_bar,
            text="🟢 30.0 FPS • Motor Activ",
            font=("Segoe UI", 9, "bold"),
            fg="#00FF78",
            bg="#11291f",
            padx=12,
            pady=3,
            relief="flat"
        )
        self.lbl_fps_badge.pack(side="right")

        # 2. Main Content Split: Rock-Solid 2-Column Grid
        content_frame = tk.Frame(self.root, bg="#070a0f", padx=12, pady=10)
        content_frame.pack(fill="both", expand=True)

        content_frame.grid_columnconfigure(0, weight=1)              # Left Video Feed
        content_frame.grid_columnconfigure(1, weight=0, minsize=430) # Right Sidebar fixed width
        content_frame.grid_rowconfigure(0, weight=1)

        # Left Column: Video Feed Container
        self.video_box = tk.Frame(content_frame, bg="#000000", highlightthickness=1, highlightbackground="#1e293b")
        self.video_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.video_box.pack_propagate(False)
        self.video_box.grid_propagate(False)
        self.video_box.bind("<Configure>", self._on_canvas_resize)

        # Flicker-free centered video label
        self.video_label = tk.Label(self.video_box, bg="#000000", borderwidth=0, highlightthickness=0)
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        # Right Column: Studio Control Hub
        sidebar = tk.Frame(content_frame, bg="#0d131f", width=430, highlightthickness=1, highlightbackground="#1e293b")
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.pack_propagate(False)

        # Notebook tabs for sidebar
        notebook = ttk.Notebook(sidebar)
        notebook.pack(fill="both", expand=True, padx=4, pady=4)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#0d131f", borderwidth=0)
        style.configure("TNotebook.Tab", background="#131d31", foreground="#cbd5e1", padding=[12, 7], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

        tab_live = tk.Frame(notebook, bg="#0d131f", padx=10, pady=10)
        tab_telemetry = tk.Frame(notebook, bg="#0d131f", padx=10, pady=10)
        tab_settings = tk.Frame(notebook, bg="#0d131f", padx=10, pady=10)

        notebook.add(tab_live, text="📊 Tablou Principal")
        notebook.add(tab_telemetry, text="🔬 Telemetrie Detaliată")
        notebook.add(tab_settings, text="⚙️ Setări & Praguri")

        self._build_sidebar_live(tab_live)
        self._build_sidebar_telemetry(tab_telemetry)
        self._build_sidebar_settings(tab_settings)

    def _on_canvas_resize(self, event):
        """Pre-calculates aspect ratio fitting only when window dimensions change."""
        box_w = max(100, event.width)
        box_h = max(100, event.height)
        aspect = 16.0 / 9.0

        if box_w / box_h > aspect:
            self._target_h = box_h
            self._target_w = int(box_h * aspect)
        else:
            self._target_w = box_w
            self._target_h = int(box_w / aspect)

    def _show_toast(self, message: str, duration_sec: float = 3.0):
        """Displays temporary user-friendly status banner in the top bar."""
        self.lbl_toast.configure(text=message, fg="#00FF78")
        self.root.after(int(duration_sec * 1000), lambda: self.lbl_toast.configure(
            text="[Comenzi Rapide: C=Calibrare | P=Pomodoro | M=Monk | S=Sunet | F=Plasă]",
            fg="#38bdf8"
        ))

    def _on_key_press(self, event):
        """Handles instant global keyboard shortcuts."""
        k = event.char.lower() if event.char else ""
        if k == "c":
            self._do_calib_center()
        elif k == "k":
            self._do_calib_9point()
        elif k == "p" or event.keysym == "space":
            self._do_toggle_pomo()
        elif k == "m":
            self._do_toggle_monk()
        elif k == "s":
            self._do_toggle_sound()
        elif k == "f":
            self._do_toggle_mesh()
        elif k in ["r", "e"]:
            self._do_open_report()
        elif event.keysym in ["Escape", "q", "Q"]:
            self.on_close()

    def _build_sidebar_live(self, parent: tk.Frame):
        # Card 1: Focus Score, Flow & Pomodoro
        card_focus = tk.Frame(parent, bg="#131d31", padx=12, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        card_focus.pack(fill="x", pady=(0, 6))

        tk.Label(card_focus, text="STARE DE CONCENTRARE & POMODORO", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w")

        row1 = tk.Frame(card_focus, bg="#131d31")
        row1.pack(fill="x", pady=4)

        self.lbl_focus_pct = tk.Label(row1, text="100%", font=("Segoe UI", 28, "bold"), fg="#00FF78", bg="#131d31")
        self.lbl_focus_pct.pack(side="left")

        info_box = tk.Frame(row1, bg="#131d31", padx=10)
        info_box.pack(side="left", fill="x", expand=True)

        self.lbl_state = tk.Label(info_box, text="Stare: CONCENTRAT", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#131d31")
        self.lbl_state.pack(anchor="w")

        self.lbl_pomo = tk.Label(info_box, text="Pomodoro: 25:00 [STUDIU]", font=("Segoe UI", 8), fg="#94a3b8", bg="#131d31")
        self.lbl_pomo.pack(anchor="w")

        self.lbl_flow_zone = tk.Label(info_box, text="Flow: 🟢 DEEP FLOW (Optimal)", font=("Segoe UI", 8, "bold"), fg="#00FF78", bg="#131d31")
        self.lbl_flow_zone.pack(anchor="w")

        # Card 2: Ergonomics & Quick Eye Overview
        card_ergo = tk.Frame(parent, bg="#131d31", padx=12, pady=8, highlightthickness=1, highlightbackground="#1e293b")
        card_ergo.pack(fill="x", pady=(0, 6))

        row_ergo = tk.Frame(card_ergo, bg="#131d31")
        row_ergo.pack(fill="x")

        self.lbl_posture = tk.Label(row_ergo, text="📏 Distanță: 52 cm (Optim)", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#131d31")
        self.lbl_posture.pack(side="left")

        self.lbl_ear_quick = tk.Label(row_ergo, text="👁️ Ochi: DESCHIȘI", font=("Segoe UI", 8), fg="#00FF78", bg="#131d31")
        self.lbl_ear_quick.pack(side="right")

        # Card 3: Level & XP Gamification
        card_xp = tk.Frame(parent, bg="#131d31", padx=12, pady=8, highlightthickness=1, highlightbackground="#1e293b")
        card_xp.pack(fill="x", pady=(0, 6))

        row_xp = tk.Frame(card_xp, bg="#131d31")
        row_xp.pack(fill="x")

        self.lbl_level = tk.Label(row_xp, text="🏆 Nivel 1 (Novice)", font=("Segoe UI", 9, "bold"), fg="#fbbf24", bg="#131d31")
        self.lbl_level.pack(side="left")

        self.lbl_xp_txt = tk.Label(row_xp, text="0 / 100 XP", font=("Segoe UI", 8), fg="#94a3b8", bg="#131d31")
        self.lbl_xp_txt.pack(side="right")

        self.progress_xp = ttk.Progressbar(card_xp, orient="horizontal", length=360, mode="determinate")
        self.progress_xp.pack(fill="x", pady=4)

        # 1-Click Action Buttons
        tk.Label(parent, text="ACȚIUNI RAPIDE (1-CLICK & TASTE RAPIDE)", font=("Segoe UI", 8, "bold"), fg="#64748b", bg="#0d131f").pack(anchor="w", pady=(2, 4))

        btn_grid = tk.Frame(parent, bg="#0d131f")
        btn_grid.pack(fill="x")

        def make_btn(text, cmd, color="#1e293b", hover="#334155", fg="#ffffff"):
            return tk.Button(
                btn_grid,
                text=text,
                command=cmd,
                font=("Segoe UI", 8, "bold"),
                bg=color,
                fg=fg,
                activebackground=hover,
                activeforeground="#ffffff",
                relief="flat",
                padx=6,
                pady=7,
                cursor="hand2"
            )

        b1 = make_btn("🎯 Calibrează Centru [C]", self._do_calib_center, color="#0284c7")
        b1.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        b2 = make_btn("📐 Calibrare 9 Pct [K]", self._do_calib_9point, color="#4f46e5")
        b2.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

        b3 = make_btn("⏱️ Start Pomodoro [P]", self._do_toggle_pomo, color="#059669")
        b3.grid(row=1, column=0, padx=2, pady=2, sticky="nsew")

        self.btn_monk = make_btn("🛡️ Monk Mode [M]: OFF", self._do_toggle_monk, color="#1e293b")
        self.btn_monk.grid(row=1, column=1, padx=2, pady=2, sticky="nsew")

        self.btn_sound = make_btn("🔔 Sunet [S]: ON", self._do_toggle_sound, color="#1e293b")
        self.btn_sound.grid(row=2, column=0, padx=2, pady=2, sticky="nsew")

        self.btn_mesh = make_btn("🎭 Plasă [F]: ON", self._do_toggle_mesh, color="#1e293b")
        self.btn_mesh.grid(row=2, column=1, padx=2, pady=2, sticky="nsew")

        b7 = make_btn("📊 Raport & Heatmap [R]", self._do_open_report, color="#d97706")
        b7.grid(row=3, column=0, columnspan=2, padx=2, pady=2, sticky="nsew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

    def _build_sidebar_telemetry(self, parent: tk.Frame):
        """Builds structured eye, pupil, and head pose telemetry cards with clear explanations."""
        # Telemetry Card 1: Eye & Pupil Metrics
        card_eyes = tk.Frame(parent, bg="#131d31", padx=12, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        card_eyes.pack(fill="x", pady=(0, 8))

        tk.Label(card_eyes, text="BIOMETRIE OCHI & PUPILLOMETRIE", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w", pady=(0, 6))

        def add_row(parent_card, label_text):
            r = tk.Frame(parent_card, bg="#131d31")
            r.pack(fill="x", pady=2)
            lbl = tk.Label(r, text=label_text, font=("Segoe UI", 8), fg="#94a3b8", bg="#131d31")
            lbl.pack(side="left")
            val_lbl = tk.Label(r, text="--", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#131d31")
            val_lbl.pack(side="right")
            return val_lbl

        self.val_ear = add_row(card_eyes, "Deschidere Ochi (EAR):")
        self.val_perclos = add_row(card_eyes, "Scor PERCLOS (Oboseală):")
        self.val_pupil = add_row(card_eyes, "Diametru Pupilă (Daugman):")
        self.val_cog = add_row(card_eyes, "Efort Cognitiv (Pupilometrie):")
        self.val_reading = add_row(card_eyes, "Ritm Citire / Saccade:")
        self.val_lux = add_row(card_eyes, "Lumină Ambient (PLR Lux):")

        # Telemetry Card 2: Head Pose & Ergonomics
        card_head = tk.Frame(parent, bg="#131d31", padx=12, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        card_head.pack(fill="x")

        tk.Label(card_head, text="POSTURĂ & UNGHIURI PRIVIRE", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w", pady=(0, 6))

        self.val_yaw_pitch = add_row(card_head, "Unghi Cap (Yaw / Pitch):")
        self.val_vor = add_row(card_head, "Privire Totală Foveală (VOR):")
        self.val_dist = add_row(card_head, "Distanță Optică Ecran:")
        self.val_posture = add_row(card_head, "Stare Postură Birou:")
        self.val_expr = add_row(card_head, "Expresie Facială:")

    def _build_sidebar_settings(self, parent: tk.Frame):
        card = tk.Frame(parent, bg="#131d31", padx=12, pady=12, highlightthickness=1, highlightbackground="#1e293b")
        card.pack(fill="both", expand=True)

        tk.Label(card, text="SENSIBILITATE & CONFIGURARE", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w", pady=(0, 8))

        # Slider 1: Unghi Limita Lateral
        tk.Label(card, text="Unghi Limită Monitor (Yaw °):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#131d31").pack(anchor="w")
        self.scale_yaw = tk.Scale(card, from_=12.0, to=35.0, resolution=1.0, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#070a0f")
        self.scale_yaw.set(float(self.config.get("head_yaw_threshold", 18.0)))
        self.scale_yaw.pack(fill="x", pady=1)

        # Slider 2: Timp Alerta Distragere
        tk.Label(card, text="Timp Alertă Distragere (secunde):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#131d31").pack(anchor="w", pady=(4, 0))
        self.scale_delay = tk.Scale(card, from_=2.0, to=15.0, resolution=0.5, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#070a0f")
        self.scale_delay.set(float(self.config.get("away_threshold_seconds", 5.0)))
        self.scale_delay.pack(fill="x", pady=1)

        # Slider 3: Durata Pomodoro
        tk.Label(card, text="Durată Pomodoro (minute):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#131d31").pack(anchor="w", pady=(4, 0))
        self.scale_pomo = tk.Scale(card, from_=10.0, to=60.0, resolution=5.0, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#070a0f")
        self.scale_pomo.set(float(self.config.get("pomodoro_focus_minutes", 25.0)))
        self.scale_pomo.pack(fill="x", pady=1)

        # Action Button: Test Alert Sound
        btn_test_snd = tk.Button(
            card,
            text="🔊 Testează Sunet Alerte",
            command=self.alert_mgr.trigger_test_alert,
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#cbd5e1",
            activebackground="#334155",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2"
        )
        btn_test_snd.pack(fill="x", pady=(8, 4))

        # Save Button
        btn_save = tk.Button(
            card,
            text="💾 Salvează Preferințele",
            command=self._do_save_settings,
            font=("Segoe UI", 9, "bold"),
            bg="#00FF78",
            fg="#070a0f",
            activebackground="#00dcff",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2"
        )
        btn_save.pack(fill="x", pady=8)

    def _do_calib_center(self):
        if hasattr(self, 'current_gaze') and self.current_gaze.face_detected:
            g = self.current_gaze
            self.detector.calibrate_baseline(
                self.detector.calibrated_yaw + g.head_yaw,
                self.detector.calibrated_pitch + g.head_pitch,
                g.ipd_pixels
            )
            self.away_start_time = None
            self.away_elapsed = 0.0
            self._show_toast(f"✓ Centru calibrat la baseline (Yaw: {self.detector.calibrated_yaw:+.1f}°, Pitch: {self.detector.calibrated_pitch:+.1f}°)")

    def _do_calib_9point(self):
        self.calibrator.start_calibration()
        self._show_toast("📐 Calibrare 9 puncte inițiată (privește spre țintele de pe ecran)")

    def _do_toggle_pomo(self):
        active = self.study_mgr.toggle_pomodoro()
        self._show_toast(f"⏱️ Pomodoro: {'PORNIT' if active else 'PAUZĂ'}")

    def _do_toggle_monk(self):
        self.monk_mode_enabled = not self.monk_mode_enabled
        self.btn_monk.configure(
            text=f"🛡️ Monk Mode [M]: {'ON' if self.monk_mode_enabled else 'OFF'}",
            bg="#b91c1c" if self.monk_mode_enabled else "#1e293b"
        )
        self._show_toast(f"🛡️ Monk Mode: {'ACTIVAT (Scut Distrageri)' if self.monk_mode_enabled else 'DEZACTIVAT'}")

    def _do_toggle_sound(self):
        active = self.alert_mgr.toggle_sound()
        self.btn_sound.configure(
            text=f"🔔 Sunet [S]: {'ON' if active else 'OFF'}",
            bg="#059669" if active else "#1e293b"
        )
        self._show_toast(f"🔔 Sunet alerte: {'ACTIVAT' if active else 'OPRIT'}")

    def _do_toggle_mesh(self):
        self.show_mesh = not self.show_mesh
        self.btn_mesh.configure(
            text=f"🎭 Plasă [F]: {'ON' if self.show_mesh else 'OFF'}",
            bg="#059669" if self.show_mesh else "#1e293b"
        )
        self._show_toast(f"🎭 Plasă & Raze: {'VIZIBILE' if self.show_mesh else 'ASCUNSE'}")

    def _do_open_report(self):
        p = self.study_mgr.generate_html_report("study_report.html")
        if p:
            webbrowser.open(p)
            self._show_toast("📊 Raport & Heatmap deschise în browser!")

    def _do_save_settings(self):
        self.config["head_yaw_threshold"] = float(self.scale_yaw.get())
        self.config["away_threshold_seconds"] = float(self.scale_delay.get())
        self.config["pomodoro_focus_minutes"] = float(self.scale_pomo.get())
        self.detector.head_yaw_thresh = float(self.scale_yaw.get())
        self.alert_mgr.away_delay_sec = float(self.scale_delay.get())
        self.study_mgr.focus_duration_sec = float(self.scale_pomo.get()) * 60.0
        self._save_config()
        self._show_toast("💾 Preferințele au fost salvate cu succes!")

    def start_loop(self):
        """Main update loop."""
        self._update_frame()
        self.root.mainloop()

    def _update_frame(self):
        if not self.is_running:
            return

        ret, frame = self.camera.read()
        if ret and frame is not None and frame.size > 0:
            now = time.time()
            self._fps_counter += 1
            if now - self._fps_time >= 1.0:
                self.fps = self._fps_counter / (now - self._fps_time)
                self._fps_counter = 0
                self._fps_time = now
                self.lbl_fps_badge.configure(text=f"🟢 {self.fps:.1f} FPS • Motor Activ")

            # Run Gaze AI Pipeline
            gaze: GazeResult = self.detector.process_frame(frame)
            self.current_gaze = gaze

            # Update Study Performance
            self.study_mgr.update(gaze.is_looking_at_screen, gaze.smart_state, gaze.is_yawning)

            # 9-Point Calibrator Routine (if active)
            if self.calibrator.is_calibrating:
                if gaze.face_detected and len(gaze.raw_features) >= 8:
                    self.calibrator.add_sample(gaze.raw_features)
                self.calibrator.draw_calibration_overlay(frame)

            # Screen Gaze Prediction & Heatmap
            screen_gaze_pos = None
            if self.calibrator.is_calibrated and gaze.face_detected and len(gaze.raw_features) >= 8:
                screen_gaze_pos = self.calibrator.predict_screen_pos(gaze.raw_features)

            if screen_gaze_pos is not None:
                self.study_mgr.add_gaze_point(screen_gaze_pos[0], screen_gaze_pos[1])
            elif gaze.face_detected and gaze.is_looking_at_screen:
                norm_x = 0.5 + (gaze.total_gaze_yaw / 36.0)
                norm_y = 0.5 - (gaze.total_gaze_pitch / 28.0)
                self.study_mgr.add_gaze_point(norm_x, norm_y)

            # Distraction Away Timing
            if not gaze.face_detected or not gaze.is_looking_at_screen:
                if self.away_start_time is None:
                    self.away_start_time = now
                self.away_elapsed = now - self.away_start_time
            else:
                self.away_start_time = None
                self.away_elapsed = 0.0

            # Alerts & Ergonomics Coach
            reason = ", ".join(gaze.reasons) if gaze.reasons else "Utilizator absent"
            self.alert_mgr.check_and_alert(self.away_elapsed, gaze.smart_state, reason)
            if gaze.face_detected:
                self.alert_mgr.check_posture_and_alert(gaze.is_slouching, gaze.distance_cm)

            # Adaptive Flow Pomodoro Auto-Extension
            self.study_mgr.check_flow_extension(gaze.flow_state_zone)

            # Draw AI Overlays on Camera Frame
            h, w = frame.shape[:2]
            scale = min(w / 640.0, h / 480.0)
            if gaze.face_detected and self.show_mesh and gaze.landmarks_2d is not None:
                draw_pixel_perfect_mesh(
                    frame=frame,
                    landmarks_2d=gaze.landmarks_2d,
                    scale=scale,
                    pupil_left=gaze.left_iris_center,
                    pupil_right=gaze.right_iris_center,
                    gaze_ray_l_end=gaze.left_gaze_ray_end,
                    gaze_ray_r_end=gaze.right_gaze_ray_end,
                    pupil_radius_l=gaze.left_pupil_radius,
                    pupil_radius_r=gaze.right_pupil_radius,
                    is_focused=gaze.is_looking_at_screen
                )

            # Top HUD Status Banner on Video
            badge_color = (0, 255, 120) if gaze.is_looking_at_screen else (0, 60, 255)
            badge_text = f"FOCUS ({int(gaze.focus_confidence * 100)}%)" if gaze.is_looking_at_screen else f"PRIVIRE IN ALTA PARTE ({self.away_elapsed:.1f}s)"
            cv2.rectangle(frame, (10, 10), (w - 10, 46), (15, 20, 28), -1)
            cv2.rectangle(frame, (10, 10), (w - 10, 46), badge_color, 1)
            cv2.putText(frame, badge_text, (20, 34), cv2.FONT_HERSHEY_DUPLEX, 0.65, badge_color, 2, cv2.LINE_AA)

            # Bottom Left Camera Diagnostic Overlay (Sleek dark HUD pill)
            diag_text = f"Yaw: {gaze.head_yaw:+.1f}  Pitch: {gaze.head_pitch:+.1f} | Dist: {int(gaze.distance_cm)}cm | {gaze.flow_state_zone[:18]}"
            (tw, th_text), _ = cv2.getTextSize(diag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.40 * scale, 1)
            cv2.rectangle(frame, (12, h - th_text - 18), (12 + tw + 16, h - 8), (15, 20, 28), -1)
            cv2.rectangle(frame, (12, h - th_text - 18), (12 + tw + 16, h - 8), (30, 41, 59), 1)
            cv2.putText(frame, diag_text, (20, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.40 * scale, (0, 255, 180), 1, cv2.LINE_AA)

            # Monk Mode Distraction Shield
            if self.monk_mode_enabled and self.away_elapsed > 2.0:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 50), -1)
                cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)
                cv2.rectangle(frame, (8, 8), (w - 8, h - 8), (0, 0, 255), 4)
                cv2.putText(frame, "MONK MODE: ATENTIE LA ECRAN!", (int(w * 0.18), int(h * 0.52)), cv2.FONT_HERSHEY_DUPLEX, 0.70, (0, 140, 255), 2, cv2.LINE_AA)

            # Fast Flicker-Free Image Swap with Double Buffering
            resized = cv2.resize(frame, (self._target_w, self._target_h), interpolation=cv2.INTER_LINEAR)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            # Throttle UI text telemetry updates to 10 FPS to save CPU for maximum fluid video
            if now - self._last_ui_update >= 0.10:
                self._last_ui_update = now
                eff = self.study_mgr.get_efficiency_score()
                lvl, cur_xp, needed_xp, ratio = self.study_mgr.get_level_info()
                col = "#00FF78" if gaze.is_looking_at_screen else "#FF3250"
                self.lbl_focus_pct.configure(text=f"{eff}%", fg=col)
                self.lbl_state.configure(text=f"Stare: {gaze.expression_label if gaze.face_detected else 'ABSENT'}")
                self.lbl_pomo.configure(text=f"Pomodoro: {self.study_mgr.get_pomodoro_string()}")
                self.lbl_flow_zone.configure(text=f"Flow: {gaze.flow_state_zone[:24]}")
                self.lbl_level.configure(text=f"🏆 Nivel {lvl} • {self.study_mgr.total_xp} XP")
                self.lbl_xp_txt.configure(text=f"{cur_xp} / {needed_xp} XP")
                self.progress_xp["value"] = ratio * 100.0

                dist_col = "#00FF78" if 45 <= gaze.distance_cm <= 80 else "#FFC800"
                self.lbl_posture.configure(text=f"📏 Distanță: {int(gaze.distance_cm)} cm ({gaze.posture_status})", fg=dist_col)

                if gaze.face_detected:
                    ear_val = (gaze.left_ear + gaze.right_ear) / 2.0
                    ear_status = "DESCHIȘI" if ear_val >= self.detector.ear_thresh else "ÎNCHIȘI"
                    self.lbl_ear_quick.configure(text=f"👁️ Ochi: {ear_status}", fg="#00FF78" if ear_status == "DESCHIȘI" else "#FFC800")
                    self.val_ear.configure(text=f"{gaze.left_ear:.2f} L / {gaze.right_ear:.2f} R [{ear_status}]", fg="#00FF78" if ear_status == "DESCHIȘI" else "#FFC800")
                    self.val_perclos.configure(text=f"{int(gaze.perclos_score * 100)}% (PERCLOS Oboseală)", fg="#00FF78" if gaze.perclos_score < 0.15 else "#FF3250")
                    self.val_pupil.configure(text=f"{int(gaze.pupil_diameter_ratio * 100)}% ({gaze.pupil_state_label})", fg="#38bdf8")
                    self.val_cog.configure(text=f"{gaze.cognitive_load_pct}% (Efort Mental)", fg="#fbbf24")
                    self.val_reading.configure(text=f"{gaze.reading_state_label}", fg="#a78bfa")
                    self.val_lux.configure(text=f"{int(gaze.ambient_lux)} Lux (PLR Compensat)", fg="#e2e8f0")

                    self.val_yaw_pitch.configure(text=f"Yaw: {gaze.head_yaw:+.1f}° | Pitch: {gaze.head_pitch:+.1f}°")
                    self.val_vor.configure(text=f"Yaw: {gaze.total_gaze_yaw:+.1f}° | Pitch: {gaze.total_gaze_pitch:+.1f}°")
                    self.val_dist.configure(text=f"{int(gaze.distance_cm)} cm", fg=dist_col)
                    self.val_posture.configure(text=f"{gaze.posture_status}", fg=dist_col)
                    self.val_expr.configure(text=f"{gaze.expression_label} {gaze.expression_emoji}")

        # Schedule next frame (30 FPS -> ~25ms)
        self.root.after(25, self._update_frame)

    def on_close(self):
        self.is_running = False
        self.study_mgr.save_session(self.session_logger)
        self.study_mgr.generate_html_report("study_report.html")
        self.detector.close()
        self.camera.release()
        self.root.destroy()
        print("\n[+] Sesiune salvata. Aplicatia GazeAlert a fost inchisa cu succes.")


def main():
    app = UnifiedGazeApp()
    app.start_loop()


if __name__ == "__main__":
    main()
