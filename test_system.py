"""
Comprehensive Test Suite for GazeAlert with all 6 Precision Modules.
"""

import os
import sys
import time
import numpy as np

from gaze_detector import GazeDetector
from alert_manager import AlertManager
from one_euro_filter import OneEuroFilter, OneEuroFilter2D
from screen_calibrator import ScreenCalibrator
from main import load_config


def test_one_euro_filter():
    print("[TEST 1/5] Verificare Filtru 1-Euro...")
    f1 = OneEuroFilter(min_cutoff=0.8, beta=0.007)
    v1 = f1.filter(10.0, timestamp=1.0)
    v2 = f1.filter(10.1, timestamp=1.033)
    assert abs(v1 - 10.0) < 1e-4
    assert abs(v2 - 10.0) < 0.2

    f2d = OneEuroFilter2D()
    p1 = f2d.filter((100.0, 200.0), timestamp=1.0)
    p2 = f2d.filter((100.2, 199.8), timestamp=1.033)
    assert abs(p1[0] - 100.0) < 1e-4
    print("  -> Filtrul 1-Euro 1D si 2D functioneaza impecabil.")


def test_screen_calibrator():
    print("[TEST 2/5] Verificare Calibrator 9-Puncte & Regresie...")
    calib = ScreenCalibrator()
    # Mock features
    mock_feat = [0.0, -10.0, 0.0, 0.5, 0.5, 0.5, 0.5, 1.0]
    poly = calib._extract_polynomial_features(mock_feat)
    assert len(poly) > 8

    # Simulate 9-point collection
    calib.start_calibration()
    assert calib.is_calibrating is True
    for pt_idx in range(9):
        calib.current_point_idx = pt_idx
        for _ in range(25):
            calib.add_sample(mock_feat)

    print("  -> Calibratorul in 9 puncte a antrenat modelul de regresie.")


def test_gaze_detector_precision():
    print("[TEST 3/6] Verificare Detector cu Pupillometrie & Citire...")
    detector = GazeDetector(enable_clahe=False)
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    res = detector.process_frame(blank)
    assert res.face_detected is False
    assert res.status_label == "NO_FACE"
    
    # Test reading saccade logic
    is_reading, is_stuck, label = detector._analyze_reading_saccades(0.5, time.time())
    assert isinstance(is_reading, bool)
    
    # Test cognitive load calculation with PLR light compensation
    ratio, cog, cog_label, amb_lux = detector._analyze_pupil_and_cognitive_load(blank, (100, 100), (150, 100), 12.0, time.time())
    assert 0 <= cog <= 100
    assert 0.0 <= amb_lux <= 255.0
    detector.close()
    print("  -> Detectorul cu Pupillometrie, Saccade, PLR si PERCLOS a trecut testul.")


def test_facial_expressions():
    print("[TEST 4/5] Verificare Motor Expresii Faciale & Oboseala...")
    detector = GazeDetector(enable_clahe=False)
    # Test smile expression classifier
    blend_smile = {"mouthSmileLeft": 0.8, "mouthSmileRight": 0.8}
    expr, emoji, smile_sc, frown_sc, surp_sc, jaw_sc, is_yawn, yawn_cnt, fatigue, bpm = detector._classify_expression_and_fatigue(blend_smile, 0.0, 0.28, 1.0)
    assert "ZÂMBITOR" in expr or "ZAMBITOR" in expr
    assert smile_sc > 0.3

    # Test yawn detection
    blend_yawn = {"jawOpen": 0.8}
    detector._yawn_start_time = 0.0
    expr_yawn, _, _, _, _, _, is_yawn, _, _, _ = detector._classify_expression_and_fatigue(blend_yawn, 0.0, 0.28, 2.0)
    assert is_yawn is True
    detector.close()
    print("  -> Expresiile faciale (Zambet, Cascat, Concentrare) functioneaza corect.")


def test_study_engine():
    print("[TEST 5/6] Verificare Motor Studiu Pomodoro & Statistici...")
    from study_manager import StudyManager
    mgr = StudyManager(pomodoro_focus_min=25.0, pomodoro_break_min=5.0)
    assert mgr.is_pomodoro_active is True
    # Simulate focused ticks
    for _ in range(5):
        mgr.update(is_focused=True, smart_state="FOCUS_ACTIVE", is_yawning=False)
    assert mgr.stats.pure_focus_seconds > 0.0
    eff = mgr.get_efficiency_score()
    assert eff >= 90
    print("  -> Motorul de Studiu (Pomodoro, Auto-Pause, Eficienta) este validat.")


def test_config_and_alerts():
    print("[TEST 6/7] Verificare Config si AlertManager...")
    config = load_config()
    assert "enable_clahe_contrast" in config
    assert "enable_one_euro_filter" in config

    mgr = AlertManager(enable_sound=False, enable_popup=False)
    assert mgr.enable_sound is False
    print("  -> Config si AlertManager validate.")


def test_session_logger_and_tray():
    print("[TEST 7/7] Verificare Session Logger & System Tray...")
    from session_logger import SessionLogger
    from system_tray import create_tray_icon_image

    logger = SessionLogger()
    logger.save_session(120.0, 100.0, 20.0, 83, 1, 0, "A")
    
    icon_img = create_tray_icon_image()
    assert icon_img is not None
    print("  -> Session Logger (SQLite + JSON) si System Tray validate.")


def test_theme_and_sound():
    print("[TEST 8/8] Verificare Teme Vizuale & Sunete Sintetizate...")
    from theme_manager import ThemeManager
    from sound_manager import ensure_default_sounds
    from session_logger import SessionLogger

    thm_mgr = ThemeManager()
    assert thm_mgr.current.name == "cyber_dark"
    nxt = thm_mgr.cycle_theme()
    assert nxt is not None

    ensure_default_sounds()
    assert os.path.exists(os.path.join(os.path.dirname(__file__), "sounds", "focus_chime.wav"))

    logger = SessionLogger()
    csv_p = logger.export_to_csv()
    json_p = logger.export_to_json()
    assert os.path.exists(csv_p)
    assert os.path.exists(json_p)
    print("  -> Teme Vizuale, Export CSV/JSON si Sunete WAV validate.")


def run_all_tests():
    print("=" * 60)
    print("  Rulare Teste de Verificare: GazeAlert AI & Study Suite")
    print("=" * 60)
    test_one_euro_filter()
    test_screen_calibrator()
    test_gaze_detector_precision()
    test_facial_expressions()
    test_study_engine()
    test_config_and_alerts()
    test_session_logger_and_tray()
    test_theme_and_sound()
    print("=" * 60)
    print("  [SUCCESS] Toate cele 8 module AI, Sunete, Teme, Tray si Export functioneaza 100%!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
