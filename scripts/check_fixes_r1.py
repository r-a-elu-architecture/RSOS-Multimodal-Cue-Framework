"""Browser acceptance for spec/FIXES_R1.md: the reviewer's page scenarios. Needs Playwright and Chrome.

python3 scripts/check_fixes_r1.py [docs_dir] [chrome_path]
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
CRISIS_STATE = "() => { const S = RSOSSafety; localStorage.setItem('rsos.safety', JSON.stringify(S.observe(S.newState(), S.eventFromCheck({clinical_result: 'high'}), Date.now()/1000)[0])); }"


SETPIN = "() => { const c = JSON.parse(localStorage.getItem('rsos.clinical') || '{}'); c.pin_salt = 'ab'; c.pin_hash = RSOSWatchdog.sha256('ab:4826'); localStorage.setItem('rsos.clinical', JSON.stringify(c)); }"   # the clinician sets a PIN first (FIXES_R2 R2-1)


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

        def page(ctx):
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            return pg

        # S-1: resuming from the clinician-led protocol needs the clinician PIN
        ctx = b.new_context(); pg = page(ctx)
        pg.goto(f"{base}/safety.html?profile=clinical"); pg.wait_for_timeout(400)
        pg.check("#clinOn"); pg.fill("#clinName", "Dr A"); pg.select_option("#clinRes", "high")
        pg.click("#clinSave"); pg.wait_for_timeout(150)
        out["S1_no_pin"] = pg.inner_text("#sfMode")
        pg.fill("#clinPin", "4826"); pg.click("#clinSave"); pg.wait_for_timeout(150)
        out["S1_after_pin"] = pg.inner_text("#sfMode")
        pg.fill("#clinPin", "0000"); pg.check("#clinOk"); pg.click("#clinGo"); pg.wait_for_timeout(150)
        out["S1_wrong_pin"] = [pg.inner_text("#sfMode"), pg.inner_text("#sfNote")]
        pg.fill("#clinPin", "4826"); pg.click("#clinGo"); pg.wait_for_timeout(150)
        out["S1_right_pin"] = pg.inner_text("#sfMode")
        if "Clinician-led" in out["S1_no_pin"]: fails.append("S-1: a result was recorded without setting a PIN")
        if "Clinician-led" not in out["S1_after_pin"]: fails.append("S-1: high result did not start the clinician-led protocol")
        if "Clinician-led" not in out["S1_wrong_pin"][0]: fails.append("S-1: a wrong PIN resumed practice")
        if "Standard" not in out["S1_right_pin"]: fails.append("S-1: the right PIN did not resume")
        ctx.close()

        # S-4b: an override renamed paced_breathing does not run during Stabilisation
        ctx = b.new_context(); pg = page(ctx)
        pg.goto(f"{base}/player.html"); pg.wait_for_timeout(1200)
        pg.evaluate("() => { const S = RSOSSafety; localStorage.setItem('rsos.safety', JSON.stringify(S.enterStabilise(S.newState(), 'person', Date.now()/1000)[0])); }")
        pg.evaluate("() => { $('program').value = 'override'; selectProgram(); }"); pg.wait_for_timeout(300)
        pg.evaluate("() => { $('source').value = $('source').value.replace('PROTOCOL override', 'PROTOCOL paced_breathing'); recompile(); }"); pg.wait_for_timeout(300)
        out["S4b"] = pg.evaluate("() => { const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}); return [timeline.protocol, d.decision]; }")
        pg.evaluate("() => { $('program').value = 'interrupt_only'; selectProgram(); }"); pg.wait_for_timeout(400)
        out["S4b_real"] = pg.evaluate("() => safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision")
        if out["S4b"][1] != "block": fails.append(f"S-4b: renamed override allowed {out['S4b']}")
        if out["S4b_real"] != "allow": fails.append("S-4b: the real interrupt-only program is no longer allowed in Stabilisation")
        ctx.close()

        # W-4: a clinician-led plan's observer node is held in Workplace; W-13: Clinical shows the clinician box
        for prof in ("workplace", "clinical"):
            ctx = b.new_context(); pg = page(ctx)
            pg.goto(f"{base}/player.html?profile={prof}"); pg.wait_for_timeout(600)
            pg.evaluate("""() => { const N = RSOSNodes; const p = N.plan({concerns: ['ptsd'], author: 'therapist', nodes: [{archetype: 'OBSERVER'}]});
              p.approved = true; p.intake = {concerns: ['ptsd']}; localStorage.setItem('rsos.plan', JSON.stringify(p)); }""")
            pg.goto(f"{base}/player.html?program=plan:0&profile={prof}"); pg.wait_for_timeout(1200)
            out[f"W4_{prof}"] = pg.evaluate("() => [runFlags(), safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision, !document.getElementById('clinRun').hidden]")
            ctx.close()
        if out["W4_workplace"][1] != "block": fails.append(f"W-4: observer node of a clinician-led plan runs in Workplace {out['W4_workplace']}")
        if not out["W4_clinical"][2]: fails.append("W-13: the clinician box is not shown for a clinician-led run in Clinical")

        # W-5: automatic firing with one signal becomes an offer
        ctx = b.new_context(); pg = page(ctx)
        pg.goto(f"{base}/player.html"); pg.wait_for_timeout(1000)
        out["W5"] = pg.evaluate("""() => { const one = RSOSGuard.ask({kind: 'cue', protocol: 'anchor:a', trigger: 'device', source: 'person', auto: true, signals: ['heart_rate']}, {});
          localStorage.setItem('rsos.consents', JSON.stringify([{scope: 'automatic_firing', by: 'person', given: 0, withdrawn: null}]));
          const two = RSOSGuard.ask({kind: 'cue', protocol: 'anchor:a', trigger: 'device', source: 'person', auto: true, signals: ['heart_rate', 'hrv']}, {});
          return [one.decision, two.decision, /signals: sig/.test(String(anchorOffer))]; }""")
        if out["W5"][:2] != ["ask", "allow"] or not out["W5"][2]: fails.append(f"W-5: {out['W5']}")
        ctx.close()

        # W-3: clinician-led THERA session: screening on the start panel; steps locked; yes closes
        ctx = b.new_context(); pg = page(ctx)
        pg.goto(f"{base}/therapist.html?profile=clinical"); pg.wait_for_timeout(600)
        pg.evaluate(SETPIN); pg.reload(); pg.wait_for_timeout(600)
        pg.check('input[name="proto"][value="trauma_observer"]'); pg.check("#present"); pg.click("#begin"); pg.wait_for_timeout(300)
        out["W3_no_screen"] = pg.inner_text("#msg")
        pg.check('input[name="startScreen"][value="no"]'); pg.click("#begin"); pg.wait_for_timeout(400)
        pg.locator("#steps li").nth(4).click(); pg.wait_for_timeout(200)
        out["W3_locked"] = pg.evaluate("() => [cur.at, screenIndex(), cur.screenOk]")
        pg.locator("#steps li").nth(1).click(); pg.wait_for_timeout(200)
        pg.select_option("#m-screen", "yes"); pg.click("text=Done, next step"); pg.wait_for_timeout(300)
        out["W3_yes"] = [pg.is_visible("#session"), pg.is_visible("#done")]
        if "Watchdog" not in out["W3_no_screen"]: fails.append("W-3: a clinician-led session started without a screening answer")
        if out["W3_locked"][0] > out["W3_locked"][1]: fails.append(f"W-3: a step after the screening opened {out['W3_locked']}")
        if out["W3_yes"] != [False, True]: fails.append(f"W-3: a yes did not close the session {out['W3_yes']}")
        ctx.close()

        # P-5: choosing Clinical from the menu asks first
        ctx = b.new_context(); pg = page(ctx)
        pg.goto(f"{base}/index.html?profile=personal"); pg.wait_for_timeout(400)
        pg.select_option("#profileSelect", "clinical"); pg.wait_for_timeout(300)
        out["P5"] = [pg.is_visible("#profileConfirm"), pg.evaluate("RSOSProfiles.current()")]
        pg.click("text=Switch to Clinical"); pg.wait_for_timeout(500)
        out["P5_after"] = pg.evaluate("RSOSProfiles.current()")
        if out["P5"] != [True, "personal"] or out["P5_after"] != "clinical": fails.append(f"P-5: {out['P5']} {out['P5_after']}")
        ctx.close()
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
