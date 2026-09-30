"""Convert the original's images into standard PNGs in images/.

Usage: python tools/extract_images.py

Most of the app's PNGs are Apple's iPhone-only "CgBI" variant: the pixel data has no zlib
header, the colours are stored blue-green-red, and the colours are premultiplied by
transparency. This fixes all three. Standard PNGs and JPEGs are copied as they are.

Only the 1x images are converted (320 by 480 point screens). Shared images go to images/,
each language's to images/<code>/ (English, de, es, fr, it), keeping the original names.
"""

import io
import shutil
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bopit.config import ORIGINAL_APP_DIR, PROJECT_ROOT  # noqa: E402

IMAGES_DIR = PROJECT_ROOT / "images"
LANGUAGE_FOLDERS = {"English.lproj": "en", "de.lproj": "de", "es.lproj": "es",
                    "fr.lproj": "fr", "it.lproj": "it"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunks(data: bytes):
    pos = len(PNG_SIGNATURE)
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def chunk(kind: bytes, body: bytes) -> bytes:
    return (struct.pack(">I", len(body)) + kind + body
            + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))


def uncrush(data: bytes) -> Image.Image:
    """A CgBI PNG as a normal RGBA image."""
    parts = list(chunks(data))
    pixels = zlib.decompress(b"".join(b for k, b in parts if k == b"IDAT"), -15)
    rebuilt = PNG_SIGNATURE
    for kind, body in parts:
        if kind == b"CgBI":
            continue
        if kind == b"IDAT":
            continue
        if kind == b"IEND":
            rebuilt += chunk(b"IDAT", zlib.compress(pixels))
        rebuilt += chunk(kind, body)
    image = Image.open(io.BytesIO(rebuilt))
    image.load()
    array = np.array(image.convert("RGBA"), dtype=np.float32)
    array[..., [0, 2]] = array[..., [2, 0]]
    alpha = array[..., 3:4]
    visible = alpha[..., 0] > 0
    array[visible, :3] = np.clip(array[visible, :3] * 255.0 / alpha[visible], 0, 255)
    return Image.fromarray(array.round().astype(np.uint8), "RGBA")


def convert(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    if source.suffix.lower() == ".png" and b"CgBI" in data[:40]:
        uncrush(data).save(target)
    else:
        shutil.copy2(source, target)


def main() -> None:
    folders = [(ORIGINAL_APP_DIR, IMAGES_DIR)]
    folders += [(ORIGINAL_APP_DIR / name, IMAGES_DIR / code)
                for name, code in LANGUAGE_FOLDERS.items()]
    failed: list[str] = []
    for source_dir, target_dir in folders:
        count = 0
        for source in sorted(source_dir.iterdir()):
            if source.suffix.lower() not in (".png", ".jpg") or "@2x" in source.name:
                continue
            try:
                convert(source, target_dir / source.name)
                count += 1
            except Exception as error:
                failed.append(f"{source.name}: {error}")
        print(f"{target_dir.relative_to(PROJECT_ROOT).as_posix()}: {count}")
    for failure in failed:
        print(f"failed {failure}")


if __name__ == "__main__":
    main()
