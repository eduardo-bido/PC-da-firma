"""Motion 001 v6: local-only editorial assembly, provisional synthetic umbrella sound.

Requires the *real* complete 360 Blender frames and the supplied Manrope.ttf.
Does not reconstruct missing frames, assets or brand artwork.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 24
FRAMES = 360
DURATION = FRAMES / FPS
RATE = 48_000
NAME = "motion-001-v6"
COPY = (
    "Você esperou a queda.",
    "Seu site também precisa prender.",
    "E converter.",
    "Conheça a Umbrella no perfil.",
    "Products that scale, solutions that fit.",
)


def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3.0 - 2.0 * x)


def gate(t: float, start: float, end: float, fade_in=0.22, fade_out=0.20) -> float:
    return ease((t-start)/fade_in) * (1.0-ease((t-(end-fade_out))/fade_out))


def font_at(path: Path, size: int, weight=500) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), max(12, size))
    try:
        font.set_variation_by_axes([weight])
    except (AttributeError, OSError, ValueError):
        pass
    return font


def compose_frame(frame: Image.Image, index: int, font_path: Path) -> Image.Image:
    """Text deliberately avoids source logo/printed gore and Reels lower safe edge."""
    w, h = frame.size
    t = index / FPS
    if t < 5.33:
        return frame.convert("RGB")
    alpha_1 = gate(t, 5.38, 6.98, 0.18, 0.23)
    alpha_2 = gate(t, 8.62, 11.24, 0.21, 0.25)
    alpha_3 = gate(t, 11.36, 14.98, 0.23, 0.24)
    alpha_sig = gate(t, 13.15, 15.15, 0.35, 0.18)
    active = max(alpha_1, alpha_2, alpha_3, alpha_sig)
    if active < 0.003:
        return frame.convert("RGB")

    over = Image.new("RGBA", (w, h))
    shade = ImageDraw.Draw(over)
    # Atmospheric shadow only at bottom; no opaque rectangular lower-third.
    y0, y1 = int(.615*h), int(.855*h)
    for y in range(y0, y1):
        q = ease((y-y0)/max(1, y1-y0))
        shade.line((0, y, w, y), fill=(8, 7, 12, round(q*155*active)), width=1)
    d = ImageDraw.Draw(over)
    max_width = int(.87*w)

    def line(msg: str, y: float, pt: int, weight: int, a: float) -> None:
        if a <= 0.003:
            return
        size = max(12, round(pt*w/1080))
        f = font_at(font_path, size, weight)
        bounds = d.textbbox((0, 0), msg, font=f)
        while bounds[2]-bounds[0] > max_width and size > 12:
            size -= 1
            f = font_at(font_path, size, weight)
            bounds = d.textbbox((0, 0), msg, font=f)
        tw = bounds[2]-bounds[0]
        x = round((w-tw)/2)-bounds[0]
        yy = round(y*h) - round((bounds[1]+bounds[3])/2)
        assert x+bounds[0] >= .06*w and x+bounds[2] <= .94*w, msg
        assert yy+bounds[1] >= .14*h and yy+bounds[3] <= .833*h, msg
        shadow = round(95*a)
        d.text((x, yy+round(2*w/540)), msg, font=f, fill=(0, 0, 0, shadow))
        d.text((x, yy), msg, font=f, fill=(245, 241, 245, round(247*a)))

    if alpha_1:
        line(COPY[0], .765, 74, 620, alpha_1)
    if alpha_2:
        line(COPY[1], .716, 61, 570, alpha_2)
        line(COPY[2], .777, 77, 730, alpha_2 * ease((t-9.23)/.35))
    if alpha_3:
        line(COPY[3], .714, 66, 640, alpha_3)
    if alpha_sig:
        # A subordinate sign-off, not an invented replacement for the source print.
        line(COPY[4], .802, 37, 420, alpha_sig)
    return Image.alpha_composite(frame.convert("RGBA"), over).convert("RGB")


def avg(x: np.ndarray, width: int) -> np.ndarray:
    """Running mean in O(n), deterministic and memory bounded."""
    s = np.cumsum(np.pad(x.astype(np.float64), (1, 0)))
    hi = np.arange(len(x)) + 1
    lo = np.maximum(0, hi-width)
    return ((s[hi]-s[lo]) / (hi-lo)).astype(np.float32)


def audio_sketch(dst: Path, impact_events: list[float] | None = None) -> None:
    """Locally synthesized *placeholder*, NOT authentic recorded umbrella foley."""
    n = RATE*FRAMES//FPS
    t = np.arange(n, dtype=np.float64)/RATE
    rng = np.random.default_rng(1001)
    noise = rng.standard_normal(n).astype(np.float32)
    soft = avg(noise, 38)
    high = noise - avg(noise, 180)
    fall = np.asarray([ease(float(v/.50))*(1-ease((float(v)-4.86)/.045))
                       for v in t], dtype=np.float32)
    sound = .017*soft*fall
    sound += .028*high*np.maximum(0, 1-t/.45)**2

    def click(when: float, freq: float, gain: float, decay: float) -> None:
        nonlocal sound
        delta = t-when
        env = (delta >= 0)*np.exp(-np.maximum(delta, 0)*decay)
        sound += (gain*env*np.sin(2*math.pi*freq*delta) +
                  .28*gain*env*high)

    # Timeline matches actual source motion (impact at 4.90, opens 5.00-5.30).
    click(4.900, 480, .27, 58)
    click(5.008, 1220, .12, 92)
    click(5.232, 690, .19, 55)
    open_env = np.asarray([ease((float(v)-5.025)/.08)*
                           (1-ease((float(v)-5.29)/.20)) for v in t], dtype=np.float32)
    sound += .064*high*open_env + .017*soft*open_env
    settle_env = np.asarray([ease((float(v)-5.31)/.17)*
                             (1-ease((float(v)-7.3)/1.5)) for v in t], dtype=np.float32)
    sound += .006*soft*settle_env
    # Extra canopy-contact taps require actual event evidence from render-report.
    for index, when in enumerate((impact_events or [4.90])[1:]):
        click(float(when), 370-index*70, .055/(1+index), 75+index*5)
    peak = float(np.max(np.abs(sound)))
    if peak > .90:
        sound *= .90/peak
    pcm = (np.clip(sound, -.94, .94)*32767).astype("<i2")
    with wave.open(str(dst), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(pcm.tobytes())


def command(args: list[str], log=False):
    p = subprocess.run(args, text=True, capture_output=True, check=False)
    if p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): {args!r}\n{p.stderr[-5000:]}")
    return p.stdout if log else None


def probe(path: Path, ffprobe: str) -> dict:
    return json.loads(command([ffprobe, "-v", "error", "-count_frames",
                               "-show_entries",
                               "format=duration:stream=codec_type,codec_name,width,height,nb_read_frames",
                               "-of", "json", str(path)], log=True))


def validate(path: Path, ffmpeg: str, ffprobe: str, width: int, height: int):
    info = probe(path, ffprobe)
    video = next((s for s in info["streams"] if s.get("codec_type") == "video"), None)
    audio = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    assert video and video["width"] == width and video["height"] == height, info
    assert video["codec_name"] == "h264" and int(video["nb_read_frames"]) == FRAMES, info
    assert audio and audio["codec_name"] == "aac", info
    assert abs(float(info["format"]["duration"])-DURATION) <= .09, info
    command([ffmpeg, "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-"])
    return info


def make_contact_sheet(frames: Path, font: Path, out: Path):
    ids = [0, 12, 60, 80, 105, 118, 124, 136, 168, 200, 220, 274, 324, 356]
    tile_w, tile_h = 216, 384
    atlas = Image.new("RGB", (tile_w*7, (tile_h+26)*2), (18, 17, 22))
    d = ImageDraw.Draw(atlas)
    label_font = ImageFont.load_default()
    for n, i in enumerate(ids):
        with Image.open(frames/f"frame-{i:04d}.png") as raw:
            im = compose_frame(raw.convert("RGB"), i, font)
            im.thumbnail((tile_w, tile_h), Image.Resampling.LANCZOS)
        x = (n%7)*tile_w
        y = (n//7)*(tile_h+26)
        atlas.paste(im, (x+(tile_w-im.width)//2, y))
        d.text((x+8, y+tile_h+4), f"{i/FPS:04.2f}s · {i:03d}", font=label_font,
               fill=(230, 226, 230))
    atlas.save(out, optimize=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--font", type=Path, default=Path("public/fonts/Manrope.ttf"))
    p.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    p.add_argument("--ffprobe", default=shutil.which("ffprobe"))
    p.add_argument("--name", default=NAME)
    p.add_argument("--skip-decode-check", action="store_true")
    a = p.parse_args()
    if not a.ffmpeg or not a.ffprobe:
        p.error("FFmpeg and FFprobe are required, provide --ffmpeg and --ffprobe")
    a.frames = a.frames.resolve()
    a.out = a.out.resolve()
    a.font = a.font.resolve()
    if not a.font.is_file():
        p.error(f"Required original Manrope font unavailable: {a.font}")
    missing = [str(i) for i in range(FRAMES)
               if not (a.frames/f"frame-{i:04d}.png").is_file()]
    if missing:
        p.error(f"{len(missing)} source frames missing (first: {', '.join(missing[:12])})")
    with Image.open(a.frames/"frame-0000.png") as first:
        width, height = first.size
    if (width, height) not in {(540, 960), (1080, 1920)}:
        p.error(f"Unexpected frame size {(width, height)}; expected 540x960 or 1080x1920.")
    a.out.mkdir(parents=True, exist_ok=True)
    wav = a.out/"motion-001-v6-provisional-synthetic.wav"
    motion_report = a.frames / "render-report.json"
    impacts = None
    if motion_report.is_file():
        data = json.loads(motion_report.read_text(encoding="utf-8"))
        impacts = data.get("impact_events_s")
        if not isinstance(impacts, list) or not impacts or abs(float(impacts[0])-4.90) > .03:
            raise ValueError("Unexpected contact timing in render-report.json")
    audio_sketch(wav, impacts)

    out = a.out/f"{a.name}-{width}x{height}.mp4"
    cmd = [str(a.ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
           "-r", str(FPS), "-i", "-", "-i", str(wav),
           "-map", "0:v:0", "-map", "1:a:0", "-frames:v", str(FRAMES),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-ar", str(RATE), "-t", str(DURATION),
           "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for i in range(FRAMES):
            with Image.open(a.frames/f"frame-{i:04d}.png") as im:
                if im.size != (width, height):
                    raise ValueError(f"Frame {i} has inconsistent dimensions: {im.size}")
                buf = compose_frame(im.convert("RGB"), i, a.font)
                proc.stdin.write(buf.tobytes())
        proc.stdin.close()
        error = proc.stderr.read().decode("utf-8", "replace")
        if proc.wait() != 0:
            raise RuntimeError(error[-5000:])
    except Exception:
        proc.kill()
        proc.wait()
        out.unlink(missing_ok=True)
        raise

    files = [out]
    if width == 1080:
        small = a.out/f"{a.name}-540x960.mp4"
        command([str(a.ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
                 "-i", str(out), "-vf", "scale=540:960:flags=lanczos",
                 "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                 "-pix_fmt", "yuv420p", "-c:a", "copy",
                 "-movflags", "+faststart", str(small)])
        files.append(small)
    make_contact_sheet(a.frames, a.font, a.out/"motion-001-v6-contact-sheet.png")
    reports = {}
    for item in files:
        expected = (540, 960) if "-540x960" in item.name else (width, height)
        reports[item.name] = (probe(item, a.ffprobe) if a.skip_decode_check else
                              validate(item, a.ffmpeg, a.ffprobe, *expected))
    (a.out/"motion-001-v6-validation.json").write_text(
        json.dumps({"status": "technical_validation_only",
                    "editorial_approval": False,
                    "synthetic_audio": True, "outputs": reports}, indent=2),
        encoding="utf-8")
    for item in files:
        print("RENDERED_AND_PROBED", item)


if __name__ == "__main__":
    main()
