import cv2
import time
import numpy as np
from gaze_detector import GazeDetector

def test_camera_detection():
    print("Testing GazeDetector with live camera...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[!] Cannot open camera 0!")
        return

    ret, frame = cap.read()
    if not ret or frame is None:
        print("[!] Cannot read frame from camera!")
        cap.release()
        return

    print(f"[+] Camera frame read success: shape {frame.shape}, dtype {frame.dtype}")
    
    detector = GazeDetector()
    print(f"[+] Task landmarker initialized: {detector.task_landmarker is not None}")
    
    for i in range(10):
        ret, frame = cap.read()
        if not ret:
            continue
        gaze = detector.process_frame(frame)
        print(f"Frame {i+1}: face_detected={gaze.face_detected}, is_looking={gaze.is_looking_at_screen}, state={gaze.smart_state}, yaw={gaze.head_yaw:.1f}, pitch={gaze.head_pitch:.1f}, reasons={gaze.reasons}")
        time.sleep(0.05)

    cap.release()
    print("Test complete!")

if __name__ == "__main__":
    test_camera_detection()
