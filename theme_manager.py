"""
Theme Manager for GazeAlert UI.
Provides tailored modern color palettes for Dark, Light, Cyberpunk, and Warm Amber modes.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class UITheme:
    name: str
    label: str
    bg_panel: Tuple[int, int, int]         # BGR format for OpenCV
    border_panel: Tuple[int, int, int]
    text_primary: Tuple[int, int, int]
    text_secondary: Tuple[int, int, int]
    focus_color: Tuple[int, int, int]
    warning_color: Tuple[int, int, int]
    alert_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    is_light: bool = False


THEMES: Dict[str, UITheme] = {
    "cyber_dark": UITheme(
        name="cyber_dark",
        label="Cyber Dark (Neon)",
        bg_panel=(15, 18, 22),
        border_panel=(60, 70, 80),
        text_primary=(255, 255, 255),
        text_secondary=(180, 190, 200),
        focus_color=(0, 255, 120),       # Neon Emerald
        warning_color=(0, 180, 255),     # Electric Amber
        alert_color=(50, 50, 255),       # Vibrant Coral Red
        accent_color=(255, 220, 0),      # Cyan
        is_light=False
    ),
    "nord_slate": UITheme(
        name="nord_slate",
        label="Nord Frost (Slate)",
        bg_panel=(40, 32, 28),
        border_panel=(80, 70, 65),
        text_primary=(240, 245, 250),
        text_secondary=(170, 180, 195),
        focus_color=(220, 200, 140),     # Nordic Frost Blue
        warning_color=(120, 200, 240),
        alert_color=(100, 110, 230),
        accent_color=(210, 180, 130),
        is_light=False
    ),
    "warm_amber": UITheme(
        name="warm_amber",
        label="Warm Amber (Anti-Fatigue)",
        bg_panel=(18, 24, 32),
        border_panel=(45, 65, 85),
        text_primary=(220, 235, 250),
        text_secondary=(140, 170, 200),
        focus_color=(80, 200, 255),      # Warm Golden Glow
        warning_color=(50, 140, 245),
        alert_color=(70, 80, 240),
        accent_color=(100, 210, 255),
        is_light=False
    ),
    "clean_light": UITheme(
        name="clean_light",
        label="Clean Light Mode",
        bg_panel=(245, 245, 248),
        border_panel=(200, 200, 210),
        text_primary=(30, 30, 35),
        text_secondary=(90, 95, 105),
        focus_color=(50, 160, 0),        # Forest Green
        warning_color=(0, 130, 220),     # Deep Orange
        alert_color=(20, 20, 210),       # Bold Red
        accent_color=(180, 90, 0),       # Royal Blue
        is_light=True
    )
}


class ThemeManager:
    """Manages active UI themes and switching."""
    def __init__(self, default_theme: str = "cyber_dark"):
        self.theme_keys = list(THEMES.keys())
        self.current_idx = self.theme_keys.index(default_theme) if default_theme in THEMES else 0

    @property
    def current(self) -> UITheme:
        return THEMES[self.theme_keys[self.current_idx]]

    def cycle_theme(self) -> UITheme:
        self.current_idx = (self.current_idx + 1) % len(self.theme_keys)
        return self.current

    def set_theme(self, name: str) -> bool:
        if name in THEMES:
            self.current_idx = self.theme_keys.index(name)
            return True
        return False
