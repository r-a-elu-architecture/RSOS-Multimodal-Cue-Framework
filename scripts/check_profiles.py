"""Browser acceptance for spec/PROFILES.md (P6, P7). Needs Playwright and Chrome.

python3 scripts/check_profiles.py [docs_dir] [chrome_path]
"""
import functools
import http.server
import json
import pathlib
import re
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
sys.path.insert(0, str(ROOT / "rsso"))
from rsso import profiles as P  # noqa: E402

PAGES = ["index", "player", "nodes", "therapist", "contribute", "night", "safety", "world", "metrics", "anchors",
         "identity", "atlas", "trials", "device", "agents"]
RX = re.compile(P.CLINICAL_WORDS, re.I)
CRISIS = re.compile(r"\b(?:crisis|suicid\w*|self-harm|harming yourself|helpline|emergency services|not wanting to live|at risk of harm)\b", re.I)   # FIXES_R1 S-7
ALL_PAGES = sorted(f.stem for f in DOCS.glob("*.html"))
VISIBLE = """() => { document.querySelectorAll('nav,[data-raw]').forEach(e => e.style.setProperty('display','none','important'));
  return document.title + '\\n' + document.body.innerText; }"""


def main():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    H = functools.partial(Quiet, directory=str(DOCS))
    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    fails, errs, counts = [], [], {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for prof in P.IDS:
            ctx = b.new_context()
            pg = ctx.new_page()
            pg.on("pageerror", lambda e, p=prof: errs.append(f"{p}: {e}"))
            pg.on("console", lambda m, p=prof: errs.append(f"{p} console: {m.text}") if m.type == "error" and "net::ERR_" not in m.text else None)   # FIXES_R2: only blocked network requests are ignored   # FIXES_R1 P-6
            n = 0
            for name in PAGES:
                pg.goto(f"{base}/{name}.html?profile={prof}")
                pg.wait_for_timeout(350)
                if name == "nodes":
                    for c in pg.locator("#concerns input").all():
                        if c.is_visible():
                            c.check()
                    pg.wait_for_timeout(200)
                if name == "therapist" and pg.locator("#cpDemo").count():
                    pg.click("#cpDemo")
                    pg.wait_for_timeout(1500)
                    pg.click("#cpDemo")
                t = pg.evaluate(VISIBLE)
                hits = sorted(set(m.group(0) for m in RX.finditer(t)))
                n += len(hits)
                if not P.clinical_vocab(prof) and hits:
                    fails.append(f"P6 {prof} {name}: {hits}")
            counts[prof] = n
            for name in [n for n in ALL_PAGES if n + ".html" not in P.EXEMPT_PAGES]:   # FIXES_R1 S-7, A7 scope: research records excepted
                pg.goto(f"{base}/{name}.html?profile={prof}")
                pg.wait_for_timeout(250)
                hits = sorted(set(m.group(0) for m in CRISIS.finditer(pg.evaluate(VISIBLE))))
                if hits:
                    fails.append(f"S-7 {prof} {name}: {hits}")
            # P7 safety page
            pg.goto(f"{base}/safety.html?profile={prof}")
            pg.wait_for_timeout(300)
            head = pg.is_visible("#clinHead")
            want = P.get(prof)["clinical_module"] != "none"
            if head != want:
                fails.append(f"P7 {prof}: clinical module shown={head}, expected {want}")
            pg.evaluate("""() => { const S = RSOSSafety; const [st] = S.observe(S.newState(), S.eventFromCheck({clinical_result: 'high'}), Date.now()/1000);
              localStorage.setItem('rsos.safety', JSON.stringify(st)); }""")
            pg.reload()
            pg.wait_for_timeout(300)
            if not pg.is_visible("#clinResume"):
                fails.append(f"P7 {prof}: clinician resume hidden during the clinician-led protocol")
            ctx.close()
        # clinical profile shows the canonical words unchanged
        ctx = b.new_context()
        pg = ctx.new_page()
        pg.goto(f"{base}/nodes.html?profile=clinical")
        pg.wait_for_timeout(350)
        if "PTSD or trauma" not in pg.inner_text("#concerns"):
            fails.append("P3 clinical: canonical labels changed")
        pg.goto(f"{base}/nodes.html?profile=performance")
        pg.wait_for_timeout(350)
        sample = pg.inner_text("#concerns")
        b.close()
    srv.shutdown()
    print(json.dumps({"clinical_words_seen": counts, "performance_concerns": sample.split("\n"), "page_errors": errs, "fails": fails}, indent=1))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
