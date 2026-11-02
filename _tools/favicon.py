"""Draw the site's favicon: a single thick squiggle, like a monospace '~'.

Usage (from the repo root):
    python3 _tools/favicon.py

Writes assets/favicon.svg (used by modern browsers)
and assets/favicon.png (fallback), both from the same curve below.
"""
import os
import struct
import zlib

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

# the squiggle, in a 32x32 box: two cubic curves forming one smooth wave
START = (4, 19)
CURVES = [((8, 10), (13, 10), (16, 16)),
          ((19, 22), (24, 22), (28, 13))]
STROKE = 4.2
INK = "#FFFFFF"


def svg():
    (c1, c2, e1), (d1, d2, e2) = CURVES
    path = (f"M{START[0]} {START[1]} C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {e1[0]} {e1[1]} "
            f"C{d1[0]} {d1[1]} {d2[0]} {d2[1]} {e2[0]} {e2[1]}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <path d="{path}" fill="none" stroke="{INK}" stroke-width="{STROKE}" stroke-linecap="round"/>
</svg>
"""


def points(steps=60):
    pts, p0 = [START], START
    for c1, c2, p3 in CURVES:
        for i in range(1, steps + 1):
            t = i / steps
            u = 1 - t
            pts.append(tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                             for a, b, c, d in zip(p0, c1, c2, p3)))
        p0 = p3
    return pts


def dist_to_segment(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def png(size=64, samples=4):
    pts = points()
    segs = list(zip(pts, pts[1:]))
    scale, r = 32 / size, STROKE / 2
    ink = tuple(int(INK[i:i + 2], 16) for i in (1, 3, 5))
    rows = []
    for y in range(size):
        row = bytearray([0])                         # PNG filter byte
        for x in range(size):
            hit = 0
            for sy in range(samples):
                for sx in range(samples):
                    px = (x + (sx + 0.5) / samples) * scale
                    py = (y + (sy + 0.5) / samples) * scale
                    if min(dist_to_segment(px, py, a, b) for a, b in segs) <= r:
                        hit += 1
            row += bytes(ink) + bytes([round(255 * hit / samples ** 2)])
        rows.append(bytes(row))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
            + chunk(b"IEND", b""))


with open(os.path.join(ASSETS, "favicon.svg"), "w") as f:
    f.write(svg())
with open(os.path.join(ASSETS, "favicon.png"), "wb") as f:
    f.write(png())
print("Wrote assets/favicon.svg and assets/favicon.png")
