import os
import subprocess


def stitch(
    date_str: str,
    photos_dir: str,
    output_dir: str,
    framerate: int = 2,
    width: int = 1920,
    height: int = 1080,
) -> str | None:
    """
    Stitch JPEG photos from photos_dir/date_str/ into an MP4 video.
    Output is written to output_dir/date_str.mp4.
    Returns the output path on success, None on failure.
    """
    src_dir = os.path.join(photos_dir, date_str)
    if not os.path.isdir(src_dir):
        return None

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{date_str}.mp4")
    input_pattern = os.path.join(src_dir, "*.jpg")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(framerate),
        "-pattern_type", "glob",
        "-i", input_pattern,
        "-vf", f"scale={width}:{height}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return output_path if result.returncode == 0 else None
