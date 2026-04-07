import os
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.animation import FuncAnimation
from pathlib import Path

def generate_2d_animation(json_folder, output_video_path):
    """Generate 2D skeleton animation from coordinates JSON

    Args:
        json_folder: Folder containing coordinates.json file
        output_video_path: Path to save animation MP4

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        CONF_THRESHOLD = 0.5

        # ── LOAD JSON ────────────────────────────────────────────────────────────────
        def load_json_from_folder(folder):
            for file in os.listdir(folder):
                if file.endswith(".json"):
                    path = os.path.join(folder, file)
                    print(f"📂 Loading JSON: {file}")
                    with open(path, "r") as f:
                        return json.load(f)
            raise FileNotFoundError(f"No JSON file found in {folder}")

        data = load_json_from_folder(json_folder)

        # ── SKELETON CONNECTIONS ──────────────────────────────────────────────────────
        CONNECTIONS = [
            ("head",           "sholder_center"),
            ("sholder_center", "sholder_left"),
            ("sholder_center", "sholder_right"),
            ("sholder_left",   "elbow_left"),
            ("elbow_left",     "wrist_left"),
            ("wrist_left",     "hand_left"),
            ("sholder_right",  "elbow_right"),
            ("elbow_right",    "wrist_right"),
            ("wrist_right",    "hand_right"),
        ]

        # ── SKELETON DATA ─────────────────────────────────────────────────────────────
        joints = data.get("skeleton", {})
        if not joints:
            raise ValueError("No skeleton data found in JSON.")

        first_joint = next(iter(joints))
        num_frames  = len(joints[first_joint]["x"])
        print(f"🦴 Skeleton joints: {list(joints.keys())}  |  Frames: {num_frames}")

        # ── FIND GLOBAL X/Y RANGE across all joints (for normalisation) ───────────────
        all_x, all_y = [], []
        for jdata in joints.values():
            all_x += [v for v in jdata["x"]          if v is not None]
            all_y += [v for v in jdata["y"]          if v is not None]

        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        x_range = max(x_max - x_min, 1e-6)
        y_range = max(y_max - y_min, 1e-6)
        print(f"📏 Raw coord range  X:[{x_min:.1f}, {x_max:.1f}]  Y:[{y_min:.1f}, {y_max:.1f}]")

        def norm_x(v): return (v - x_min) / x_range
        def norm_y(v): return (v - y_min) / y_range

        # ── AUTO-DETECT Y ORIENTATION ─────────────────────────────────────────────────
        # Screen-space (MediaPipe): Y=0 top, increases down  → head has SMALLER Y → flip axis
        # World-space  (Kinect):   Y=0 bottom, increases up  → head has LARGER  Y → normal axis
        def _joint_y_mean(name):
            if name not in joints: return None
            vals = [norm_y(v) for v in joints[name]["y"] if v is not None]
            return sum(vals) / len(vals) if vals else None

        head_y_mean  = _joint_y_mean("head")
        hand_y_means = [m for m in [_joint_y_mean("hand_left"), _joint_y_mean("hand_right")] if m is not None]
        hand_y_mean  = sum(hand_y_means) / len(hand_y_means) if hand_y_means else None

        # If head Y < hand Y → screen-space (Y-down) → need to flip axis so head appears at top
        if head_y_mean is not None and hand_y_mean is not None:
            Y_SCREEN_SPACE = head_y_mean < hand_y_mean
        else:
            Y_SCREEN_SPACE = False   # default: world-space (no flip)
        print(f"📐 Y orientation: {'Screen-space (Y-down, will flip axis)' if Y_SCREEN_SPACE else 'World-space (Y-up, no flip)'}")

        # ── EYE GAZE DATA ────────────────────────────────────────────────────────────
        gaze   = data.get("eye_gaze", {})
        rx_arr = np.array([float(v) if v is not None else np.nan for v in gaze.get("rx", [])])
        ry_arr = np.array([float(v) if v is not None else np.nan for v in gaze.get("ry", [])])
        print(f"👀 Eye gaze frames: {len(rx_arr)}  |  Keys: {list(gaze.keys())}")

        fps      = float(data.get("frame_rate", 25.0))
        interval = 1000.0 / fps

        # ── COLOURS ───────────────────────────────────────────────────────────────────
        JOINT_COLOR = "#2196F3"    # blue dots
        BONE_COLOR  = "#FF9800"    # orange bones
        LEFT_COLOR  = "#4CAF50"    # green  – left eye gaze
        RIGHT_COLOR = "#F44336"    # red    – right eye gaze

        GAZE_SCALE = 0.15          # arrow length in normalised space
        EYE_OFFSET = 0.025         # half-distance between L and R eye

        # ── FIGURE ────────────────────────────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(6, 7))
        ax.set_facecolor("white")
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_aspect("equal")
        ax.invert_xaxis()
        if Y_SCREEN_SPACE:
            ax.invert_yaxis()
        ax.set_xlabel("X", fontsize=10)
        ax.set_ylabel("Y", fontsize=10)
        ax.set_title(f"Behavior Analysis Animation ({fps:.1f} FPS)", fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.2)

        # ── SCATTER & LINE PLOTS ──────────────────────────────────────────────────────
        scatter = ax.scatter([], [], s=100, c=JOINT_COLOR, zorder=3, alpha=0.8)
        boneplot, = ax.plot([], [], color=BONE_COLOR, linewidth=2, zorder=2)
        gazeleft, = ax.plot([], [], color=LEFT_COLOR, linewidth=2, marker='>', markersize=8, zorder=2)
        gazeright, = ax.plot([], [], color=RIGHT_COLOR, linewidth=2, marker='<', markersize=8, zorder=2)

        frame_text = ax.text(0.02, 0.98, "", transform=ax.transAxes, fontsize=10, color='black', verticalalignment='top')

        # ── ANIMATION LOOP ───────────────────────────────────────────────────────────────
        def update_frame(frame_idx):
            if frame_idx >= num_frames:
                return scatter, boneplot, gazeleft, gazeright, frame_text

            # SKELETON DATA
            xs, ys = [], []
            for joint_name in joints.keys():
                x_val = joints[joint_name]["x"][frame_idx] if frame_idx < len(joints[joint_name]["x"]) else None
                y_val = joints[joint_name]["y"][frame_idx] if frame_idx < len(joints[joint_name]["y"]) else None
                conf  = joints[joint_name]["confidence"][frame_idx] if frame_idx < len(joints[joint_name]["confidence"]) else 0

                if x_val is not None and y_val is not None and conf > CONF_THRESHOLD:
                    xs.append(norm_x(x_val))
                    ys.append(norm_y(y_val) if not Y_SCREEN_SPACE else (1 - norm_y(y_val)))

            scatter.set_offsets(np.c_[xs, ys] if xs else [])

            # BONES
            bone_xs, bone_ys = [], []
            for joint_a, joint_b in CONNECTIONS:
                if joint_a in joints and joint_b in joints:
                    x1 = joints[joint_a]["x"][frame_idx] if frame_idx < len(joints[joint_a]["x"]) else None
                    y1 = joints[joint_a]["y"][frame_idx] if frame_idx < len(joints[joint_a]["y"]) else None
                    x2 = joints[joint_b]["x"][frame_idx] if frame_idx < len(joints[joint_b]["x"]) else None
                    y2 = joints[joint_b]["y"][frame_idx] if frame_idx < len(joints[joint_b]["y"]) else None
                    conf1 = joints[joint_a]["confidence"][frame_idx] if frame_idx < len(joints[joint_a]["confidence"]) else 0
                    conf2 = joints[joint_b]["confidence"][frame_idx] if frame_idx < len(joints[joint_b]["confidence"]) else 0

                    if (x1 is not None and y1 is not None and x2 is not None and y2 is not None and
                        conf1 > CONF_THRESHOLD and conf2 > CONF_THRESHOLD):
                        bone_xs.append([norm_x(x1), norm_x(x2)])
                        bone_ys.append([norm_y(y1) if not Y_SCREEN_SPACE else (1 - norm_y(y1)),
                                       norm_y(y2) if not Y_SCREEN_SPACE else (1 - norm_y(y2))])

            if bone_xs:
                boneplot.set_data(np.array(bone_xs).T, np.array(bone_ys).T)
            else:
                boneplot.set_data([], [])

            # EYE GAZE (LEFT & RIGHT)
            if frame_idx < len(rx_arr):
                # Left eye gaze
                left_x = 0.35 - EYE_OFFSET
                left_y = 0.25
                left_gaze_x = left_x + GAZE_SCALE * np.cos(np.radians(rx_arr[frame_idx]))
                left_gaze_y = left_y + GAZE_SCALE * np.sin(np.radians(ry_arr[frame_idx]))
                gazeleft.set_data([left_x, left_gaze_x], [left_y, left_gaze_y])

                # Right eye gaze
                right_x = 0.35 + EYE_OFFSET
                right_gaze_x = right_x + GAZE_SCALE * np.cos(np.radians(rx_arr[frame_idx]))
                right_gaze_y = left_y + GAZE_SCALE * np.sin(np.radians(ry_arr[frame_idx]))
                gazeright.set_data([right_x, right_gaze_x], [left_y, right_gaze_y])
            else:
                gazeleft.set_data([], [])
                gazeright.set_data([], [])

            frame_text.set_text(f"Frame: {frame_idx+1}/{num_frames}")
            return scatter, boneplot, gazeleft, gazeright, frame_text

        # ── CREATE ANIMATION ──────────────────────────────────────────────────────────
        anim = FuncAnimation(fig, update_frame, frames=num_frames, interval=interval, blit=True, repeat=False)

        # ── SAVE ANIMATION ────────────────────────────────────────────────────────────
        Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)
        print(f"🎬 Saving animation to: {output_video_path}")

        # Use ffmpeg writer
        Writer = matplotlib.animation.writers['ffmpeg']
        writer = Writer(fps=fps, bitrate=1800)
        anim.save(output_video_path, writer=writer, dpi=80)

        plt.close(fig)
        print(f"✅ Animation created successfully: {output_video_path}")
        return True

    except Exception as e:
        print(f"❌ Animation generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Allow script to be run standalone for testing
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 2d_animation.py <json_folder> <output_video_path>")
        sys.exit(1)

    json_folder = sys.argv[1]
    output_video_path = sys.argv[2]

    success = generate_2d_animation(json_folder, output_video_path)
    sys.exit(0 if success else 1)
