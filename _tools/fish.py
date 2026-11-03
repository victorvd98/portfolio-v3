"""Draw the phone homepage's ASCII fish: lying diagonally down the screen, head
top right, tail bottom left. It's drawn in the same characters as the desktop
tree: outlined in its wood strokes / | \\ _ ~, with scales of ; : , . (heavy
along the back, thinning towards the belly) and '&' gathered under the dorsal fin. The
site's links are written on its body. scripts/fish.js makes it twitch and flop.

Usage (from the repo root):
    python3 _tools/fish.py                  rewrite the fish inside index.html
    python3 _tools/fish.py --preview        print it as plain text
    python3 _tools/fish.py --preview --all  ...with every tail frame

Shapes are worked out in "visual" units (em), so the diagonal looks right even
though a character cell is taller than it is wide. The tail is drawn in several
frames; each tail cell is written out as <span class="tail" data-f="...">
holding its character in every frame, so the script can flick the tail without
touching the rest of the fish.
"""
import math
import os
import random
import sys
from html import escape

INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")

CW, LH = 0.6, 1.15                          # a cell is 0.6em wide, 1.15em tall
TILT = math.radians(32)                     # head leans this far right of straight up
A, B = 16.0, 7.0                            # body half-length, half-width (em)
TAIL_LEN = 9.5
BENDS = (0.0, math.radians(14), math.radians(-14))   # tail at rest, flicked each way
SEED = 4

LINKS = [                                   # head to tail along the body
    ("About", "/about/", "#7dd87d"),
    ("Work Archive", "/work/", "#ff8a94"),
    ("GitHub", "https://github.com/victorvd98", "#66b3ff"),
    ("Are.na", "https://www.are.na/victor-van-damme/", "#ffcc66"),
    ("E-mail", "mailto:victor.van.damme@icloud.com", "#836953"),
]

# a generous working grid; the finished fish is cropped out of it
GW, GH = 80, 60
CU, CV = GW * CW / 2, GH * LH / 2
AX = (math.sin(TILT), -math.cos(TILT))      # along the body, towards the head
AC = (math.cos(TILT), math.sin(TILT))       # across it, towards the belly
rnd = random.Random(SEED)


def frame_of(x, y):
    """Cell -> (along, across) in em, measured from the middle of the body."""
    du, dv = (x + 0.5) * CW - CU, (y + 0.5) * LH - CV
    return du * AX[0] + dv * AX[1], du * AC[0] + dv * AC[1]


def cell_of(s, t):
    return (int((CU + s * AX[0] + t * AC[0]) / CW),
            int((CV + s * AX[1] + t * AC[1]) / LH))


def half_width(s):
    """A rounded head, widest just behind it, tapering to a slim tail end."""
    if not -A < s < A:
        return 0.0
    k = (s + A) / (2 * A)                                   # 0 at the tail, 1 at the nose
    return B * (0.28 + 0.72 * math.sin(math.pi * k ** 0.85) ** 0.75) * (1 - k ** 10) ** 0.7


def dorsal(s, t):                                           # a low fin along the back
    lo, hi = -A * 0.35, A * 0.15
    if not lo < s < hi:
        return False
    k = (s - lo) / (hi - lo)
    return 0 < -t - half_width(s) < 1.6 * math.sin(math.pi * k) * (1.3 - k)


def belly_fin(s, t):                                        # and a small one underneath
    lo, hi = -A * 0.62, -A * 0.3
    if not lo < s < hi:
        return False
    k = (s - lo) / (hi - lo)
    return 0 < t - half_width(s) < 1.4 * math.sin(math.pi * k) * (0.3 + k)


def body(s, t):
    return abs(t) < half_width(s) or dorsal(s, t) or belly_fin(s, t)


def tail(s, t, bend):
    """A forked tail fanning out behind the body."""
    bs = -A + 0.6
    ds, dt = s - bs, t
    r = math.hypot(ds, dt)
    ang = math.atan2(dt, -ds) - bend                        # 0 = straight back
    spread = math.radians(36)
    if r < 0.2 or abs(ang) > spread:
        return False
    return r < TAIL_LEN * (0.55 + 0.45 * (abs(ang) / spread) ** 1.6)


def stroke(du, dv):
    """The character for a line running in this direction (em, y down)."""
    ang = math.degrees(math.atan2(-dv, du)) % 180
    if ang < 22 or ang > 158:
        return "_"
    if ang < 68:
        return "/"
    if ang < 112:
        return "|"
    return "\\"


def outline_char(x, y, solid):
    """Edge character: runs at right angles to the way out of the shape."""
    nu = nv = 0.0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if (dx or dy) and not solid(x + dx, y + dy):
                nu += dx * CW
                nv += dy * LH
    return stroke(-nv, nu)


