"""Browser acceptance for spec/LOW_MOOD.md (L1-L4). Needs Playwright and Chrome.
python3 scripts/check_low_mood.py [docs_dir] [chrome_path]
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
SETPIN = "() => { const c = JSON.parse(localStorage.getItem('rsos.clinical') || '{}'); c.pin_salt = 'ab'; c.pin_hash = RSOSWatchdog.sha256('ab:4826'); localStorage.setItem('rsos.clinical', JSON.stringify(c)); }"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    out, fails, errs = {}, [], []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        def fresh(url):
            ctx = b.new_context(); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.goto(base + url); pg.wait_for_timeout(600); return ctx, pg

        def plan(pg, dx, clinician):
            pg.locator("button.pick", has_text="Lion").first.click(); pg.wait_for_timeout(150)
            pg.locator('#concerns input[value="depression"]').check()
            if dx: pg.check("#dxDep")
            pg.wait_for_timeout(150)
            if clinician:
                pg.check("#therapistHere")
                if pg.is_visible('input[name="screen"][value="no"]'): pg.check('input[name="screen"][value="no"]')
            pg.check("#consent"); pg.click("#save"); pg.wait_for_timeout(1300)
            return pg.url.split("/")[-1], pg.evaluate("JSON.parse(localStorage.getItem('rsos.plan') || 'null')")

        # L1: the diagnosed choice only with the clinical vocabulary
        for prof in ("personal", "performance", "workplace", "clinical"):
            ctx, pg = fresh(f"/nodes.html?profile={prof}")
            out[f"L1_{prof}"] = pg.is_visible("#dxDep")
            ctx.close()
        if out["L1_clinical"] is not True or any(out[f"L1_{p}"] for p in ("personal", "performance", "workplace")): fails.append(f"L1: {out}")

        # L2: a diagnosed plan is held without the clinician, saved with clinician + screening + PIN; its nodes are clinician-led
        ctx, pg = fresh("/nodes.html?profile=clinical")
        pg.evaluate(SETPIN); pg.reload(); pg.wait_for_timeout(600)
        url, p = plan(pg, True, False)
        out["L2_no_clinician"] = url
        if "player.html" in url: fails.append("L2: diagnosed plan saved without a clinician")
        pg.reload(); pg.wait_for_timeout(600)
        url, p = plan(pg, True, True)
        out["L2_with_clinician"] = [url, (p or {}).get("dx"), (p or {}).get("therapist_led")]
        if "player.html" not in url or (p or {}).get("dx") != ["depression"]: fails.append(f"L2: not saved with clinician {out['L2_with_clinician']}")
        pg.goto(base + "/player.html?program=plan:0&profile=clinical"); pg.wait_for_timeout(1200)
        out["L2_run"] = pg.evaluate("() => [runFlags().therapist_led, safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision]")
        if out["L2_run"] != [True, "block"]: fails.append(f"L2: diagnosed plan node not clinician-led in the player {out['L2_run']}")
        ctx.close()

        # L3: an everyday low-mood plan stays structured
        ctx, pg = fresh("/nodes.html?profile=personal")
        url, p = plan(pg, False, False)
        out["L3"] = [url, (p or {}).get("therapist_led")]
        if "player.html" not in url or (p or {}).get("therapist_led"): fails.append(f"L3: {out['L3']}")

        # L4: escalation (the plan from L3 has the low energy or mood concern)
        def checks(pg, n):
            for _ in range(n):
                pg.select_option("#sfInt", "8"); pg.click("#sfSave"); pg.wait_for_timeout(120)
            return pg.inner_text("#sfMsgs"), (pg.evaluate("JSON.parse(localStorage.getItem('rsos.plan'))") or {}).get("practitioner_recommended")
        pg.goto(base + "/safety.html?profile=personal"); pg.wait_for_timeout(500)
        t2, r2 = checks(pg, 2)
        t3, r3 = checks(pg, 1)
        out["L4"] = ["practitioner" in t2, bool(r2), "practitioner" in t3, bool(r3)]
        if out["L4"] != [False, False, True, True]: fails.append(f"L4: {out['L4']}")
        pg.evaluate("() => { const p = JSON.parse(localStorage.getItem('rsos.plan')); p.intake.concerns = ['stress']; delete p.practitioner_recommended; localStorage.setItem('rsos.plan', JSON.stringify(p)); localStorage.removeItem('rsos.selfchecks'); }")
        pg.reload(); pg.wait_for_timeout(500)
        t4, r4 = checks(pg, 3)
        out["L4_no_concern"] = ["practitioner" in t4, bool(r4)]
        if out["L4_no_concern"] != [False, False]: fails.append(f"L4 without the concern: {out['L4_no_concern']}")
        ctx.close()
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
