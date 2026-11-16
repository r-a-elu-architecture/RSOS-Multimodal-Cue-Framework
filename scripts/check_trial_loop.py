"""Browser acceptance for spec/TRIAL_LOOP.md (T8). Needs Playwright and Chrome.

python3 scripts/check_trial_loop.py [docs_dir] [chrome_path]
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
DOCS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def run_session(pg):
    pg.click("text=Start today's session")
    pg.wait_for_timeout(300)
    btn = pg.locator("button", has_text="Play today's code")
    if btn.count():
        btn.first.click()
    scales = pg.locator(".scale")
    scales.nth(0).locator("button", has_text="4").first.click()
    scales.nth(1).locator("button").nth(7).click()
    pg.click("text=Save this session")
    pg.wait_for_timeout(400)
    return pg.inner_text("#trialArea") if pg.locator("#trialArea").count() else pg.inner_text("body")


def main():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    fails, errs, out = [], [], {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = b.new_context()
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"{base}/trials.html")
        pg.wait_for_timeout(400)
        pg.evaluate("""() => { const a = RSOSPeak.makeAnchor('a1', 'Test anchor', '🦁', '..-'); localStorage.setItem('rsos.anchors', JSON.stringify([a]));
          const t = RSOSTrial.newTrial('anchor_vs_sham', 2, 123456789, 't1', 0); t.anchor = 'a1'; localStorage.setItem('rsos.trial', JSON.stringify(t)); }""")
        pg.reload()
        pg.wait_for_timeout(500)
        msgs = []
        for k in range(2):
            pg.reload()
            pg.wait_for_timeout(400)
            msgs.append(pg.locator(".stage").last.inner_text() if pg.locator(".stage").count() else "")
            run_session(pg)
            msgs[-1] = pg.inner_text("body")
        state = pg.evaluate("""() => { const t = JSON.parse(localStorage.getItem('rsos.trial')), a = JSON.parse(localStorage.getItem('rsos.anchors'))[0];
          const wl = JSON.parse(localStorage.getItem('rsos.watchdog.log') || '[]');
          return { sessions: t.sessions, probes: a.probes, expected: t.sessions.map((s, i) => s.arm === 'sham' ? RSOSTrial.shamCode(t, i, '..-') : '..-'),
                   watchdog: wl.map(r => r.decision + ' ' + r.protocol), runs: localStorage.getItem('rsos.runs') }; }""")
        out = state
        if len(state["probes"]) != len(state["sessions"]):
            fails.append(f"probes {len(state['probes'])} != sessions {len(state['sessions'])}")
        for s, exp, p in zip(state["sessions"], state["expected"], state["probes"]):
            if (s.get("detail") or {}).get("code") != exp:
                fails.append(f"session {s['i']}: recorded code {s.get('detail')} != expected {exp}")
            if p["kind"] != ("cue" if s["arm"] == "anchor" else "sham") or p["calm_before"] != 4 or p["calm_after"] != 7:
                fails.append(f"probe mismatch {p}")
        if len([w for w in state["watchdog"] if w.startswith("allow trial_anchor_vs_sham")]) != 2:
            fails.append(f"Watchdog not asked twice: {state['watchdog']}")
        if state["runs"] not in (None, "[]"):
            fails.append("the run log was written")
        b.close()
    srv.shutdown()
    print(json.dumps({"state": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
