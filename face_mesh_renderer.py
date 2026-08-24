"""
High-Precision Facial Contours & Landmark Indices for MediaPipe 478 FaceMesh.
Provides exact connected contour loops for Eyes, Irises, Eyebrows, Lips, Nose, and Face Oval.
"""

from typing import List, Tuple
import cv2
import numpy as np

# Anatomical FaceMesh Contours (MediaPipe 468/478 Canonical Indices)
LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185, 61]
LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191, 78]

LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33]
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 362]

LEFT_EYEBROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
RIGHT_EYEBROW = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]

NOSE_BRIDGE = [168, 6, 197, 195, 5, 4, 1]
NOSE_BASE = [98, 97, 2, 326, 327]

FACE_OVAL = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365,
    379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93,
    234, 127, 162, 21, 54, 103, 67, 109, 10
]

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


def draw_face_mesh_contours(frame: np.ndarray, landmarks_2d: np.ndarray, scale: float = 1.0):
    """Draw continuous Hollywood/FaceID style glowing contours on the face."""
    if landmarks_2d is None or len(landmarks_2d) < 468:
        return

    pts = landmarks_2d.astype(np.int32)
    th = max(1, int(1.2 * scale))

    # 1. Face Oval / Jawline
    oval_pts = pts[FACE_OVAL]
    cv2.polylines(frame, [oval_pts], isClosed=True, color=(120, 120, 120), thickness=th, lineType=cv2.LINE_AA)

    # 2. Eyebrows
    l_brow = pts[LEFT_EYEBROW]
    r_brow = pts[RIGHT_EYEBROW]
    cv2.polylines(frame, [l_brow], isClosed=False, color=(0, 220, 255), thickness=th, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [r_brow], isClosed=False, color=(0, 220, 255), thickness=th, lineType=cv2.LINE_AA)

    # 3. Eyes (Outer loops)
    l_eye = pts[LEFT_EYE]
    r_eye = pts[RIGHT_EYE]
    cv2.polylines(frame, [l_eye], isClosed=True, color=(0, 255, 255), thickness=th + 1, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [r_eye], isClosed=True, color=(0, 255, 255), thickness=th + 1, lineType=cv2.LINE_AA)

    # 4. Nose Bridge & Base
    nose_b = pts[NOSE_BRIDGE]
    nose_base = pts[NOSE_BASE]
    cv2.polylines(frame, [nose_b], isClosed=False, color=(0, 200, 255), thickness=th, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [nose_base], isClosed=False, color=(0, 200, 255), thickness=th, lineType=cv2.LINE_AA)

    # 5. Lips
    lips_o = pts[LIPS_OUTER]
    lips_i = pts[LIPS_INNER]
    cv2.polylines(frame, [lips_o], isClosed=True, color=(255, 120, 180), thickness=th, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [lips_i], isClosed=True, color=(200, 80, 140), thickness=th, lineType=cv2.LINE_AA)

    # 6. Iris Contours & Pupil Core
    if len(landmarks_2d) > 473:
        l_iris = pts[LEFT_IRIS]
        r_iris = pts[RIGHT_IRIS]
        # Draw iris circles
        cv2.polylines(frame, [l_iris[1:]], isClosed=True, color=(0, 255, 120), thickness=th, lineType=cv2.LINE_AA)
        cv2.polylines(frame, [r_iris[1:]], isClosed=True, color=(0, 255, 120), thickness=th, lineType=cv2.LINE_AA)
        
        # Draw pupil core & corneal glint
        cv2.circle(frame, tuple(l_iris[0]), int(3.5 * scale), (20, 20, 20), -1, cv2.LINE_AA)
        cv2.circle(frame, tuple(r_iris[0]), int(3.5 * scale), (20, 20, 20), -1, cv2.LINE_AA)
        cv2.circle(frame, tuple(l_iris[0]), int(3.5 * scale), (0, 255, 0), 1, cv2.LINE_AA)
        cv2.circle(frame, tuple(r_iris[0]), int(3.5 * scale), (0, 255, 0), 1, cv2.LINE_AA)
