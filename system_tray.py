"""
System Tray Manager for GazeAlert using pystray.
Runs a sleek notification area icon with right-click menu controls.
"""

import threading
import time
from typing import Callable, Optional
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item, Menu
except ImportError:
    pystray = None


def create_tray_icon_image(color=(0, 255, 120)) -> Image.Image:
    """Create a high-contrast 64x64 glowing orb icon for system tray."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer circle
    draw.ellipse((8, 8, 56, 56), fill=(20, 30, 25, 220), outline=color, width=3)
    # Inner glowing eye pupil
    draw.ellipse((22, 22, 42, 42), fill=color)
    draw.ellipse((28, 28, 36, 36), fill=(10, 10, 10))
    return img


class SystemTrayManager:
    """Non-blocking Windows System Tray Icon with controls and Minimize to Tray."""
    def __init__(
        self,
        on_toggle_window: Optional[Callable[[], None]] = None,
        on_toggle_widget: Optional[Callable[[], None]] = None,
        on_toggle_hide: Optional[Callable[[], None]] = None,
        on_calibrate: Optional[Callable[[], None]] = None,
        on_toggle_pomodoro: Optional[Callable[[], None]] = None,
        on_toggle_sound: Optional[Callable[[], None]] = None,
        on_cycle_theme: Optional[Callable[[], None]] = None,
        on_export: Optional[Callable[[], None]] = None,
        on_open_report: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        self.on_toggle_window = on_toggle_window
        self.on_toggle_widget = on_toggle_widget
        self.on_toggle_hide = on_toggle_hide
        self.on_calibrate = on_calibrate
        self.on_toggle_pomodoro = on_toggle_pomodoro
        self.on_toggle_sound = on_toggle_sound
        self.on_cycle_theme = on_cycle_theme
        self.on_export = on_export
        self.on_open_report = on_open_report
        self.on_exit = on_exit

        self.icon = None
        self.thread = None
        self.is_running = False

    def start(self):
        if pystray is None:
            return

        def _action_toggle_hide(icon, item):
            if self.on_toggle_hide:
                self.on_toggle_hide()

        def _action_toggle_win(icon, item):
            if self.on_toggle_window:
                self.on_toggle_window()

        def _action_widget(icon, item):
            if self.on_toggle_widget:
                self.on_toggle_widget()

        def _action_calib(icon, item):
            if self.on_calibrate:
                self.on_calibrate()

        def _action_pomo(icon, item):
            if self.on_toggle_pomodoro:
                self.on_toggle_pomodoro()

        def _action_sound(icon, item):
            if self.on_toggle_sound:
                self.on_toggle_sound()

        def _action_theme(icon, item):
            if self.on_cycle_theme:
                self.on_cycle_theme()

        def _action_export(icon, item):
            if self.on_export:
                self.on_export()

        def _action_report(icon, item):
            if self.on_open_report:
                self.on_open_report()

        def _action_exit(icon, item):
            if self.on_exit:
                self.on_exit()
            if self.icon:
                self.icon.stop()

        menu = Menu(
            item("👁️ Arata / Minimizeaza in Bara (Tray)", _action_toggle_hide, default=True),
            Menu.SEPARATOR,
            item("🖥️ Fereastra Mare", _action_toggle_win),
            item("🔲 Mini-Widget (Always on Top)", _action_widget),
            Menu.SEPARATOR,
            item("🎯 Calibreaza Centru (Ctrl+Alt+C)", _action_calib),
            item("⏱️ Toggle Pomodoro (Ctrl+Alt+P)", _action_pomo),
            item("🔔 Toggle Sunet Alerte (Ctrl+Alt+S)", _action_sound),
            item("🎨 Schimba Tema (O)", _action_theme),
            item("📁 Exporta CSV / JSON (E)", _action_export),
            Menu.SEPARATOR,
            item("📊 Deschide Raport Studiu", _action_report),
            item("❌ Iesire GazeAlert", _action_exit),
        )

        icon_img = create_tray_icon_image()
        self.icon = pystray.Icon("GazeAlert AI", icon_img, "GazeAlert - AI Study & Focus Suite", menu)
        self.is_running = True

        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def update_status(self, is_focused: bool, is_alert: bool):
        if self.icon is None:
            return
        try:
            if is_alert:
                col = (255, 40, 40)
            elif is_focused:
                col = (0, 255, 120)
            else:
                col = (255, 180, 0)
            self.icon.icon = create_tray_icon_image(col)
        except Exception:
            pass

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
        self.is_running = False
