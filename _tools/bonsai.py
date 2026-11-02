"""Draw the homepage's ASCII bonsai (leaves of '&', wood of / | \\ ~ _, roots)
with the site's links spelled out inside the foliage.

Usage (from the repo root):
    python3 _tools/bonsai.py              rewrite the tree inside index.html
    python3 _tools/bonsai.py --preview    print the tree as plain text instead

The folder starts with "_" so GitHub Pages (Jekyll) leaves it off the live site.
The random seed is fixed, so the same settings always draw the same tree.
Change the seed for a new variation, or edit PADS to move leaf pads and links.
scripts/tree.js animates whatever this script puts in the page.
"""
import math
import os
import random
import sys
from html import escape

INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")

# Set True to wrap each character in a colour class (l1-l4 leaves, w1-w2 wood,
# ground). The site currently renders the tree in a single colour.
COLOURS = False

W, H = 96, 37
rnd = random.Random(11)
chars = [[" "] * W for _ in range(H)]
kind = [[None] * W for _ in range(H)]     # css class per cell
link_at = {}                              # (x, y) -> link index


def put(x, y, ch, k, force=True):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H and (force or chars[y][x] == " "):
        chars[y][x], kind[y][x] = ch, k


def leaf_class():
    return rnd.choice(["l1", "l1", "l2", "l2", "l3", "l4"])


def wood_class():
    return rnd.choice(["w1", "w1", "w2"])


# ------------------------------------------------------------------ layout
GROUND_Y = 30                                 # where the trunk meets the roots
# leaf pads: (cx, cy, rx, ry, link label, href, hover colour)
PADS = [
    (46, 3, 14, 2.6, "About", "about.html", "#7dd87d"),
    (23, 9, 16, 2.6, "Work Archive", "work.html", "#ff8a94"),
    (71, 8, 14, 2.6, "GitHub", "https://github.com/victorvd98", "#66b3ff"),
    (77, 16, 12, 2.3, "Are.na", "https://www.are.na/victor-van-damme/", "#ffcc66"),
    (19, 18, 12, 2.3, "E-mail", "mailto:victor.van.damme@icloud.com", "#836953"),
    (57, 12, 7, 1.7, None, None, None),
    (35, 14, 7, 1.7, None, None, None),
    (63, 22, 7, 1.5, None, None, None),
    (31, 24, 8, 1.6, None, None, None),
]


def trunk_x(y):
    t = (GROUND_Y - y) / (GROUND_Y - 5)                 # 0 at the base, 1 near the crown
    return 48 + 4 * math.sin(t * math.pi * 1.5) - 2 * t


# ------------------------------------------------------------------ leaves
for cx, cy, rx, ry, *_ in PADS:
    blobs = [(cx, cy, rx, ry),
             (cx - rx * 0.5, cy + ry * 0.2, rx * 0.55, ry * 0.8),
             (cx + rx * 0.5, cy - ry * 0.15, rx * 0.55, ry * 0.85)]
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx * 1.3), int(cx + rx * 1.3) + 1):
            d = min(((x - bx) / brx) ** 2 + ((y - by) / bry) ** 2
                    for bx, by, brx, bry in blobs) + rnd.uniform(-0.2, 0.2)
            if d <= 1 and rnd.random() < (0.85 if d < 0.7 else 0.55):
                put(x, y, "&", leaf_class())


# ------------------------------------------------------------------ wood
def wood(x, y, dx, dy, force):
    if dy < 0 and dx < 0:
        ch = "\\"
    elif dy < 0 and dx > 0:
        ch = "/"
    elif dy < 0:
        ch = "|"
    else:
        ch = rnd.choice(["~", "_", "~"])
    # inside the foliage only some of the wood shows through
    if force or chars[int(round(y))][int(round(x))] == " " or rnd.random() < 0.45:
        put(x, y, ch, wood_class())


# trunk: two strands near the base that merge higher up
for y in range(GROUND_Y - 1, 4, -1):
    t = (GROUND_Y - y) / (GROUND_Y - 5)
    x = trunk_x(y)
    dx = trunk_x(y - 1) - x
    step = 1 if dx > 0.25 else -1 if dx < -0.25 else 0
    wood(x, y, step, -1, force=False)
    if t < 0.45:
        wood(x + 2 - t * 2, y, step, -1, force=False)


