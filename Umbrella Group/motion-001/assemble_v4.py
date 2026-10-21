"""Assemble v4 frames with the exact closing copy and local ASMR sound sketch."""
from __future__ import annotations

import argparse
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


FPS = 24
COUNT = 360
RATE = 48000


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def audio_sketch(path):
    """Deterministic editorial placeholder, pending actual umbrella foley."""
    rng = np.random.default_rng(1001)
    n = RATE * 15
    t = np.arange(n) / RATE
    noise = rng.standard_normal(n).astype(np.float32)
    soft = np.convolve(noise, np.ones(24, dtype=np.float32) / 24, mode="same")
    high = noise - np.convolve(noise, np.ones(140, dtype=np.float32) / 140, mode="same")
    fall = np.array([(.35 + .65 * smooth(x / 3.0)) * (1 - smooth((x - 5.13) / .08)) for x in t], dtype=np.float32)
    sound = .027 * soft * fall
    dt = t - 5.17
    impact = (dt >= 0) * np.exp(-np.maximum(dt, 0) * 55)
    sound += .27 * impact * np.sin(2 * math.pi * 920 * dt)
    sound += .065 * impact * high
    sound += .09 * (dt >= 0) * np.exp(-np.maximum(dt, 0) * 24) * np.sin(2 * math.pi * 285 * dt)
    # Two mechanism clicks plus a fabric swish across the opening motion.
    for when, pitch, gain in ((5.38, 1280, .11), (6.86, 680, .14)):
        d = t - when
        env = (d >= 0) * np.exp(-np.maximum(d, 0) * 65)
        sound += gain * env * np.sin(2 * math.pi * pitch * d)
        sound += gain * .27 * env * high
    open_env = np.array([smooth((x - 5.38) / .43) * (1 - smooth((x - 6.87) / .32)) for x in t], dtype=np.float32)
    sound += .028 * open_env * high
    sound += .012 * open_env * soft
    spin_env = np.array([smooth((x - 7.2) / .35) * (1 - smooth((x - 10.4) / 1.5)) for x in t], dtype=np.float32)
    sound += .008 * spin_env * soft * (1 + np.sin(2 * math.pi * .95 * t))
    for when, gain in ((7.66, .039), (8.10, .027), (8.86, .017)):
        d = t - when
        env = (d >= 0) * np.exp(-np.maximum(d, 0) * 51)
        sound += gain * env * high
        sound += .55 * gain * env * np.sin(2 * math.pi * 300 * d)
    pcm = (np.clip(sound, -.94, .94) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())


def lettered(frame, index, font_path):
    t = index / FPS
    w, h = frame.size
    layer = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(layer)
    title_font = ImageFont.truetype(str(font_path), round(112 * w / 1080))
    sub_font = ImageFont.truetype(str(font_path), round(42 * w / 1080))
    title_font.set_variation_by_axes([600])
    sub_font.set_variation_by_axes([400])
    for text, font, start, y in (
        ("Umbrella", title_font, 10.45, .696 * h),
        ("Products that scale, solutions that fit.", sub_font, 10.95, .784 * h),
    ):
        progress = smooth((t - start) / .95)
        if progress <= 0:
            continue
        alpha = round(242 * progress)
        rise = round((1 - progress) * .055 * h)
        box = draw.textbbox((0, 0), text, font=font)
        x = round((w - (box[2] - box[0])) / 2)
        draw.text((x, round(y) + rise), text, font=font,
                  fill=(239, 235, 241, alpha), stroke_width=0)
    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")


def assemble(frames, out, ffmpeg, font, name):
    first = Image.open(frames / "frame-0000.png")
    w, h = first.size
    for i in range(COUNT):
        if not (frames / f"frame-{i:04d}.png").is_file():
            raise FileNotFoundError(f"Missing frame {i}: render is incomplete")
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "sound-placeholder.wav"
    audio_sketch(wav)
    master = out / f"{name}-{w}x{h}.mp4"
    cmd = [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0", "-frames:v", str(COUNT),
           "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(master)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    for index in range(COUNT):
        frame = Image.open(frames / f"frame-{index:04d}.png")
        process.stdin.write(lettered(frame, index, font).tobytes())
    process.stdin.close()
    error = process.stderr.read().decode("utf-8", "replace") if process.stderr else ""
    if process.wait():
        raise RuntimeError(error)
    print(master)
    if w > 540:
        preview = out / f"{name}-540x960.mp4"
        subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(master), "-vf", "scale=540:960:flags=lanczos",
                        "-c:v", "libx264", "-crf", "23", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                        "-movflags", "+faststart", str(preview)], check=True)
        print(preview)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--font", type=Path, default=Path("public/fonts/Manrope.ttf"))
    parser.add_argument("--name", default="motion-001-v4")
    args = parser.parse_args()
    assemble(args.frames.resolve(), args.out.resolve(), args.ffmpeg.resolve(), args.font.resolve(), args.name)


if __name__ == "__main__":
    main()
