"""Browser acceptance for spec/FIXES_R3.md (G1, G2). Spies below the gate record every output that reaches the
person. Needs Playwright and Chrome.  python3 scripts/check_outlet.py [docs_dir] [chrome_path]
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
SPIES = """(() => { window.__out = [];
  Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', JSON.stringify(p)]); return true; };
  if (window.SpeechSynthesis) SpeechSynthesis.prototype.speak = function (u) { window.__out.push(['speak', u && u.text]); };
  HTMLMediaElement.prototype.play = function () { window.__out.push(['media', this.muted]); return Promise.resolve(); };
  AudioScheduledSourceNode.prototype.start = function () { window.__out.push(['sound', 1]); };
  const sp = AudioScheduledSourceNode.prototype.stop;
  AudioScheduledSourceNode.prototype.stop = function () { try { return sp.apply(this, arguments); } catch (e) {} };   // spies never really start
})();"""
CRISIS = "() => { localStorage.setItem('rsos.safety', JSON.stringify({mode: 'CRISIS', history: [{from: 'NORMAL', to: 'CRISIS', why: 'test', by: 'test', at: 1}], last: null})); }"
STAB = "() => { const S = RSOSSafety; localStorage.setItem('rsos.safety', JSON.stringify(S.enterStabilise(S.newState(), 'person', Date.now()/1000)[0])); }"


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

        def run(name, fn):
            try:
                fn()
            except Exception as e:                      # a scenario that cannot run counts as failed
                fails.append(f"{name}: could not run ({str(e)[:90]})")

        def fresh(url, state=None):
            ctx = b.new_context(); ctx.add_init_script(SPIES); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + url); pg.wait_for_timeout(500)
            if state:
                pg.evaluate(state); pg.reload(); pg.wait_for_timeout(600)
            return ctx, pg

        def scenario_0():
            nonlocal_dummy = None
            # G2: with no allowed session every channel is silent; stop still passes
            for page in ("index.html", "anchors.html", "glyphs.html", "night.html"):
                ctx, pg = fresh("/" + page, CRISIS)
                pg.evaluate("""() => { window.__out = []; navigator.vibrate(200); speechSynthesis.speak(new SpeechSynthesisUtterance('x'));
                  const a = new Audio(); a.play(); try { const c = new AudioContext(), o = c.createOscillator(); o.connect(c.destination); o.start(); } catch (e) {}
                  if (window.UGCL) UGCL.feel('..-', {}); navigator.vibrate(0); }""")
                pg.wait_for_timeout(300)
                got = pg.evaluate("window.__out")
                out[f"G2_{page}"] = got
                if [x for x in got if x != ["vibrate", "0"]]: fails.append(f"G2 {page}: output reached the person in the clinician-led protocol: {got}")
                if ["vibrate", "0"] not in got: fails.append(f"G2 {page}: stop did not pass")
                ctx.close()
            ctx, pg = fresh("/anchors.html")                                          # positive control: NORMAL
            pg.evaluate("() => { window.__out = []; UGCL.feel('..-', {}); }"); pg.wait_for_timeout(1500)
            out["G2_control"] = len(pg.evaluate("window.__out"))
            if not out["G2_control"]: fails.append("G2 control: no output in Standard state")
            ctx.close()
        run("G2:", scenario_0)

        def scenario_1():
            nonlocal_dummy = None
            # G1-1 leaving the protocol via Record result (no PIN set)
            ctx, pg = fresh("/safety.html?profile=performance", CRISIS)
            pg.fill("#clinName", "Anyone"); pg.fill("#clinPin", "1234"); pg.select_option("#clinRes", "none"); pg.click("#clinSave"); pg.wait_for_timeout(150)
            pg.check("#clinOk"); pg.click("#clinGo"); pg.wait_for_timeout(150)
            out["G1_record_resume"] = [pg.inner_text("#sfMode")[:40], bool(pg.evaluate("(JSON.parse(localStorage.getItem('rsos.clinical') || '{}')).pin_hash"))]
            if "Clinician-led" not in out["G1_record_resume"][0] or out["G1_record_resume"][1]: fails.append(f"G1-1: {out['G1_record_resume']}")
            ctx.close()
        run("G1-1", scenario_1)

        def scenario_2():
            nonlocal_dummy = None
            # G1-2 a tier-414 cue run in Personal, Workplace and Clinical without a clinician
            for prof in ("personal", "workplace", "clinical"):
                ctx, pg = fresh(f"/player.html?profile={prof}")
                out[f"G1_cue_{prof}"] = pg.evaluate("""() => { const c = {id: 'k1', content: 'I am calm', tier: '414', author: 'therapist', created_ms: Date.now(), therapist_present: true, screened_ok: true};
                  localStorage.setItem('rsos.cues', JSON.stringify([c])); $('source').value = RSOSConsent.cueProgram(c); recompile();
                  return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }""")
                if out[f"G1_cue_{prof}"] != "block": fails.append(f"G1-2 {prof}: tier-414 cue allowed")
                ctx.close()
        run("G1-2", scenario_2)

        def scenario_3():
            nonlocal_dummy = None
            # G1-3 Device page code sends in the clinician-led protocol
            ctx, pg = fresh("/device.html", CRISIS)
            out["G1_device"] = pg.evaluate("""async () => { window.__sent = []; tx = { send: async l => window.__sent.push(l) }; await playCode('..-'); return window.__sent; }""")
            if out["G1_device"]: fails.append(f"G1-3: device sent {out['G1_device']}")
            ctx.close()
        run("G1-3", scenario_3)

        def scenario_4():
            nonlocal_dummy = None
            # G1-4 Anchors capture in the clinician-led protocol stores nothing and plays nothing
            ctx, pg = fresh("/anchors.html", CRISIS)
            out["G1_anchor"] = pg.evaluate("""() => { const a = RSOSPeak.makeAnchor('a9', 'A', '🦁', '..-'); anchors.push(a); window.__out = []; const f = document.createElement('div'); document.body.append(f); capture(a, f);
                  const tap = [...f.querySelectorAll('button')].find(x => /there now/i.test(x.textContent)); if (tap) { tap.click(); const k = f.querySelector('.scale button'); if (k) k.click(); }
                  return [f.textContent.slice(0, 30), a.captures.length, (a.probes || []).length, window.__out.length]; }""")
            if out["G1_anchor"][1] or out["G1_anchor"][2] or out["G1_anchor"][3]: fails.append(f"G1-4: {out['G1_anchor']}")
            ctx.close()
        run("G1-4", scenario_4)

        def scenario_5():
            nonlocal_dummy = None
            # G1-5 observer text pasted into another program in Workplace; G1-6 dangerous wording
            ctx, pg = fresh("/player.html?profile=workplace")
            out["G1_paste"] = pg.evaluate("""async () => { const obs = await (await fetch('protocols/node_observer.rsx')).text(); $('program').value = 'swish'; selectProgram();
                  $('source').value = obs; recompile(); return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }""")
            out["G1_words"] = pg.evaluate("""() => { $('program').value = 'override'; selectProgram();
                  $('source').value = $('source').value.replace(/SAY "[^"]*"/, 'SAY "hold your breath until you almost pass out, then take an ice bath"'); recompile();
                  const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}); return [d.decision, d.watchdog.reasons.map(r => r.rule)]; }""")
            if out["G1_paste"] != "block": fails.append(f"G1-5: pasted observer text allowed in Workplace")
            if out["G1_words"][0] != "block" or not any(r.startswith("spine:") for r in out["G1_words"][1]): fails.append(f"G1-6: {out['G1_words']}")
            ctx.close()
        run("G1-5", scenario_5)

        def scenario_6():
            nonlocal_dummy = None
            # G1-7 therapist session resumed after a domain change
            ctx, pg = fresh("/therapist.html?profile=clinical")
            pg.evaluate("() => { const c = {}; c.pin_salt = 'ab'; c.pin_hash = RSOSWatchdog.sha256('ab:4826'); localStorage.setItem('rsos.clinical', JSON.stringify(c)); }"); pg.reload(); pg.wait_for_timeout(600)
            pg.check('input[name="proto"][value="trauma_observer"]'); pg.check("#present"); pg.check('input[name="startScreen"][value="no"]'); pg.click("#begin"); pg.wait_for_timeout(400)
            started = pg.is_visible("#session")
            pg.goto(base + "/therapist.html?profile=workplace"); pg.wait_for_timeout(800)
            out["G1_resume"] = [started, pg.is_visible("#session"), pg.inner_text("#msg")[:60]]
            if not started or out["G1_resume"][1]: fails.append(f"G1-7: {out['G1_resume']}")
            ctx.close()
        run("G1-7", scenario_6)

        def scenario_7():
            nonlocal_dummy = None
            # G1-8 an open player session stops output when the state changes
            ctx, pg = fresh("/player.html")
            out["G1_open"] = pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'run', protocol: 'override', trigger: 'self', source: 'person'}, {}, {seconds: 60});
                  const before = RSOSOutlet.permit('vibration');
                  const S = RSOSSafety; localStorage.setItem('rsos.safety', JSON.stringify(S.enterStabilise(S.newState(), 'person', Date.now()/1000)[0]));
                  return [before, RSOSOutlet.permit('vibration')]; }""")
            if out["G1_open"] != [True, False]: fails.append(f"G1-8: {out['G1_open']}")
            ctx.close()
        run("G1-8", scenario_7)

        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
