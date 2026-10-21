"""Overlay Manrope, create local foley and encode MP4 without standalone FFmpeg."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image

from assemble_v5 import COUNT, audio_sketch, lettered


HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--blender", required=True, type=Path)
    parser.add_argument("--font", type=Path, default=Path("public/fonts/Manrope.ttf"))
    parser.add_argument("--name", default="motion-001-v5")
    args = parser.parse_args()

    frames = args.frames.resolve()
    out = args.out.resolve()
    blender = args.blender.resolve()
    font = args.font.resolve()
    if not blender.is_file():
        raise FileNotFoundError(blender)
    if not font.is_file():
        raise FileNotFoundError(font)
    first = Image.open(frames / "frame-0000.png")
    width, height = first.size
    for index in range(COUNT):
        if not (frames / f"frame-{index:04d}.png").is_file():
            raise FileNotFoundError(f"Incomplete render: frame {index}")

    out.mkdir(parents=True, exist_ok=True)
    wav = out / "sound-placeholder.wav"
    audio_sketch(wav)
    full_frames = out / f"lettered-{width}x{height}"
    full_frames.mkdir(exist_ok=True)
    preview_frames = out / "lettered-540x960" if width > 540 else None
    if preview_frames:
        preview_frames.mkdir(exist_ok=True)
    for index in range(COUNT):
        with Image.open(frames / f"frame-{index:04d}.png") as raw:
            final = lettered(raw, index, font)
        final.save(full_frames / f"frame-{index:04d}.png", compress_level=1)
        if preview_frames:
            final.resize((540, 960), Image.Resampling.LANCZOS).save(
                preview_frames / f"frame-{index:04d}.png", compress_level=1
            )
        if index % 60 == 0:
            print("LETTERED", index, flush=True)

    outputs = [(full_frames, width, height, out / f"{args.name}-{width}x{height}.mp4")]
    if preview_frames:
        outputs.append((preview_frames, 540, 960, out / f"{args.name}-540x960.mp4"))
    for images, w, h, video in outputs:
        subprocess.run([
            str(blender), "--background", "--factory-startup", "--python", str(HERE / "encode_v5_blender.py"),
            "--", "--frames", str(images), "--wav", str(wav), "--out", str(video),
            "--width", str(w), "--height", str(h),
        ], check=True)
        if not video.is_file() or video.stat().st_size == 0:
            raise RuntimeError(f"Blender did not write {video}")
        print("VIDEO", video, flush=True)


if __name__ == "__main__":
    main()
