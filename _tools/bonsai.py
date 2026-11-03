"""Draw the homepage's ASCII bonsai (leaves of '&', wood of / | \\ ~ _, roots)
with the site's links spelled out inside the foliage.

This is the desktop homepage. Phones and narrow windows get a fish instead
(_tools/fish.py); styles/styles.css shows one or the other.

Usage (from the repo root):
    python3 _tools/bonsai.py              rewrite the tree inside index.html
    python3 _tools/bonsai.py --preview    print the tree as plain text instead

The folder starts with "_" so GitHub Pages (Jekyll) leaves it off the live site.
Each tree's random seed is fixed, so the same settings always draw the same tree.
Change a seed for a new variation, or edit its pads to move leaf pads and links.
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

ABOUT = ("About", "/about/", "#7dd87d")
WORK = ("Work Archive", "/work/", "#ff8a94")
GITHUB = ("GitHub", "https://github.com/victorvd98", "#66b3ff")
ARENA = ("Are.na", "https://www.are.na/victor-van-damme/", "#ffcc66")
EMAIL = ("E-mail", "mailto:victor.van.damme@icloud.com", "#836953")
NONE = (None, None, None)

TREES = {
    "wide": dict(
        size=(96, 37), seed=11,
        ground_y=30,                              # where the trunk meets the roots
        trunk=(48, 4, 2),                         # base column, sway, lean
        # leaf pads: (cx, cy, rx, ry) + (link label, href, hover colour)
        pads=[
            ((46, 3, 14, 2.6), ABOUT),
            ((23, 9, 16, 2.6), WORK),
            ((71, 8, 14, 2.6), GITHUB),
            ((77, 16, 12, 2.3), ARENA),
            ((19, 18, 12, 2.3), EMAIL),
            ((57, 12, 7, 1.7), NONE),
            ((35, 14, 7, 1.7), NONE),
            ((63, 22, 7, 1.5), NONE),
            ((31, 24, 8, 1.6), NONE),
        ],
        # roots: (side, start offset, length, how eagerly it dives)
        roots=[(-1, 0, 30, 0.7), (-1, 1, 18, 0.5), (-1, 0, 10, 0.9),
               (1, 2, 32, 0.7), (1, 1, 20, 0.5), (1, 3, 11, 0.9)],
        ground=(-36, 38),
    ),
}


def draw(size, seed, ground_y, trunk, pads, roots, ground):
    W, H = size
    rnd = random.Random(seed)
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

    base, sway, lean = trunk

    def trunk_x(y):
        t = (ground_y - y) / (ground_y - 5)                 # 0 at the base, 1 near the crown
        return base + sway * math.sin(t * math.pi * 1.5) - lean * t

    # -------------------------------------------------------------- leaves
    for (cx, cy, rx, ry), _ in pads:
        blobs = [(cx, cy, rx, ry),
                 (cx - rx * 0.5, cy + ry * 0.2, rx * 0.55, ry * 0.8),
                 (cx + rx * 0.5, cy - ry * 0.15, rx * 0.55, ry * 0.85)]
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx * 1.3), int(cx + rx * 1.3) + 1):
                d = min(((x - bx) / brx) ** 2 + ((y - by) / bry) ** 2
                        for bx, by, brx, bry in blobs) + rnd.uniform(-0.2, 0.2)
                if d <= 1 and rnd.random() < (0.85 if d < 0.7 else 0.55):
                    put(x, y, "&", leaf_class())

    # -------------------------------------------------------------- wood
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
    for y in range(ground_y - 1, 4, -1):
        t = (ground_y - y) / (ground_y - 5)
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

    for (cx, cy, rx, ry), _ in pads:
        ty = min(max(cy + ry + 3, 6), ground_y - 4)
        tx = trunk_x(ty)
        branch(tx, ty, cx + (rx * 0.3 if cx < tx else -rx * 0.3), cy + 1)

    # -------------------------------------------------------------- roots
    # each root leaves the base, dips down at first, then creeps along the ground
    base_x = trunk_x(ground_y - 1)
    for side, start, length, dive in roots:
        x, y = int(round(base_x)) + start, ground_y
        for s in range(length):
            down = y < ground_y + 4 and rnd.random() < dive * (1 - s / length)
            x += side
            if down:
                y += 1
                ch = "/" if side < 0 else "\\"
            else:
                ch = rnd.choice(["_", "_", "~"])
            put(x, y, ch, wood_class(), force=False)

    # a faint ground line under the roots
    for x in range(int(base_x) + ground[0], int(base_x) + ground[1]):
        if rnd.random() < 0.3:
            put(x, ground_y + 5, rnd.choice([".", "_", "-"]), "ground", force=False)

    # -------------------------------------------------------------- hidden labels
    links = []
    for (cx, cy, rx, ry), (label, href, colour) in pads:
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
            if 0 <= x < W:
                chars[y][x] = " "

    # -------------------------------------------------------------- output
    out_html, out_txt = [], []
    for y in range(H):
        row_txt = "".join(chars[y]).rstrip()
        parts, cur_link, cur_cls, buf = [], None, None, [""]

        def flush():
            if buf[0]:
                text = escape(buf[0], quote=False)
                parts.append(f'<span class="{cur_cls}">{text}</span>' if cur_cls else text)
            buf[0] = ""

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
            buf[0] += ch
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
    return out_html, out_txt


if "--preview" in sys.argv:
    for name, settings in TREES.items():
        print(f"--- {name}")
        print("\n".join(draw(**settings)[1]))
else:
    with open(INDEX) as f:
        page = f.read()
    for name, settings in TREES.items():
        tag = f'<pre class="tree-{name}">'
        start = page.index(tag) + len(tag) + 1
        end = page.index("</pre>", start)
        page = page[:start] + "\n".join(draw(**settings)[0]) + "\n" + page[end:]
    with open(INDEX, "w") as f:
        f.write(page)
    print("Updated the tree in index.html")
