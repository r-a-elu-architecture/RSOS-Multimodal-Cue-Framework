"""Convert an image (for example the lock-screen PNG from docs/device.html) into a display file for the RSOS display
module: 240 x 240 pixels, RGB565 little-endian, saved as data/img/<name>.rgb. Upload the data folder with
`pio run -e display -t uploadfs`; then `D <t> <dur> <name>` shows it.

  python make_image.py lion.png lion
"""
import pathlib
import re
import sys

SIZE = 240


def convert(src, name, out_dir="data/img"):
    if not re.fullmatch(r"[a-z0-9_-]{1,23}", name):
        raise ValueError("the name must be 1-23 characters of a-z, 0-9, _ and - (it names a file, never a path)")
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((SIZE, SIZE))
    buf = bytearray()
    for r, g, b in im.getdata():
        v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        buf += bytes((v & 0xFF, v >> 8))
    out = pathlib.Path(out_dir) / f"{name}.rgb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(buf)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)
    print(convert(sys.argv[1], sys.argv[2]))
