// Light/dark theme. Loaded in <head> (not deferred) so the right colours are
// set before the page paints. Follows the system setting until the visitor
// picks one in the footer, then remembers their choice.
(function () {
    const root = document.documentElement;
    const system = window.matchMedia('(prefers-color-scheme: dark)');
    const saved = () => { try { return localStorage.getItem('theme'); } catch (e) { return null; } };

    function apply(theme) {
        root.dataset.theme = theme;
        document.querySelectorAll('.theme-toggle button').forEach((b) => {
            b.setAttribute('aria-pressed', String(b.dataset.themeChoice === theme));
        });
    }

    apply(saved() || (system.matches ? 'dark' : 'light'));
    system.addEventListener('change', (e) => { if (!saved()) apply(e.matches ? 'dark' : 'light'); });

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.theme-toggle button').forEach((b) => {
            b.addEventListener('click', () => {
                try { localStorage.setItem('theme', b.dataset.themeChoice); } catch (e) { /* private mode */ }
                apply(b.dataset.themeChoice);
            });
        });
        apply(root.dataset.theme);
    });
})();
