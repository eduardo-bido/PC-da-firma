#!/usr/bin/env python3
"""Motion 001 fall study: local edit of the actual Umbrella LP footage.

The falling translation is a 2D treatment of an existing closed frame. The
opening and printed-name close-up reuse original frames; no new umbrella asset.
"""

from __future__ import annotations

import argparse
import math
import random
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


FPS = 24
SECONDS = 12
FRAMES = FPS * SECONDS
SOURCE = Path("public/experiencia/umbrella-b1/motion-v4.mp4")
SW, SH = 1280, 720
W, H = 1080, 1920
FLOOR = 1560
RESAMPLE = Image.Resampling.LANCZOS


def smooth(value: float) -> float:
    x = max(0.0, min(1.0, value))
    return x * x * (3 - 2 * x)


def frames_from_video(ffmpeg: str, source: Path, start: int, stop: int) -> list[Image.Image]:
    args = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(source),
            "-vf", f"select=between(n\\,{start}\\,{stop}),format=rgb24",
            "-fps_mode", "vfr", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    result = []
    size = SW * SH * 3
    for _ in range(stop - start + 1):
        chunks = bytearray()
        while len(chunks) < size:
            part = proc.stdout.read(size - len(chunks))
            if not part:
                raise RuntimeError("A tomada não contém todos os quadros esperados.")
            chunks.extend(part)
        result.append(Image.frombytes("RGB", (SW, SH), bytes(chunks)))
    proc.stdout.close()
    error = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
    if proc.wait() != 0:
        raise RuntimeError(error)
    return result


def keyed(image: Image.Image) -> Image.Image:
    pixels = np.asarray(image.convert("RGB"), dtype=np.uint8)
    value = pixels.max(axis=2).astype(np.int16)
    # The encoded source has a lifted near-black background (usually 1–9).
    # Remove it before compositing onto the charcoal set.
    alpha = np.clip((value - 11) * 16, 0, 255).astype(np.uint8)
    rgba = np.empty((*pixels.shape[:2], 4), dtype=np.uint8)
    rgba[:, :, :3] = pixels
    rgba[:, :, 3] = alpha
    return Image.fromarray(rgba, "RGBA")


def studio() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    light = np.exp(-(((xx - 535) / 570) ** 2 + ((yy - 820) / 820) ** 2) * 1.4)
    floor_light = np.exp(-(((xx - 535) / 680) ** 2 + ((yy - FLOOR) / 190) ** 2))
    ground = (yy >= FLOOR).astype(np.float32)
    rgb = np.empty((H, W, 3), dtype=np.uint8)
    for channel, base, gain in ((0, 15, 13), (1, 15, 12), (2, 18, 15)):
        rgb[:, :, channel] = np.clip(base + gain * light + ground * (3 + 5 * floor_light), 0, 255)
    background = Image.fromarray(rgb, "RGB").convert("RGBA")
    line = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(line)
    draw.line((0, FLOOR, W, FLOOR), fill=(92, 85, 105, 30), width=2)
    background = Image.alpha_composite(background, line)
    return background


def shadow() -> Image.Image:
    image = Image.new("RGBA", (W, H))
    ImageDraw.Draw(image).ellipse((275, FLOOR - 42, 805, FLOOR + 40), fill=(0, 0, 0, 100))
    return image.filter(ImageFilter.GaussianBlur(34))


def impact_light() -> Image.Image:
    image = Image.new("RGBA", (W, H))
    ImageDraw.Draw(image).ellipse((320, FLOOR - 14, 760, FLOOR + 16), fill=(145, 127, 165, 65))
    return image.filter(ImageFilter.GaussianBlur(40))


def sound(path: Path) -> None:
    """Deterministic sound sketch; a real recorded contact/cloth track is preferred."""
    rate = 48000
    rng = random.Random(1001)
    low = 0.0
    air = 0.0
    samples = bytearray()
    for i in range(SECONDS * rate):
        t = i / rate
        noise = rng.uniform(-1, 1)
        low = .88 * low + .12 * noise
        air = .97 * air + .03 * noise
        near = smooth((t - 1.1) / 3.7) * (1 - smooth((t - 5.15) / .25))
        cloth = smooth((t - 5.45) / .5) * (1 - smooth((t - 9.2) / .45))
        thud = 0.0
        dt = t - 5.2
        if 0 <= dt < .32:
            thud = .26 * math.exp(-18 * dt) * math.sin(2 * math.pi * 86 * dt)
            thud += .12 * math.exp(-75 * dt) * noise
        click = 0.0
        if 5.58 <= t < 5.7:
            d = t - 5.58
            click = .055 * math.exp(-48 * d) * math.sin(2 * math.pi * 1100 * d)
        value = .085 * near * air + .07 * cloth * low + thud + click
        samples.extend(struct.pack("<h", round(max(-1, min(1, value)) * 32767)))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples)


def composite(base: Image.Image, image: Image.Image, x: int, y: int) -> None:
    base.alpha_composite(image, (x, y))


