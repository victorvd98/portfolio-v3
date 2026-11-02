"""Serve the site locally without browser caching, so a normal reload always
shows the latest files.

Usage (from the repo root):
    python3 _tools/serve.py [port]
"""
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
print(f"Serving {ROOT} at http://localhost:{port}")
ThreadingHTTPServer(("", port), partial(NoCacheHandler, directory=str(ROOT))).serve_forever()
