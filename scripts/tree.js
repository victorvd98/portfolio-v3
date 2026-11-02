// Homepage bonsai: rustling leaves, falling leaves, wisps of wind, and leaves
// that stir under the cursor. Titles and wood never move.
(function () {
    const pre = document.querySelector('.tree pre');
    if (!pre || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const LEAF = '&';
    const RUSTLE = ['%', '*', '8', '@', '$'];

    // --- wrap every leaf in a span and remember where it sits on the grid
    const leaves = [];          // { el, col, row }
    const grid = new Map();     // "col,row" -> leaf
    const solid = new Set();    // "col,row" of every cell the tree (or a title) occupies
    let row = 0, col = 0, cols = 0;

    function wrapText(node) {
        const frag = document.createDocumentFragment();
        let buf = '';
        const flush = () => { if (buf) { frag.appendChild(document.createTextNode(buf)); buf = ''; } };
        for (const ch of node.textContent) {
            if (ch === '\n') { buf += ch; row++; col = 0; continue; }
            if (ch !== ' ') solid.add(col + ',' + row);
            if (ch === LEAF) {
                flush();
                const el = document.createElement('span');
                el.className = 'leaf';
                el.textContent = LEAF;
                frag.appendChild(el);
                const leaf = { el, col, row, busy: false };
                leaves.push(leaf);
                grid.set(col + ',' + row, leaf);
            } else {
                buf += ch;
            }
            col++;
            cols = Math.max(cols, col);
        }
        flush();
        node.replaceWith(frag);
    }

    for (const node of [...pre.childNodes]) {
        if (node.nodeType === Node.TEXT_NODE) wrapText(node);
        else {                                  // links: count their columns, leave them alone
            for (let i = 0; i < node.textContent.length; i++) solid.add((col + i) + ',' + row);
            col += node.textContent.length;
        }
    }
    const rows = row + 1;

    // --- grid metrics (the font scales with the viewport, so measure on demand)
    let cw = 0, lh = 0;
    function measure() {
        const probe = document.createElement('span');
        probe.textContent = LEAF.repeat(20);
        probe.style.visibility = 'hidden';
        pre.appendChild(probe);
        cw = probe.getBoundingClientRect().width / 20;
        probe.remove();
        lh = pre.getBoundingClientRect().height / rows;
    }
    measure();
    window.addEventListener('resize', measure);
    document.fonts.ready.then(measure);
    // if the page wasn't laid out yet when we measured, try again before drawing
    const ready = () => (cw && lh) || (measure(), cw && lh);

    // --- rustle: briefly swap a leaf for another glyph
    function rustle(leaf, duration) {
        if (leaf.busy || leaf.fallen) return;
        leaf.busy = true;
        leaf.el.textContent = RUSTLE[Math.floor(Math.random() * RUSTLE.length)];
        setTimeout(() => {
            if (!leaf.fallen) leaf.el.textContent = LEAF;
            leaf.busy = false;
        }, duration || 250 + Math.random() * 500);
    }

    const random = (list) => list[Math.floor(Math.random() * list.length)];

    // 2. wind: a constant light flicker across the canopy
    setInterval(() => {
        for (let i = 0; i < 3; i++) rustle(random(leaves));
    }, 140);

    // 3. falling leaves: one breaks off, drifts down cell by cell, settles and fades
    const layer = document.createElement('div');
    layer.className = 'falling-layer';
    layer.setAttribute('aria-hidden', 'true');
    pre.appendChild(layer);

    function fall(leaf) {
        if (!ready() || leaf.busy || leaf.fallen) return;
        leaf.fallen = true;
        leaf.el.textContent = ' ';
        const el = document.createElement('span');
        el.className = 'falling-leaf';
        el.textContent = LEAF;
        layer.appendChild(el);

        let x = leaf.col, y = leaf.row, sway = Math.random() < 0.5 ? 1 : -1;
        const place = () => { el.style.transform = `translate(${x * cw}px, ${y * lh}px)`; };
        place();
        const timer = setInterval(() => {
            y += 1;
            if (Math.random() < 0.5) x += sway;
            if (Math.random() < 0.25) sway = -sway;
            place();
            if (y >= rows - 1) {
                clearInterval(timer);
                setTimeout(() => { el.style.opacity = '0'; }, 1500);
                setTimeout(() => el.remove(), 3000);
            }
        }, 220);

        // the canopy grows the leaf back
        setTimeout(() => { leaf.el.textContent = LEAF; leaf.fallen = false; }, 8000);
    }

    function dropLeaf() {
        fall(random(leaves));
        setTimeout(dropLeaf, 6000 + Math.random() * 8000);
    }
    setTimeout(dropLeaf, 3000);

    // wisps of wind: each one appears in place, unfurls over a few frames while
    // drifting a little, then breaks up into dots and dissipates
    const WISPS = [
        [   // a gentle wave
            '~',
            '~-',
            '.~-',
            '.~-~.',
            '.~-~-.\n      `',
            ' .~-~ .\n       `',
            '  . ~ .',
            '    .  .',
            '      .',
        ],
        [   // a long, low streak
            '-',
            '-~',
            '_.-~',
            '_.-~~',
            '_.-~~-.',
            ' _.-~ -.',
            '  . ~  .',
            '     .  .',
            '       .',
        ],
        [   // a soft ribbon that dips at the end
            '~',
            '~~',
            '~~-.',
            '~~-._',
            '~~-._\n     `~',
            ' ~-._\n      `~-',
            '  ~ ._\n       ` -',
            '    .\n        .',
            '         .',
        ],
        [   // a short flick
            '-',
            '-~',
            '-~-.',
            '-~-.\n    \'',
            ' ~-.\n     \'',
            '  . .',
            '    .',
        ],
    ];
    // does this frame, placed at (x, y), stay clear of the tree with a 1-cell margin?
    function clear(frame, x, y) {
        const lines = frame.split('\n');
        for (let r = 0; r < lines.length; r++) {
            for (let c = 0; c < lines[r].length; c++) {
                if (lines[r][c] === ' ') continue;
                const cx = x + c, cy = y + r;
                if (cx < 0 || cx >= cols || cy < 0 || cy >= rows) return false;
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        if (solid.has((cx + dx) + ',' + (cy + dy))) return false;
                    }
                }
            }
        }
        return true;
    }

    function findSpot(frames, dir) {
        for (let attempt = 0; attempt < 80; attempt++) {
            const x = Math.floor(Math.random() * cols);
            const y = Math.floor(Math.random() * rows);
            // every frame must fit wherever the drift might take it
            const ok = frames.every((f, i) => {
                for (let d = 0; d <= i; d++) if (!clear(f, x + d * dir, y)) return false;
                return true;
            });
            if (ok) return { x, y };
        }
        return null;
    }

    function wisp() {
        setTimeout(wisp, 1200 + Math.random() * 2800);
        const frames = random(WISPS);
        const dir = Math.random() < 0.75 ? 1 : -1;     // mostly with the breeze, sometimes against
        const spot = ready() && findSpot(frames, dir);
        if (!spot) return;                             // no room this time; try again later

        const el = document.createElement('span');
        el.className = 'wisp';
        layer.appendChild(el);
        let { x, y } = spot;
        let i = 0;
        (function step() {
            if (i >= frames.length) { el.remove(); return; }
            el.textContent = frames[i];
            if (i > 1 && Math.random() < 0.6 && clear(frames[i], x + dir, y)) x += dir;
            el.style.transform = `translate(${x * cw}px, ${y * lh}px)`;
            // fade in over the first frames, thin out over the last ones
            const left = frames.length - 1 - i;
            el.style.opacity = String(0.55 * Math.min(1, (i + 1) / 2, (left + 1) / 3));
            i++;
            setTimeout(step, 130 + Math.random() * 150);
        })();
    }
    setTimeout(wisp, 800);

    // 4. cursor: leaves shiver as the pointer brushes past, and a quick swipe
    //    can knock one loose. Each leaf is a little spring.
    const RX = 5, RY = 2.5;     // reach of the cursor, in columns / rows
    const moving = new Set();   // leaves currently off their resting spot
    let mouse = null;           // pointer position in cells, or null when away
    let last = null, frame = null, lastDrop = 0;

    // how strongly a leaf feels the cursor (0..1)
    function touch(leaf) {
        const d = Math.hypot((leaf.col + 0.5 - mouse.c) / RX, (leaf.row + 0.5 - mouse.r) / RY);
        return d >= 1 ? null : { f: 1 - d };
    }

    function near(fn) {
        const c = Math.floor(mouse.c), r = Math.floor(mouse.r);
        for (let dy = -Math.ceil(RY); dy <= Math.ceil(RY); dy++) {
            for (let dx = -RX; dx <= RX; dx++) {
                const leaf = grid.get((c + dx) + ',' + (r + dy));
                if (!leaf || leaf.fallen) continue;
                const t = touch(leaf);
                if (t) fn(leaf, t);
            }
        }
    }

    let then = 0;
    function tick(now) {
        frame = null;
        // step the springs at a fixed 60 steps a second, whatever the screen's refresh rate
        const steps = then ? Math.min(4, Math.round((now - then) / 16.7)) : 1;
        then = now;
        for (const leaf of moving) {
            for (let s = 0; s < steps; s++) {
                leaf.vx = (leaf.vx - leaf.x * 0.12) * 0.78;
                leaf.vy = (leaf.vy - leaf.y * 0.12) * 0.78;
                leaf.x += leaf.vx;
                leaf.y += leaf.vy;
            }
            if (leaf.fallen || (Math.abs(leaf.x) + Math.abs(leaf.y) + Math.abs(leaf.vx) + Math.abs(leaf.vy) < 0.05)) {
                leaf.el.style.transform = '';
                moving.delete(leaf);
            } else {
                leaf.el.style.transform = `translate(${leaf.x.toFixed(2)}px, ${leaf.y.toFixed(2)}px)`;
            }
        }
        if (moving.size) frame = requestAnimationFrame(tick);
        else then = 0;
    }
    const wake = () => { if (!frame) frame = requestAnimationFrame(tick); };

    pre.addEventListener('mousemove', (e) => {
        if (!ready()) return;
        const box = pre.getBoundingClientRect();
        mouse = { c: (e.clientX - box.left) / cw, r: (e.clientY - box.top) / lh };
        const now = performance.now();
        // speed in cells per millisecond decides how hard the leaves shiver
        const speed = last ? Math.hypot(mouse.c - last.c, mouse.r - last.r) / Math.max(1, now - last.t) : 0;
        last = { c: mouse.c, r: mouse.r, t: now };
        const kick = Math.min(1, speed * 12);

        near((leaf, t) => {
            if (!moving.has(leaf)) {
                leaf.x = leaf.x || 0; leaf.y = leaf.y || 0;
                leaf.vx = leaf.vx || 0; leaf.vy = leaf.vy || 0;
                moving.add(leaf);
            }
            leaf.vx += (Math.random() - 0.5) * cw * 0.35 * kick * t.f;
            leaf.vy += (Math.random() - 0.5) * lh * 0.2 * kick * t.f;
            // a fast swipe right through the canopy now and then shakes one loose
            if (speed > 0.06 && t.f > 0.5 && now - lastDrop > 400 && Math.random() < 0.04) {
                lastDrop = now;
                fall(leaf);
            }
        });
        wake();
    });
    pre.addEventListener('mouseleave', () => { mouse = null; last = null; wake(); });
})();
