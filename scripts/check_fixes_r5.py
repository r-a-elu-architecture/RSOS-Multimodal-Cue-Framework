"""Browser acceptance for spec/FIXES_R5.md (Q1): the fifth reviewer's scenarios (review/r5/attacks.py), driven through the
real page paths (Start and Begin, the cue's Load button, the program menu, the device page's Play and code buttons, a
second tab), each with its expected outcome. Spies sit below the output gate, so they see only what passed it.
python3 scripts/check_fixes_r5.py [docs_dir] [chrome_path]      Needs Playwright, Chrome and node.
"""
import functools
import http.server
import json
import os
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
  const st = AudioScheduledSourceNode.prototype.start; AudioScheduledSourceNode.prototype.start = function () { window.__out.push(['sound', 1]); return st.apply(this, arguments); };
})();"""
CRISIS = """() => { localStorage.setItem('rsos.safety', JSON.stringify({mode: 'CRISIS', history: [{from: 'NORMAL', to: 'CRISIS', why: 't', by: 't', at: 1}], last: null}));
  window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'})); }"""
PLANS = json.loads(subprocess.run(["node", "-e", """const N = require(process.argv[1]);
let d = N.plan({concerns: ['depression'], nodes: [{archetype: 'LION'}]}); d.approved = true; d.therapist_led = true; d.dx = ['depression']; d.intake = {concerns: ['depression']};
let p = N.plan({concerns: ['ptsd'], author: 'therapist', nodes: [{archetype: 'LION'}, {archetype: 'OBSERVER'}]}); p.approved = true; p.therapist_led = true; p.intake = {concerns: ['ptsd']};
process.stdout.write(JSON.stringify([d, p]));""", str(DOCS / "js" / "nodes.js")], capture_output=True, text=True, check=True).stdout)
DECIDE = "safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'})"


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
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])

        def page(url, plan=None, ctx=None):
            ctx = ctx or b.new_context(); ctx.add_init_script(SPIES); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(url + ": " + str(e)))
            pg.goto(base + url.split("?")[0] + "?profile=personal")
            if plan is not None:
                pg.evaluate("p => localStorage.setItem('rsos.plan', JSON.stringify(p))", plan)
            pg.goto(base + url); pg.wait_for_timeout(1000); return ctx, pg

        def start_run(pg):   # the real path: Start, then Begin in the check-in dialog
            pg.click("#start"); pg.wait_for_selector("#checkinGo", state="visible", timeout=5000); pg.click("#checkinGo"); pg.wait_for_timeout(400)

        def run(name, fn):
            try:
                fn()
            except Exception as e:
                fails.append(f"{name}: could not run ({str(e)[:160]})")

        def r1():   # R5-1: a real memory-work run stops when another tab switches to Workplace
            ctx, pg = page("/player.html?profile=personal&program=plan:0", PLANS[1])
            pg.evaluate("() => { $('optVib').checked = true; $('optVoice').checked = true; }")
            start_run(pg)
            running = pg.evaluate("!!run")
            p2 = ctx.new_page(); p2.goto(base + "/safety.html?profile=workplace"); p2.wait_for_timeout(1500)
            pg.evaluate("() => { window.__out = []; }"); pg.wait_for_timeout(3000)
            expect("R5-1 real run stops on a domain switch", [running, pg.evaluate("!!run"), pg.evaluate("window.__hold") > 0, pg.evaluate("window.__out.filter(x => x[0] !== 'vibrate' || x[1] !== '0').length")], [True, False, True, 0])
            ctx.close()
            ctx, pg = page("/therapist.html?profile=personal")
            got = pg.evaluate("""() => { const h = RSOSOutlet.adopt({kind: 'session', protocol: 'session_trauma_observer', memory_work: true, source: 'practitioner'},
                {clinician_present: true, screening_recorded: true, max_level: 'structured', memory_work_allowed: true}, {seconds: 60});
              const a = RSOSOutlet.permit('sound'); localStorage.setItem('rsos.profile', JSON.stringify('workplace')); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.profile'}));
              return [a, RSOSOutlet.permit('sound')]; }""")
            expect("R5-1 therapist session stops on a domain switch", got, [True, False])
            ctx.close()

        def r2():   # R5-2: a refused code or offer keeps the run's session; CRISIS then sends STOP
            ctx, pg = page("/device.html?profile=personal", PLANS[0])
            pg.evaluate("() => { window.__sent = []; tx = { send: async l => { window.__sent.push(l); } }; $('run').disabled = false; $('prog').value = 'override'; }")
            pg.click("#run"); pg.wait_for_timeout(900)
            started = pg.evaluate("window.__sent.includes('START')")
            pg.evaluate("async () => { window.__sent = []; await playCode('..-'); }")
            held_code = pg.evaluate("window.__sent.slice()")
            pg.evaluate("() => { window.__sent = []; }"); pg.evaluate(CRISIS); pg.wait_for_timeout(1500)
            expect("R5-2 band gets STOP after a refused code", [started, held_code, "STOP" in pg.evaluate("window.__sent")], [True, [], True])
            ctx.close()
            ctx, pg = page("/player.html?profile=personal")
            got = pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'run', protocol: 'override', trigger: 'self', source: 'person'}, {}, {seconds: 60});
              const c = RSOSContain.newState(); c.quarantine.override = {since: 1, reason: 't', signals: ['worse'], therapist: false}; localStorage.setItem('rsos.contain', JSON.stringify(c));
              const a = RSOSOutlet.permit('vibration');
              const o = RSOSOutlet.open({kind: 'cue', protocol: 'offer:vibration', trigger: 'device', source: 'person', auto: true, signals: ['heart_rate']}, {}, {seconds: 5});
              return [a, o.opened, RSOSOutlet.permit('vibration'), RSOSOutlet.sessions().length]; }""")
            expect("R5-2 refused offer keeps the held run", got, [False, False, False, 1])
            ctx.close()

        def r3():   # R5-3: copies of held plan nodes with no-op edits stay held
            ctx, pg = page("/player.html?profile=personal", PLANS[0])
            got = pg.evaluate("""() => { const sel = v => { $('program').value = v; $('program').dispatchEvent(new Event('change')); };
              sel('plan:0'); const node = $('source').value, res = [""" + DECIDE + """.decision];
              for (const t of [node, node.replace('VERSION 1.0', 'VERSION 1.0 # copy'), node.replace(/\\n\\n/g, '\\n;\\n'), node + '\\nPHASE extra dur=2s {\\n  SAY "My own line"\\n}\\n']) {
                sel('swish'); $('source').value = t; $('source').dispatchEvent(new Event('input')); recompile(); res.push(""" + DECIDE + """.decision); }
              return res; }""")
            expect("R5-3 diagnosed-plan node copies (Personal)", got, ["block"] * 5)
            pg.evaluate("() => { window.__out = []; $('optVib').checked = true; $('optVoice').checked = true; }")
            pg.click("#start"); pg.wait_for_timeout(1500)
            expect("R5-3 nothing plays from the copy", pg.evaluate("[!!run, window.__out.length]"), [False, 0])
            ctx.close()
            ctx, pg = page("/player.html?profile=workplace", PLANS[1])
            got = pg.evaluate("""() => { const sel = v => { $('program').value = v; $('program').dispatchEvent(new Event('change')); };
              sel('plan:0'); const node = $('source').value; sel('swish'); $('source').value = node.replace('VERSION 1.0', 'VERSION 1.0 # x'); recompile();
              const d = """ + DECIDE + """; return [d.decision, d.watchdog.reasons.map(x => x.rule).includes('memory')]; }""")
            expect("R5-3 memory-work node copy (Workplace)", got, ["block", True])
            ctx.close()

        def r4():   # R5-4: a cue's text keeps its level after another program is chosen
            ctx, pg = page("/player.html?profile=personal")
            pg.evaluate("""() => localStorage.setItem('rsos.cues', JSON.stringify([{id: 'k1', content: 'I let the old fear go', tier: '414', person: 'P', author: 'therapist',
              created_ms: Date.now() - 1000, therapist_present: true, screened_ok: true}]))""")
            pg.reload(); pg.wait_for_timeout(1000)
            pg.locator("button", has_text="Load into the player").first.click(); pg.wait_for_timeout(200)
            got = pg.evaluate("""() => { const res = [""" + DECIDE + """.decision];
              const txt = $('source').value.split('\\n').filter(l => !/^\\s*#|MARK/.test(l)).join('\\n');
              $('program').value = 'swish'; $('program').dispatchEvent(new Event('change')); $('source').value = txt; recompile(); res.push(""" + DECIDE + """.decision);
              $('source').value = 'PROTOCOL mine "Mine"\\nPHASE a dur=3s {\\n  SAY "Today I let the old fear go, slowly"\\n}\\n'; recompile(); res.push(""" + DECIDE + """.decision);
              return res; }""")
            expect("R5-4 cue text after choosing another program", got, ["block", "block", "block"])
            ctx.close()

        def r5():   # R5-5: Unicode spaces before "observer"
            ctx, pg = page("/player.html?profile=workplace", PLANS[1])
            got = pg.evaluate("""() => { const sel = v => { $('program').value = v; $('program').dispatchEvent(new Event('change')); }; const res = {};
              sel('plan:1'); const node = $('source').value; sel('node_observer');
              for (const [k, sp] of [['nbsp', '\\u00a0'], ['vt', '\\u000b'], ['em', '\\u2003'], ['ideo', '\\u3000']]) {
                $('source').value = node.replace('MODE "observer"', 'MODE' + sp + '"observer"').replace('VERSION 1.0', 'VERSION 1.0 # ' + k); recompile();
                res[k] = """ + DECIDE + """.decision; }
              return Object.values(res); }""")
            expect("R5-5 observer mode with Unicode spaces (Workplace)", got, ["block"] * 4)
            ctx.close()

        def r6():   # R5-6: the futures fields go through the Spine check
            ctx, pg = page("/player.html?profile=personal&program=override")
            got = pg.evaluate("""() => { $('f0').value = 'Hold your breath until you almost pass out, then take an ice bath'; $('f0').dispatchEvent(new Event('input')); recompile();
              const d = """ + DECIDE + """; return [d.decision, d.watchdog.reasons.map(x => x.rule).filter(r => r.startsWith('spine')).length > 0]; }""")
            expect("R5-6 futures field wording", got, ["block", True])
            ctx.close()

        def r7():   # R5-7: Play on the band follows the same content rules as the player
            for prof in ("workplace", "personal"):
                ctx, pg = page(f"/device.html?profile={prof}", PLANS[1])
                pg.evaluate("() => { window.__sent = []; tx = { send: async l => { window.__sent.push(l); } }; $('run').disabled = false; $('prog').value = 'node_observer'; }")
                pg.click("#run"); pg.wait_for_timeout(1000)
                expect(f"R5-7 built-in observer with a held plan on the band ({prof})", pg.evaluate("window.__sent.includes('START')"), False)
                ctx.close()
            ctx, pg = page("/device.html?profile=personal")
            pg.evaluate("() => { window.__sent = []; tx = { send: async l => { window.__sent.push(l); } }; $('run').disabled = false; $('prog').value = 'node_observer'; }")
            pg.click("#run"); pg.wait_for_timeout(1000)
            expect("R5-7 built-in observer with no plan plays", pg.evaluate("window.__sent.includes('START')"), True)
            ctx.close()

        def r11():   # R5-11: code variants and buttons with a diagnosed plan's code
            ctx, pg = page("/device.html?profile=personal", PLANS[0])
            got = pg.evaluate("""async () => { const res = []; tx = { send: async l => { window.__sent.push(l); } };
              for (const c of ['..-', '..- ..-', '..- -']) { window.__sent = []; await playCode(c); res.push(window.__sent.includes('START')); }
              window.__sent = []; Array.from(document.querySelectorAll('#codes button')).find(b => b.textContent.endsWith('Lion + Dragon')).click();
              await new Promise(r => setTimeout(r, 300)); res.push(window.__sent.includes('START'));
              window.__sent = []; await playCode('---'); res.push(window.__sent.includes('START')); return res; }""")
            expect("R5-11 held code in any form; other codes play", got, [False, False, False, False, True])
            ctx.close()

        def r12():   # R5-12: no gate, no sound
            ctx = b.new_context(); ctx.route("**/js/outlet.js*", lambda r: r.abort()); ctx.add_init_script(SPIES)
            pg = ctx.new_page(); pg.goto(base + "/device.html?profile=personal"); pg.wait_for_timeout(900)
            pg.evaluate("() => { window.__out = []; }"); pg.click("#cfPlay"); pg.wait_for_timeout(300)
            dev = pg.evaluate("window.__out.length"); pg.close()
            pg = ctx.new_page(); pg.goto(base + "/glyphs.html?profile=personal"); pg.wait_for_timeout(900)
            pg.evaluate("() => { window.__out = []; if (typeof current !== 'undefined' && current) play(current); }"); pg.wait_for_timeout(300)
            expect("R5-12 direct sound without the gate", [dev, pg.evaluate("window.__out.length")], [0, 0])
            ctx.close()

        def r15_r8():   # R5-15 wording in Workplace; R5-8 the registered count
            ctx = b.new_context(); ctx.add_init_script(SPIES)
            pg = ctx.new_page(); pg.goto(base + "/night.html?profile=workplace"); pg.wait_for_timeout(700); n = pg.inner_text("body").lower()
            pg.goto(base + "/therapist.html?profile=workplace"); pg.wait_for_timeout(700); t = pg.inner_text("body").lower()
            expect("R5-15 Workplace wording", ["nightmare" in n, "re-living" in t], [False, False])
            pg.goto(base + "/safety.html?profile=performance"); pg.wait_for_timeout(500)
            pg.evaluate("() => { localStorage.setItem('rsos.plan', JSON.stringify({approved: true, nodes: [], intake: {concerns: ['depression']}})); localStorage.setItem('rsos.selfchecks', '[]'); }")
            pg.reload(); pg.wait_for_timeout(500)
            for _ in range(3):
                pg.select_option("#sfInt", "8"); pg.click("#sfSave"); pg.wait_for_timeout(100)
            msg = pg.inner_text("#sfMsgs")
            expect("R5-8 three high checks on one day recommend a practitioner", ["practitioner" in msg, "several times" in msg], [True, True])
            ctx.close()

        def r16_r17():   # R5-16 the session opens after the check-in; R5-17 copies
            ctx, pg = page("/player.html?profile=personal&program=paced_breathing")
            pg.click("#start"); pg.wait_for_selector("#checkinGo", state="visible", timeout=5000)
            before = pg.evaluate("RSOSOutlet.sessions().length"); pg.wait_for_timeout(1500); pg.click("#checkinGo"); pg.wait_for_timeout(500)
            got = [before, pg.evaluate("!!run"), pg.evaluate("RSOSOutlet.sessions().length")]
            got.append(pg.evaluate("() => { const s = RSOSOutlet.session(); try { s.held = true; } catch (e) {} return RSOSOutlet.session().held; }"))
            expect("R5-16/17 session after check-in; copies only", got, [0, True, 1, False])
            ctx.close()

        def builtins():   # Q3: built-in programs run as before with no plan saved
            ctx, pg = page("/player.html?profile=personal")
            got = pg.evaluate("""() => PROTOCOLS.map(p => { $('program').value = p; selectProgram(); return [p, """ + DECIDE + """.decision]; }).filter(x => x[1] !== 'allow')""")
            expect("Q3 built-ins allowed in Personal with no plan", got, [])
            ctx.close()

        for name, fn in (("R5-1", r1), ("R5-2", r2), ("R5-3", r3), ("R5-4", r4), ("R5-5", r5), ("R5-6", r6), ("R5-7", r7), ("R5-11", r11), ("R5-12", r12),
                         ("R5-15/R5-8", r15_r8), ("R5-16/17", r16_r17), ("Q3", builtins)):
            run(name, fn)
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
