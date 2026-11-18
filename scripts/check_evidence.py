"""Browser acceptance for spec/EVIDENCE_LABELS.md, L7: every live page shows its label as generated, without page errors.
python3 scripts/check_evidence.py [docs_dir] [chrome_path]      Needs Playwright and Chrome.
"""
import functools
import http.server
import json
import pathlib
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
PROFILES = ["", "?profile=performance", "?profile=workplace", "?profile=clinical"]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    data = json.loads((DOCS / "data/evidence.json").read_text(encoding="utf-8"))
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    fails, errs, n = [], [], 0
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for page, want in sorted(data["pages"].items()):
            for q in PROFILES:
                for w in (1280, 390):
                    url = f"/{page}.html{q}"
                    ctx = b.new_context(viewport={"width": w, "height": 900}); pg = ctx.new_page()
                    pg.on("pageerror", lambda e, u=url: errs.append(u + ": " + str(e)))
                    pg.on("console", lambda m, u=url: errs.append(u + ": console " + m.text)
                          if m.type == "error" and "net::ERR_" not in m.text and "Failed to load resource" not in m.text else None)
                    pg.goto(base + url); pg.wait_for_timeout(500)
                    loc = pg.locator("p.evidence")
                    got = [loc.count(), loc.first.inner_text().strip() if loc.count() else None,
                           loc.first.is_visible() if loc.count() else False,
                           pg.evaluate("() => { const e = document.querySelector('p.evidence'); return !!e && e.getBoundingClientRect().right <= window.innerWidth + 1; }")]
                    exp = [1, want["text"], True, True]
                    if got != exp:
                        fails.append(f"{url} at {w}px: got {got}, expected {exp}")
                    n += 1
                    ctx.close()
        b.close()
    srv.shutdown()
    for f in fails:
        print("FAIL", f)
    for e in errs:
        print("PAGE ERROR", e)
    print(f"{n - len(fails)}/{n} page views show the generated label; {len(errs)} page errors")
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
