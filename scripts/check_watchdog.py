"""Browser acceptance for spec/WATCHDOG.md (W9). Needs Playwright and Chrome.

python3 scripts/check_watchdog.py [docs_dir] [chrome_path]
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


def node_plan(pg, base, profile):
    """Build a clinician-led plan in the node studio (difficult memories + Observer node, clinician present, screening no)."""
    pg.goto(f"{base}/nodes.html?profile={profile}")
    pg.wait_for_timeout(500)
    pg.locator("button.pick", has_text="(no ego)").first.click()
    pg.locator('#concerns input[value="ptsd"]').check()
    pg.wait_for_timeout(200)
    pg.check("#therapistHere")
    pg.check('input[name="screen"][value="no"]')
    pg.check("#consent")
    pg.click("#save")
    pg.wait_for_timeout(1500)
    return pg.url, pg.inner_text("#msg") if "nodes.html" in pg.url else ""


def session(pg, base, profile, proto="trauma_observer"):
    pg.goto(f"{base}/therapist.html?profile={profile}")
    pg.wait_for_timeout(500)
    pg.check(f'input[name="proto"][value="{proto}"]')
    pg.check("#present")
    pg.click("#begin")
    pg.wait_for_timeout(300)
    return pg.inner_text("#msg")


def main():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    out, fails, errs = {}, [], []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for prof in ("performance", "clinical"):
            ctx = b.new_context()
            pg = ctx.new_page()
            pg.on("pageerror", lambda e, p=prof: errs.append(f"{p}: {e}"))
            url, msg = node_plan(pg, base, prof)
            out[f"plan:{prof}"] = {"url": url.split("/")[-1], "msg": msg}
            ctx.close()
        if "nodes.html" not in out["plan:performance"]["url"] or "Watchdog" not in out["plan:performance"]["msg"]:
            fails.append("clinician-led plan was not held in Performance")
        if "player.html" not in out["plan:clinical"]["url"]:
            fails.append("clinician-led plan with clinician and screening was not saved in Clinical")
        for prof in ("workplace", "clinical"):
            ctx = b.new_context()
            pg = ctx.new_page()
            pg.on("pageerror", lambda e, p=prof: errs.append(f"{p}: {e}"))
            out[f"session:{prof}"] = session(pg, base, prof)
            if prof == "workplace":
                pg.goto(f"{base}/nodes.html?profile=workplace")
                pg.wait_for_timeout(400)
                out["plan:workplace"] = pg.evaluate("""() => RSOSGuard.ask({kind: 'plan', protocol: 'plan', therapist_led: true, source: 'practitioner'},
                  {clinician_present: true, screening_recorded: true, max_level: RSOSProfiles.get('workplace').max_level}).decision""")
            pg.goto(f"{base}/safety.html?profile={prof}")
            pg.wait_for_timeout(400)
            out[f"log:{prof}"] = pg.inner_text("#wdSay")
            ctx.close()
        if "Watchdog" not in out["session:workplace"]:
            fails.append("clinician-led session was not held in Workplace")
        if out["session:clinical"].strip():
            fails.append("clinician-led session did not start in Clinical: " + out["session:clinical"])
        if out["plan:workplace"] != "hold":
            fails.append("clinician-led plan was not held in Workplace")
        for prof in ("workplace", "clinical"):
            if "chain verifies" not in out[f"log:{prof}"]:
                fails.append(f"audit chain not verified on the safety page ({prof})")
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
