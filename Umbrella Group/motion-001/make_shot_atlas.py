"""Orient the LP's existing print for the inverted hero shot.

This makes a local shot variant of the supplied atlas. It does not redraw the
wordmark or modify the LP source texture.
"""
from pathlib import Path

from PIL import Image


source = Path(__file__).resolve().parent / "source" / "umbrella-print-atlas.png"
target = source.with_name("umbrella-print-atlas-inverted-shot.png")
atlas = Image.open(source).convert("RGBA")
bounds = atlas.getbbox()
if atlas.size != (4096, 1024) or bounds is None or bounds[2] > 512:
    raise ValueError("Unexpected print atlas layout; refusing to alter a different asset")
wordmark = atlas.crop(bounds)
atlas.paste(Image.new("RGBA", wordmark.size), bounds[:2])
atlas.paste(wordmark.transpose(Image.Transpose.ROTATE_180), bounds[:2])
atlas.save(target)
print(target)