def branch(x0, y0, x1, y1):
    """Walk cell by cell from the trunk out to a pad, mostly sideways."""
    x, y = int(round(x0)), int(round(y0))
    x1, y1 = int(round(x1)), int(round(y1))
    while (x, y) != (x1, y1):
        dx = (x1 > x) - (x1 < x)
        dy = (y1 > y) - (y1 < y)
        # rise only part of the time, so branches sweep outwards
        if dx and dy and rnd.random() < 0.55:
            dy = 0
        x, y = x + dx, y + dy
        wood(x, y, dx, dy, force=False)


for cx, cy, rx, ry, *_ in PADS:
    ty = min(max(cy + ry + 3, 6), GROUND_Y - 4)
    tx = trunk_x(ty)
    branch(tx, ty, cx + (rx * 0.3 if cx < tx else -rx * 0.3), cy + 1)

# ------------------------------------------------------------------ roots
# each root leaves the base, dips down at first, then creeps along the ground
base_x = trunk_x(GROUND_Y - 1)
for side, start, length, dive in [(-1, 0, 30, 0.7), (-1, 1, 18, 0.5), (-1, 0, 10, 0.9),
                                  (1, 2, 32, 0.7), (1, 1, 20, 0.5), (1, 3, 11, 0.9)]:
    x, y = int(round(base_x)) + start, GROUND_Y
    for s in range(length):
        down = y < GROUND_Y + 4 and rnd.random() < dive * (1 - s / length)
        x += side
        if down:
            y += 1
            ch = "/" if side < 0 else "\\"
        else:
            ch = rnd.choice(["_", "_", "~"])
        put(x, y, ch, wood_class(), force=False)

# a faint ground line under the roots
for x in range(int(base_x) - 36, int(base_x) + 38):
    if rnd.random() < 0.3:
        put(x, GROUND_Y + 5, rnd.choice([".", "_", "-"]), "ground", force=False)

# ------------------------------------------------------------------ hidden labels
links = []
for cx, cy, rx, ry, label, href, colour in PADS:
    if not label:
        continue
    idx = len(links)
    links.append((href, colour))
    y = int(cy)
    x0 = int(round(cx - len(label) / 2))
    for i, ch in enumerate(label):
        put(x0 + i, y, ch, leaf_class())
        link_at[(x0 + i, y)] = idx
    # a clearing either side so the title reads against the leaves
    for x in (x0 - 1, x0 + len(label)):
        chars[y][x] = " "

# ------------------------------------------------------------------ output
out_html, out_txt = [], []
for y in range(H):
    row_txt = "".join(chars[y]).rstrip()
    parts, cur_link, cur_cls, buf = [], None, None, ""

    def flush():
        global buf
        if buf:
            parts.append(f'<span class="{cur_cls}">{escape(buf, quote=False)}</span>' if cur_cls else escape(buf, quote=False))
        buf = ""

    for x in range(len(row_txt)):
        ch, li = chars[y][x], link_at.get((x, y))
        cls = kind[y][x] if COLOURS and ch != " " else None
        if li != cur_link:
            flush()
            if cur_link is not None:
                parts.append("</a>")
            if li is not None:
                href, colour = links[li]
                ext = ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""
                parts.append(f'<a class="tree-link" href="{href}"{ext} style="--hover: {colour}">')
            cur_link = li
            cur_cls = None
        if cls != cur_cls:
            flush()
            cur_cls = cls
        buf += ch
    flush()
    if cur_link is not None:
        parts.append("</a>")
    out_html.append("".join(parts))
    out_txt.append(row_txt)

while out_txt and not out_txt[0].strip():
    out_txt.pop(0)
    out_html.pop(0)
while out_txt and not out_txt[-1].strip():
    out_txt.pop()
    out_html.pop()

if "--preview" in sys.argv:
    print("\n".join(out_txt))
else:
    with open(INDEX) as f:
        page = f.read()
    start = page.index("<pre>", page.index('<nav class="tree"')) + len("<pre>\n")
    end = page.index("</pre>", start)
    with open(INDEX, "w") as f:
        f.write(page[:start] + "\n".join(out_html) + "\n" + page[end:])
    print("Updated the tree in index.html")
