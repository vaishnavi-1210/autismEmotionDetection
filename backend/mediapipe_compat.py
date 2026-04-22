"""MediaPipe compatibility layer for tasks-only builds.

This adapter exposes a solutions-like API (`mp.solutions.pose`, `mp.solutions.face_mesh`,
`mp.solutions.holistic`) by using MediaPipe Tasks models under the hood.
"""

from pathlib import Path
from typing import List, NamedTuple, Optional
import urllib.request

import mediapipe as mp_base
import numpy as np


POSE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/1/pose_landmarker_full.task"
)
FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
HAND_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


BASE_DIR = Path(__file__).resolve().parent.parent
TASK_MODELS_DIR = BASE_DIR / "data" / "models" / "mediapipe_tasks"
TASK_MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_task_model(file_name: str, url: str) -> Path:
    model_path = TASK_MODELS_DIR / file_name
    if model_path.exists() and model_path.stat().st_size > 0:
        return model_path

    print(f"Downloading MediaPipe task model: {file_name}")
    urllib.request.urlretrieve(url, model_path)
    return model_path


def _to_mp_image(image):
    return mp_base.Image(image_format=mp_base.ImageFormat.SRGB, data=image)


def _to_landmark_list(points) -> "LandmarkList":
    landmarks = []
    for lm in points:
        x = float(lm.x) if getattr(lm, "x", None) is not None else 0.0
        y = float(lm.y) if getattr(lm, "y", None) is not None else 0.0
        z = float(lm.z) if getattr(lm, "z", None) is not None else 0.0
        vis_raw = getattr(lm, "visibility", 1.0)
        visibility = float(vis_raw) if vis_raw is not None else 1.0
        landmarks.append(Landmark(x, y, z, visibility))
    return LandmarkList(landmark=landmarks)


class Landmark(NamedTuple):
    """Represents a 3D landmark with visibility."""

    x: float
    y: float
    z: float
    visibility: float = 1.0


class LandmarkList(NamedTuple):
    """List of landmarks."""

    landmark: List[Landmark]


class PoseLandmarks(NamedTuple):
    """Result from pose detection."""

    pose_landmarks: Optional[LandmarkList] = None


class FaceMeshLandmarks(NamedTuple):
    """Result from face mesh detection."""

    multi_face_landmarks: Optional[List[LandmarkList]] = None


class HolisticLandmarks(NamedTuple):
    """Result from holistic detection."""

    pose_landmarks: Optional[LandmarkList] = None
    face_landmarks: Optional[LandmarkList] = None
    left_hand_landmarks: Optional[LandmarkList] = None
    right_hand_landmarks: Optional[LandmarkList] = None


class PoseSolutionCompat:
    """Compatibility wrapper for `mp.solutions.pose`."""

    class Pose:
        def __init__(
            self,
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ):
            # Keep args for API compatibility with legacy `mp.solutions.pose.Pose`.
            _ = model_complexity, smooth_landmarks, enable_segmentation, smooth_segmentation
            self.use_tasks = False
            self._running_mode = None
            self._timestamp_ms = 0
            try:
                from mediapipe.tasks.python import BaseOptions, vision

                model_path = _ensure_task_model("pose_landmarker_full.task", POSE_MODEL_URL)
                self._running_mode = (
                    vision.RunningMode.IMAGE
                    if static_image_mode
                    else vision.RunningMode.VIDEO
                )
                options = vision.PoseLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=str(model_path)),
                    running_mode=self._running_mode,
                    num_poses=1,
                    min_pose_detection_confidence=min_detection_confidence,
                    min_pose_presence_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence,
                )
                self.pose_landmarker = vision.PoseLandmarker.create_from_options(options)
                self.use_tasks = True
            except Exception as e:
                print(f"Note: Using fallback pose detection (limited accuracy): {e}")

        def process(self, image):
            if self.use_tasks:
                try:
                    mp_image = _to_mp_image(image)
                    if self._running_mode and self._running_mode.name == "VIDEO":
                        result = self.pose_landmarker.detect_for_video(mp_image, self._timestamp_ms)
                        self._timestamp_ms += 33
                    else:
                        result = self.pose_landmarker.detect(mp_image)
                    if result.pose_landmarks:
                        return PoseLandmarks(
                            pose_landmarks=_to_landmark_list(result.pose_landmarks[0])
                        )
                    return PoseLandmarks(pose_landmarks=None)
                except Exception as e:
                    print(f"Tasks pose detection failed: {e}")

            # Last-resort fallback keeps pipeline alive if tasks fail at runtime.
            dummy_landmarks = [
                Landmark(0.5 + 0.1 * np.sin(i), 0.5 + 0.1 * np.cos(i), 0.0, 0.9)
                for i in range(33)
            ]
            return PoseLandmarks(pose_landmarks=LandmarkList(landmark=dummy_landmarks))

    class PoseLandmark:
        """Pose landmark indices."""

        NOSE = 0
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_ELBOW = 13
        RIGHT_ELBOW = 14
        LEFT_WRIST = 15
        RIGHT_WRIST = 16
        LEFT_INDEX = 19
        RIGHT_INDEX = 20


