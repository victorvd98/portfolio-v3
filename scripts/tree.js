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

    function dropLeaf() {
        const leaf = random(leaves);
        if (!leaf.busy && !leaf.fallen) {
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
        setTimeout(dropLeaf, 1500 + Math.random() * 3000);
    }
    setTimeout(dropLeaf, 1500);

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
        const spot = findSpot(frames, dir);
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

    // 4. cursor: leaves near the pointer stir as it moves
    let pending = null;
    pre.addEventListener('mousemove', (e) => {
        if (pending) return;
        pending = requestAnimationFrame(() => {
            pending = null;
            const box = pre.getBoundingClientRect();
            const c = Math.floor((e.clientX - box.left) / cw);
            const r = Math.floor((e.clientY - box.top) / lh);
            for (let dy = -2; dy <= 2; dy++) {
                for (let dx = -4; dx <= 4; dx++) {
                    const leaf = grid.get((c + dx) + ',' + (r + dy));
                    if (leaf && (dx / 4) ** 2 + (dy / 2) ** 2 <= 1 && Math.random() < 0.5) rustle(leaf, 400);
                }
            }
        });
    });
})();
