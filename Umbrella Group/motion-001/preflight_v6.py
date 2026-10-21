"""Non-rendering local prerequisites audit for Umbrella Motion 001 v6.

Run from "Umbrella Group"; no download, installation or production changes.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def exists(root, relative):
    path = root / relative
    return {"relative": relative, "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else None}


def run(command):
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        return {"exit": proc.returncode, "output": (proc.stdout + proc.stderr).strip()[:500]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--blender", default=shutil.which("blender"))
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe"))
    parser.add_argument("--require-frames", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    requirements = [
        "motion-001/source/geometry.py",
        "motion-001/source/scene.py",
        "motion-001/source/umbrella-print-atlas.png",
        "motion-001/source/umbrella-print-atlas-inverted-shot.png",
        "motion-001/render_3d_v5.py",
        "motion-001/render_3d_v6.py",
        "motion-001/lookdev_v6.py",
        "motion-001/motion_v6.py",
        "motion-001/assemble_v6.py",
        "public/fonts/Manrope.ttf",
    ]
    assets = [exists(root, p) for p in requirements]
    cloth_files = list((root / "motion-001/source/assets/cloth").glob("*"))
    blender = run([args.blender, "--background", "--version"]) if args.blender else {"error": "Blender not on PATH; pass --blender"}
    ffmpeg = run([args.ffmpeg, "-version"]) if args.ffmpeg else {"error": "FFmpeg not on PATH; pass --ffmpeg"}
    ffprobe = run([args.ffprobe, "-version"]) if args.ffprobe else {"error": "FFprobe not on PATH; pass --ffprobe"}
    nvidia = run(["nvidia-smi", "-L"]) if shutil.which("nvidia-smi") else {"note": "No NVIDIA CLI found; CPU or other GPU possible"}
    free = shutil.disk_usage(root).free if root.exists() else 0
    frames = None
    if args.require_frames:
        folder = args.require_frames.resolve()
        missing = [i for i in range(360) if not (folder / f"frame-{i:04d}.png").is_file()]
        frames = {"directory": str(folder), "count": 360-len(missing), "missing": len(missing),
                  "first_missing": missing[:12]}
    report = {
        "python": sys.version.split()[0], "platform": platform.platform(),
        "cpus_visible": os.cpu_count(), "root": str(root),
        "free_disk_gib": round(free/1024**3, 2),
        "files": assets,
        "source_cloth_assets": [{"name": f.name, "bytes": f.stat().st_size} for f in cloth_files if f.is_file()],
        "blender": blender, "ffmpeg": ffmpeg, "ffprobe": ffprobe, "nvidia": nvidia,
        "frames": frames,
        "render_executed": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    ready = all(item["exists"] for item in assets) and len(cloth_files) > 0
    ready &= "exit" in blender and blender["exit"] == 0
    ready &= "exit" in ffmpeg and ffmpeg["exit"] == 0
    ready &= "exit" in ffprobe and ffprobe["exit"] == 0
    ready &= free >= 2*1024**3
    if frames is not None:
        ready &= frames["missing"] == 0
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
