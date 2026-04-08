import cv2
import mediapipe_compat  # Apply compatibility patches (from venv site-packages)
import mediapipe as mp
import numpy as np
import json
import sys
from pathlib import Path

def extract_coordinates_from_video(video_path, output_json_path):
    """Extract coordinates from video and save as JSON

    Args:
        video_path: Path to input video file
        output_json_path: Path to save coordinates.json

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # MediaPipe Pose
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose()

        # MediaPipe Face Mesh (for eye/head gaze)
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)

        # JSON structure
        data = {
            "$id": str(video_path),
            "frame_rate": fps,
            "eye_gaze": {"rx": [], "ry": [], "rz": []},
            "head_gaze": {"rx": [], "ry": [], "rz": []},
            "skeleton": {
                "elbow_left": {"confidence": [], "x": [], "y": [], "z": []},
                "elbow_right": {"confidence": [], "x": [], "y": [], "z": []},
                "hand_left": {"confidence": [], "x": [], "y": [], "z": []},
                "hand_right": {"confidence": [], "x": [], "y": [], "z": []},
                "head": {"confidence": [], "x": [], "y": [], "z": []},
                "sholder_center": {"confidence": [], "x": [], "y": [], "z": []},
                "sholder_left": {"confidence": [], "x": [], "y": [], "z": []},
                "sholder_right": {"confidence": [], "x": [], "y": [], "z": []},
                "wrist_left": {"confidence": [], "x": [], "y": [], "z": []},
                "wrist_right": {"confidence": [], "x": [], "y": [], "z": []}
            }
        }

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            mesh_results = face_mesh.process(rgb)

            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark

                def add_point(name, landmark):
                    data["skeleton"][name]["x"].append(landmark.x)
                    data["skeleton"][name]["y"].append(landmark.y)
                    data["skeleton"][name]["z"].append(landmark.z)
                    data["skeleton"][name]["confidence"].append(landmark.visibility)

                # Head
                add_point("head", lm[mp_pose.PoseLandmark.NOSE])

                # Shoulders
                add_point("sholder_left", lm[mp_pose.PoseLandmark.LEFT_SHOULDER])
                add_point("sholder_right", lm[mp_pose.PoseLandmark.RIGHT_SHOULDER])

                # Shoulder center
                l = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
                r = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]

                data["skeleton"]["sholder_center"]["x"].append((l.x + r.x) / 2)
                data["skeleton"]["sholder_center"]["y"].append((l.y + r.y) / 2)
                data["skeleton"]["sholder_center"]["z"].append((l.z + r.z) / 2)
                data["skeleton"]["sholder_center"]["confidence"].append((l.visibility + r.visibility) / 2)

                # Elbows
                add_point("elbow_left", lm[mp_pose.PoseLandmark.LEFT_ELBOW])
                add_point("elbow_right", lm[mp_pose.PoseLandmark.RIGHT_ELBOW])

                # Wrists
                add_point("wrist_left", lm[mp_pose.PoseLandmark.LEFT_WRIST])
                add_point("wrist_right", lm[mp_pose.PoseLandmark.RIGHT_WRIST])

                # Hands (using index finger)
                # add_point("hand_left", lm[mp_pose.PoseLandmark.LEFT_INDEX])
                # add_point("hand_right", lm[mp_pose.PoseLandmark.RIGHT_INDEX])

            if mesh_results and mesh_results.multi_face_landmarks:
                mesh_lm = mesh_results.multi_face_landmarks[0].landmark
                h, w, _ = frame.shape
                def to_vec(idx): return np.array([mesh_lm[idx].x * w, mesh_lm[idx].y * h, mesh_lm[idx].z * w])

                nose = to_vec(1)
                chin = to_vec(152)
                left_eye = to_vec(33)
                right_eye = to_vec(263)

                # 1. Head Pose (Pitch, Yaw, Roll)
                x_axis = right_eye - left_eye
                x_axis = x_axis / np.linalg.norm(x_axis)
                v = chin - nose
                v = v / np.linalg.norm(v)
                z_axis = np.cross(x_axis, v)
                z_axis = z_axis / np.linalg.norm(z_axis)
                y_axis = np.cross(z_axis, x_axis)

                R = np.column_stack((x_axis, y_axis, z_axis))
                sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])

                if sy > 1e-6:
                    rx = np.arctan2(R[2,1], R[2,2])
                    ry = np.arctan2(-R[2,0], sy)
                    rz = np.arctan2(R[1,0], R[0,0])
                else:
                    rx = np.arctan2(-R[1,2], R[1,1])
                    ry = np.arctan2(-R[2,0], sy)
                    rz = 0

                data["head_gaze"]["rx"].append(float(np.degrees(rx)))
                data["head_gaze"]["ry"].append(float(np.degrees(ry)))
                data["head_gaze"]["rz"].append(float(np.degrees(rz)))

                # 2. Eye Gaze (Iris offset relative to eye center)
                left_iris = to_vec(473)
                left_eye_center = (left_eye + to_vec(133)) / 2
                right_iris = to_vec(468)
                right_eye_center = (right_eye + to_vec(362)) / 2

                eye_vec = ((left_iris - left_eye_center) + (right_iris - right_eye_center)) / 2.0
                eb_radius = np.linalg.norm(right_eye - left_eye) / 4.0

                e_rx = np.arctan2(eye_vec[1], eb_radius)
                e_ry = np.arctan2(eye_vec[0], eb_radius)

                data["eye_gaze"]["rx"].append(float(np.degrees(e_rx)))
                data["eye_gaze"]["ry"].append(float(np.degrees(e_ry)))
                data["eye_gaze"]["rz"].append(0.0)
            else:
                # Default fallback values
                data["head_gaze"]["rx"].append(0.0)
                data["head_gaze"]["ry"].append(0.0)
                data["head_gaze"]["rz"].append(0.0)
                data["eye_gaze"]["rx"].append(0.0)
                data["eye_gaze"]["ry"].append(0.0)
                data["eye_gaze"]["rz"].append(0.0)

        cap.release()

        # Ensure output directory exists
        Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)

        # Save JSON
        with open(output_json_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"✅ Coordinates extracted: {output_json_path} ({frame_count} frames)")
        return True

    except Exception as e:
        print(f"❌ Coordinate extraction error: {e}")
        return False


# Allow script to be run standalone for testing
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python video_to_coordinates.py <video_path> <output_json_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    output_json_path = sys.argv[2]

    success = extract_coordinates_from_video(video_path, output_json_path)
    sys.exit(0 if success else 1)
