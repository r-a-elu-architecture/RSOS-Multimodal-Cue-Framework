"""Browser acceptance for spec/FIXES_R6.md (Q1): the sixth reviewer's scenarios (review/r6/attacks.py, C1-C8) through the
real page paths, each with its expected outcome; the run is changed after Begin. Spies sit below the output gate.
python3 scripts/check_fixes_r6.py [docs_dir] [chrome_path]      Needs Playwright, Chrome and node.
"""
import functools
import http.server
import json
import pathlib
import socketserver
import subprocess
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
SPIES = """(() => { window.__out = []; window.__hold = 0; window.addEventListener('rsos-outlet-hold', () => { window.__hold++; });
  Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', JSON.stringify(p)]); return true; };
  SpeechSynthesis.prototype.speak = function (u) { window.__out.push(['speak', u.text]); };
})();"""
STATE = """(m) => { if (m) localStorage.setItem('rsos.safety', JSON.stringify({mode: m, history: [{from: 'NORMAL', to: m, why: 't', by: 't', at: 1}], last: null}));
  else localStorage.removeItem('rsos.safety'); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'})); }"""
FAKETX = """() => { window.__sent = []; tx = { kind: 'fake', send: async l => { if (/^\\s*START\\b/im.test(String(l)) && !(window.RSOSOutlet && RSOSOutlet.permit('wristband'))) return; window.__sent.push(l); } };
  for (const id of ['stop', 'check', 'play', 'run']) $(id).disabled = false; }"""
PLANS = json.loads(subprocess.run(["node", "-e", """const N = require(process.argv[1]);
const mk = (concerns, nodes, extra) => { const p = N.plan({ concerns, nodes, author: extra.author }); p.approved = true; Object.assign(p, extra.set); return p; };
const DX = { therapist_led: true, dx: ['depression'], intake: { concerns: ['depression'] } };
process.stdout.write(JSON.stringify({
  dx: mk(['depression'], [{ archetype: 'LION' }], { set: DX }),
  ptsd: mk(['ptsd'], [{ archetype: 'LION' }, { archetype: 'OBSERVER' }], { author: 'therapist', set: { therapist_led: true, intake: { concerns: ['ptsd'] } } }),
  dxOwn: mk(['depression'], [{ name: 'Anchor', frames: ['I am steady and I choose my next step'], contexts: ['At my desk'], representation: 'A warm blue lake' }], { set: DX }),
  dxSteady: mk(['depression'], [{ archetype: 'LION', frames: ['I am steady'] }], { set: DX }) }));""", str(DOCS / "js" / "nodes.js")],
    capture_output=True, text=True, check=True).stdout)
