#!/usr/bin/env python3
"""Local Motion 001 study using the Umbrella LP's existing CGI take.

No media is downloaded, generated remotely, or substituted when an asset is absent.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path


FPS = 24
FRAMES = 274
DURATION = FRAMES / FPS
SOURCE = Path("public/experiencia/umbrella-b1/motion-v4.mp4")
FONT = Path("public/fonts/Manrope.ttf")


def inspect_video(ffmpeg: str, ffprobe: str | None, source: Path) -> dict:
    if ffprobe:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate,duration", "-of", "json", str(source)],
            check=True, capture_output=True, text=True,
        )
        streams = json.loads(result.stdout).get("streams", [])
        if streams:
            return streams[0]
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(source)],
                            capture_output=True, text=True)
    video_line = next((line for line in result.stderr.splitlines() if "Video:" in line), "")
    size = re.search(r"\b(\d{2,5})x(\d{2,5})\b", video_line)
    if not size:
        raise ValueError("O arquivo de origem não contém vídeo válido.")
    return {"width": int(size.group(1)), "height": int(size.group(2))}


def make_foley(path: Path) -> None:
    """Deterministic, quiet timing sketch. Replace with recorded foley before release."""
    rate = 48000
    rng = random.Random(1001)
    low = 0.0
    samples = bytearray()
    for i in range(round(DURATION * rate)):
        t = i / rate
        noise = rng.uniform(-1.0, 1.0)
        low = 0.93 * low + 0.07 * noise
        rustle = 0.0
        for start, end, gain in ((0.45, 2.3, 0.075), (5.8, 7.7, 0.055)):
            if start < t < end:
                phase = (t - start) / (end - start)
                rustle += gain * math.sin(math.pi * phase) ** 2
        click = 0.0
        for at in (3.15, 8.45):
            dt = t - at
            if 0 <= dt < 0.09:
                click += 0.11 * math.exp(-85 * dt) * math.sin(2 * math.pi * 920 * dt)
        sample = max(-1.0, min(1.0, rustle * low + click))
        samples.extend(struct.pack("<h", round(sample * 32767)))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples)


def render(args: argparse.Namespace) -> int:
    repo = args.repo.expanduser().resolve()
    source = (repo / SOURCE).resolve()
    font = (repo / FONT).resolve()
    missing = [str(p) for p in (source, font) if not p.is_file()]
    if missing:
        print("Assets reais ausentes; render interrompido:\n" + "\n".join(missing), file=sys.stderr)
        return 2
    ffmpeg = str(args.ffmpeg.expanduser().resolve()) if args.ffmpeg else shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not Path(ffmpeg).is_file():
        print("Instale FFmpeg ou informe --ffmpeg antes de renderizar.", file=sys.stderr)
        return 2
    info = inspect_video(ffmpeg, ffprobe, source)
    if int(info["width"]) < 1080 or int(info["height"]) < 608:
        print("Aviso: o quadro de origem terá ampliação visível no filme vertical.", file=sys.stderr)
    if args.check:
        print(json.dumps({"source": str(source), "font": str(font), "video": info,
                          "frames": FRAMES, "duration": DURATION}, indent=2))
        return 0

    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    full = out / "motion-001-1080x1920.mp4"
    preview = out / "motion-001-540x960.mp4"
    audio = args.foley.expanduser().resolve() if args.foley else out / "timing-foley.wav"
    if not args.foley:
        make_foley(audio)
    elif not audio.is_file():
        print(f"Foley não encontrado: {audio}", file=sys.stderr)
        return 2
    # The LP uses Manrope text for UmbrellaWordmark. This is not a new logo master.
    vf = (
        f"color=c=0x101013:s=1080x1920:r={FPS}:d={DURATION}[bg];"
        f"[0:v]fps={FPS},crop=960:720:x='max(160\\,320-160*t/3)':y=0,"
        "scale=1080:-2:flags=lanczos,"
        f"fade=t=out:st=9.25:d=1.2,setpts=PTS-STARTPTS[hero];"
        "[bg][hero]overlay=x=(W-w)/2:y=520:shortest=1[plate];"
        "[plate]drawtext=fontfile='public/fonts/Manrope.ttf':text='Umbrella':"
        "fontcolor=0xF5F3F7:fontsize=76:x=(w-text_w)/2:y=1375:"
        r"alpha='min(1\,max(0\,t-9.2))'[v]"
    )
    command = [ffmpeg, "-hide_banner", "-y", "-i", str(source), "-i", str(audio),
               "-filter_complex", vf, "-map", "[v]", "-map", "1:a:0", "-frames:v", str(FRAMES),
               "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-movflags", "+faststart", str(full)]
    subprocess.run(command, check=True, cwd=repo)
    subprocess.run([ffmpeg, "-hide_banner", "-y", "-i", str(full),
                    "-vf", "scale=540:960:flags=lanczos", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(preview)],
                   check=True, cwd=repo)
    for video in (full, preview):
        probe = inspect_video(ffmpeg, ffprobe, video)
        print(f"{video}: {probe['width']}×{probe['height']}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="Checkout local de eduardo-bido/umbrellahq")
    parser.add_argument("--out", type=Path, default=Path("motion-001/dist"))
    parser.add_argument("--foley", type=Path, help="WAV real gravado localmente; substitui o áudio de estudo")
    parser.add_argument("--ffmpeg", type=Path, help="Caminho do FFmpeg quando ele não está no PATH")
    parser.add_argument("--check", action="store_true", help="Valida assets e informa a origem sem renderizar")
    try:
        sys.exit(render(parser.parse_args()))
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(f"Falha na validação ou renderização: {exc}", file=sys.stderr)
        sys.exit(1)
