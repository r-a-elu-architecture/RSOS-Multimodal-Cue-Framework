"""spec/LAB_LINK.md K2: the agent pane's link plays the Person Lab. Usage: python3 scripts/check_lab_link.py docs"""
import functools, http.server, sys, threading, pathlib
from playwright.sync_api import sync_playwright

docs = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs").resolve()
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(docs)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
ok, fails = 0, []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in ((1280, 900), (390, 844)):
        pg = b.new_page(viewport={"width": w, "height": h}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{base}/world.html"); pg.wait_for_timeout(800)
        tag = f"{w}px"
        inside = pg.evaluate("() => !!document.querySelector('#graph').closest('.pane').querySelector('#labJump')")
        (ok := ok + 1) if inside else fails.append(f"{tag}: link not in the agent pane")
        pg.click("#labJump"); pg.wait_for_timeout(1500)
        state = pg.inner_text("#labRun").strip()
        (ok := ok + 1) if state == "Pause" else fails.append(f"{tag}: lab button reads {state!r} after the click")
        top = pg.evaluate("() => document.getElementById('lab').getBoundingClientRect().top")
        (ok := ok + 1) if -50 <= top <= h * 0.6 else fails.append(f"{tag}: #lab not in view (top {top:.0f})")
        pg.evaluate("() => document.getElementById('run').scrollIntoView()"); pg.click("#labJump"); pg.wait_for_timeout(600)
        state2 = pg.inner_text("#labRun").strip()
        (ok := ok + 1) if state2 == "Pause" else fails.append(f"{tag}: second click stopped the lab ({state2!r})")
        (ok := ok + 1) if not errs else fails.append(f"{tag}: page errors {errs}")
        pg.close()
    b.close()
srv.shutdown()
print(f"{ok}/{ok + len(fails)} checks pass", *fails, sep="\n")
sys.exit(1 if fails else 0)
