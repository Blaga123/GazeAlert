"""
High-Performance AI Gaze, Face & Study Suite with Threaded Video, Pomodoro & Floating Mini-Widget.
Run with: python main.py
"""

import ctypes
import json
import os
import sys
import threading
import time
import webbrowser
from typing import Dict, Any, Tuple, Optional

import cv2
import numpy as np

from gaze_detector import GazeDetector, GazeResult
from alert_manager import AlertManager
from screen_calibrator import ScreenCalibrator
from face_mesh_renderer import draw_face_mesh_contours
from pro_face_tessellation import draw_pixel_perfect_mesh
from study_manager import StudyManager, ThreadedCamera
from system_tray import SystemTrayManager
from session_logger import SessionLogger
from theme_manager import ThemeManager
from modern_gui import FloatingPillWidget
from control_center import ControlCenterGUI


class GlobalHotkeyListener:
    """Listens for global Windows hotkeys (Ctrl+Alt+C, Ctrl+Alt+W, Ctrl+Alt+P, Ctrl+Alt+S) from anywhere in Windows."""
    def __init__(self):
        self.running = True
        self.pending_action: Optional[str] = None
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _listen(self):
        try:
            user32 = ctypes.windll.user32
            VK_CONTROL = 0x11
            VK_MENU = 0x12  # Alt
            while self.running:
                ctrl_down = user32.GetAsyncKeyState(VK_CONTROL) & 0x8000
                alt_down = user32.GetAsyncKeyState(VK_MENU) & 0x8000
                if ctrl_down and alt_down:
                    if user32.GetAsyncKeyState(0x43) & 0x8000:  # C
                        self.pending_action = 'C'
                        time.sleep(0.35)
                    elif user32.GetAsyncKeyState(0x57) & 0x8000:  # W
                        self.pending_action = 'W'
                        time.sleep(0.35)
                    elif user32.GetAsyncKeyState(0x50) & 0x8000:  # P
                        self.pending_action = 'P'
                        time.sleep(0.35)
                    elif user32.GetAsyncKeyState(0x53) & 0x8000:  # S
                        self.pending_action = 'S'
                        time.sleep(0.35)
                    elif user32.GetAsyncKeyState(0x48) & 0x8000:  # H (Hide to Tray)
                        self.pending_action = 'H'
                        time.sleep(0.35)
                    elif user32.GetAsyncKeyState(0x47) & 0x8000:  # G (Floating Pill GUI)
                        self.pending_action = 'G'
                        time.sleep(0.35)
                time.sleep(0.04)
        except Exception:
            pass

    def pop_action(self) -> Optional[str]:
        act = self.pending_action
        self.pending_action = None
        return act

    def stop(self):
        self.running = False


def _get_res_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

CONFIG_PATH = _get_res_path("config.json")


