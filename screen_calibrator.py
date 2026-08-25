"""
9-Point Screen Calibration and Polynomial Gaze Mapping Model.
Maps head pose + iris feature vectors directly to 2D Screen Coordinates (X, Y).
"""

import json
import math
import os
import time
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np


def _get_writable_dir() -> str:
    try:
        local_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(local_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return local_dir
    except Exception:
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        target = os.path.join(appdata, "GazeAlert")
        os.makedirs(target, exist_ok=True)
        return target

CALIBRATION_FILE = os.path.join(_get_writable_dir(), "calibration_matrix.json")


class ScreenCalibrator:
    def __init__(self):
        # 9 Target points on normalized screen (0.0 to 1.0)
        self.target_points = [
            (0.15, 0.15),  # Top-Left
            (0.50, 0.15),  # Top-Center
            (0.85, 0.15),  # Top-Right
            (0.15, 0.50),  # Mid-Left
            (0.50, 0.50),  # Center
            (0.85, 0.50),  # Mid-Right
            (0.15, 0.85),  # Bottom-Left
            (0.50, 0.85),  # Bottom-Center
            (0.85, 0.85),  # Bottom-Right
        ]

        self.point_labels = [
            "Stanga-Sus", "Mijloc-Sus", "Dreapta-Sus",
            "Mijloc-Stanga", "Centru Ecran", "Mijloc-Dreapta",
            "Stanga-Jos", "Mijloc-Jos", "Dreapta-Jos"
        ]

        self.is_calibrating = False
        self.current_point_idx = 0
        self.samples_per_point = 20
        self.collected_features: List[List[float]] = []
        self.collected_targets: List[List[float]] = []

        self.weights_x: Optional[np.ndarray] = None
        self.weights_y: Optional[np.ndarray] = None
        self.is_calibrated = False

        self._point_start_time: float = 0.0
        self._current_point_samples: int = 0

        # Load saved calibration if available
        self.load_calibration()

    def _extract_polynomial_features(self, feat: List[float]) -> np.ndarray:
        """
        Input features: [yaw, pitch, roll, iris_lx, iris_ly, iris_rx, iris_ry, ipd]
        Generates 2nd degree polynomial terms + bias.
        """
        f = np.array(feat, dtype=np.float64)
        terms = [1.0] # Bias
        terms.extend(f.tolist()) # Linear terms

        # Key quadratic and cross terms
        # yaw^2, pitch^2, yaw*pitch, iris_lx^2, iris_ly^2
        if len(f) >= 8:
            yaw, pitch, roll = f[0], f[1], f[2]
            ilx, ily, irx, iry = f[3], f[4], f[5], f[6]
            terms.extend([
                yaw * yaw,
                pitch * pitch,
                yaw * pitch,
                ilx * ilx,
                ily * ily,
                yaw * ilx,
                pitch * ily
            ])
        return np.array(terms, dtype=np.float64)

    def start_calibration(self):
        """Begin 9-point calibration routine."""
        self.is_calibrating = True
        self.current_point_idx = 0
        self.collected_features.clear()
        self.collected_targets.clear()
        self._point_start_time = time.time()
        self._current_point_samples = 0
        print("[*] S-a initiat calibrarea in 9 puncte pe ecran. Priveste spre fiecare tinta!")

    def add_sample(self, raw_features: List[float]) -> bool:
        """
        Add a calibration sample for the current point.
        Returns True when entire 9-point calibration is complete.
        """
        if not self.is_calibrating:
            return False

        # Wait 0.5s settle time after switching points
        if time.time() - self._point_start_time < 0.5:
            return False

        target = self.target_points[self.current_point_idx]
        poly_feat = self._extract_polynomial_features(raw_features)

        self.collected_features.append(poly_feat.tolist())
        self.collected_targets.append(list(target))
        self._current_point_samples += 1

        # Advance to next point after collecting samples
        if self._current_point_samples >= self.samples_per_point:
            self.current_point_idx += 1
            self._current_point_samples = 0
            self._point_start_time = time.time()

            if self.current_point_idx >= len(self.target_points):
                # All 9 points completed -> Train regression model
                self._train_model()
                self.is_calibrating = False
                return True

        return False

    def _train_model(self):
        """Train Ridge Regression mapping from features to screen coordinates."""
        try:
            X = np.array(self.collected_features, dtype=np.float64)
            Y = np.array(self.collected_targets, dtype=np.float64)

            if len(X) < 10:
                return

            # Ridge regression: (X^T * X + lambda * I)^-1 * X^T * Y
            ridge_lambda = 1e-3
            n_features = X.shape[1]
            I = np.eye(n_features)
            I[0, 0] = 0.0  # Do not regularize bias term

            XtX = X.T @ X + ridge_lambda * I
            XtY = X.T @ Y

            W = np.linalg.solve(XtX, XtY)
            self.weights_x = W[:, 0]
            self.weights_y = W[:, 1]
            self.is_calibrated = True

            self.save_calibration()
            print("[+] Antrenare finalizata cu succes! Modelul de privire pe ecran este activ.")
        except Exception as e:
            print(f"[!] Eroare la antrenarea calibrarii: {e}")

    def predict_screen_pos(self, raw_features: List[float]) -> Optional[Tuple[float, float]]:
        """Predict normalized screen coordinates (0.0 - 1.0) from current features."""
        if not self.is_calibrated or self.weights_x is None or self.weights_y is None:
            return None
        try:
            poly = self._extract_polynomial_features(raw_features)
            sx = float(poly @ self.weights_x)
            sy = float(poly @ self.weights_y)
            return sx, sy
        except Exception:
            return None

    def save_calibration(self):
        if not self.is_calibrated or self.weights_x is None:
            return
        data = {
            "weights_x": self.weights_x.tolist(),
            "weights_y": self.weights_y.tolist(),
            "timestamp": time.time(),
        }
        try:
            with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[+] Calibrarea a fost salvata in {CALIBRATION_FILE}")
        except Exception as e:
            print(f"[!] Salvare calibrare esuata: {e}")

    def load_calibration(self) -> bool:
        if not os.path.exists(CALIBRATION_FILE):
            return False
        try:
            with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.weights_x = np.array(data["weights_x"], dtype=np.float64)
                self.weights_y = np.array(data["weights_y"], dtype=np.float64)
                self.is_calibrated = True
                print("[+] Calibrare anterioara incarcata cu succes din disc!")
                return True
        except Exception:
            return False

    def draw_calibration_overlay(self, frame: np.ndarray):
        """Draw animated calibration target on frame."""
        if not self.is_calibrating or self.current_point_idx >= len(self.target_points):
            return

        h, w = frame.shape[:2]
        tx, ty = self.target_points[self.current_point_idx]
        px, py = int(tx * w), int(ty * h)

        # Pulse animation
        pulse = int(12 + 6 * math.sin(time.time() * 8))
        label = self.point_labels[self.current_point_idx]
        progress_str = f"Punct {self.current_point_idx + 1}/9: {label} ({self._current_point_samples}/{self.samples_per_point})"

        # Background dim
        cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 0), -1)

        # Target concentric rings
        cv2.circle(frame, (px, py), pulse + 12, (0, 100, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (px, py), pulse, (0, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 4, (0, 0, 255), -1, cv2.LINE_AA)

        # Guidance text
        cv2.putText(frame, "CALIBRARE PRIVIRE PE ECRAN", (w // 2 - 190, 40), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Priveste fix tinta portocalie/galbena!", (w // 2 - 180, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, progress_str, (w // 2 - 170, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 100), 2, cv2.LINE_AA)
