"""
Smart Non-Intrusive Focus & Distraction Alert Manager for GazeAlert.
Features:
1. Anti-Spam Intelligent Cooldowns (No annoying sound loops or notification floods)
2. Progressive Notification Tiers (Soft Harmonic Chime -> Polite Reminder -> Away Alert)
3. Instant Silence on Return (Zero delay when returning focus to screen)
4. Smooth musical frequencies (C5-E5 harmonic chords instead of harsh beeps)
"""

import os
import sys
import threading
import time
from typing import Optional

try:
    import winsound
except ImportError:
    winsound = None

try:
    from win10toast import ToastNotifier
    _win_toaster = ToastNotifier()
except Exception:
    _win_toaster = None

try:
    from plyer import notification
except ImportError:
    notification = None

from sound_manager import ensure_default_sounds, play_sound_async


class AlertManager:
    """Smart Non-Intrusive Focus Notification & Audio Coach."""
    def __init__(
        self,
        enable_sound: bool = True,
        enable_popup: bool = True,
        frequency: int = 1200,
        duration_ms: int = 300,
        repeat_interval_sec: float = 3.0,
        nudge_delay_sec: float = 4.5,          # Seconds of distraction before soft nudge
        warn_delay_sec: float = 12.0,          # Seconds before polite warning
        away_delay_sec: float = 25.0,          # Seconds before full away alert
        cooldown_sec: float = 12.0,            # Anti-spam cooldown between sounds
        toast_cooldown_sec: float = 35.0,      # Anti-spam cooldown between desktop toasts
        **kwargs
    ):
        self.enable_sound = enable_sound
        self.enable_popup = enable_popup
        self.frequency = frequency
        self.duration_ms = duration_ms
        self.repeat_interval_sec = repeat_interval_sec
        self.nudge_delay_sec = nudge_delay_sec
        self.warn_delay_sec = warn_delay_sec
        self.away_delay_sec = away_delay_sec
        self.cooldown_sec = max(3.0, cooldown_sec)
        self.toast_cooldown_sec = toast_cooldown_sec

        ensure_default_sounds()

        self.last_sound_time: float = 0.0
        self.last_toast_time: float = 0.0
        self._last_nudge_stage: int = 0
        self._is_playing: bool = False

    def _play_soft_harmonic_chime(self):
        """Soft non-intrusive harmonic chord."""
        if not self.enable_sound:
            return
        play_sound_async("focus_chime")

    def _play_polite_warning_chime(self):
        """Polite double chime."""
        if not self.enable_sound:
            return
        play_sound_async("away_warning")

    def _play_away_chime(self):
        """Distinctive away alert chime."""
        if not self.enable_sound:
            return
        play_sound_async("away_warning")

    def _show_desktop_toast(self, title: str, message: str):
        """Display a native Windows desktop toast without interrupting user workflow."""
        try:
            if _win_toaster is not None:
                _win_toaster.show_toast(title, message, duration=4, threaded=True)
            elif notification is not None:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="GazeAlert Focus Coach",
                    timeout=4
                )
            elif winsound is not None:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def check_and_alert(self, away_elapsed: float, smart_state: str, reason: str = ""):
        """
        Smart progressive notifier.
        Fires only at appropriate milestones with strict anti-spam cooldowns.
        """
        now = time.time()

        # If user is in short thinking glance or focused, reset stage and do nothing
        if smart_state in ["FOCUS_ACTIVE", "THINKING_GLANCE"] or away_elapsed < self.nudge_delay_sec:
            self._last_nudge_stage = 0
            return

        # Stage 1: Soft Nudge (4.5s - 12s)
        if self.nudge_delay_sec <= away_elapsed < self.warn_delay_sec:
            if self._last_nudge_stage < 1 and (now - self.last_sound_time >= self.cooldown_sec):
                self._last_nudge_stage = 1
                self.last_sound_time = now
                if self.enable_sound:
                    threading.Thread(target=self._play_soft_harmonic_chime, daemon=True).start()

        # Stage 2: Polite Reminder (12s - 25s)
        elif self.warn_delay_sec <= away_elapsed < self.away_delay_sec:
            if self._last_nudge_stage < 2 and (now - self.last_sound_time >= self.cooldown_sec):
                self._last_nudge_stage = 2
                self.last_sound_time = now
                if self.enable_sound:
                    threading.Thread(target=self._play_polite_warning_chime, daemon=True).start()

                # Discrete Toast Notification (Throttled)
                if self.enable_popup and (now - self.last_toast_time >= self.toast_cooldown_sec):
                    self.last_toast_time = now
                    cause = "Privire coborata la telefon" if smart_state == "PHONE_DOWN" else "Privire distrasa de la ecran"
                    threading.Thread(
                        target=self._show_desktop_toast,
                        args=("🎯 Memento Focus", f"{cause} ({int(away_elapsed)}s). Revino usor la studiu!"),
                        daemon=True
                    ).start()

        # Stage 3: Away Alert (> 25s)
        elif away_elapsed >= self.away_delay_sec:
            if self._last_nudge_stage < 3 and (now - self.last_sound_time >= self.cooldown_sec):
                self._last_nudge_stage = 3
                self.last_sound_time = now
                if self.enable_sound:
                    threading.Thread(target=self._play_away_chime, daemon=True).start()

                if self.enable_popup and (now - self.last_toast_time >= self.toast_cooldown_sec):
                    self.last_toast_time = now
                    threading.Thread(
                        target=self._show_desktop_toast,
                        args=("⚠️ Sesiune Studiu in Pauza", f"Ai fost plecat {int(away_elapsed)}s. Pomodoro s-a oprit automat."),
                        daemon=True
                    ).start()

    def trigger_alert(self, away_duration: float, reason: str = ""):
        """Legacy compatibility method."""
        self.check_and_alert(away_duration, "LOOKING_AWAY", reason)

    def check_posture_and_alert(self, is_slouching: bool, distance_cm: float):
        """Discreet posture reminder for slouching or dangerous eye-strain distance (<40cm)."""
        if not self.enable_sound:
            return
        now = time.time()
        if not hasattr(self, '_last_posture_alert'):
            self._last_posture_alert = 0.0
            self._slouch_start_time = None

        is_bad_posture = is_slouching or (distance_cm < 40.0)
        if is_bad_posture:
            if self._slouch_start_time is None:
                self._slouch_start_time = now
            elif (now - self._slouch_start_time > 6.0) and (now - self._last_posture_alert > 25.0):
                self._last_posture_alert = now
                threading.Thread(target=lambda: play_sound_async("posture_chime"), daemon=True).start()
        else:
            self._slouch_start_time = None

    def trigger_test_alert(self):
        """Manually test alert sounds and popups."""
        threading.Thread(target=self._play_soft_harmonic_chime, daemon=True).start()

    def toggle_sound(self) -> bool:
        self.enable_sound = not self.enable_sound
        return self.enable_sound

    def toggle_popup(self) -> bool:
        self.enable_popup = not self.enable_popup
        return self.enable_popup
