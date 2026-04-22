import os
import json
import sys
import numpy as np
import matplotlib

# ✅ ffmpeg path (must be .exe)
matplotlib.rcParams['animation.ffmpeg_path'] = r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"

matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from pathlib import Path


def generate_2d_animation(json_folder, output_video_path, progress_callback=None):
    try:
        def report_progress(percent, message):
            if not callable(progress_callback):
                return
            try:
                progress_callback(float(percent), message)
            except Exception:
                # Progress updates should never interrupt animation export.
                pass

        CONF_THRESHOLD = 0.5

        # LOAD JSON
        def load_json(folder):
            for f in os.listdir(folder):
                if f.endswith(".json"):
                    with open(os.path.join(folder, f)) as file:
                        print(f"📂 Loading JSON: {f}")
                        return json.load(file)
            raise Exception("No JSON found")

        data = load_json(json_folder)

        CONNECTIONS = [
            ("head","sholder_center"),
            ("sholder_center","sholder_left"),
            ("sholder_center","sholder_right"),
            ("sholder_left","elbow_left"),
            ("elbow_left","wrist_left"),
            ("sholder_right","elbow_right"),
            ("elbow_right","wrist_right"),
        ]

        joints = data["skeleton"]
        first_joint = next(iter(joints))
        num_frames = len(joints[first_joint]["x"])

        print(f"🦴 Joints: {list(joints.keys())} | Frames: {num_frames}")

        # NORMALIZATION
        all_x = [v for j in joints.values() for v in j["x"] if v is not None]
        all_y = [v for j in joints.values() for v in j["y"] if v is not None]

        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)

        def nx(v): return (v - x_min) / (x_max - x_min + 1e-6)
        def ny(v): return (v - y_min) / (y_max - y_min + 1e-6)

        fps = float(data.get("frame_rate", 25))
        interval = 1000 / fps

        fig, ax = plt.subplots()
        ax.set_xlim(0,1)
        ax.set_ylim(0,1)
        # 🔥 IMPORTANT: separate lines for each bone
        

        def update(i):
            ax.clear()
            ax.set_xlim(0,1)
            ax.set_ylim(0,1)

    # DRAW JOINTS
            xs, ys = [], []
            for j in joints:
                if i >= len(joints[j]["x"]):
                    continue

                x = joints[j]["x"][i]
                y = joints[j]["y"][i]
                c = joints[j]["confidence"][i]

                if x is not None and y is not None and c > CONF_THRESHOLD:
                    xs.append(nx(x))
                    ys.append(ny(y))

            ax.scatter(xs, ys)

    # DRAW BONES
            for a, b in CONNECTIONS:
                if a in joints and b in joints:
                    if i >= len(joints[a]["x"]) or i >= len(joints[b]["x"]):
                        continue

                    x1 = joints[a]["x"][i]
                    y1 = joints[a]["y"][i]
                    x2 = joints[b]["x"][i]
                    y2 = joints[b]["y"][i]

                    if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                        ax.plot(
                            [nx(x1), nx(x2)],
                            [ny(y1), ny(y2)]
                        )

            return []

        anim = FuncAnimation(
            fig,
            update,
            frames=num_frames,
            interval=interval,
            blit=False  # 🔥 important
        )

        Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)

        print("🎬 Saving animation...")
        report_progress(0, "Preparing animation export")

        last_report_bucket = -1

        def mpl_progress_callback(current_frame, total_frames):
            nonlocal last_report_bucket
            if total_frames is None or total_frames <= 0:
                return
            percent = ((current_frame + 1) / total_frames) * 100.0
            bucket = int(percent // 5)
            if bucket > last_report_bucket:
                last_report_bucket = bucket
                report_progress(percent, f"Rendering animation ({current_frame + 1}/{total_frames} frames)")

        writer = FFMpegWriter(fps=fps, bitrate=1800)
        anim.save(output_video_path, writer=writer, progress_callback=mpl_progress_callback)

        plt.close()
        report_progress(100, "Animation export complete")
        print("✅ Animation created successfully")
        return True

    except Exception as e:
        print("❌ ERROR:", e)
        return False


if __name__ == "__main__":
    generate_2d_animation(sys.argv[1], sys.argv[2])