DECIDE = "() => safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    out, fails, errs = {}, [], []

    def expect(name, got, want):
        out[name] = got
        if got != want:
            fails.append(f"{name}: got {got!r}, expected {want!r}")

    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        def page(url, plan=None, route=None):
            ctx = b.new_context(); ctx.add_init_script(SPIES)
            if route:
                ctx.route(route, lambda rt: rt.fulfill(status=404, body=""))
            pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(url + ": " + str(e)))
            pg.goto(base + url); pg.wait_for_timeout(600)
            if plan is not None:
                pg.evaluate("p => localStorage.setItem('rsos.plan', JSON.stringify(p))", plan); pg.reload()
            pg.wait_for_function("window.RSOSLineage && RSOSLineage.loaded", timeout=5000); pg.wait_for_timeout(300)
            return ctx, pg

        def begin(pg):   # Start and Begin, as a person clicks them
            pg.evaluate("() => { $('optVib').checked = true; $('optVoice').checked = true; }")
            pg.click("#start"); pg.wait_for_selector("#checkinGo", state="visible", timeout=5000); pg.click("#checkinGo"); pg.wait_for_timeout(300)
            return pg.evaluate("!!run")

        def node(pg, i):
            pg.select_option("#program", f"plan:{i}"); pg.wait_for_timeout(300); return pg.evaluate("$('source').value")

        def typed(pg, text):
            pg.fill("#source", text); pg.wait_for_timeout(450)

        def run(name, fn):
            try:
                fn()
            except Exception as e:
                fails.append(f"{name}: could not run ({str(e)[:200]})")

        def c1():   # F1-F3: the running program cannot change
            ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
            pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
            started = begin(pg)
            locked = pg.evaluate("['program', 'source', 'f0', 'inhale'].map(id => $(id).disabled)")
            pg.evaluate("() => { window.__out = []; $('program').value = 'plan:0'; $('program').dispatchEvent(new Event('change')); }")   # a script, not the menu
            pg.wait_for_timeout(1500)
            said = pg.evaluate("window.__out.filter(x => x[0] === 'speak').map(x => x[1])")
            expect("C1a menu locked; a changed program stops the run", [started, locked, pg.evaluate("!!run"), any("hold my ground" in s for s in said),
                                                                       "changed while running" in pg.evaluate("$('compileMsg').textContent")],
                   [True, [True] * 4, False, False, True])
            expect("C1a controls unlocked after the run", pg.evaluate("$('program').disabled"), False)
            ctx.close()
            ctx, pg = page("/player.html?profile=workplace", PLANS["ptsd"])
            obs = node(pg, 1); pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
            started = begin(pg)
            pg.evaluate("(t) => { window.__out = []; $('source').value = t; recompile(); }", obs); pg.wait_for_timeout(1500)
            said = pg.evaluate("window.__out.filter(x => x[0] === 'speak').map(x => x[1])")
            expect("C1b typed observer node stops the run (Workplace)", [started, pg.evaluate("!!run"), any("Nothing binds" in s for s in said)], [True, False, False])
            ctx.close()
            ctx, pg = page("/player.html?profile=personal")
            pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300); started = begin(pg)
            pg.evaluate(STATE, "CRISIS"); pg.wait_for_timeout(1500)
            expect("C1c control: CRISIS during a run", [started, pg.evaluate("!!run"), pg.evaluate("window.__hold") > 0], [True, False, True])
            ctx.close()

        def p1():   # FIXES_R6C P1: text typed and Started at once is decided and played as typed
            ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
            n = node(pg, 0); pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
            pg.evaluate("(t) => { $('source').value = t; $('source').dispatchEvent(new Event('input')); $('start').click(); }", n)   # no wait for the 250 ms
            pg.wait_for_timeout(600)
            held = [pg.is_visible("#checkinGo"), pg.evaluate("!!run"), "Held by the Watchdog" in pg.evaluate("$('compileMsg').textContent")]
            ctx.close()
            ctx, pg = page("/player.html?profile=personal")
            pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
            mine = 'PROTOCOL mine "Mine"\nPHASE a dur=3s {\n  SAY "My own words now"\n}\n'
            pg.evaluate("(t) => { $('source').value = t; $('source').dispatchEvent(new Event('input')); $('start').click(); }", mine)
            pg.wait_for_selector("#checkinGo", state="visible", timeout=5000); pg.click("#checkinGo"); pg.wait_for_timeout(300)
            expect("P1 decided and played as typed, without the 250 ms wait", held + [pg.evaluate("run ? run.tl.protocol : null")], [False, False, True, "mine"])
            ctx.close()

        def c2():   # §2 share = shared / |origin|
            ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
            n = node(pg, 0).replace("warmth in the belly", "warmth in the chest"); pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
            got = []
            for k in (0, 1, 4, 8):
                typed(pg, n + "".join('PHASE mine%d {\n  SAY "My own line number %d"\n}\n' % (i, i) for i in range(k))); got.append(pg.evaluate(DECIDE))
            expect("C2 diagnosed node reworded plus own lines", got, ["block"] * 4)
            ctx.close()

        def c3_c5():   # §2 $future, joined text; §3 accents and look-alikes
            ctx, pg = page("/player.html?profile=personal", PLANS["dxOwn"])
            n = node(pg, 0)
            pg.fill("#f0", "At my dęsk"); pg.wait_for_timeout(300); pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
            v = (n.replace("I am steady and I choose my next step", "I am stéady and I choose my next stép").replace("A warm blue lake", "A wɑrm blue lake")
                 .replace("At my desk", "At my dеsk").replace("Spine straight, warmth in the belly", "Spine straïght, warmth in the belly")
                 .replace("Hold the anchor in you as you enter", "Hold the anchօr in you as you enter").replace("ANCHOR", "ANKER").replace('TACTON "."', 'TACTON ".."'))
            typed(pg, v); c3 = pg.evaluate(DECIDE)
            pg.select_option("#program", "plan:0"); pg.wait_for_timeout(300)
            pg.fill("#f0", "At my"); pg.fill("#f1", "desk"); pg.wait_for_timeout(300); pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
            v = (n.replace('  SAY "I am steady and I choose my next step"', '  SAY "I am steady and"\n  SAY "I choose my next step"')
                 .replace('  A "I am steady and I choose my next step"', '  A "I am steady"').replace('  FRAME "I am steady and I choose my next step"', '  FRAME "I choose"')
                 .replace('  V "A warm blue lake"', '  V "A warm"').replace('SEE "A warm blue lake"', 'SEE "A warm"\n  SEE "blue lake"')
                 .replace('FUTURES "At my desk"', 'FUTURES "At my" | "desk"').replace('"Spine straight, warmth in the belly"', '"Spine straight,"')
                 .replace('FEEL "Hold the anchor in you as you enter"', 'FEEL "Hold the anchor"\n  FEEL "in you as you enter"').replace("ANCHOR", "ANKER").replace('TACTON "."', 'TACTON ".."'))
            typed(pg, v); c4 = pg.evaluate(DECIDE)
            pg.select_option("#program", "plan:0"); pg.wait_for_timeout(300)
            pg.fill("#f0", "$future"); pg.fill("#f1", ""); pg.fill("#f2", ""); pg.wait_for_timeout(300); pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
            v = (n.replace('FUTURES "At my desk"', 'FUTURES "$future"')
                 .replace('PHASE frame1 breath=exhale {\n  SAY "I am steady and I choose my next step"\n}',
                          'PHASE frame1 breath=exhale {\n  FOR FUTURE {\n    SAY "I am steady and I choose my next step $future"\n    SEE "A warm blue lake $future"\n  }\n}')
                 .replace('  SEE "A warm blue lake"\n', '').replace('  V "A warm blue lake"\n', '  V "Blue"\n').replace('  A "I am steady and I choose my next step"\n', '  A "Hum"\n')
                 .replace('  FRAME "I am steady and I choose my next step"\n', '').replace('  K "Spine straight, warmth in the belly"\n', '  K "Calm"\n')
                 .replace('  FEEL "Hold the anchor in you as you enter"\n', '').replace("ANCHOR", "ANKER").replace('TACTON "."', 'TACTON ".."'))
            typed(pg, v); c5 = pg.evaluate(DECIDE)
            expect("C3 accents/look-alikes, C4 split sentence, C5 $future", [c3, c4, c5], ["block"] * 3)
            ctx.close()

        def c6():   # §2 no over-blocking from a short frame
            ctx, pg = page("/player.html?profile=personal", PLANS["dxSteady"])
            got = {}
            for p in ("ssit_higher", "ssit_calm", "swish", "override", "interrupt_only"):
                pg.select_option("#program", p); pg.wait_for_timeout(250); got[p] = pg.evaluate(DECIDE)
            typed(pg, 'PROTOCOL mine "Mine"\nPHASE a {\n  SAY "I am steady today"\n}\n'); got["own: I am steady today"] = pg.evaluate(DECIDE)
            typed(pg, 'PROTOCOL mine "Mine"\nPHASE a {\n  SAY "I am steady"\n}\n'); got["own: I am steady (exact)"] = pg.evaluate(DECIDE)
            expect("C6 short frame holds only its exact text", got, {"ssit_higher": "allow", "ssit_calm": "allow", "swish": "allow", "override": "allow",
                                                                    "interrupt_only": "allow", "own: I am steady today": "allow", "own: I am steady (exact)": "block"})
            ctx.close()

        def c7():   # §2 R6-9: one built-in fails to load: strict, and the page says so
            ctx, pg = page("/player.html?profile=personal", PLANS["dx"], route="**/protocols/tier579_glyph.rsx")
            pg.select_option("#program", "override"); pg.wait_for_timeout(250)
            d = pg.evaluate(DECIDE); pg.click("#start"); pg.wait_for_timeout(400)
            expect("C7 strict lineage is explained", [pg.evaluate("RSOSLineage.strict"), d, "could not be loaded" in pg.evaluate("$('compileMsg').textContent")], [True, "block", True])
            ctx.close()

        def c8():   # H1: the device page closes its held sessions
            ctx, pg = page("/device.html?profile=personal")
            pg.evaluate(FAKETX); pg.select_option("#prog", "override"); pg.click("#run"); pg.wait_for_timeout(800)
            a = pg.evaluate("window.__sent.includes('START')")
            pg.evaluate(STATE, "CRISIS"); pg.wait_for_timeout(1500)
            stopped = [pg.evaluate("window.__sent.includes('STOP')"), pg.evaluate("$('msg').textContent")]
            pg.evaluate(STATE, None); pg.wait_for_timeout(500); pg.evaluate("() => { window.__sent = []; }")
            pg.fill("#code", "-.-"); pg.click("#play"); pg.wait_for_timeout(600)
            expect("C8 device page after a hold", [a] + stopped + [pg.evaluate("window.__sent.includes('START')")], [True, True, "Stopped by the Watchdog.", True])
            ctx.close()

        def controls():   # Q3 and the recorded consequence of §2
            ctx, pg = page("/player.html?profile=personal")
            expect("Control: no plan, every built-in allowed", pg.evaluate("() => PROTOCOLS.filter(p => { $('program').value = p; selectProgram(); return (" + DECIDE + ")() !== 'allow'; })"), [])
            ctx.close()
            ctx, pg = page("/device.html?profile=personal")
            pg.evaluate(FAKETX); pg.select_option("#prog", "node_observer"); pg.click("#run"); pg.wait_for_timeout(900)
            expect("Control: no plan, built-in Observer plays on the band", pg.evaluate("window.__sent.includes('START')"), True)
            ctx.close()
            ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
            pg.select_option("#program", "node_lion"); pg.wait_for_timeout(250)
            expect("Recorded: with a diagnosed plan the built-in Lion node is held", pg.evaluate(DECIDE), "block")
            ctx.close()

        for name, fn in (("C1", c1), ("P1", p1), ("C2", c2), ("C3-C5", c3_c5), ("C6", c6), ("C7", c7), ("C8", c8), ("controls", controls)):
            run(name, fn)
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
