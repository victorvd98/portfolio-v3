// Homepage bonsai: rustling leaves, falling leaves, and leaves that stir
// under the cursor. Titles and wood never move.
(function () {
    const pre = document.querySelector('.tree pre');
    if (!pre || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const LEAF = '&';
    const RUSTLE = ['%', '*', '8', '@', '$'];

    // --- wrap every leaf in a span and remember where it sits on the grid
    const leaves = [];          // { el, col, row }
    const grid = new Map();     // "col,row" -> leaf
    let row = 0, col = 0;

    function wrapText(node) {
        const frag = document.createDocumentFragment();
        let buf = '';
        const flush = () => { if (buf) { frag.appendChild(document.createTextNode(buf)); buf = ''; } };
        for (const ch of node.textContent) {
            if (ch === '\n') { buf += ch; row++; col = 0; continue; }
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
        }
        flush();
        node.replaceWith(frag);
    }

    for (const node of [...pre.childNodes]) {
        if (node.nodeType === Node.TEXT_NODE) wrapText(node);
        else col += node.textContent.length;    // links: count their columns, leave them alone
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