LEAF = "&"


def shade(s, t):
    """Scales: heavy ; and : along the back, thinning to , and . on the belly.
    The tree's '&' gather along the back, under the dorsal fin."""
    w = half_width(s) or 1
    k = (t + w) / (2 * w)                                   # 0 on the back, 1 on the belly
    if rnd.random() > max(0.0, 0.95 - 0.7 * k):
        return " "
    r = rnd.random()
    if rnd.random() < 0.06 + 0.6 * max(0.0, 1 - k / 0.4) ** 1.5:
        return LEAF
    if k < 0.35:
        return ";" if r < 0.6 else ":"
    if k < 0.65:
        return ":" if r < 0.45 else (";" if r < 0.6 else ",")
    return "," if r < 0.5 else "."


def wood(ch):
    """Long flat edges get the tree's mix of _ and ~."""
    return rnd.choice(["_", "~", "_"]) if ch == "_" else ch


# ------------------------------------------------------------------ body
grid = [[" "] * GW for _ in range(GH)]
link_at = {}
in_body = lambda x, y: 0 <= x < GW and 0 <= y < GH and body(*frame_of(x, y))
GILL = A * 0.5

for y in range(GH):
    for x in range(GW):
        if not in_body(x, y):
            continue
        s, t = frame_of(x, y)
        if not all(in_body(x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
            grid[y][x] = wood(outline_char(x, y, in_body))
        elif abs(t) < half_width(s):
            grid[y][x] = shade(s, t) if s < GILL else " "
        else:
            # fins: the dorsal fin is thick with '&', the belly fin light
            grid[y][x] = (LEAF if rnd.random() < 0.6 else "~") if t < 0 else \
                ("~" if rnd.random() < 0.4 else " ")

# head: a curved gill line, an eye, a mouth, and a little shading on top
for y in range(GH):
    for x in range(GW):
        s, t = frame_of(x, y)
        w = half_width(s)
        if not (abs(t) < w and grid[y][x] in " " + LEAF + ";:,."):
            continue
        arc = GILL + 0.8 - 1.2 * (t / B) ** 2
        if abs(s - arc) < 0.4:
            grid[y][x] = stroke(AC[0] - 0.4 * t / B * AX[0], AC[1] - 0.4 * t / B * AX[1])
        elif s > arc + 0.4 and (t + w) / (2 * w) < 0.3 and rnd.random() < 0.6:
            grid[y][x] = rnd.choice([";", ":", LEAF])               # the top of the head
ex, ey = cell_of(A * 0.76, -B * 0.05)
grid[ey][ex - 1], grid[ey][ex], grid[ey][ex + 1] = "(", "X", ")"        # a dead fish eye


def draw_line(points, ch=None):
    """A stroke between points given as (along, across), in body coordinates."""
    cells = []
    for (s0, t0), (s1, t1) in zip(points, points[1:]):
        x0, y0 = CU + s0 * AX[0] + t0 * AC[0], CV + s0 * AX[1] + t0 * AC[1]
        x1, y1 = CU + s1 * AX[0] + t1 * AC[0], CV + s1 * AX[1] + t1 * AC[1]
        c = ch or stroke(x1 - x0, y1 - y0)
        n = int(math.hypot(x1 - x0, y1 - y0) / 0.2) + 1
        for k in range(n + 1):
            x, y = int((x0 + (x1 - x0) * k / n) / CW), int((y0 + (y1 - y0) * k / n) / LH)
            grid[y][x] = c
            cells.append((x, y))
    return cells


# mouth: a slightly open jaw at the tip of the snout, on the belly side
# (a side-on fish's mouth runs from the tip of the snout back along its middle)
draw_line([(A * 0.99, B * 0.0), (A * 0.86, B * 0.1)])
mx, my = cell_of(A * 0.845, B * 0.14)
grid[my][mx] = ","

# side fin: a fan of rays just behind the gill, sweeping back towards the tail
fin = set()
base = (GILL - 0.6, B * 0.28)
for k, ang in enumerate([-0.55, -0.25, 0.05, 0.35]):           # radians from straight back
    ang += 0.25                                                  # tipped towards the belly
    tip = (base[0] - 4.6 * math.cos(ang), base[1] + 4.6 * math.sin(ang))
    fin.update(draw_line([base, tip]))
fin_edge = [(base[0] - 4.6 * math.cos(a + 0.25), base[1] + 4.6 * math.sin(a + 0.25))
            for a in (-0.55, -0.25, 0.05, 0.35)]
fin.update(draw_line(fin_edge, "~"))
# clear the scales between the rays so the fin reads
for y in range(GH):
    for x in range(GW):
        s, t = frame_of(x, y)
        r = math.hypot(s - base[0], t - base[1])
        a = math.atan2(t - base[1], -(s - base[0])) - 0.25
        if 0.3 < r < 4.4 and -0.55 < a < 0.35 and (x, y) not in fin:
            grid[y][x] = " "
            fin.add((x, y))

# ------------------------------------------------------------------ titles
# scattered over the body (head to tail in order), each somewhere it fits:
# on the scales, clear of the outline, the side fin and the other titles
place = random.Random(SEED + 1)
rows_taken = set()
for i, (label, href, colour) in enumerate(LINKS):
    for attempt in range(400):
        s = A * (0.3 - 0.235 * i) + place.uniform(-1.6, 1.6)
        t = place.uniform(-B, B)
        x, y = cell_of(s, t)
        x0 = int(round(x + 0.5 - len(label) / 2))
        span = [(xx, y) for xx in range(x0 - 1, x0 + len(label) + 1)]
        def fits(xx, yy):
            ss, tt = frame_of(xx, yy)
            return abs(tt) < half_width(ss) - 1.1 and ss < GILL - 0.3 and (xx, yy) not in fin
        # every title gets a row of its own, with a row of scales between titles
        if all(fits(*c) for c in span) and not any(y + d in rows_taken for d in (-1, 0, 1)):
            break
    else:
        raise SystemExit(f"no room for {label}")
    rows_taken.add(y)
    for xx, yy in span:
        grid[yy][xx] = " "
    for j, ch in enumerate(label):
        grid[y][x0 + j] = ch
        link_at[(x0 + j, y)] = i

# ------------------------------------------------------------------ tail frames
tail_cells = {}                             # (x, y) -> [char per frame]
for f, bend in enumerate(BENDS):
    in_tail = lambda x, y: 0 <= x < GW and 0 <= y < GH and tail(*frame_of(x, y), bend) \
        and not in_body(x, y)
    for y in range(GH):
        for x in range(GW):
            if not in_tail(x, y):
                continue
            edge = not all(in_tail(x + dx, y + dy) or in_body(x + dx, y + dy)
                           for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
            ch = wood(outline_char(x, y, lambda a, b: in_tail(a, b) or in_body(a, b))) if edge \
                else ("~" if rnd.random() < 0.4 else " ")
            tail_cells.setdefault((x, y), [" "] * len(BENDS))[f] = ch

# ------------------------------------------------------------------ crop
used = [(x, y) for y in range(GH) for x in range(GW) if grid[y][x] != " "] + list(tail_cells)
X0, Y0 = min(x for x, _ in used), min(y for _, y in used)
X1, Y1 = max(x for x, _ in used), max(y for _, y in used)


def text(frame):
    rows = []
    for y in range(Y0, Y1 + 1):
        row = [tail_cells[(x, y)][frame] if (x, y) in tail_cells else grid[y][x]
               for x in range(X0, X1 + 1)]
        rows.append("".join(row).rstrip())
    return rows


def html():
    out = []
    for y in range(Y0, Y1 + 1):
        parts, cur = [], None
        cells = [x for x in range(X0, X1 + 1) if grid[y][x] != " " or (x, y) in tail_cells]
        for x in range(X0, (max(cells) + 1) if cells else X0):
            li = link_at.get((x, y))
            if li != cur:
                if cur is not None:
                    parts.append("</a>")
                if li is not None:
                    label, href, colour = LINKS[li]
                    ext = ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""
                    parts.append(f'<a class="tree-link" href="{href}"{ext} style="--hover: {colour}">')
                cur = li
            if (x, y) in tail_cells:
                frames = tail_cells[(x, y)]
                parts.append(f'<span class="tail" data-f="{escape("".join(frames))}">{escape(frames[0])}</span>')
            else:
                parts.append(escape(grid[y][x], quote=False))
        if cur is not None:
            parts.append("</a>")
        out.append("".join(parts))
    return out


if "--preview" in sys.argv:
    print(f"{X1 - X0 + 1} columns x {Y1 - Y0 + 1} rows")
    for f in range(len(BENDS)):
        print(f"--- tail frame {f}")
        print("\n".join(text(f)))
        if "--all" not in sys.argv:
            break
else:
    with open(INDEX) as fh:
        page = fh.read()
    tag = '<pre class="fish">'
    start = page.index(tag) + len(tag) + 1      # just after the newline that follows it
    end = page.index("</pre>", start)
    with open(INDEX, "w") as fh:
        fh.write(page[:start] + "\n".join(html()) + "\n" + page[end:])
    print("Updated the fish in index.html")
