import cv2
import time
from study_manager import ThreadedCamera
from gaze_detector import GazeDetector

def test_full_pipeline():
    print("Testing full camera + detector pipeline...")
    cam = ThreadedCamera(src=0, width=640, height=480, fps=30, use_mjpg=False)
    time.sleep(1.0)
    detector = GazeDetector()
    
    for i in range(15):
        ret, frame = cam.read()
        if ret and frame is not None:
            # Check frame properties
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = detector.mp_image(image_format=detector.mp_image_format.SRGB, data=rgb)
            det = detector.task_landmarker.detect(mp_img)
            num_faces = len(det.face_landmarks) if det.face_landmarks else 0
            
            gaze = detector.process_frame(frame)
            print(f"Frame {i+1}: w={w} h={h} | num_faces={num_faces} | face_detected={gaze.face_detected} | state={gaze.smart_state} | is_looking={gaze.is_looking_at_screen} | ear={gaze.left_ear:.2f}")
        else:
            print(f"Frame {i+1}: NO FRAME from camera")
        time.sleep(0.05)

    cam.release()

if __name__ == "__main__":
    test_full_pipeline()
