"""Encode a numbered PNG sequence and local WAV with Blender's bundled FFmpeg."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--wav", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--count", type=int, default=360)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    frames = args.frames.resolve()
    wav = args.wav.resolve()
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    for index in range(args.count):
        image = frames / f"frame-{index:04d}.png"
        if not image.is_file():
            raise FileNotFoundError(image)
    if not wav.is_file():
        raise FileNotFoundError(wav)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = args.count
    scene.render.use_sequencer = True
    editor = scene.sequence_editor_create()
    sequence = editor.sequences.new_image("Umbrella Motion 001", str(frames / "frame-0000.png"), 1, 1)
    for index in range(1, args.count):
        sequence.elements.append(f"frame-{index:04d}.png")
    editor.sequences.new_sound("Provisional umbrella foley", str(wav), 2, 1)

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.audio_mixrate = 48000
    scene.render.ffmpeg.audio_channels = "MONO"
    scene.render.ffmpeg.audio_bitrate = 160
    scene.render.filepath = str(output)
    scene.render.use_file_extension = False
    bpy.ops.render.render(animation=True)
    print("UMBRELLA_VIDEO", output, flush=True)


if __name__ == "__main__":
    main()
