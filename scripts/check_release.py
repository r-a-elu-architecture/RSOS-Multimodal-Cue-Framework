#!/usr/bin/env python3
"""Release page check (spec/RELEASE_1.md A3).

Serves the site the way the Pages workflow publishes it (the docs folder at the root and a copy under /dev/) and opens
every docs/*.html page in Chrome at desktop (1280x800) and phone (390x844) size. For each page:
  - no uncaught page error and no console.error (a "Failed to load resource: net::ERR_..." error is not counted when, in
    that view, a request to an external host failed and no same-origin request failed: RELEASE_1 A1 F2);
  - no failed same-origin request (status >= 400 or a network failure);
  - every same-origin href / src in the page resolves to a file;
  - the "DEVELOPMENT VERSION" banner is absent at the root and present under /dev/ (checked at desktop size).
External links are listed in the report, not fetched.

  python3 scripts/check_release.py docs [--out report.json]
Exit 0 when every page passes.
"""
from __future__ import annotations

import functools
import http.server
import json
import pathlib
import shutil
import socketserver
import sys
import tempfile
import threading
import urllib.parse

from playwright.sync_api import sync_playwright

CHROME = "/usr/bin/google-chrome"
SIZES = {"desktop": (1280, 800), "phone": (390, 844)}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main(argv):
    docs = pathlib.Path(argv[1] if len(argv) > 1 else "docs").resolve()
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else None
    root = pathlib.Path(tempfile.mkdtemp(prefix="rsos-release-"))
    site = root / "site"
    shutil.copytree(docs, site)
    shutil.copytree(docs, site / "dev")
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(site)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    pages = sorted(p.name for p in docs.glob("*.html"))
    report, external = {}, set()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for name in pages:
            for size, (w, h) in SIZES.items():
                for prefix in ("/", "/dev/") if size == "desktop" else ("/",):
                    url = base + prefix + name
                    ctx = browser.new_context(viewport={"width": w, "height": h}, service_workers="block")
                    pg = ctx.new_page()
                    errs, failed = [], []
                    pg.on("pageerror", lambda e, errs=errs: errs.append("pageerror: " + str(e)[:300]))
                    pg.on("console", lambda m, errs=errs: errs.append("console.error: " + m.text[:300]) if m.type == "error" else None)
                    ext_failed = []
                    pg.on("requestfailed", lambda r, failed=failed, ext_failed=ext_failed:
                          (failed if r.url.startswith(base) else ext_failed).append(f"{r.url} ({r.failure})"))
                    pg.on("response", lambda r, failed=failed: failed.append(f"{r.url} ({r.status})") if r.url.startswith(base) and r.status >= 400 else None)
                    pg.goto(url, wait_until="load")
                    pg.wait_for_timeout(800)
                    links = pg.evaluate("""() => [...document.querySelectorAll('[href],[src]')]
                        .map(e => e.getAttribute('href') !== null && e.tagName !== 'LINK' || e.tagName === 'A' ? e.href : (e.src || e.href))
                        .filter(Boolean)""")
                    missing = []
                    for link in links:
                        u = urllib.parse.urlsplit(link)
                        if u.scheme in ("http", "https") and not link.startswith(base):
                            external.add(urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, "", "")))
                            continue
                        if not link.startswith(base):
                            continue   # mailto:, data:, javascript:, blob:
                        path = urllib.parse.unquote(u.path)
                        f = site / path.lstrip("/")
                        if path.endswith("/"):
                            f = f / "index.html"
                        if not f.exists():
                            missing.append(link[len(base):])
                    banner = pg.evaluate("() => !!document.getElementById('rsosDevBanner')")
                    key = f"{prefix}{name} [{size}]"
                    want_banner = prefix == "/dev/"
                    counted = [e for e in errs if not (ext_failed and not failed and
                                                       e.startswith("console.error: Failed to load resource: net::ERR_"))]
                    report[key] = {"errors": counted, "not_counted": [e for e in errs if e not in counted],
                                   "external_failed": sorted(set(ext_failed)), "failed_requests": sorted(set(failed)),
                                   "missing_links": sorted(set(missing)), "banner": banner,
                                   "ok": not counted and not failed and not missing and banner == want_banner}
                    ctx.close()
        browser.close()
    srv.shutdown()
    shutil.rmtree(root, ignore_errors=True)
    bad = {k: v for k, v in report.items() if not v["ok"]}
    ext = sorted({u.split(" (")[0].split("?")[0] for v in report.values() for u in v["external_failed"]})
    summary = {"pages": len(pages), "views": len(report), "passed": len(report) - len(bad), "failed": bad,
               "external_failed_in_this_environment": ext, "external_links": sorted(external)}
    if out_path:
        pathlib.Path(out_path).write_text(json.dumps({"summary": summary, "views": report}, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "external_links"} | {"external_links": len(external)}, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
