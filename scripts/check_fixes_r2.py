"""Browser acceptance for spec/FIXES_R2.md: the repeat reviewer's page scenarios. Needs Playwright and Chrome.

python3 scripts/check_fixes_r2.py [docs_dir] [chrome_path]
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
CRISIS = "() => { const S = RSOSSafety; localStorage.setItem('rsos.safety', JSON.stringify(S.observe(S.newState(), S.eventFromCheck({clinical_result: 'high'}), Date.now()/1000)[0])); }"


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

        def fresh():
            ctx = b.new_context(); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); return ctx, pg

        # R2-1: clinician-led protocol with no PIN on the device: Resume with any PIN must not resume
        for prof in ("performance", "personal", "clinical"):
            ctx, pg = fresh()
            pg.goto(f"{base}/safety.html?profile={prof}"); pg.wait_for_timeout(400)
            pg.evaluate(CRISIS); pg.reload(); pg.wait_for_timeout(400)
            pg.fill("#clinName", "Anyone"); pg.fill("#clinPin", "1234"); pg.check("#clinOk"); pg.click("#clinGo"); pg.wait_for_timeout(200)
            out[f"R2_1_{prof}"] = [pg.inner_text("#sfMode")[:40], bool(pg.evaluate("(JSON.parse(localStorage.getItem('rsos.clinical') || '{}')).pin_hash"))]
            if "Clinician-led" not in out[f"R2_1_{prof}"][0] or out[f"R2_1_{prof}"][1]:
                fails.append(f"R2-1 {prof}: {out[f'R2_1_{prof}']}")
            ctx.close()
        # R2-1: without a PIN the node studio shows no screening answers in Clinical
        ctx, pg = fresh()
        pg.goto(f"{base}/nodes.html?profile=clinical"); pg.wait_for_timeout(500)
        out["R2_1_noscreen"] = pg.evaluate("() => [document.getElementById('screenQ').textContent.slice(0, 40), getComputedStyle(document.querySelector('input[name=screen]').closest('.chips')).display]")
        if out["R2_1_noscreen"][1] != "none": fails.append(f"R2-1: screening answers shown without a PIN {out['R2_1_noscreen']}")
        ctx.close()
        # R2-1: five wrong PINs lock
        ctx, pg = fresh()
        pg.goto(f"{base}/safety.html?profile=clinical"); pg.wait_for_timeout(400)
        pg.check("#clinOn"); pg.wait_for_timeout(100)
        pg.fill("#clinName", "Dr A"); pg.fill("#clinPin", "4826"); pg.click("#pinSet"); pg.wait_for_timeout(100)
        pg.evaluate(CRISIS); pg.reload(); pg.wait_for_timeout(400)
        pg.fill("#clinName", "Dr A"); pg.check("#clinOk")
        for _ in range(5):
            pg.fill("#clinPin", "0000"); pg.click("#clinGo"); pg.wait_for_timeout(60)
        pg.fill("#clinPin", "4826"); pg.click("#clinGo"); pg.wait_for_timeout(150)
        out["R2_1_lock"] = [pg.inner_text("#sfMode")[:40], pg.inner_text("#sfNote")]
        if "Clinician-led" not in out["R2_1_lock"][0]: fails.append(f"R2-1: lock not applied {out['R2_1_lock']}")
        ctx.close()

        # R2-2: Workplace, difficult-memories concern ticked (as LINX does): the plan is held
        ctx, pg = fresh()
        pg.goto(f"{base}/nodes.html?profile=workplace"); pg.wait_for_timeout(500)
        pg.evaluate("() => { const i = document.querySelector('#concerns input[value=ptsd]'); i.checked = true; i.dispatchEvent(new Event('change', {bubbles: true})); }")
        pg.locator("button.pick", has_text="Lion").first.click(); pg.wait_for_timeout(200)
        pg.check("#consent"); pg.click("#save"); pg.wait_for_timeout(600)
        out["R2_2"] = [pg.url.split("/")[-1], pg.inner_text("#msg")[:120], pg.evaluate("(JSON.parse(localStorage.getItem('rsos.watchdog.log') || '[]')).map(r => r.decision + ' ' + r.kind + ' ' + r.rules.join(','))")]
        if "player.html" in out["R2_2"][0] or not any(x.startswith("hold plan") and "memory" in x for x in out["R2_2"][2]):
            fails.append(f"R2-2: {out['R2_2']}")
        ctx.close()

        # R2-3: in Stabilisation an anchor the gate would offer is not offered
        ctx, pg = fresh()
        pg.goto(f"{base}/player.html"); pg.wait_for_timeout(1000)
        pg.evaluate("() => { const S = RSOSSafety; localStorage.setItem('rsos.safety', JSON.stringify(S.enterStabilise(S.newState(), 'person', Date.now()/1000)[0]));"
                    " localStorage.setItem('rsos.anchors', JSON.stringify([RSOSPeak.makeAnchor('a1', 'A', '🦁', '..-')])); }")
        out["R2_3"] = pg.evaluate("() => { RSOSGate.mayFire = () => ({ decision: 'allow', reasons: [] }); RSOSGate.gate = () => ({ stage: 'suggest' }); const r = anchorOffer(); return [r, document.getElementById('anchorOffer').hidden]; }")
        if out["R2_3"] != [False, True]: fails.append(f"R2-3: {out['R2_3']}")
        ctx.close()

        # R2-6: a trial session saved without pressing play adds no probe
        ctx, pg = fresh()
        pg.goto(f"{base}/trials.html"); pg.wait_for_timeout(400)
        pg.evaluate("() => { localStorage.setItem('rsos.anchors', JSON.stringify([RSOSPeak.makeAnchor('a1', 'A', '🦁', '..-')]));"
                    " const t = RSOSTrial.newTrial('anchor_vs_sham', 1, 99, 't', 0); t.anchor = 'a1'; localStorage.setItem('rsos.trial', JSON.stringify(t)); }")
        pg.reload(); pg.wait_for_timeout(400)
        pg.click("text=Start today's session"); pg.wait_for_timeout(200)
        sc = pg.locator(".scale"); sc.nth(0).locator("button").nth(4).click(); sc.nth(1).locator("button").nth(7).click()
        pg.click("text=Save this session"); pg.wait_for_timeout(400)
        out["R2_6"] = pg.evaluate("(JSON.parse(localStorage.getItem('rsos.anchors'))[0].probes || []).length")
        if out["R2_6"] != 0: fails.append(f"R2-6: {out['R2_6']} probe(s) without a code played")
        ctx.close()
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