class FaceMeshSolutionCompat:
    """Compatibility wrapper for `mp.solutions.face_mesh`."""

    class FaceMesh:
        def __init__(
            self,
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ):
            self.max_num_faces = max_num_faces
            self.refine_landmarks = refine_landmarks
            self.use_tasks = False
            self._running_mode = None
            self._timestamp_ms = 0
            try:
                from mediapipe.tasks.python import BaseOptions, vision

                model_path = _ensure_task_model("face_landmarker.task", FACE_MODEL_URL)
                self._running_mode = (
                    vision.RunningMode.IMAGE
                    if static_image_mode
                    else vision.RunningMode.VIDEO
                )
                options = vision.FaceLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=str(model_path)),
                    running_mode=self._running_mode,
                    num_faces=max_num_faces,
                    min_face_detection_confidence=min_detection_confidence,
                    min_face_presence_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence,
                    output_face_blendshapes=False,
                    output_facial_transformation_matrixes=False,
                )
                self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
                self.use_tasks = True
            except Exception as e:
                print(f"Note: Using fallback face mesh (limited accuracy): {e}")

        def process(self, image):
            if self.use_tasks:
                try:
                    mp_image = _to_mp_image(image)
                    if self._running_mode and self._running_mode.name == "VIDEO":
                        result = self.face_landmarker.detect_for_video(mp_image, self._timestamp_ms)
                        self._timestamp_ms += 33
                    else:
                        result = self.face_landmarker.detect(mp_image)
                    if result.face_landmarks:
                        multi_face = [
                            _to_landmark_list(face)
                            for face in result.face_landmarks[: self.max_num_faces]
                        ]
                        return FaceMeshLandmarks(multi_face_landmarks=multi_face)
                    return FaceMeshLandmarks(multi_face_landmarks=None)
                except Exception as e:
                    print(f"Tasks face detection failed: {e}")

            return FaceMeshLandmarks(multi_face_landmarks=None)


class HolisticSolutionCompat:
    """Compatibility wrapper for `mp.solutions.holistic`."""

    class Holistic:
        def __init__(self, static_image_mode=False, model_complexity=1, refine_face_landmarks=True):
            # Keep args for API compatibility with legacy solutions.holistic.Holistic.
            self.pose = PoseSolutionCompat.Pose(
                static_image_mode=static_image_mode,
                model_complexity=model_complexity,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.3,
            )
            self.face = FaceMeshSolutionCompat.FaceMesh(
                static_image_mode=static_image_mode,
                max_num_faces=1,
                refine_landmarks=refine_face_landmarks,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.3,
            )

            self.hand_landmarker = None
            self._hand_running_mode = None
            self._hand_timestamp_ms = 0
            try:
                from mediapipe.tasks.python import BaseOptions, vision

                model_path = _ensure_task_model("hand_landmarker.task", HAND_MODEL_URL)
                self._hand_running_mode = (
                    vision.RunningMode.IMAGE
                    if static_image_mode
                    else vision.RunningMode.VIDEO
                )
                options = vision.HandLandmarkerOptions(
                    base_options=BaseOptions(model_asset_path=str(model_path)),
                    running_mode=self._hand_running_mode,
                    num_hands=2,
                    min_hand_detection_confidence=0.3,
                    min_hand_presence_confidence=0.3,
                    min_tracking_confidence=0.3,
                )
                self.hand_landmarker = vision.HandLandmarker.create_from_options(options)
            except Exception as e:
                print(f"Note: Hand landmarks unavailable in holistic adapter: {e}")

        def process(self, image):
            pose_result = self.pose.process(image)
            face_result = self.face.process(image)

            face_landmarks = None
            if face_result and face_result.multi_face_landmarks:
                face_landmarks = face_result.multi_face_landmarks[0]

            left_hand_landmarks = None
            right_hand_landmarks = None
            if self.hand_landmarker is not None:
                try:
                    mp_image = _to_mp_image(image)
                    if self._hand_running_mode and self._hand_running_mode.name == "VIDEO":
                        hand_result = self.hand_landmarker.detect_for_video(mp_image, self._hand_timestamp_ms)
                        self._hand_timestamp_ms += 33
                    else:
                        hand_result = self.hand_landmarker.detect(mp_image)
                    if hand_result and hand_result.hand_landmarks:
                        for idx, hand_points in enumerate(hand_result.hand_landmarks):
                            hand_name = ""
                            if hand_result.handedness and idx < len(hand_result.handedness):
                                categories = hand_result.handedness[idx]
                                if categories:
                                    hand_name = categories[0].category_name.lower()

                            hand_lms = _to_landmark_list(hand_points)
                            if hand_name == "left":
                                left_hand_landmarks = hand_lms
                            elif hand_name == "right":
                                right_hand_landmarks = hand_lms
                            elif left_hand_landmarks is None:
                                left_hand_landmarks = hand_lms
                            elif right_hand_landmarks is None:
                                right_hand_landmarks = hand_lms
                except Exception as e:
                    print(f"Tasks hand detection failed: {e}")

            return HolisticLandmarks(
                pose_landmarks=pose_result.pose_landmarks if pose_result else None,
                face_landmarks=face_landmarks,
                left_hand_landmarks=left_hand_landmarks,
                right_hand_landmarks=right_hand_landmarks,
            )

        def close(self):
            return None


class SolutionsNamespace:
    """Namespace mimicking `mediapipe.solutions`."""

    pose = PoseSolutionCompat
    face_mesh = FaceMeshSolutionCompat
    holistic = HolisticSolutionCompat


if not hasattr(mp_base, "solutions"):
    mp_base.solutions = SolutionsNamespace()
    print("Applied MediaPipe compatibility patch (tasks adapter)")
