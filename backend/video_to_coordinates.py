import cv2
import mediapipe_compat  # Apply compatibility patches when legacy solutions API is unavailable.
import mediapipe as mp
import numpy as np
import json
from pathlib import Path


def normalize(v):
    norm = np.linalg.norm(v)
    return v / norm if norm != 0 else v


def _flatten_rotation_vector(rotation_vector):
    try:
        values = np.array(rotation_vector, dtype=np.float32).reshape(-1).tolist()
        if len(values) >= 3:
            return float(values[0]), float(values[1]), float(values[2])
    except Exception:
        pass
    return 0.0, 0.0, 0.0


def _convert_dream_frames_to_pipeline_json(all_frames, frame_rate, video_path):
    data = {
        "$id": str(video_path),
        "frame_rate": frame_rate,
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
            "wrist_right": {"confidence": [], "x": [], "y": [], "z": []},
        },
    }

    joint_name_map = {
        "head": "head",
        "sholder_center": "neck",
        "sholder_left": "l_shoulder",
        "sholder_right": "r_shoulder",
        "elbow_left": "l_elbow",
        "elbow_right": "r_elbow",
        "wrist_left": "l_wrist",
        "wrist_right": "r_wrist",
        "hand_left": "l_hand",
        "hand_right": "r_hand",
    }

    for frame_data in all_frames:
        frame_skeleton = frame_data.get("skeleton", [])
        points = {
            item.get("joint"): (float(item.get("x", 0.0)), float(item.get("y", 0.0)))
            for item in frame_skeleton
            if item.get("joint")
        }

        for target_name, source_name in joint_name_map.items():
            px, py = points.get(source_name, (0.0, 0.0))
            data["skeleton"][target_name]["x"].append(px)
            data["skeleton"][target_name]["y"].append(py)
            data["skeleton"][target_name]["z"].append(0.0)
            data["skeleton"][target_name]["confidence"].append(1.0 if source_name in points else 0.0)

        eye_gaze = frame_data.get("eye_gaze_vector", {})
        data["eye_gaze"]["rx"].append(float(eye_gaze.get("x", 0.0)))
        data["eye_gaze"]["ry"].append(float(eye_gaze.get("y", 0.0)))
        data["eye_gaze"]["rz"].append(0.0)

        rotation_vector = frame_data.get("head_pose", {}).get("rotation_vector", [0.0, 0.0, 0.0])
        rx, ry, rz = _flatten_rotation_vector(rotation_vector)
        data["head_gaze"]["rx"].append(rx)
        data["head_gaze"]["ry"].append(ry)
        data["head_gaze"]["rz"].append(rz)

    return data


