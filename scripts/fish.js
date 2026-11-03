// Phone homepage fish: it lies there, twitches its tail every few seconds and
// now and then flops. Tapping it (anywhere but a link) makes it flop too.
// _tools/fish.py writes each tail cell as <span class="tail" data-f="..."> with
// its character in every tail frame: 0 at rest, 1 and 2 flicked either way.
(function () {
    const fish = document.querySelector('.tree pre.fish');
    if (!fish || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const tail = [...fish.querySelectorAll('.tail')];
    const showing = () => fish.offsetParent !== null;
    let busy = false;

    function frame(i) {
        for (const cell of tail) cell.textContent = cell.dataset.f[i];
    }

    // play tail frames one after another, then come back to rest
    function flick(frames, every) {
        frames.forEach((f, i) => setTimeout(() => frame(f), i * every));
        setTimeout(() => frame(0), frames.length * every);
    }

    function move(name, ms, frames, every) {
        if (busy || !showing()) return;
        busy = true;
        fish.classList.add(name);
        flick(frames, every);
        setTimeout(() => { fish.classList.remove(name); busy = false; }, ms);
    }

    const twitch = () => move('twitch', 350, [1, 2, 1], 70);
    const flop = () => move('flop', 1100, [1, 2, 1, 2, 1, 2, 0, 0, 1, 2, 1], 90);

    (function lie() {
        setTimeout(() => {
            Math.random() < 0.25 ? flop() : twitch();
            lie();
        }, 2000 + Math.random() * 3500);
    })();

    fish.addEventListener('click', (e) => { if (!e.target.closest('a')) flop(); });
})();
