# pf3
portfolio site

Plain HTML/CSS/JS, served by GitHub Pages at victorvandamme.com.

```
index.html              /                 homepage (tree on desktop, fish on phones)
about/index.html        /about/
work/index.html         /work/            work archive
work/<project>/         /work/aperol/, /work/auping/, /work/bpost/, /work/mcdonalds/, /work/xbox/
styles/  scripts/  assets/                shared, always linked from the root (/styles/...)
about.html, work.html, <project>.html     old addresses, each redirects to its new one
_tools/                                   generators for the tree, fish and favicon (not published)
```

Run it locally with `python3 _tools/serve.py` and open http://localhost:8000.