def extract_coordinates_from_video(video_path, output_json_path, progress_callback=None):
    """Run the exact holistic extraction flow and save both dream-style and pipeline-compatible outputs.

    Args:
        video_path: Path to input video file
        output_json_path: Path to save pipeline-compatible coordinates JSON
        progress_callback: Optional callback(percent, message)

    Returns:
        bool: True on success, False otherwise
    """
    try:
        def report_progress(percent, message):
            if not callable(progress_callback):
                return
            try:
                progress_callback(float(percent), message)
            except Exception:
                pass

        mp_holistic = mp.solutions.holistic
        holistic = mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            refine_face_landmarks=True,
        )

        output_json = Path(output_json_path)
        output_json.parent.mkdir(parents=True, exist_ok=True)

        out_dream_json = output_json.parent / "dream_output.json"
        out_skel_path = output_json.parent / "skeleton.mp4"
        out_eye_path = output_json.parent / "eye.mp4"
        out_head_path = output_json.parent / "head.mp4"

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}")

        width = int(cap.get(3))
        height = int(cap.get(4))
        fps = int(cap.get(5))
        if fps <= 0:
            fps = 25

        frame_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        last_bucket = -1

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        out_skel = cv2.VideoWriter(str(out_skel_path), fourcc, fps, (width, height))
        out_eye = cv2.VideoWriter(str(out_eye_path), fourcc, fps, (width, height))
        out_head = cv2.VideoWriter(str(out_head_path), fourcc, fps, (width, height))

        all_frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)

            frame_skel = frame.copy()
            frame_eye = frame.copy()
            frame_head = frame.copy()

            frame_data = {
                "skeleton": [],
                "eye_gaze_vector": {},
                "head_pose": {},
            }

            # Skeleton
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark

                head = np.array([lm[0].x, lm[0].y])
                l_sh = np.array([lm[11].x, lm[11].y])
                r_sh = np.array([lm[12].x, lm[12].y])
                l_el = np.array([lm[13].x, lm[13].y])
                r_el = np.array([lm[14].x, lm[14].y])
                l_wr = np.array([lm[15].x, lm[15].y])
                r_wr = np.array([lm[16].x, lm[16].y])

                neck = (l_sh + r_sh) / 2

                if results.left_hand_landmarks:
                    l_hand = np.mean([[p.x, p.y] for p in results.left_hand_landmarks.landmark], axis=0)
                else:
                    l_hand = l_wr

                if results.right_hand_landmarks:
                    r_hand = np.mean([[p.x, p.y] for p in results.right_hand_landmarks.landmark], axis=0)
                else:
                    r_hand = r_wr

                joints = {
                    "head": head,
                    "neck": neck,
                    "l_shoulder": l_sh,
                    "r_shoulder": r_sh,
                    "l_elbow": l_el,
                    "r_elbow": r_el,
                    "l_wrist": l_wr,
                    "r_wrist": r_wr,
                    "l_hand": l_hand,
                    "r_hand": r_hand,
                }

                for name, v in joints.items():
                    frame_data["skeleton"].append(
                        {
                            "joint": name,
                            "x": float(v[0]),
                            "y": float(v[1]),
                        }
                    )

                for v in joints.values():
                    cv2.circle(frame_skel, (int(v[0] * width), int(v[1] * height)), 5, (0, 0, 255), -1)

                connections = [
                    ("neck", "head"),
                    ("neck", "l_shoulder"),
                    ("neck", "r_shoulder"),
                    ("l_shoulder", "l_elbow"),
                    ("l_elbow", "l_wrist"),
                    ("l_wrist", "l_hand"),
                    ("r_shoulder", "r_elbow"),
                    ("r_elbow", "r_wrist"),
                    ("r_wrist", "r_hand"),
                ]

                for a, b in connections:
                    p1 = joints[a]
                    p2 = joints[b]
                    cv2.line(
                        frame_skel,
                        (int(p1[0] * width), int(p1[1] * height)),
                        (int(p2[0] * width), int(p2[1] * height)),
                        (255, 255, 255),
                        2,
                    )

            # Eye gaze
            if results.face_landmarks:
                h, w, _ = frame.shape

                left_eye = results.face_landmarks.landmark[33]
                right_eye = results.face_landmarks.landmark[263]

                left_eye_px = np.array([left_eye.x * w, left_eye.y * h])
                right_eye_px = np.array([right_eye.x * w, right_eye.y * h])

                eye_center = (left_eye_px + right_eye_px) / 2

                l_iris = results.face_landmarks.landmark[468]
                r_iris = results.face_landmarks.landmark[473]

                iris_center = np.array(
                    [
                        ((l_iris.x + r_iris.x) / 2) * w,
                        ((l_iris.y + r_iris.y) / 2) * h,
                    ]
                )

                gaze_vec = iris_center - eye_center
                gaze_vec = normalize(gaze_vec) * 120

                frame_data["eye_gaze_vector"] = {
                    "x": float(gaze_vec[0]),
                    "y": float(gaze_vec[1]),
                }

                cv2.arrowedLine(
                    frame_eye,
                    tuple(eye_center.astype(int)),
                    tuple((eye_center + gaze_vec).astype(int)),
                    (255, 0, 0),
                    3,
                )

            # Head pose (3D axes)
            if results.face_landmarks:
                h, w, _ = frame.shape
                image_points = np.array(
                    [
                        (results.face_landmarks.landmark[1].x * w, results.face_landmarks.landmark[1].y * h),
                        (results.face_landmarks.landmark[152].x * w, results.face_landmarks.landmark[152].y * h),
                        (results.face_landmarks.landmark[33].x * w, results.face_landmarks.landmark[33].y * h),
                        (results.face_landmarks.landmark[263].x * w, results.face_landmarks.landmark[263].y * h),
                        (results.face_landmarks.landmark[61].x * w, results.face_landmarks.landmark[61].y * h),
                        (results.face_landmarks.landmark[291].x * w, results.face_landmarks.landmark[291].y * h),
                    ],
                    dtype="double",
                )

                model_points = np.array(
                    [
                        (0.0, 0.0, 0.0),
                        (0.0, -63.6, -12.5),
                        (-43.3, 32.7, -26.0),
                        (43.3, 32.7, -26.0),
                        (-28.9, -28.9, -24.1),
                        (28.9, -28.9, -24.1),
                    ]
                )

                focal_length = w
                center = (w / 2, h / 2)

                camera_matrix = np.array(
                    [
                        [focal_length, 0, center[0]],
                        [0, focal_length, center[1]],
                        [0, 0, 1],
                    ],
                    dtype="double",
                )

                dist_coeffs = np.zeros((4, 1))

                success, rotation_vector, translation_vector = cv2.solvePnP(
                    model_points, image_points, camera_matrix, dist_coeffs
                )

                if success:
                    axis = np.float32(
                        [
                            [50, 0, 0],
                            [0, 50, 0],
                            [0, 0, 50],
                        ]
                    )

                    imgpts, _ = cv2.projectPoints(
                        axis, rotation_vector, translation_vector, camera_matrix, dist_coeffs
                    )

                    nose = tuple(image_points[0].astype(int))

                    cv2.line(frame_head, nose, tuple(imgpts[0].ravel().astype(int)), (0, 0, 255), 3)
                    cv2.line(frame_head, nose, tuple(imgpts[1].ravel().astype(int)), (0, 255, 0), 3)
                    cv2.line(frame_head, nose, tuple(imgpts[2].ravel().astype(int)), (255, 0, 0), 3)

                    frame_data["head_pose"] = {
                        "rotation_vector": rotation_vector.tolist()
                    }

            all_frames.append(frame_data)

            out_skel.write(frame_skel)
            out_eye.write(frame_eye)
            out_head.write(frame_head)

            if frame_total > 0:
                percent = (frame_count / frame_total) * 100.0
                bucket = int(percent // 5)
                if bucket > last_bucket:
                    last_bucket = bucket
                    report_progress(percent, f"Extracting dream landmarks ({frame_count}/{frame_total} frames)")

        with open(out_dream_json, "w", encoding="utf-8") as f:
            json.dump(all_frames, f, indent=2)

        pipeline_json = _convert_dream_frames_to_pipeline_json(all_frames, fps, video_path)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(pipeline_json, f, indent=4)

        cap.release()
        out_skel.release()
        out_eye.release()
        out_head.release()
        holistic.close()

        report_progress(100, "Dream extraction complete")
        print(f"FINAL OUTPUT GENERATED SUCCESSFULLY: {output_json}")
        print(f"DREAM JSON GENERATED: {out_dream_json}")
        print(f"DREAM VIDEOS GENERATED: {out_skel_path}, {out_eye_path}, {out_head_path}")
        return True

    except Exception as e:
        print(f"Coordinate extraction error: {e}")
        return False
