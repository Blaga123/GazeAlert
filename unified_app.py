"""
GazeAlert Unified Studio App.
Integrates the Real-Time AI Camera Feed and the Interactive Control Center
into a SINGLE, modern, seamless dark-mode Desktop Application window.
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
from face_mesh_renderer import draw_face_mesh_contours
from pro_face_tessellation import draw_pixel_perfect_mesh
from study_manager import StudyManager, ThreadedCamera
from system_tray import SystemTrayManager
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
        self.is_running = True

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

        # Build Single GUI Window
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
        self.root.geometry("1240x740")
        self.root.minsize(1050, 650)
        self.root.configure(bg="#070a0f")

        try:
            icon_p = os.path.join(os.path.dirname(__file__), "app_icon.ico")
            if os.path.exists(icon_p):
                self.root.iconbitmap(icon_p)
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 1. Top Global Navigation & Status Bar
        top_bar = tk.Frame(self.root, bg="#0d131f", height=50, padx=18, pady=8)
        top_bar.pack(fill="x")

        title_frame = tk.Frame(top_bar, bg="#0d131f")
        title_frame.pack(side="left")

        tk.Label(
            title_frame,
            text="⚡ GazeAlert Studio",
            font=("Segoe UI", 15, "bold"),
            fg="#ffffff",
            bg="#0d131f"
        ).pack(side="left")

        tk.Label(
            title_frame,
            text="  |  Medical-Grade Eye & Focus Engine",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg="#0d131f"
        ).pack(side="left")

        self.lbl_fps_badge = tk.Label(
            top_bar,
            text="🟢 30.0 FPS • AMD RX 6600 XT",
            font=("Segoe UI", 9, "bold"),
            fg="#00FF78",
            bg="#11291f",
            padx=12,
            pady=4,
            relief="flat"
        )
        self.lbl_fps_badge.pack(side="right")

        # 2. Main Content Split (Left = Video Stream Canvas, Right = Studio Controls)
        content_frame = tk.Frame(self.root, bg="#070a0f", padx=12, pady=10)
        content_frame.pack(fill="both", expand=True)

        # Left Column: Video Feed Canvas Frame
        video_box = tk.Frame(content_frame, bg="#0d131f", highlightthickness=1, highlightbackground="#1e293b", padx=4, pady=4)
        video_box.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.video_canvas = tk.Label(video_box, bg="#000000")
        self.video_canvas.pack(fill="both", expand=True)

        # Right Column: Studio Control Hub
        sidebar = tk.Frame(content_frame, bg="#070a0f", width=420)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        # Notebook tabs for sidebar
        notebook = ttk.Notebook(sidebar)
        notebook.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#070a0f", borderwidth=0)
        style.configure("TNotebook.Tab", background="#131d31", foreground="#cbd5e1", padding=[14, 8], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

        tab_live = tk.Frame(notebook, bg="#0d131f", padx=14, pady=14)
        tab_settings = tk.Frame(notebook, bg="#0d131f", padx=14, pady=14)

        notebook.add(tab_live, text="📊 Monitor Live")
        notebook.add(tab_settings, text="⚙️ Setări & Praguri")

        self._build_sidebar_live(tab_live)
        self._build_sidebar_settings(tab_settings)

    def _build_sidebar_live(self, parent: tk.Frame):
        # Card: Focus Score & Pomodoro
        card_focus = tk.Frame(parent, bg="#131d31", padx=14, pady=12, highlightthickness=1, highlightbackground="#1e293b")
        card_focus.pack(fill="x", pady=(0, 8))

        tk.Label(card_focus, text="SCOR CONCENTRARE", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w")

        row1 = tk.Frame(card_focus, bg="#131d31")
        row1.pack(fill="x", pady=6)

        self.lbl_focus_pct = tk.Label(row1, text="100%", font=("Segoe UI", 30, "bold"), fg="#00FF78", bg="#131d31")
        self.lbl_focus_pct.pack(side="left")

        info_box = tk.Frame(row1, bg="#131d31", padx=12)
        info_box.pack(side="left", fill="x", expand=True)

        self.lbl_state = tk.Label(info_box, text="Stare: CONCENTRAT", font=("Segoe UI", 10, "bold"), fg="#ffffff", bg="#131d31")
        self.lbl_state.pack(anchor="w")

        self.lbl_pomo = tk.Label(info_box, text="Pomodoro: 25:00 [STUDIU]", font=("Segoe UI", 9), fg="#94a3b8", bg="#131d31")
        self.lbl_pomo.pack(anchor="w")

        self.lbl_posture = tk.Label(info_box, text="Distanță: 52 cm (Optim)", font=("Segoe UI", 9), fg="#38bdf8", bg="#131d31")
        self.lbl_posture.pack(anchor="w")

        # Card: Level & XP Gamification
        card_xp = tk.Frame(parent, bg="#131d31", padx=14, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        card_xp.pack(fill="x", pady=(0, 10))

        row_xp = tk.Frame(card_xp, bg="#131d31")
        row_xp.pack(fill="x")

        self.lbl_level = tk.Label(row_xp, text="🏆 Nivel 1 (Novice)", font=("Segoe UI", 10, "bold"), fg="#fbbf24", bg="#131d31")
        self.lbl_level.pack(side="left")

        self.lbl_xp_txt = tk.Label(row_xp, text="0 / 100 XP", font=("Segoe UI", 9), fg="#94a3b8", bg="#131d31")
        self.lbl_xp_txt.pack(side="right")

        self.progress_xp = ttk.Progressbar(card_xp, orient="horizontal", length=360, mode="determinate")
        self.progress_xp.pack(fill="x", pady=6)

        # 1-Click Action Buttons
        tk.Label(parent, text="ACȚIUNI RAPIDE (1-CLICK)", font=("Segoe UI", 9, "bold"), fg="#64748b", bg="#0d131f").pack(anchor="w", pady=(4, 6))

        btn_grid = tk.Frame(parent, bg="#0d131f")
        btn_grid.pack(fill="x")

        def make_btn(text, cmd, color="#1e293b", hover="#334155", fg="#ffffff"):
            return tk.Button(
                btn_grid,
                text=text,
                command=cmd,
                font=("Segoe UI", 9, "bold"),
                bg=color,
                fg=fg,
                activebackground=hover,
                activeforeground="#ffffff",
                relief="flat",
                padx=10,
                pady=9,
                cursor="hand2"
            )

        b1 = make_btn("🎯 Calibrează Centru (1s)", self._do_calib_center, color="#0284c7")
        b1.grid(row=0, column=0, padx=3, pady=3, sticky="nsew")

        b2 = make_btn("📐 Calibrare 9 Puncte", self._do_calib_9point, color="#4f46e5")
        b2.grid(row=0, column=1, padx=3, pady=3, sticky="nsew")

        b3 = make_btn("⏱️ Start/Pauză Pomodoro", self._do_toggle_pomo, color="#059669")
        b3.grid(row=1, column=0, padx=3, pady=3, sticky="nsew")

        self.btn_monk = make_btn("🛡️ Monk Mode: OFF", self._do_toggle_monk, color="#1e293b")
        self.btn_monk.grid(row=1, column=1, padx=3, pady=3, sticky="nsew")

        self.btn_sound = make_btn("🔔 Sunet: ON", self._do_toggle_sound, color="#1e293b")
        self.btn_sound.grid(row=2, column=0, padx=3, pady=3, sticky="nsew")

        b6 = make_btn("📊 Raport & Heatmap", self._do_open_report, color="#d97706")
        b6.grid(row=2, column=1, padx=3, pady=3, sticky="nsew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

    def _build_sidebar_settings(self, parent: tk.Frame):
        card = tk.Frame(parent, bg="#131d31", padx=14, pady=14, highlightthickness=1, highlightbackground="#1e293b")
        card.pack(fill="both", expand=True)

        tk.Label(card, text="SENSIBILITATE & CONFIGURARE", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#131d31").pack(anchor="w", pady=(0, 10))

        # Slider 1: Unghi Limita Lateral
        tk.Label(card, text="Unghi Limită Lateral Monitor (Yaw °):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#131d31").pack(anchor="w")
        self.scale_yaw = tk.Scale(card, from_=12.0, to=35.0, resolution=1.0, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#070a0f")
        self.scale_yaw.set(float(self.config.get("head_yaw_threshold", 18.0)))
        self.scale_yaw.pack(fill="x", pady=2)

        # Slider 2: Timp Alerta Distragere
        tk.Label(card, text="Timp Alertă Distragere (secunde):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#131d31").pack(anchor="w", pady=(6, 0))
        self.scale_delay = tk.Scale(card, from_=2.0, to=15.0, resolution=0.5, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#070a0f")
        self.scale_delay.set(float(self.config.get("away_threshold_seconds", 5.0)))
        self.scale_delay.pack(fill="x", pady=2)

        # Slider 3: Durata Pomodoro
        tk.Label(card, text="Durată Pomodoro (minute):", font=("Segoe UI", 8), fg="#cbd5e1", bg="#131d31").pack(anchor="w", pady=(6, 0))
        self.scale_pomo = tk.Scale(card, from_=10.0, to=60.0, resolution=5.0, orient="horizontal", bg="#131d31", fg="#ffffff", highlightthickness=0, troughcolor="#070a0f")
        self.scale_pomo.set(float(self.config.get("pomodoro_focus_minutes", 25.0)))
        self.scale_pomo.pack(fill="x", pady=2)

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
            padx=14,
            pady=8,
            cursor="hand2"
        )
        btn_save.pack(fill="x", pady=12)

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

    def _do_calib_9point(self):
        self.calibrator.start_calibration()

    def _do_toggle_pomo(self):
        self.study_mgr.toggle_pomodoro()

    def _do_toggle_monk(self):
        self.monk_mode_enabled = not self.monk_mode_enabled
        self.btn_monk.configure(
            text=f"🛡️ Monk Mode: {'ON' if self.monk_mode_enabled else 'OFF'}",
            bg="#b91c1c" if self.monk_mode_enabled else "#1e293b"
        )

    def _do_toggle_sound(self):
        active = self.alert_mgr.toggle_sound()
        self.btn_sound.configure(
            text=f"🔔 Sunet: {'ON' if active else 'OFF'}",
            bg="#059669" if active else "#1e293b"
        )

    def _do_open_report(self):
        p = self.study_mgr.generate_html_report("study_report.html")
        if p:
            webbrowser.open(p)

    def _do_save_settings(self):
        self.config["head_yaw_threshold"] = float(self.scale_yaw.get())
        self.config["away_threshold_seconds"] = float(self.scale_delay.get())
        self.config["pomodoro_focus_minutes"] = float(self.scale_pomo.get())
        self.detector.head_yaw_thresh = float(self.scale_yaw.get())
        self.alert_mgr.away_delay_sec = float(self.scale_delay.get())
        self.study_mgr.focus_duration_sec = float(self.scale_pomo.get()) * 60.0
        self._save_config()
        messagebox.showinfo("GazeAlert Studio", "Setările au fost salvate cu succes!")

    def start_loop(self):
        """Main update loop."""
        self._update_frame()
        self.root.mainloop()

    def _update_frame(self):
        if not self.is_running:
            return

        frame = self.camera.read()
        if frame is not None and frame.size > 0:
            # FPS Tracking
            self._fps_counter += 1
            now = time.time()
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
            if gaze.face_detected and self.show_mesh:
                if len(gaze.landmarks_2d) > 400:
                    draw_pixel_perfect_mesh(frame, gaze.landmarks_2d, gaze.iris_points_left, gaze.iris_points_right)
                else:
                    draw_face_mesh_contours(frame, gaze.landmarks_2d, gaze.iris_points_left, gaze.iris_points_right)

            # Top HUD Status Banner
            badge_color = (0, 255, 120) if gaze.is_looking_at_screen else (0, 60, 255)
            badge_text = f"FOCUS ({int(gaze.focus_confidence * 100)}%)" if gaze.is_looking_at_screen else f"PRIVIRE IN ALTA PARTE ({self.away_elapsed:.1f}s)"
            cv2.rectangle(frame, (10, 10), (w - 10, 48), (15, 20, 28), -1)
            cv2.rectangle(frame, (10, 10), (w - 10, 48), badge_color, 1)
            cv2.putText(frame, badge_text, (20, 36), cv2.FONT_HERSHEY_DUPLEX, 0.65, badge_color, 2, cv2.LINE_AA)

            # Monk Mode Distraction Shield
            if self.monk_mode_enabled and self.away_elapsed > 2.0:
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 50), -1)
                cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)
                cv2.rectangle(frame, (8, 8), (w - 8, h - 8), (0, 0, 255), 4)
                cv2.putText(frame, "MONK MODE: ATENTIE LA ECRAN!", (int(w * 0.18), int(h * 0.52)), cv2.FONT_HERSHEY_DUPLEX, 0.70, (0, 140, 255), 2, cv2.LINE_AA)

            # Render to Tkinter Video Canvas
            canvas_w = self.video_canvas.winfo_width()
            canvas_h = self.video_canvas.winfo_height()
            if canvas_w > 50 and canvas_h > 50:
                resized = cv2.resize(frame, (canvas_w, canvas_h), interpolation=cv2.INTER_LINEAR)
            else:
                resized = cv2.resize(frame, (760, 480), interpolation=cv2.INTER_LINEAR)

            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_canvas.imgtk = imgtk
            self.video_canvas.configure(image=imgtk)

            # Update Right Sidebar Telemetry
            eff = self.study_mgr.get_efficiency_score()
            lvl, cur_xp, needed_xp, ratio = self.study_mgr.get_level_info()
            col = "#00FF78" if gaze.is_looking_at_screen else "#FF3250"
            self.lbl_focus_pct.configure(text=f"{eff}%", fg=col)
            self.lbl_state.configure(text=f"Stare: {gaze.expression_label if gaze.face_detected else 'ABSENT'}")
            self.lbl_pomo.configure(text=f"Pomodoro: {self.study_mgr.get_pomodoro_string()}")
            self.lbl_posture.configure(text=f"Distanță: {int(gaze.distance_cm)} cm ({gaze.posture_status})")
            self.lbl_level.configure(text=f"🏆 Nivel {lvl} • {self.study_mgr.total_xp} XP")
            self.lbl_xp_txt.configure(text=f"{cur_xp} / {needed_xp} XP")
            self.progress_xp["value"] = ratio * 100.0

        # Schedule next frame (30 FPS -> ~25ms)
        self.root.after(25, self._update_frame)

    def on_close(self):
        self.is_running = False
        self.study_mgr.save_session(self.session_logger)
        self.study_mgr.generate_html_report("study_report.html")
        self.detector.close()
        self.camera.release()
        self.root.destroy()
        print("\n[+] Sesiune salvata. Aplicatia GazeAlert a fost inchisa.")


def main():
    app = UnifiedGazeApp()
    app.start_loop()


if __name__ == "__main__":
    main()
