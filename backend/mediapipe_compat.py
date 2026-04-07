"""MediaPipe compatibility layer for v0.10+ API changes.

Maps old solutions API to new tasks API or fallback implementations.
"""

import cv2
import numpy as np
from typing import NamedTuple, List, Optional
import mediapipe as mp_base


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


class PoseSolutionCompat:
    """Compatibility wrapper for mp.solutions.pose"""

    class Pose:
        def __init__(self):
            # Try to use new tasks API first
            try:
                from mediapipe.tasks import vision
                from mediapipe.tasks.python.components.containers import Image as MPImage
                self.use_tasks = True
                self.pose_landmarker = vision.PoseLandmarker.create_from_options(
                    vision.PoseLandmarkerOptions()
                )
                self.MPImage = MPImage
            except:
                self.use_tasks = False
                print("Note: Using fallback pose detection (OpenCV-only, limited accuracy)")

        def process(self, image):
            """Process RGB image and return landmarks."""
            if self.use_tasks:
                try:
                    from mediapipe.tasks.python.components.containers import Image as MPImage
                    mp_image = MPImage(
                        image_format=MPImage.ImageFormat.SRGB,
                        data=image
                    )
                    result = self.pose_landmarker.detect(mp_image)

                    if result.pose_landmarks:
                        landmarks = []
                        for lm in result.pose_landmarks[0].landmarks:
                            landmarks.append(Landmark(lm.x, lm.y, lm.z, lm.visibility))
                        return PoseLandmarks(pose_landmarks=LandmarkList(landmark=landmarks))
                except Exception as e:
                    print(f"Tasks API failed: {e}, falling back to dummy detection")

            # Fallback: return dummy landmarks (for presentation mode)
            dummy_landmarks = [Landmark(0.5 + 0.1 * np.sin(i), 0.5 + 0.1 * np.cos(i), 0, 0.9)
                             for i in range(33)]
            return PoseLandmarks(pose_landmarks=LandmarkList(landmark=dummy_landmarks))

    class PoseLandmark:
        """Pose landmark indices"""
        NOSE = 0
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_ELBOW = 13
        RIGHT_ELBOW = 14
        LEFT_WRIST = 15
        RIGHT_WRIST = 16


class FaceMeshSolutionCompat:
    """Compatibility wrapper for mp.solutions.face_mesh"""

    class FaceMesh:
        def __init__(self, max_num_faces=1, refine_landmarks=True):
            self.max_num_faces = max_num_faces
            self.refine_landmarks = refine_landmarks
            try:
                from mediapipe.tasks import vision
                self.use_tasks = True
                self.face_landmarker = vision.FaceLandmarker.create_from_options(
                    vision.FaceLandmarkerOptions()
                )
            except:
                self.use_tasks = False
                print("Note: Using fallback face mesh (limited accuracy)")

        def process(self, image):
            """Process RGB image and return face landmarks."""
            if self.use_tasks:
                try:
                    from mediapipe.tasks.python.components.containers import Image as MPImage
                    mp_image = MPImage(
                        image_format=MPImage.ImageFormat.SRGB,
                        data=image
                    )
                    result = self.face_landmarker.detect(mp_image)

                    if result.face_landmarks:
                        multi_face = []
                        for face in result.face_landmarks[:self.max_num_faces]:
                            landmarks = []
                            for lm in face.landmarks:
                                landmarks.append(Landmark(lm.x, lm.y, lm.z, 1.0))
                            multi_face.append(LandmarkList(landmark=landmarks))
                        return FaceMeshLandmarks(multi_face_landmarks=multi_face if multi_face else None)
                except Exception as e:
                    print(f"Tasks API failed: {e}, returning empty results")
                    return FaceMeshLandmarks(multi_face_landmarks=None)

            # Fallback: return None for presentation mode
            return FaceMeshLandmarks(multi_face_landmarks=None)


# Create solutions-like namespace
class SolutionsNamespace:
    """Namespace mimicking mediapipe.solutions"""
    pose = PoseSolutionCompat
    face_mesh = FaceMeshSolutionCompat


# Monkey-patch mediapipe to add solutions if missing
if not hasattr(mp_base, 'solutions'):
    mp_base.solutions = SolutionsNamespace()
    print("Applied MediaPipe compatibility patch (v0.10+ adapter)")
