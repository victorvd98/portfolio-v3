// Reel carousels: in each one, whichever video is in the middle plays (muted until
// the visitor turns sound on) and the rest pause. A carousel only plays while it's
// on screen, so with several on a page just the one you're looking at runs. Swipe, scroll, use the arrows or the
// prev / next buttons. Clicking a reel off to the side brings it to the middle;
// clicking the middle one pauses or resumes it.
(function () {
    document.querySelectorAll('.reels').forEach((root) => {
        const track = root.querySelector('.reels-track');
        const reels = [...root.querySelectorAll('.reel')];
        const prev = root.querySelector('.reels-prev');
        const next = root.querySelector('.reels-next');
        const count = root.querySelector('.reels-count');
        const soundButtons = [...root.querySelectorAll('[data-sound]')];
        const stillMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        let current = 0;
        let sound = false;
        let onScreen = false;

        // a reel whose file isn't there yet shows a dashed placeholder instead
        reels.forEach((reel, i) => {
            const video = reel.querySelector('video');
            reel.dataset.name = video.getAttribute('src').split('/').pop();
            video.addEventListener('error', () => reel.classList.add('missing'));
            if (video.error) reel.classList.add('missing');
        });

        function show(i) {
            current = i;
            reels.forEach((reel, j) => {
                const video = reel.querySelector('video');
                reel.classList.toggle('active', j === i);
                if (j === i && onScreen && !stillMotion && !reel.classList.contains('missing')) {
                    video.play().catch(() => {});      // autoplay can be refused; a click starts it
                } else {
                    video.pause();
                }
            });
            count.textContent = `${i + 1} / ${reels.length}`;
            prev.disabled = i === 0;
            next.disabled = i === reels.length - 1;
        }

        function go(i) {
            i = Math.max(0, Math.min(reels.length - 1, i));
            const reel = reels[i];
            if (i !== current) show(i);
            track.scrollTo({
                left: reel.offsetLeft - (track.clientWidth - reel.clientWidth) / 2,
                behavior: stillMotion ? 'auto' : 'smooth',
            });
        }

        // after a swipe or scroll settles, the reel nearest the middle is the current one
        let settle = null;
        track.addEventListener('scroll', () => {
            clearTimeout(settle);
            settle = setTimeout(() => {
                const middle = track.scrollLeft + track.clientWidth / 2;
                let best = 0;
                reels.forEach((reel, j) => {
                    const c = reel.offsetLeft + reel.clientWidth / 2;
                    const b = reels[best].offsetLeft + reels[best].clientWidth / 2;
                    if (Math.abs(c - middle) < Math.abs(b - middle)) best = j;
                });
                if (best !== current) show(best);
            }, 120);
        });

        prev.addEventListener('click', () => go(current - 1));
        next.addEventListener('click', () => go(current + 1));
        track.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') { e.preventDefault(); go(current - 1); }
            if (e.key === 'ArrowRight') { e.preventDefault(); go(current + 1); }
        });

        reels.forEach((reel, j) => reel.addEventListener('click', () => {
            if (j !== current) return go(j);
            const video = reel.querySelector('video');
            video.paused ? video.play().catch(() => {}) : video.pause();
        }));

        function setSound(on) {
            sound = on;
            reels.forEach((reel) => { reel.querySelector('video').muted = !on; });
            soundButtons.forEach((b) => b.setAttribute('aria-pressed', String((b.dataset.sound === 'on') === on)));
        }
        soundButtons.forEach((b) => b.addEventListener('click', () => setSound(b.dataset.sound === 'on')));

        // play when at least half the carousel is visible, pause when it scrolls away
        new IntersectionObserver(([entry]) => {
            const now = entry.intersectionRatio >= 0.5;
            if (now !== onScreen) { onScreen = now; show(current); }
        }, { threshold: [0, 0.5, 1] }).observe(root);

        setSound(false);
        show(0);
        go(0);
    });
})();
