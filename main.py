"""
GazeAlert Studio - All-in-One Desktop AI Eye Tracking & Productivity Suite.
Integrates Live Webcam AI Feed, Telemetry, and Interactive Control Hub in a Single Unified Window.
Run with: python main.py or run.bat
"""

import json
import os
import sys
from typing import Any, Dict
from unified_app import UnifiedGazeApp


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
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
        "eye_open_ratio_threshold": 0.12,
        "iris_gaze_threshold_min": 0.20,
        "iris_gaze_threshold_max": 0.80,
        "enable_clahe_contrast": False,
        "enable_one_euro_filter": True,
        "enable_sound_alert": True,
        "enable_desktop_popup": True,
        "theme": "cyber_dark",
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults


def main():
    app = UnifiedGazeApp()
    app.start_loop()


if __name__ == "__main__":
    main()