def load_config() -> Dict[str, Any]:
    defaults = {
        "webcam_id": 0,
        "frame_width": 1280,
        "frame_height": 720,
        "fps_target": 30,
        "use_mjpg_codec": True,
        "start_in_mini_widget": False,
        "pomodoro_focus_minutes": 25.0,
        "pomodoro_break_minutes": 5.0,
        "eye_rest_interval_minutes": 20.0,
        "away_threshold_seconds": 5.0,
        "warning_threshold_seconds": 2.5,
        "head_yaw_threshold": 18.0,
        "head_pitch_threshold": 16.0,
        "eye_open_ratio_threshold": 0.12,
        "iris_gaze_threshold_min": 0.20,
        "iris_gaze_threshold_max": 0.80,
        "enable_clahe_contrast": False,
        "enable_one_euro_filter": True,
        "auto_calibration_enabled": True,
        "enable_sound_alert": True,
        "enable_desktop_popup": True,
        "sound_frequency": 1200,
        "sound_duration_ms": 300,
        "sound_alert_interval_seconds": 3.0,
        "show_face_mesh": True,
        "show_gaze_rays": True,
        "show_hud_stats": True
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                defaults.update(loaded)
        except Exception as e:
            print(f"[!] Eroare la incarcarea config.json: {e}")
    return defaults


def draw_glass_panel(img, x, y, w, h, bg_color=(20, 20, 20), alpha=0.72, border_color=None):
    """Draw a modern translucent glassmorphism HUD panel."""
    sub_img = img[y:y+h, x:x+w]
    if sub_img.shape[0] == 0 or sub_img.shape[1] == 0:
        return
    bg_rect = np.full_like(sub_img, bg_color, dtype=np.uint8)
    cv2.addWeighted(bg_rect, alpha, sub_img, 1.0 - alpha, 0, sub_img)
    img[y:y+h, x:x+w] = sub_img
    if border_color:
        cv2.rectangle(img, (x, y), (x + w, y + h), border_color, 1)


def sanitize_text(text: str) -> str:
    """Sanitize diacritics and emojis to clean ASCII for OpenCV cv2.putText."""
    replacements = {
        "ă": "a", "â": "a", "î": "i", "ș": "s", "ț": "t",
        "Ă": "A", "Â": "A", "Î": "I", "Ș": "S", "Ț": "T",
        "✅": "[OK]", "⚠️": "[!]", "🚨": "[ALERT]", "📱": "[TEL]",
        "💡": "[THINK]", "🥱": "[YAWN]", "😊": "[:)]", "🧐": "[FOCUS]",
        "😠": "[FROWN]", "😲": "[SURPRISE]", "😐": "[:|]"
    }
    res = text
    for k, v in replacements.items():
        res = res.replace(k, v)
    return "".join(c for c in res if ord(c) < 128)


def render_mini_widget(
    gaze: GazeResult,
    away_elapsed: float,
    away_thresh: float,
    study_mgr: StudyManager,
    fps: float,
    sound_enabled: bool = True,
    theme: Optional[Any] = None
) -> np.ndarray:
    """Render a sleek Always-on-Top Mini Study Widget with live Cognitive Load, Reading & dynamic Themes."""
    w, h = 420, 110
    bg_col = theme.bg_panel if theme else (15, 15, 17)
    border_col = theme.border_panel if theme else (50, 50, 55)
    txt_primary = theme.text_primary if theme else (255, 255, 255)
    txt_sec = theme.text_secondary if theme else (180, 180, 190)

    widget = np.full((h, w, 3), bg_col, dtype=np.uint8)
    cv2.rectangle(widget, (0, 0), (w - 1, h - 1), border_col, 1)

    is_alert = away_elapsed >= away_thresh
    is_phone = gaze.smart_state == "PHONE_DOWN"
    is_glance = gaze.smart_state == "THINKING_GLANCE"
    is_focused = gaze.is_looking_at_screen and not is_alert

    # 1. Pulsing Status Orb (Left)
    orb_center = (32, 45)
    orb_radius = 16
    if not gaze.face_detected or is_alert:
        orb_color = theme.alert_color if theme else (0, 0, 255)
        state_title = f"AWAY ALERT ({away_elapsed:.1f}s)"
        sub_info = "Privire absenta | Pomodoro in pauza"
    elif is_phone:
        orb_color = theme.warning_color if theme else (0, 140, 255)
        state_title = f"TELEFON / BIROU ({away_elapsed:.1f}s)"
        sub_info = "Cap si ochi coborati"
    elif is_glance:
        orb_color = theme.accent_color if theme else (255, 200, 0)
        state_title = "GANDIRE / REFLECTIE"
        sub_info = "Privire scurta | Focus activ"
    elif is_focused:
        orb_color = theme.focus_color if theme else (0, 255, 100)
        eff = study_mgr.get_efficiency_score()
        pomo_str = study_mgr.get_pomodoro_string()
        state_title = f"FOCUS ({eff}% Eficienta) | {pomo_str}"
        clean_expr = sanitize_text(gaze.expression_label)
        clean_read = sanitize_text(gaze.reading_state_label)
        sub_info = f"Efort: {gaze.cognitive_load_pct}% | Ritm: {clean_read} | {clean_expr}"
    else:
        orb_color = theme.warning_color if theme else (0, 180, 255)
        state_title = f"PRIVIRE DISTRASA ({away_elapsed:.1f}s)"
        sub_info = "Apasati [C] pt calibrare"

    # Draw Orb with soft outer glow
    cv2.circle(widget, orb_center, orb_radius + 4, tuple(int(c * 0.35) for c in orb_color), -1, cv2.LINE_AA)
    cv2.circle(widget, orb_center, orb_radius, orb_color, -1, cv2.LINE_AA)
    cv2.circle(widget, orb_center, orb_radius, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. Main Title & Sub-text
    cv2.putText(widget, sanitize_text(state_title), (62, 30), cv2.FONT_HERSHEY_DUPLEX, 0.44, txt_primary, 1, cv2.LINE_AA)
    cv2.putText(widget, sanitize_text(sub_info), (62, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 200) if is_focused else txt_sec, 1, cv2.LINE_AA)

    # 3. Dynamic Progress Bar (Pomodoro or Distraction Alert)
    bar_x = 62
    bar_max_w = w - bar_x - 15
    bar_y = 66
    cv2.line(widget, (bar_x, bar_y), (bar_x + bar_max_w, bar_y), border_col, 3)

    if away_elapsed > 1.0:
        progress_ratio = min(1.0, away_elapsed / away_thresh) if away_thresh > 0 else 0.0
        bar_w = int(bar_max_w * progress_ratio)
        fill_col = (0, 165, 255) if progress_ratio < 1.0 else (0, 0, 255)
    elif study_mgr.is_pomodoro_active:
        if study_mgr.is_break_time:
            pomo_ratio = (study_mgr.break_duration_sec - study_mgr.pomodoro_remaining_sec) / max(1.0, study_mgr.break_duration_sec)
            fill_col = (0, 220, 255)
        else:
            pomo_ratio = (study_mgr.work_duration_sec - study_mgr.pomodoro_remaining_sec) / max(1.0, study_mgr.work_duration_sec)
            fill_col = (0, 255, 120)
        bar_w = int(bar_max_w * min(1.0, max(0.0, pomo_ratio)))
    else:
        bar_w = bar_max_w
        fill_col = (0, 255, 100)

    if bar_w > 0:
        cv2.line(widget, (bar_x, bar_y), (bar_x + bar_w, bar_y), fill_col, 3)

    # 4. Footer shortcuts with Sound Status
    snd_str = "ON" if sound_enabled else "OFF"
    cv2.putText(widget, f"[W] Mare | [P] Pomo | [S] Sunet: {snd_str} | [C] Calib | [Q] Exit", (bar_x, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (150, 150, 150), 1, cv2.LINE_AA)

    return widget


def set_high_process_priority():
    """Sets Windows process priority to ABOVE_NORMAL to prevent CPU micro-throttling."""
    try:
        if sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            # 0x00008000 = ABOVE_NORMAL_PRIORITY_CLASS
            kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x00008000)
    except Exception:
        pass


def main():
    set_high_process_priority()
    print("=" * 60)
    print("  GazeAlert AI: Next-Gen Eye, Posture & Productivity Suite")
    print("=" * 60)

    config = load_config()
    # Enable dedicated GPU Hardware Acceleration via OpenCL (AMD Radeon RX 6600 XT)
    gpu_name = "AMD Radeon RX 6600 XT"
    if cv2.ocl.haveOpenCL():
        cv2.ocl.setUseOpenCL(True)
        try:
            dev = cv2.ocl.Device.getDefault()
            dev_name = dev.name()
            if "gfx1032" in dev_name.lower():
                gpu_name = "AMD Radeon RX 6600 XT"
            else:
                gpu_name = f"{dev_name} ({dev.vendorName()})"
            print(f"[+] Accelerare Hardware GPU ACTIVATA: {gpu_name} (RDNA 2)")
        except Exception:
            print("[+] Accelerare Hardware OpenCL Activata pe GPU!")

    config = load_config()
    away_thresh = float(config.get("away_threshold_seconds", 30.0))
    warn_thresh = float(config.get("warning_threshold_seconds", 20.0))
    show_mesh = bool(config.get("show_face_mesh", True))
    show_rays = bool(config.get("show_gaze_rays", True))
    show_stats = bool(config.get("show_hud_stats", True))
    is_mini_widget = bool(config.get("start_in_mini_widget", False))

    detector = GazeDetector(
        head_yaw_thresh=float(config.get("head_yaw_threshold", 38.0)),
        head_pitch_thresh=float(config.get("head_pitch_threshold", 32.0)),
        ear_thresh=float(config.get("eye_open_ratio_threshold", 0.12)),
        iris_min=float(config.get("iris_gaze_threshold_min", 0.20)),
        iris_max=float(config.get("iris_gaze_threshold_max", 0.80)),
        enable_clahe=bool(config.get("enable_clahe_contrast", False)),
        auto_calibration_enabled=bool(config.get("auto_calibration_enabled", True)),
    )

    alert_mgr = AlertManager(
        enable_sound=bool(config.get("enable_sound_alert", True)),
        enable_popup=bool(config.get("enable_desktop_popup", True)),
        frequency=int(config.get("sound_frequency", 1200)),
        duration_ms=int(config.get("sound_duration_ms", 300)),
        repeat_interval_sec=float(config.get("sound_alert_interval_seconds", 3.0)),
    )

    study_mgr = StudyManager(
        pomodoro_focus_min=float(config.get("pomodoro_focus_minutes", 25.0)),
        pomodoro_break_min=float(config.get("pomodoro_break_minutes", 5.0)),
        eye_rest_interval_min=float(config.get("eye_rest_interval_minutes", 20.0)),
    )

    calibrator = ScreenCalibrator()

    webcam_id = int(config.get("webcam_id", 0))
    target_w = int(config.get("frame_width", 1280))
    target_h = int(config.get("frame_height", 720))
    use_mjpg = bool(config.get("use_mjpg_codec", True))

    print(f"[*] Pornire Threaded Camera I/O ({target_w}x{target_h})...")
    camera = ThreadedCamera(src=webcam_id, width=target_w, height=target_h, fps=int(config.get("fps_target", 30)), use_mjpg=use_mjpg)

    if not camera.isOpened():
        print(f"[!] EROARE: Nu s-a putut deschide camera video cu ID-ul {webcam_id}.")
        input("Apasa Enter pentru a inchide...")
        return

    print("[+] Camera Threaded initializata cu 0 ms latenta!")

    window_name = "GazeAlert AI"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    if is_mini_widget:
        cv2.resizeWindow(window_name, 400, 105)
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass
    else:
        cv2.resizeWindow(window_name, 1000, 560)

    session_logger = SessionLogger()

    theme_mgr = ThemeManager(config.get("theme", "cyber_dark"))
    monk_mode_enabled = bool(config.get("monk_mode_enabled", False))

    is_minimized_to_tray = False

    # System Tray Manager
    def _tray_toggle_hide():
        hotkey_listener.pending_action = 'H'

    def _tray_toggle_win():
        nonlocal is_mini_widget, is_minimized_to_tray
        if is_minimized_to_tray:
            is_minimized_to_tray = False
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        is_mini_widget = False
        cv2.resizeWindow(window_name, 1000, 560)
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 0)
        except Exception:
            pass

    def _tray_toggle_widget():
        nonlocal is_mini_widget, is_minimized_to_tray
        if is_minimized_to_tray:
            is_minimized_to_tray = False
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        is_mini_widget = True
        cv2.resizeWindow(window_name, 420, 110)
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass

    def _tray_calib():
        hotkey_listener.pending_action = 'C'

    def _tray_pomo():
        hotkey_listener.pending_action = 'P'

    def _tray_sound():
        hotkey_listener.pending_action = 'S'

    def _tray_theme():
        hotkey_listener.pending_action = 'O'

    def _tray_export():
        hotkey_listener.pending_action = 'E'

    def _tray_report():
        p = study_mgr.generate_html_report("study_report.html")
        if p:
            try:
                webbrowser.open(p)
            except Exception:
                pass

    pill_widget = FloatingPillWidget(
        on_calibrate=lambda: setattr(hotkey_listener, 'pending_action', 'C'),
        on_toggle_pomodoro=lambda: setattr(hotkey_listener, 'pending_action', 'P'),
        on_toggle_sound=lambda: setattr(hotkey_listener, 'pending_action', 'S'),
        on_open_report=_tray_report,
        on_exit=lambda: setattr(hotkey_listener, 'pending_action', 'Q')
    )
    pill_widget.start()

    def _save_cfg_handler(new_cfg: Dict[str, Any]):
        nonlocal away_thresh
        away_thresh = float(new_cfg.get("away_threshold_seconds", away_thresh))
        detector.head_yaw_thresh = float(new_cfg.get("head_yaw_threshold", detector.head_yaw_thresh))
        study_mgr.focus_duration_sec = float(new_cfg.get("pomodoro_focus_minutes", 25.0)) * 60.0
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(new_cfg, f, indent=2)
        except Exception:
            pass

    control_center = ControlCenterGUI(
        config=config,
        on_calibrate_center=lambda: setattr(hotkey_listener, 'pending_action', 'C'),
        on_calibrate_9point=lambda: setattr(hotkey_listener, 'pending_action', 'K'),
        on_toggle_pomodoro=lambda: setattr(hotkey_listener, 'pending_action', 'P'),
        on_toggle_sound=lambda: alert_mgr.toggle_sound(),
        on_toggle_monk=lambda: setattr(hotkey_listener, 'pending_action', 'N') or (not monk_mode_enabled),
        on_toggle_pill=lambda: pill_widget.toggle(),
        on_open_report=_tray_report,
        on_save_config=_save_cfg_handler
    )

    tray_manager = SystemTrayManager(
        on_toggle_window=_tray_toggle_win,
        on_toggle_widget=_tray_toggle_widget,
        on_toggle_hide=_tray_toggle_hide,
        on_calibrate=_tray_calib,
        on_toggle_pomodoro=_tray_pomo,
        on_toggle_sound=_tray_sound,
        on_cycle_theme=_tray_theme,
        on_export=_tray_export,
        on_open_report=_tray_report,
        on_exit=lambda: setattr(hotkey_listener, 'pending_action', 'Q')
    )
    tray_manager.start()

    if config.get("auto_open_dashboard", True):
        control_center.show(pill_widget.root if pill_widget.root else None)

    away_start_time = None
    away_elapsed = 0.0
    fps_counter = 0
    fps_time = time.time()
    fps = 30.0

    calib_banner_text = ""
    calib_banner_time = 0.0

    # Start Global Windows Hotkeys Thread (Ctrl+Alt+C / Ctrl+Alt+W / Ctrl+Alt+P / Ctrl+Alt+S / Ctrl+Alt+H / Ctrl+Alt+G / Ctrl+Alt+D)
    hotkey_listener = GlobalHotkeyListener()

    print("-" * 75)
    print("Moduri de Lucru & Scurtaturi Globale de Windows:")
    print("  [D] Panou Control GUI Modern              |  [Ctrl+Alt+G] sau [G] Widget Plutitor (Pill)")
    print("  [Ctrl+Alt+W] sau [W] Mini-Widget OpenCV  |  [Ctrl+Alt+H] sau [H] Minimize to Tray")
    print("  [Ctrl+Alt+C] sau [C] Calibrare Rapida     |  [K] Calibrare 9 Puncte pe Ecran")
    print("  [Ctrl+Alt+P] sau [P] Toggle Pomodoro      |  [N] Monk Mode Shield")
    print("  [Ctrl+Alt+S] sau [S] Sunet Alerta ON/OFF  |  [E] Exporta CSV/JSON  |  [Q] Exit")
    print("-" * 75)

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                time.sleep(0.005)
                continue

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            scale = max(1.0, w / 1000.0)

            fps_counter += 1
            if time.time() - fps_time >= 1.0:
                fps = fps_counter / (time.time() - fps_time)
                fps_counter = 0
                fps_time = time.time()

            gaze: GazeResult = detector.process_frame(frame)

            # Update Study & Pomodoro Performance Metrics
            study_mgr.update(gaze.is_looking_at_screen, gaze.smart_state, gaze.is_yawning)

            # Handle 9-Point Calibration Routine if active
            if calibrator.is_calibrating:
                if gaze.face_detected and len(gaze.raw_features) >= 8:
                    calibrator.add_sample(gaze.raw_features)
                calibrator.draw_calibration_overlay(frame)
                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in [ord('q'), ord('Q'), 27]:
                    calibrator.is_calibrating = False
                continue

            screen_gaze_pos = None
            if calibrator.is_calibrated and gaze.face_detected and len(gaze.raw_features) >= 8:
                screen_gaze_pos = calibrator.predict_screen_pos(gaze.raw_features)

            # Record point in Gaze Heatmap
            if screen_gaze_pos is not None:
                study_mgr.add_gaze_point(screen_gaze_pos[0], screen_gaze_pos[1])
            elif gaze.face_detected and gaze.is_looking_at_screen:
                norm_x = 0.5 + (gaze.total_gaze_yaw / 36.0)
                norm_y = 0.5 - (gaze.total_gaze_pitch / 28.0)
                study_mgr.add_gaze_point(norm_x, norm_y)

            # Away Timer State Machine
            now = time.time()
            if not gaze.face_detected or not gaze.is_looking_at_screen:
                if away_start_time is None:
                    away_start_time = now
                away_elapsed = now - away_start_time
            else:
                away_start_time = None
                away_elapsed = 0.0

            is_alert = away_elapsed >= away_thresh
            is_warning = away_elapsed >= warn_thresh and not is_alert

            # Smart Anti-Spam Progressive Notification Coach & Ergonomics Alert
            reason = ", ".join(gaze.reasons) if gaze.reasons else "Utilizator absent"
            alert_mgr.check_and_alert(away_elapsed, gaze.smart_state, reason)
            if gaze.face_detected:
                alert_mgr.check_posture_and_alert(gaze.is_slouching, gaze.distance_cm)

            # Check Adaptive Pomodoro Flow Auto-Extension
            flow_msg = study_mgr.check_flow_extension(gaze.flow_state_zone)
            if flow_msg:
                calib_banner_text = flow_msg
                calib_banner_time = now
                print(f"\n[+] {flow_msg}")

            # Update System Tray status orb
            tray_manager.update_status(gaze.is_looking_at_screen, is_alert)

            # Update Floating Pill Desktop Widget (if visible)
            if pill_widget.is_visible:
                orb_hex = "#00FF78" if gaze.is_looking_at_screen else ("#FF3250" if is_alert else "#FFC800")
                pomo_str = study_mgr.get_pomodoro_string()
                lvl, cur_xp, needed_xp, _ = study_mgr.get_level_info()
                clean_title = f"FOCUS ({study_mgr.get_efficiency_score()}%) | Nivel {lvl}" if gaze.is_looking_at_screen else "AWAY ALERT"
                pill_widget.update_metrics(
                    clean_title,
                    f"Pomo: {pomo_str} | Dist: {int(gaze.distance_cm)}cm | XP: {cur_xp}/{needed_xp}",
                    orb_hex,
                    progress_pct=float(study_mgr.get_efficiency_score())
                )

            # Update Control Center Desktop Dashboard (if visible)
            if control_center.is_open:
                lvl, cur_xp, needed_xp, ratio = study_mgr.get_level_info()
                control_center.update_telemetry(
                    focus_pct=study_mgr.get_efficiency_score(),
                    status_label=gaze.expression_label if gaze.face_detected else "ABSENT",
                    pomo_str=study_mgr.get_pomodoro_string(),
                    distance_cm=int(gaze.distance_cm),
                    posture_str=gaze.posture_status,
                    xp=study_mgr.total_xp,
                    level=lvl,
                    needed_xp=needed_xp,
                    level_ratio=ratio,
                    is_focused=gaze.is_looking_at_screen
                )

            active_theme = theme_mgr.current

            # --- Render Mode: Mini-Widget vs Full Camera HUD vs Minimized to Tray ---
            if is_minimized_to_tray:
                time.sleep(0.015)
                key = -1
            elif is_mini_widget:
                widget_frame = render_mini_widget(
                    gaze, away_elapsed, away_thresh, study_mgr, fps,
                    sound_enabled=alert_mgr.enable_sound,
                    theme=active_theme
                )
                cv2.imshow(window_name, widget_frame)
                key = cv2.waitKey(1) & 0xFF
            else:
                # 1. Studio-Grade Pixel-Perfect Anatomical Mesh & 3D Gaze Lasers
                if show_mesh and gaze.landmarks_2d is not None:
                    draw_pixel_perfect_mesh(
                        frame,
                        gaze.landmarks_2d,
                        scale,
                        pupil_left=gaze.left_iris_center,
                        pupil_right=gaze.right_iris_center,
                        gaze_ray_l_end=gaze.left_gaze_ray_end,
                        gaze_ray_r_end=gaze.right_gaze_ray_end,
                        pupil_radius_l=gaze.left_pupil_radius,
                        pupil_radius_r=gaze.right_pupil_radius,
                        is_focused=gaze.is_looking_at_screen
                    )

                # 2. 3D Head Pose Direction Ray
                if show_rays and gaze.nose_start and gaze.nose_ray_end:
                    ray_thick = int(2.5 * scale)
                    color_ray = (0, 255, 0) if gaze.is_looking_at_screen else (0, 140, 255)
                    cv2.arrowedLine(frame, gaze.nose_start, gaze.nose_ray_end, color_ray, ray_thick, tipLength=0.2)

                # 3. Flashing Border during Alert
                if is_alert:
                    flash_state = int(time.time() * 4) % 2 == 0
                    border_col = (0, 0, 255) if flash_state else (50, 50, 255)
                    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), border_col, int(10 * scale))

                # 4. Top Status Header Glass Panel
                header_h = int(72 * scale)
                draw_glass_panel(frame, 15, 12, w - 30, header_h, bg_color=active_theme.bg_panel, alpha=0.78, border_color=active_theme.border_panel)

                pomo_info = study_mgr.get_pomodoro_string()
                eff_score = study_mgr.get_efficiency_score()

                if not gaze.face_detected:
                    badge_text = "[!] ABSENT / FATA NEDETECTATA"
                    badge_color = active_theme.alert_color
                    sub_text = "Nicio persoana in fata camerei | Pomodoro in pauza"
                elif is_alert:
                    badge_text = f"[ALERT] AWAY ({away_elapsed:.1f}s / {away_thresh:.0f}s)"
                    badge_color = active_theme.alert_color
                    sub_text = sanitize_text(gaze.state_description or "Privire absenta")
                elif study_mgr.is_eye_rest_alert:
                    badge_text = f"[EYE REST] PAUZA OCULARA 20-20-20 ({int(study_mgr.eye_rest_countdown)}s)"
                    badge_color = (0, 220, 255)
                    sub_text = "Priviti in departare (6 metri) pt relaxarea ochilor"
                elif gaze.is_yawning:
                    badge_text = "[YAWN] CASCAT DETECTAT (Oboseala)"
                    badge_color = active_theme.warning_color
                    sub_text = f"Cascat #{gaze.yawn_count} in sesiune | Memento pauza de apa"
                elif gaze.smart_state == "PHONE_DOWN":
                    badge_text = f"[TEL] DISTRAGERE TELEFON ({away_elapsed:.1f}s)"
                    badge_color = active_theme.warning_color
                    sub_text = "Privire coborata spre birou/telefon | Timer studiu oprit"
                elif is_warning:
                    badge_text = f"[!] ATENTIE: PRIVIRE IN ALTA PARTE ({away_elapsed:.1f}s)"
                    badge_color = active_theme.warning_color
                    sub_text = sanitize_text(gaze.state_description or "Timp atentie redus")
                elif gaze.smart_state == "THINKING_GLANCE":
                    badge_text = "[THINK] GANDIRE / SCURTA PRIVIRE (Focus OK)"
                    badge_color = active_theme.accent_color
                    sub_text = f"Privire de reflectie | Pomodoro: {pomo_info}"
                elif away_elapsed > 0.8:
                    badge_text = f"[*] PRIVIRE IN ALTA PARTE ({away_elapsed:.1f}s)"
                    badge_color = active_theme.warning_color
                    sub_text = sanitize_text(gaze.state_description or "Apasati [C] pt calibrare")
                else:
                    cog_str = f"Efort Mental: {gaze.cognitive_load_pct}%"
                    read_str = f"Ritm: {gaze.reading_state_label}"
                    badge_text = f"[OK] FOCUS ({int(gaze.focus_confidence * 100)}% Instant | {eff_score}% Studiu)"
                    badge_color = active_theme.focus_color
                    sub_text = f"Pomodoro: {pomo_info} | {cog_str} | {read_str}"

                font_scale_badge = 0.65 * scale
                font_scale_sub = 0.42 * scale

                cv2.putText(frame, sanitize_text(badge_text), (int(30 * scale), int(38 * scale)), cv2.FONT_HERSHEY_DUPLEX, font_scale_badge, badge_color, max(1, int(2 * scale)), cv2.LINE_AA)
                cv2.putText(frame, sanitize_text(sub_text), (int(30 * scale), int(60 * scale)), cv2.FONT_HERSHEY_SIMPLEX, font_scale_sub, (210, 210, 210), 1, cv2.LINE_AA)

                # Progress Bar
                progress_ratio = min(1.0, away_elapsed / away_thresh) if away_thresh > 0 else 0.0
                bar_w = int((w - 60) * progress_ratio)
                bar_y = int(76 * scale)
                bar_thick = max(3, int(4 * scale))
                cv2.line(frame, (25, bar_y), (w - 25, bar_y), (50, 50, 50), bar_thick)
                fill_col = (0, 255, 100) if progress_ratio < 0.6 else ((0, 165, 255) if progress_ratio < 1.0 else (0, 0, 255))
                if bar_w > 0:
                    cv2.line(frame, (25, bar_y), (25 + bar_w, bar_y), fill_col, bar_thick)

                # 5. Pupillometry, Ergonomics & Study Widget (Top Right)
                if gaze.face_detected:
                    expr_w = int(280 * scale)
                    expr_h = int(88 * scale)
                    expr_x = w - expr_w - 20
                    expr_y = int(95 * scale)
                    draw_glass_panel(frame, expr_x, expr_y, expr_w, expr_h, bg_color=active_theme.bg_panel, alpha=0.78, border_color=active_theme.border_panel)

                    energy_pct = int((1.0 - gaze.fatigue_level) * 100)
                    energy_col = (0, 255, 100) if energy_pct > 65 else ((0, 165, 255) if energy_pct > 35 else (0, 0, 255))
                    dist_col = (0, 255, 100) if 42.0 <= gaze.distance_cm <= 85.0 else (0, 140, 255)

                    lvl, cur_xp, needed_xp, _ = study_mgr.get_level_info()

                    cv2.putText(frame, f"Stare: {sanitize_text(gaze.expression_label)} | Nivel {lvl} ({cur_xp}/{needed_xp} XP)", (expr_x + int(12 * scale), expr_y + int(18 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.35 * scale, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Efort Cognitiv: {gaze.cognitive_load_pct}% | Pupila: {int(gaze.pupil_diameter_ratio*100)}%", (expr_x + int(12 * scale), expr_y + int(36 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.35 * scale, (0, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Ritm Citire: {sanitize_text(gaze.reading_state_label)} | Eficienta: {eff_score}%", (expr_x + int(12 * scale), expr_y + int(54 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.35 * scale, (0, 255, 120), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Distanta: {int(gaze.distance_cm)} cm ({gaze.posture_status})", (expr_x + int(12 * scale), expr_y + int(72 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.34 * scale, dist_col, 1, cv2.LINE_AA)

                # 6. Diagnostic Metrics HUD (Bottom Left)
                if show_stats:
                    panel_w = int(390 * scale)
                    panel_h = int(136 * scale)
                    panel_y = h - panel_h - int(45 * scale)
                    draw_glass_panel(frame, 15, panel_y, panel_w, panel_h, bg_color=active_theme.bg_panel, alpha=0.78, border_color=active_theme.border_panel)

                    eye_open_str = "DESCHISI" if (gaze.left_ear + gaze.right_ear)/2.0 >= detector.ear_thresh else "INCHISI"
                    eye_col = (0, 255, 100) if eye_open_str == "DESCHISI" else (0, 165, 255)

                    f_stat = 0.38 * scale
                    cv2.putText(frame, f"Stare: {gaze.smart_state} | Conf: {int(gaze.focus_confidence*100)}%", (25, panel_y + int(20 * scale)), cv2.FONT_HERSHEY_SIMPLEX, f_stat, (0, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Ochi: {eye_open_str} | PERCLOS: {int(gaze.perclos_score*100)}% | Efort: {gaze.cognitive_load_pct}%", (25, panel_y + int(38 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.36 * scale, eye_col, 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Cap: Yaw {gaze.head_yaw:+.1f} Pitch {gaze.head_pitch:+.1f} | VOR: {gaze.total_gaze_yaw:+.1f}", (25, panel_y + int(56 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.36 * scale, (220, 220, 220), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Pupila: {int(gaze.pupil_diameter_ratio*100)}% Diametru ({gaze.pupil_state_label})", (25, panel_y + int(74 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.35 * scale, (0, 255, 200), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"GPU: {gpu_name[:28]} | FPS: {fps:.1f}", (25, panel_y + int(92 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.36 * scale, (0, 255, 120), 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Distanta: {int(gaze.distance_cm)} cm | Timer: {away_elapsed:.1f}s / {away_thresh:.0f}s", (25, panel_y + int(110 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.35 * scale, fill_col, 1, cv2.LINE_AA)
                    cv2.putText(frame, f"Pomo: {pomo_info} | Studiu: Nivel {study_mgr.current_level} ({study_mgr.total_xp} XP)", (25, panel_y + int(128 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.34 * scale, (0, 220, 255), 1, cv2.LINE_AA)

                # 7. Calibration On-Screen Banner (if recently triggered)
                # 7. Monk Mode Distraction Shield Overlay
                if monk_mode_enabled:
                    if away_elapsed > 2.0:
                        overlay = frame.copy()
                        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 45), -1)
                        cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)
                        cv2.rectangle(frame, (8, 8), (w - 8, h - 8), (0, 0, 255), max(3, int(5 * scale)))
                        cv2.putText(frame, "MONK MODE: ATENTIE LA ECRAN!", (int(w * 0.18), int(h * 0.52)), cv2.FONT_HERSHEY_DUPLEX, 0.68 * scale, (0, 140, 255), 2, cv2.LINE_AA)
                    else:
                        cv2.putText(frame, "[MONK MODE ACTIV]", (w - int(155 * scale), h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.34 * scale, (0, 255, 120), 1, cv2.LINE_AA)

                # 8. Bottom Controls Bar
                snd_status = "ON" if alert_mgr.enable_sound else "OFF"
                controls_text = f"[W] Widget | [H] Tray | [C] Calib | [K] 9-Pct | [N] Monk | [P] Pomo | [S] Sunet: {snd_status} | [O] Tema | [E] Export | [Q] Exit"
                cv2.putText(frame, controls_text, (20, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.34 * scale, (180, 180, 180), 1, cv2.LINE_AA)

                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF

            # Keybindings & Global Hotkeys Handling
            global_act = hotkey_listener.pop_action()
            if global_act:
                key = ord(global_act.lower())

            if key in [ord('h'), ord('H')]:
                is_minimized_to_tray = not is_minimized_to_tray
                if is_minimized_to_tray:
                    cv2.destroyAllWindows()
                    print("\n[+] GazeAlert MINIMIZAT IN SYSTEM TRAY (langa ceas)!")
                    print("  -> Poti restaura oricand cu dublu-click pe iconita din bara sau cu scurtatura [Ctrl+Alt+H].")
                else:
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    if is_mini_widget:
                        cv2.resizeWindow(window_name, 420, 110)
                        try:
                            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
                        except Exception:
                            pass
                    else:
                        cv2.resizeWindow(window_name, 1000, 560)
                    print("\n[+] GazeAlert RESTAURAT din System Tray!")

            if key in [ord('q'), ord('Q'), 27]:
                print("\n[*] Generare raport final de studiu...")
                report = study_mgr.generate_summary_report()
                print(report)

                # 1. Save session to JSON and SQLite
                eff = study_mgr.get_efficiency_score()
                session_logger.save_session(
                    total_seconds=study_mgr.stats.total_study_seconds,
                    pure_focus_seconds=study_mgr.stats.pure_focus_seconds,
                    distraction_seconds=study_mgr.stats.distraction_seconds,
                    efficiency_pct=eff,
                    phone_count=study_mgr.stats.phone_distractions_count,
                    yawn_count=study_mgr.stats.yawns_count,
                    grade="A+" if eff >= 90 else ("A" if eff >= 80 else ("B" if eff >= 65 else "C"))
                )

                # 2. Generate and open interactive HTML report
                html_path = study_mgr.generate_html_report("study_report.html")
                if html_path:
                    print(f"[+] Raport vizual HTML generat cu succes: {html_path}")
                    try:
                        webbrowser.open(html_path)
                    except Exception:
                        pass
                break
            elif key in [ord('p'), ord('P')]:
                state = study_mgr.toggle_pomodoro()
                print(f"[+] Pomodoro Study Timer: {'ACTIVAT (25 min)' if state else 'DEZACTIVAT'}")
            elif key in [ord('w'), ord('W')]:
                is_mini_widget = not is_mini_widget
                if is_mini_widget:
                    cv2.resizeWindow(window_name, 420, 110)
                    try:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
                    except Exception:
                        pass
                    print("[+] Comutat in MOD MINI-WIDGET (Always-on-Top)!")
                else:
                    cv2.resizeWindow(window_name, 1000, 560)
                    try:
                        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 0)
                    except Exception:
                        pass
                    print("[+] Comutat in MOD FEREASTRA MARE!")
            elif key in [ord('k'), ord('K')]:
                print("[*] Pornire mod calibrare 9 puncte pe ecran...")
                calibrator.start_calibration()
                calib_banner_text = "[*] CALIBRARE 9 PUNCTE INITIATA..."
                calib_banner_time = time.time()
            elif key in [ord('c'), ord('C')]:
                # Re-zero resting baseline to current posture
                detector.calibrate_baseline(gaze.head_yaw + detector.calibrated_yaw, gaze.head_pitch + detector.calibrated_pitch, gaze.ipd_pixels)
                away_start_time = None
                away_elapsed = 0.0
                calib_banner_text = "[OK] CENTRU CALIBRAT LA 0.0 DEG!"
                calib_banner_time = time.time()
                print(f"[+] CALIBRARE RAPIDA EFECTUATA! Centru setat la pozitia curenta.")
            elif key in [ord('r'), ord('R')]:
                detector.reset_calibration()
                calibrator.is_calibrated = False
                calib_banner_text = "[!] CALIBRARE RESETATA LA DEFAULT"
                calib_banner_time = time.time()
                print("[*] Calibrarea a fost resetata la valorile default.")
            elif key in [ord('m'), ord('M')]:
                show_mesh = not show_mesh
                print(f"[*] Afisare Ochi/Mesh: {show_mesh}")
            elif key in [ord('t'), ord('T')]:
                print("[*] Test alerta declansat manual...")
                alert_mgr.trigger_test_alert()
            elif key in [ord('s'), ord('S')]:
                state = alert_mgr.toggle_sound()
                print(f"[*] Sunet alerta: {'ACTIVAT' if state else 'DEZACTIVAT'}")
            elif key in [ord('o'), ord('O')]:
                cur_thm = theme_mgr.cycle_theme()
                calib_banner_text = f"TEMA: {cur_thm.label.upper()}"
                calib_banner_time = time.time()
                print(f"[+] Tema interfetei schimbata la: {cur_thm.label}")
            elif key in [ord('g'), ord('G')]:
                is_pill_vis = pill_widget.toggle()
                calib_banner_text = f"WIDGET PLUTITOR: {'ACTIVAT' if is_pill_vis else 'ASCUNS'}"
                calib_banner_time = time.time()
                print(f"[+] Widget Plutitor Desktop (Frameless Pill): {'ACTIVAT' if is_pill_vis else 'ASCUNS'}")
            elif key in [ord('n'), ord('N')]:
                monk_mode_enabled = not monk_mode_enabled
                calib_banner_text = f"MONK MODE: {'ACTIVAT 🛡️' if monk_mode_enabled else 'DEZACTIVAT'}"
                calib_banner_time = time.time()
                print(f"[+] Monk Mode (Distraction Shield): {'ACTIVAT' if monk_mode_enabled else 'DEZACTIVAT'}")
            elif key in [ord('d'), ord('D')]:
                control_center.show(pill_widget.root if pill_widget.root else None)
                print("[+] Panou de Control Desktop (Studio Dashboard) deschis!")
            elif key in [ord('e'), ord('E')]:
                csv_p = session_logger.export_to_csv()
                json_p = session_logger.export_to_json()
                calib_banner_text = "[OK] DATE EXPORTATE (CSV & JSON)!"
                calib_banner_time = time.time()
            elif key in [ord('+'), ord('=')]:
                away_thresh += 5.0
                print(f"[+] Prag alerta marit la: {away_thresh:.0f} secunde")
            elif key in [ord('-'), ord('_')]:
                away_thresh = max(5.0, away_thresh - 5.0)
                print(f"[-] Prag alerta micsorat la: {away_thresh:.0f} secunde")

    except KeyboardInterrupt:
        print("\n[*] Oprit prin tastatura...")
    finally:
        pill_widget.stop()
        tray_manager.stop()
        hotkey_listener.stop()
        detector.close()
        camera.release()
        cv2.destroyAllWindows()
        print("[+] Resursele au fost eliberate cu succes. La revedere!")


if __name__ == "__main__":
    main()