def contact_camera(frame: Image.Image, t: float) -> Image.Image:
    amount = smooth((t - 3.9) / 1.3)
    width = round(W - 620 * amount)
    height = round(H * width / W)
    center_y = round(960 + (FLOOR - 960) * amount)
    left = (W - width) // 2
    top = max(0, min(H - height, center_y - height // 2))
    return frame.crop((left, top, left + width, top + height)).resize((W, H), RESAMPLE)


def macro_frame(image: Image.Image) -> Image.Image:
    # The same photographed CGI texture fills the entire set softly; the
    # sharp crop feathers into it so no horizontal video rectangle remains.
    wash = ImageOps.fit(image, (W, H), method=RESAMPLE, centering=(.62, .5))
    wash = wash.filter(ImageFilter.GaussianBlur(95)).convert("RGBA")
    alpha = np.zeros((H, W), dtype=np.uint8)
    mid = H // 2
    half = image.height // 2
    top = mid - half
    for y in range(image.height):
        edge = min(y, image.height - 1 - y)
        alpha[top + y, :] = round(255 * smooth(edge / 180))
    sharp = image.convert("RGBA")
    sharp.putalpha(Image.fromarray(alpha[top:top + image.height], "L"))
    composite(wash, sharp, 0, top)
    return wash


def make_video(ffmpeg: str, source: Path, out: Path) -> None:
    start = frames_from_video(ffmpeg, source, 0, 30)
    opening = frames_from_video(ffmpeg, source, 214, 273)
    closed = keyed(opening[0].crop((680, 80, 830, 660)))
    background = studio()
    ground_shadow = shadow()
    glow = impact_light()
    audio = out / "fall-sound-sketch.wav"
    sound(audio)
    master = out / "motion-001-fall-1080x1920.mp4"
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", str(audio),
               "-map", "0:v:0", "-map", "1:a:0", "-frames:v", str(FRAMES),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(master)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    for n in range(FRAMES):
        t = n / FPS
        frame = background.copy()
        if t < 5.5:
            strength = smooth((t - 2.5) / 2.7) * .7
            shade = ground_shadow.copy()
            shade.putalpha(shade.getchannel("A").point(lambda a: round(a * strength)))
            composite(frame, shade, 0, 0)
            if t < 3.8:
                p = smooth(t / 3.8)
                bottom = -170 + 1320 * p
                scale = .75 + .65 * p
            else:
                p = smooth((t - 3.8) / 1.4)
                bottom = 1150 + 410 * p
                scale = 1.4 + .45 * p
            if t >= 5.2:
                bottom = FLOOR
                scale = 1.85
                amount = max(0, 1 - (t - 5.2) / .35)
                flash = glow.copy()
                flash.putalpha(flash.getchannel("A").point(lambda a: round(a * amount)))
                composite(frame, flash, 0, 0)
            size = (round(closed.width * scale), round(closed.height * scale))
            actor = closed.resize(size, RESAMPLE)
            x = (W - actor.width) // 2
            y = round(bottom - actor.height)
            composite(frame, actor, x, y)
            if t >= 3.9:
                frame = contact_camera(frame, t)
        elif t < 9.35:
            p = smooth((t - 5.5) / 3.85)
            index = min(59, round(59 * (t - 5.5) / 3.85))
            width = round(600 + 360 * p)
            center = 750 - 110 * p
            left = round(center - width / 2)
            actor = keyed(opening[index].crop((left, 0, left + width, SH)))
            actor = actor.resize((W, round(SH * W / width)), RESAMPLE)
            y = round(FLOOR - 644 * W / width)
            composite(frame, ground_shadow, 0, 0)
            composite(frame, actor, 0, y)
        else:
            p = smooth((t - 9.35) / 2.15)
            index = max(0, round(30 * (1 - p)))
            width = round(960 - 240 * p)
            left = round(320 + 240 * p)
            actor = start[index].crop((left, 0, left + width, SH))
            actor = actor.resize((W, round(SH * W / width)), RESAMPLE)
            frame = macro_frame(actor)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    error = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
    if proc.wait() != 0:
        raise RuntimeError(error)
    preview = out / "motion-001-fall-540x960.mp4"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(master),
                    "-vf", "scale=540:960:flags=lanczos", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", str(preview)], check=True)
    print(master)
    print(preview)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("motion-001/fall"))
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_args()
    source = args.repo.expanduser().resolve() / SOURCE
    if not source.is_file():
        raise SystemExit(f"Asset proprietário ausente: {source}")
    ffmpeg = str(args.ffmpeg.expanduser().resolve()) if args.ffmpeg else shutil.which("ffmpeg")
    if not ffmpeg or not Path(ffmpeg).is_file():
        raise SystemExit("FFmpeg não encontrado; informe --ffmpeg.")
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    make_video(ffmpeg, source, out)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Render interrompido: {exc}", file=sys.stderr)
        raise SystemExit(1)
