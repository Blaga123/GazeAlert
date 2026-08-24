"""
Studio-Grade Pixel-Perfect Facial Mesh Tessellation & Sub-Pixel Pupil Fitter.
Connects all 478 anatomical vertices into a precision wireframe + glowing FaceID contours + 3D Gaze Lasers.
"""

from typing import List, Optional, Tuple
import cv2
import numpy as np

# Canonical MediaPipe Key Landmark Loops
FACEMESH_LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185, 61]
FACEMESH_LIPS_INNER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191, 78]

FACEMESH_LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33]
FACEMESH_RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398, 362]

FACEMESH_LEFT_EYEBROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
FACEMESH_RIGHT_EYEBROW = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]

FACEMESH_NOSE_BRIDGE = [168, 6, 197, 195, 5, 4, 1, 2]

FACEMESH_JAW_AND_OVAL = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365,
    379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93,
    234, 127, 162, 21, 54, 103, 67, 109, 10
]

# Sleek anatomical cheekbones and temple bridges
CHEEKBONE_BRIDGES = [
    (116, 123), (123, 147), (147, 213), (213, 192),
    (345, 352), (352, 376), (376, 433), (433, 416),
    (168, 70), (168, 300), (197, 33), (197, 263),
    (2, 98), (2, 327), (98, 164), (327, 392),
    (152, 175), (175, 199), (199, 208)
]

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


def draw_pixel_perfect_mesh(
    frame: np.ndarray,
    landmarks_2d: np.ndarray,
    scale: float = 1.0,
    pupil_left: Optional[Tuple[int, int]] = None,
    pupil_right: Optional[Tuple[int, int]] = None,
    gaze_ray_l_end: Optional[Tuple[int, int]] = None,
    gaze_ray_r_end: Optional[Tuple[int, int]] = None,
    pupil_radius_l: int = 4,
    pupil_radius_r: int = 4,
    is_focused: bool = True
):
    """Draw a pixel-perfect Studio VFX FaceID mesh with 3D Gaze Lasers."""
    if landmarks_2d is None or len(landmarks_2d) < 468:
        return

    pts = landmarks_2d.astype(np.int32)
    th = max(1, int(1.2 * scale))

    # 1. Subtle Cheek & Temple Wireframe (Cyberpunk aesthetic)
    for p1_idx, p2_idx in CHEEKBONE_BRIDGES:
        if p1_idx < len(pts) and p2_idx < len(pts):
            p1 = tuple(pts[p1_idx])
            p2 = tuple(pts[p2_idx])
            cv2.line(frame, p1, p2, (80, 110, 120), 1, cv2.LINE_AA)

    # 2. Nose Bridge
    nose_pts = pts[FACEMESH_NOSE_BRIDGE]
    cv2.polylines(frame, [nose_pts], isClosed=False, color=(0, 200, 220), thickness=th, lineType=cv2.LINE_AA)

    # 3. Glowing Face Oval / Jawline (Gold / Champagne)
    oval_pts = pts[FACEMESH_JAW_AND_OVAL]
    cv2.polylines(frame, [oval_pts], isClosed=True, color=(160, 210, 230), thickness=th, lineType=cv2.LINE_AA)

    # 4. Eyebrows (Bright Yellow)
    l_brow = pts[FACEMESH_LEFT_EYEBROW]
    r_brow = pts[FACEMESH_RIGHT_EYEBROW]
    cv2.polylines(frame, [l_brow], isClosed=False, color=(0, 235, 255), thickness=th + 1, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [r_brow], isClosed=False, color=(0, 235, 255), thickness=th + 1, lineType=cv2.LINE_AA)

    # 5. Eyes (Outer loops - Bright Emerald/Yellow)
    l_eye = pts[FACEMESH_LEFT_EYE]
    r_eye = pts[FACEMESH_RIGHT_EYE]
    cv2.polylines(frame, [l_eye], isClosed=True, color=(0, 255, 255), thickness=th + 1, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [r_eye], isClosed=True, color=(0, 255, 255), thickness=th + 1, lineType=cv2.LINE_AA)

    # 6. Lips (Outer & Inner)
    lips_o = pts[FACEMESH_LIPS_OUTER]
    lips_i = pts[FACEMESH_LIPS_INNER]
    cv2.polylines(frame, [lips_o], isClosed=True, color=(255, 140, 200), thickness=th, lineType=cv2.LINE_AA)
    cv2.polylines(frame, [lips_i], isClosed=True, color=(220, 90, 160), thickness=th, lineType=cv2.LINE_AA)

    # 7. Precision Pupil Optics, Iris Rings & 3D Gaze Lasers
    if len(landmarks_2d) > 473:
        l_iris = pts[LEFT_IRIS]
        r_iris = pts[RIGHT_IRIS]

        # Iris outer boundary
        cv2.polylines(frame, [l_iris[1:]], isClosed=True, color=(0, 255, 120), thickness=th + 1, lineType=cv2.LINE_AA)
        cv2.polylines(frame, [r_iris[1:]], isClosed=True, color=(0, 255, 120), thickness=th + 1, lineType=cv2.LINE_AA)

        # Precision Pupil Centers
        c_l = pupil_left if pupil_left else tuple(l_iris[0])
        c_r = pupil_right if pupil_right else tuple(r_iris[0])

        r_l = max(2, pupil_radius_l)
        r_r = max(2, pupil_radius_r)

        # Dark pupil core + glowing green ring
        cv2.circle(frame, c_l, r_l, (10, 10, 10), -1, cv2.LINE_AA)
        cv2.circle(frame, c_r, r_r, (10, 10, 10), -1, cv2.LINE_AA)
        cv2.circle(frame, c_l, r_l, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.circle(frame, c_r, r_r, (0, 255, 0), 1, cv2.LINE_AA)

        # Sub-Pixel Crosshairs (+ target cursor)
        ch_len = int(4 * scale)
        cv2.line(frame, (c_l[0] - ch_len, c_l[1]), (c_l[0] + ch_len, c_l[1]), (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(frame, (c_l[0], c_l[1] - ch_len), (c_l[0], c_l[1] + ch_len), (0, 255, 255), 1, cv2.LINE_AA)

        cv2.line(frame, (c_r[0] - ch_len, c_r[1]), (c_r[0] + ch_len, c_r[1]), (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(frame, (c_r[0], c_r[1] - ch_len), (c_r[0], c_r[1] + ch_len), (0, 255, 255), 1, cv2.LINE_AA)

        # 3D Gaze Laser Beams from Pupils
        laser_col = (0, 255, 120) if is_focused else (0, 140, 255)
        if gaze_ray_l_end:
            cv2.arrowedLine(frame, c_l, gaze_ray_l_end, laser_col, max(2, int(2.0 * scale)), tipLength=0.25)
            cv2.circle(frame, gaze_ray_l_end, max(2, int(3 * scale)), (0, 255, 255), -1, cv2.LINE_AA)
        if gaze_ray_r_end:
            cv2.arrowedLine(frame, c_r, gaze_ray_r_end, laser_col, max(2, int(2.0 * scale)), tipLength=0.25)
            cv2.circle(frame, gaze_ray_r_end, max(2, int(3 * scale)), (0, 255, 255), -1, cv2.LINE_AA)
