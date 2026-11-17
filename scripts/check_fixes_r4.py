"""Browser acceptance for spec/FIXES_R4.md (Q1): the fourth reviewer's page scenarios. Needs Playwright and Chrome.
python3 scripts/check_fixes_r4.py [docs_dir] [chrome_path]
"""
import base64
import functools
import http.server
import json
import pathlib
import socketserver
import struct
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
DATA = b"\x00\x00" * 16000
WAV = "data:audio/wav;base64," + base64.b64encode(b"RIFF" + struct.pack("<I", 36 + len(DATA)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 8000, 16000, 2, 16)
                                                    + b"data" + struct.pack("<I", len(DATA)) + DATA).decode()
SPIES = """(() => { window.__out = []; window.__hold = 0; window.addEventListener('rsos-outlet-hold', () => { window.__hold++; });
  Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', JSON.stringify(p)]); return true; };
  const st = AudioScheduledSourceNode.prototype.stop;
  AudioScheduledSourceNode.prototype.stop = function () { window.__out.push(['stop', 1]); try { return st.apply(this, arguments); } catch (e) {} };
})();"""
CRISIS = "() => { localStorage.setItem('rsos.safety', JSON.stringify({mode: 'CRISIS', history: [{from: 'NORMAL', to: 'CRISIS', why: 't', by: 't', at: 1}], last: null})); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'})); }"
MEMPLAN = """() => { const p = RSOSNodes.plan({concerns: ['ptsd'], author: 'therapist', nodes: [{archetype: 'OBSERVER'}]}); p.approved = true; p.intake = {concerns: ['ptsd']};
  localStorage.setItem('rsos.plan', JSON.stringify(p)); return p.nodes[0].tacton; }"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    out, fails, errs = {}, [], []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])

        def fresh(url):
            ctx = b.new_context(); ctx.add_init_script(SPIES); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + url); pg.wait_for_timeout(900); return ctx, pg

        def run(name, fn):
            try:
                fn()
            except Exception as e:
                fails.append(f"{name}: could not run ({str(e)[:100]})")

        def g1():   # a held run session does not fall back to the page's session
            ctx, pg = fresh("/player.html")
            out["G1"] = pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'run', protocol: 'override', trigger: 'self', source: 'person'}, {}, {seconds: 60});
              const a = RSOSOutlet.permit('vibration'); const c = RSOSContain.newState(); c.quarantine.override = {since: 1, reason: 't', signals: ['worse'], therapist: false};
              localStorage.setItem('rsos.contain', JSON.stringify(c)); const b = RSOSOutlet.permit('vibration'), c2 = RSOSOutlet.permit('sound');
              return [a, b, c2, !!(RSOSOutlet.session() && RSOSOutlet.session().held)]; }""")
            if out["G1"] != [True, False, False, True]: fails.append(f"G1: {out['G1']}")
            ctx.close()

        def g2():   # the domain is re-read when it changes in another tab
            ctx, pg = fresh("/player.html?profile=personal")
            out["G2"] = pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'run', protocol: 'plan:0', memory_work: true, trigger: 'self', source: 'person'}, {}, {seconds: 60});
              const a = RSOSOutlet.permit('vibration'); localStorage.setItem('rsos.profile', JSON.stringify('workplace'));
              window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.profile'})); return [a, RSOSDomain.profile, RSOSOutlet.permit('vibration')]; }""")
            if out["G2"] != [True, "workplace", False]: fails.append(f"G2: {out['G2']}")
            ctx.close()

        def g3():   # output already playing is stopped; the band gets STOP
            ctx, pg = fresh("/player.html")
            pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'run', protocol: 'override', trigger: 'self', source: 'person'}, {}, {seconds: 60});
              const c = new AudioContext(), o = c.createOscillator(); o.connect(c.destination); o.start(); window.__out = []; }""")
            pg.evaluate(CRISIS); pg.wait_for_timeout(300)
            out["G3_player"] = [pg.evaluate("window.__hold"), pg.evaluate("window.__out"), pg.evaluate("RSOSOutlet.gains()")]
            if not out["G3_player"][0] or ["stop", 1] not in out["G3_player"][1] or ["vibrate", "0"] not in out["G3_player"][1] or any(out["G3_player"][2]):
                fails.append(f"G3 player: {out['G3_player']}")
            ctx.close()
            ctx, pg = fresh("/device.html")
            pg.evaluate("() => { window.__sent = []; tx = { send: async l => window.__sent.push(l) }; RSOSOutlet.adopt({kind: 'run', protocol: 'override', trigger: 'self', source: 'person'}, {}, {seconds: 60}); }")
            pg.evaluate(CRISIS); pg.wait_for_timeout(300)
            out["G3_band"] = pg.evaluate("window.__sent")
            if "STOP" not in out["G3_band"]: fails.append(f"G3 band: {out['G3_band']}")
            ctx.close()

        def g4():   # autoplay and unmuted media are paused without a session; speaker gains are 0
            ctx, pg = fresh("/anchors.html")
            pg.evaluate(CRISIS)
            out["G4"] = pg.evaluate("""async (src) => { const a = document.createElement('audio'); a.src = src; a.loop = true; a.autoplay = true; document.body.append(a);
              const m = document.createElement('audio'); m.src = src; m.loop = true; m.muted = true; document.body.append(m); await m.play().catch(() => {}); m.muted = false;
              const c = new AudioContext(), sp = c.createScriptProcessor(1024, 1, 1); sp.connect(c.destination);
              await new Promise(r => setTimeout(r, 800)); return [a.paused, m.paused, RSOSOutlet.gains()]; }""", WAV)
            if out["G4"][0] is not True or out["G4"][1] is not True or any(out["G4"][2]): fails.append(f"G4: {out['G4']}")
            ctx.close()

        def g5():   # device- and agent-triggered outputs need the firing rules
            ctx, pg = fresh("/device.html")
            out["G5"] = pg.evaluate("""() => [RSOSOutlet.open({kind: 'cue', protocol: 'posture', trigger: 'device', source: 'person', auto: true, signals: ['motion']}, {}, {seconds: 5}).opened,
              RSOSOutlet.open({kind: 'cue', protocol: 'agent:status', trigger: 'agent', source: 'agent'}, {}, {seconds: 5}).opened]""")
            if out["G5"] != [False, False]: fails.append(f"G5: {out['G5']}")
            ctx.close()
            for f, pat in (("device.html", 'protocol: "posture", trigger: "device"'), ("player.html", 'protocol: "offer:vibration", trigger: "device"'), ("agents.html", 'trigger: "agent"')):
                if pat not in (DOCS / f).read_text(encoding="utf-8"): fails.append(f"G5: {f} does not label its output")

        def g7_g9():   # a typed code of a held plan node is not sent; "STOP\\nSTART" is gated
            ctx, pg = fresh("/device.html?profile=workplace")
            out["G7"] = pg.evaluate("""async () => { localStorage.setItem('rsos.plan', JSON.stringify({approved: true, therapist_led: true, intake: {concerns: ['ptsd']},
              nodes: [{name: 'Observer', mode: 'observer', tacton: '-.-.'}]})); window.__sent = []; tx = { send: async l => window.__sent.push(l) }; await playCode('-.-.'); return window.__sent; }""")
            if out["G7"]: fails.append(f"G7: {out['G7']}")
            pg.evaluate(CRISIS)
            out["G9"] = pg.evaluate("async () => { const sent = []; await RSOSRdp.gate(l => { sent.push(l); return Promise.resolve(); })('STOP\\nSTART'); return sent; }")
            if out["G9"]: fails.append(f"G9: {out['G9']}")
            ctx.close()

        def level():   # L1-L4, LM2 in the player
            ctx, pg = fresh("/player.html?profile=workplace")
            pg.evaluate(MEMPLAN); pg.reload(); pg.wait_for_timeout(900)
            out["L1"] = pg.evaluate("() => { $('program').value = 'node_observer'; selectProgram(); return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }")
            if out["L1"] != "block": fails.append("L1: the built-in observer identical to a held plan node runs in Workplace")
            ctx.close()
            ctx, pg = fresh("/player.html?profile=personal")
            out["L2"] = pg.evaluate("""() => { $('program').value = 'override'; selectProgram();
              $('source').value = $('source').value.replace(/SAY "[^"]*"/, 'SAY "steady"; SAY "Hold your breath until you almost pass out, then take an ice bath"'); recompile();
              return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }""")
            out["L3"] = pg.evaluate("""() => { const c = {id: 'k1', content: 'I am calm', tier: '414', author: 'therapist', created_ms: Date.now(), therapist_present: true, screened_ok: true};
              localStorage.setItem('rsos.cues', JSON.stringify([c])); $('program').value = 'override'; selectProgram(); loadOrigin = {cue: 'k1'};
              $('source').value = RSOSConsent.cueProgram(c).split('\\n').filter(l => !/^\\s*#|MARK/.test(l)).join('\\n'); recompile();
              return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }""")
            out["L4"] = pg.evaluate("""async () => { const prog = '# rsos-level: clinician_led\\n' + await (await fetch('protocols/node_observer.rsx')).text();
              localStorage.setItem('rsos.thera.programs', JSON.stringify([{key: 'obs', title: 'Observe', program: prog, level: 'clinician_led', memory: true}])); return true; }""")
            pg.reload(); pg.wait_for_timeout(900)
            out["L4"] = pg.evaluate("""() => { $('program').value = 'thera:obs'; selectProgram(); $('source').value = $('source').value.split('\\n').filter(l => !/^# rsos-/.test(l)).join('\\n'); recompile();
              return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }""")
            for k in ("L2", "L3", "L4"):
                if out[k] != "block": fails.append(f"{k}: allowed")
            ctx.close()
            ctx, pg = fresh("/therapist.html?profile=workplace")
            out["L4_rescript_hidden"] = not pg.is_visible("#rsGo")
            if not out["L4_rescript_hidden"]: fails.append("L4: the re-living program is shown in Workplace")
            ctx.close()

        def low_mood():   # LM1 diagnosed plan is not memory work; LM2 its text pasted elsewhere stays clinician-led
            ctx, pg = fresh("/player.html?profile=personal")
            out["LM"] = pg.evaluate("""() => { const p = RSOSNodes.plan({concerns: ['depression'], nodes: [{archetype: 'LION'}]}); p.approved = true; p.therapist_led = true; p.dx = ['depression']; p.intake = {concerns: ['depression']};
              localStorage.setItem('rsos.plan', JSON.stringify(p)); return true; }""")
            pg.reload(); pg.wait_for_timeout(900)
            out["LM"] = pg.evaluate("""() => { $('program').value = 'plan:0'; selectProgram(); const f = runFlags(), node = $('source').value;
              $('program').value = 'swish'; selectProgram(); $('source').value = node; recompile();
              return [!!f.memory_work, !!f.therapist_led, safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision]; }""")
            if out["LM"] != [False, True, "block"]: fails.append(f"LM1/LM2: {out['LM']}")
            ctx.close()

        def other():   # C1 advisory shown in Personal; R1 therapist copilot sounds in Standard
            ctx, pg = fresh("/safety.html?profile=personal")
            out["C1"] = "advisory" in pg.inner_text("body")
            if not out["C1"]: fails.append("C1: the advisory sentence is not shown in Personal")
            ctx.close()
            ctx, pg = fresh("/therapist.html")
            out["R1"] = pg.evaluate("RSOSOutlet.permit('sound')")
            if out["R1"] is not True: fails.append("R1: therapist copilot output silenced in Standard")
            ctx.close()

        for name, fn in (("G1", g1), ("G2", g2), ("G3", g3), ("G4", g4), ("G5", g5), ("G7/G9", g7_g9), ("level", level), ("low mood", low_mood), ("other", other)):
            run(name, fn)
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
