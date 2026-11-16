"""Review R5 (review/r5 branch): adversarial browser scenarios against docs/ served locally.
python3 -I review/r5/attacks.py <docs_dir> [chrome] [comma-separated scenario prefixes, e.g. A1,A4]
Spies are installed below the output gate (as in scripts/check_outlet.py), so __out lists only what passed the gate.
Needs Playwright, Chrome and node (plans are generated with docs/js/nodes.js)."""
import functools, http.server, json, os, socketserver, subprocess, sys, threading
from playwright.sync_api import sync_playwright
DOCS = sys.argv[1]; CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
SPIES = """(() => { window.__out = []; window.__hold = 0; window.addEventListener('rsos-outlet-hold', () => { window.__hold++; });
  Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', JSON.stringify(p), Date.now()]); return true; };
  SpeechSynthesis.prototype.speak = function (u) { window.__out.push(['speak', u.text, Date.now()]); };
  const st = AudioScheduledSourceNode.prototype.start; AudioScheduledSourceNode.prototype.start = function () { window.__out.push(['sound', 1, Date.now()]); return st.apply(this, arguments); };
})();"""
CRISIS = "() => { localStorage.setItem('rsos.safety', JSON.stringify({mode: 'CRISIS', history: [{from: 'NORMAL', to: 'CRISIS', why: 't', by: 't', at: 1}], last: null})); }"
PLANS = json.loads(subprocess.run(["node", "-e", """const N = require(process.argv[1]);
let d = N.plan({concerns: ['depression'], nodes: [{archetype: 'LION'}]}); d.approved = true; d.therapist_led = true; d.dx = ['depression']; d.intake = {concerns: ['depression']};
let p = N.plan({concerns: ['ptsd'], author: 'therapist', nodes: [{archetype: 'LION'}, {archetype: 'OBSERVER'}]}); p.approved = true; p.therapist_led = true; p.intake = {concerns: ['ptsd']};
process.stdout.write(JSON.stringify([d, p]));""", os.path.join(os.path.abspath(DOCS), "js", "nodes.js")], capture_output=True, text=True, check=True).stdout)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=DOCS)); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
R, errs = {}, []
def T(name):
    def deco(fn):
        if len(sys.argv) > 3 and not any(name.startswith(o) for o in sys.argv[3].split(',')): return fn
        try: R[name] = fn()
        except Exception as e: R[name] = "could not run: " + str(e)[:300]
        return fn
    return deco
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    def ctxpage(url, ctx=None):
        ctx = ctx or b.new_context(); ctx.add_init_script(SPIES); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(url + ": " + str(e)))
        pg.goto(base + url); pg.wait_for_timeout(900); return ctx, pg

    DXPLAN = "() => { localStorage.setItem('rsos.plan', JSON.stringify(%s)); return true; }" % json.dumps(PLANS[0])
    PTSDPLAN = "() => { localStorage.setItem('rsos.plan', JSON.stringify(%s)); return true; }" % json.dumps(PLANS[1])
    ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    @T("A1_dx_node_copied_with_trailing_comment_personal")
    def _():
        ctx, pg = ctxpage("/player.html?profile=personal"); pg.evaluate(DXPLAN); pg.reload(); pg.wait_for_timeout(900)
        r = pg.evaluate("""() => { $('program').value = 'plan:0'; selectProgram(); const held = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          const node = $('source').value;
          $('program').value = 'swish'; selectProgram(); $('source').value = node; recompile(); const exact = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          $('source').value = node.replace('VERSION 1.0', 'VERSION 1.0 # copy'); recompile(); const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'});
          $('source').value = node.replace(/\\n\\n/g, '\\n;\\n'); recompile(); const d2 = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          return {plan0: held, exact_copy_in_swish: d.decision && exact, trailing_comment: d.decision, level: d.watchdog.level, semicolons: d2, timeline_protocol: timeline.protocol}; }""")
        # really start it and count outputs
        pg.evaluate("() => { window.__out = []; $('optVib').checked = true; $('optVoice').checked = true; }")
        pg.click("#start"); pg.wait_for_timeout(400)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(6000)
        r["outputs_in_6s"] = pg.evaluate("window.__out.map(x => x[0] + ':' + String(x[1]).slice(0, 40))")[:8]
        ctx.close(); return r

    @T("A1b_ptsd_lion_node_copied_workplace")
    def _():
        ctx, pg = ctxpage("/player.html?profile=workplace"); pg.evaluate(PTSDPLAN); pg.reload(); pg.wait_for_timeout(900)
        return pg.evaluate("""() => { $('program').value = 'plan:0'; selectProgram(); const held = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'});
          const node = $('source').value; $('program').value = 'swish'; selectProgram(); $('source').value = node.replace('VERSION 1.0', 'VERSION 1.0 # x'); recompile();
          const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'});
          return {plan0: [held.decision, held.watchdog.reasons.map(x => x.rule)], copied_edited: [d.decision, d.watchdog.reasons.map(x => x.rule)]}; }""")

    @T("A2_cue_load_then_select_other_program")
    def _():
        ctx, pg = ctxpage("/player.html?profile=personal")
        pg.evaluate("""() => { const c = {id: 'k1', content: 'I let the old fear go', tier: '414', person: 'P', author: 'therapist', created_ms: Date.now() - 1000, therapist_present: true, screened_ok: true};
          localStorage.setItem('rsos.cues', JSON.stringify([c])); }""")
        pg.reload(); pg.wait_for_timeout(900)
        btn = pg.locator("button", has_text="Load into the player")
        n = btn.count()
        if not n: return "no Load button"
        btn.first.click(); pg.wait_for_timeout(200)
        return pg.evaluate("""() => { const loaded = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          const txt = $('source').value.split('\\n').filter(l => !/^\\s*#|MARK/.test(l)).join('\\n');
          const sameSlot = (() => { $('source').value = txt; recompile(); return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; })();
          $('program').value = 'swish'; $('program').dispatchEvent(new Event('change')); $('source').value = txt; recompile();
          const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'});
          return {loaded, edited_same_slot: sameSlot, after_selecting_swish_and_pasting: d.decision, level: d.watchdog.level, says_text: /old fear/.test(txt)}; }""")

    @T("A3_G2_real_run_domain_switch")
    def _():
        ctx = b.new_context()
        ctx, pg = ctxpage("/player.html?profile=personal", ctx); pg.evaluate(PTSDPLAN); pg.goto(base + "/player.html?profile=personal&program=plan:0"); pg.wait_for_timeout(1200)
        pg.evaluate("() => { $('optVib').checked = true; $('optVoice').checked = true; $('optTone').checked = true; }")
        pre = pg.evaluate("() => { const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}); return [d.decision, d.action.memory_work]; }")
        pg.click("#start"); pg.wait_for_timeout(300)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(1500)
        sess = pg.evaluate("() => { const s = RSOSOutlet.session(); return s && {a: s.action.memory_work, x_mwa: s.extra.memory_work_allowed, x_max: s.extra.max_level}; }")
        p2 = ctx.new_page(); p2.goto(base + "/safety.html?profile=workplace"); p2.wait_for_timeout(1000)
        pg.evaluate("() => { window.__out = []; }"); pg.wait_for_timeout(6000)
        r = {"pre": pre, "session": sess, "domain_now": pg.evaluate("RSOSDomain.profile + '/' + RSOSDomain.memory_work_allowed"),
             "run_still_running": pg.evaluate("!!run"), "hold_events": pg.evaluate("window.__hold"),
             "outputs_after_switch": pg.evaluate("window.__out.map(x => x[0] + ':' + String(x[1]).slice(0, 30))")[:8],
             "fresh_watch_now": pg.evaluate("() => RSOSWatchdog.watch(RSOSOutlet.session().action, {contain: null, safety: null, memory_work_allowed: RSOSDomain.memory_work_allowed, max_level: RSOSDomain.max_level}).decision")}
        ctx.close(); return r

    @T("A4_device_band_keeps_playing_after_refused_open")
    def _():
        ctx, pg = ctxpage("/device.html?profile=personal"); pg.evaluate(DXPLAN); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("() => { window.__sent = []; tx = { send: async l => { window.__sent.push(l); } }; $('run').disabled = false; $('prog').value = 'override'; }")
        pg.click("#run"); pg.wait_for_timeout(800)
        a = pg.evaluate("() => ({started: window.__sent.includes('START'), session: RSOSOutlet.session() && RSOSOutlet.session().action.protocol})")
        pg.evaluate("async () => { window.__sent = []; await playCode('..-'); }")   # the dx node's code: held
        bmsg = pg.evaluate("() => ({sent: window.__sent.slice(), session: RSOSOutlet.session(), msg: document.querySelector('#say, .say, [role=status]') ? document.querySelector('#say, .say, [role=status]').textContent : ''})")
        pg.evaluate("() => { window.__sent = []; window.__hold = 0; }"); pg.evaluate(CRISIS)
        pg.evaluate("() => window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'}))"); pg.wait_for_timeout(2500)
        r = {"run": a, "after_held_code": bmsg, "after_crisis_sent": pg.evaluate("window.__sent"), "hold_events": pg.evaluate("window.__hold")}
        ctx.close()
        # control: without the refused code, CRISIS sends STOP
        ctx, pg = ctxpage("/device.html?profile=personal")
        pg.evaluate("() => { window.__sent = []; tx = { send: async l => { window.__sent.push(l); } }; $('run').disabled = false; $('prog').value = 'override'; }")
        pg.click("#run"); pg.wait_for_timeout(800); pg.evaluate("() => { window.__sent = []; }"); pg.evaluate(CRISIS)
        pg.evaluate("() => window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'}))"); pg.wait_for_timeout(2500)
        r["control_after_crisis_sent"] = pg.evaluate("window.__sent"); ctx.close(); return r

    @T("A5_device_run_builtin_observer_with_held_plan")
    def _():
        out = {}
        for prof in ("workplace", "personal"):
            ctx, pg = ctxpage(f"/device.html?profile={prof}"); pg.evaluate(PTSDPLAN); pg.reload(); pg.wait_for_timeout(900)
            pg.evaluate("() => { window.__sent = []; tx = { send: async l => { window.__sent.push(l); } }; $('run').disabled = false; $('prog').value = 'node_observer'; }")
            pg.click("#run"); pg.wait_for_timeout(1000)
            # the plan's observer node code on this page, for comparison
            out[prof] = {"sent_START": pg.evaluate("window.__sent.includes('START')"), "lines": pg.evaluate("window.__sent.length"),
                         "player_equiv": None}
            ctx.close()
            ctx, pg = ctxpage(f"/player.html?profile={prof}"); pg.evaluate(PTSDPLAN); pg.reload(); pg.wait_for_timeout(900)
            out[prof]["player_builtin_observer"] = pg.evaluate("() => { $('program').value = 'node_observer'; selectProgram(); return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }")
            ctx.close()
        return out

    @T("A6_G1_refused_open_falls_back_to_declared_player")
    def _():
        ctx, pg = ctxpage("/player.html?profile=personal")
        return pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'run', protocol: 'override', trigger: 'self', source: 'person'}, {}, {seconds: 60});
          const c = RSOSContain.newState(); c.quarantine.override = {since: 1, reason: 't', signals: ['worse'], therapist: false}; localStorage.setItem('rsos.contain', JSON.stringify(c));
          const heldNow = RSOSOutlet.permit('vibration');
          const o = RSOSOutlet.open({kind: 'cue', protocol: 'offer:vibration', trigger: 'device', source: 'person', auto: true, signals: ['heart_rate']}, {}, {seconds: 5});
          const after = RSOSOutlet.permit('vibration'); return {held_run_permit: heldNow, refused_open: o.opened, session_after: RSOSOutlet.session() && RSOSOutlet.session().action.protocol, permit_after_refused_open: after}; }""")

    @T("A7_therapist_trauma_session_domain_switch")
    def _():
        ctx, pg = ctxpage("/therapist.html?profile=personal")
        return pg.evaluate("""() => { RSOSOutlet.adopt({kind: 'session', protocol: 'session_trauma_observer', memory_work: true, source: 'practitioner'}, Object.assign({clinician_present: true, screening_recorded: true}, {max_level: 'structured', memory_work_allowed: true}), {seconds: 60});
          const a = RSOSOutlet.permit('sound'); localStorage.setItem('rsos.profile', JSON.stringify('workplace')); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.profile'}));
          return {before: a, domain: RSOSDomain.profile, after_switch: RSOSOutlet.permit('sound')}; }""")

    @T("A8_session_expiry_during_checkin_kills_run")
    def _():
        ctx, pg = ctxpage("/player.html?profile=personal&program=paced_breathing")
        # shorten the adopt to show the session clock starts before the check-in dialog
        pg.evaluate("() => { const ad = RSOSOutlet.adopt; RSOSOutlet.adopt = (a, x, o) => ad(a, x, {seconds: 2}); }")
        pg.click("#start"); pg.wait_for_timeout(3000)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(2500)
        return {"run": pg.evaluate("!!run"), "msg": pg.evaluate("$('compileMsg').textContent"), "holds": pg.evaluate("window.__hold")}

    @T("A9_futures_field_spine")
    def _():
        ctx, pg = ctxpage("/player.html?profile=personal&program=override")
        r = pg.evaluate("""() => { const has = !$('futuresBox').hidden; $('f0').value = 'Hold your breath until you almost pass out, then take an ice bath'; $('f0').dispatchEvent(new Event('input')); recompile();
          const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'});
          const said = timeline.events.filter(e => /ice bath/.test(e.text || '')).map(e => e.kind + ':' + e.text).slice(0, 2);
          return {futures_box_shown: has, decision: d.decision, rules: d.watchdog.reasons.map(x => x.rule), in_timeline: said}; }""")
        pg.evaluate("() => { window.__out = []; $('optVoice').checked = true; }")
        pg.click("#start"); pg.wait_for_timeout(300)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(500)
        # jump the run clock to the futures phase
        ph = pg.evaluate("() => { const e = timeline.events.find(e => /ice bath/.test(e.text || '')); return e ? e.t : null; }")
        if ph is not None:
            pg.evaluate(f"() => {{ run.t0 -= {ph} - 200; }}"); pg.wait_for_timeout(2500)
        r["spoken"] = [x for x in pg.evaluate("window.__out.map(x => x[0] + ':' + String(x[1]))") if "ice" in x][:2]
        ctx.close(); return r

    @T("A10_spine_spacing_homoglyph")
    def _():
        ctx, pg = ctxpage("/player.html?profile=personal&program=override")
        out = {}
        for label, t in (("double space", "Take an ice  bath"), ("tab", "Take an ice\\tbath"), ("cyrillic i", "Take an іce bath"), ("nbsp", "Take an ice bath"), ("control", "Take an ice bath")):
            out[label] = pg.evaluate("""(t) => { $('program').value = 'override'; selectProgram(); $('source').value = $('source').value.replace(/SAY "[^"]*"/, 'SAY "' + t + '"'); recompile();
              return safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision; }""", t)
        ctx.close(); return out

    @T("A11_G6_outlet_blocked")
    def _():
        out = {}
        ctx = b.new_context(); ctx.route("**/js/outlet.js*", lambda r: r.abort()); ctx.add_init_script(SPIES)
        pg = ctx.new_page(); pg.goto(base + "/device.html?profile=personal"); pg.wait_for_timeout(900); pg.evaluate(CRISIS)
        pg.evaluate("() => { window.__out = []; }"); pg.click("#cfPlay"); pg.wait_for_timeout(300)
        out["device_carrier_in_crisis"] = pg.evaluate("window.__out.map(x => x[0])"); pg.close()
        pg = ctx.new_page(); pg.goto(base + "/glyphs.html?profile=personal"); pg.wait_for_timeout(900); pg.evaluate(CRISIS)
        pg.evaluate("() => { window.__out = []; }")
        try:
            pg.evaluate("() => { const g = window.current || (typeof current !== 'undefined' ? current : null); if (g) { play(g); g.tacton ? null : navigator.vibrate(UGCL.hapticSignature(g).flat()); } }")
        except Exception as e:
            out["glyph_err"] = str(e)[:120]
        pg.wait_for_timeout(300)
        out["glyphs_in_crisis"] = pg.evaluate("window.__out.map(x => x[0])"); pg.close()
        pg = ctx.new_page(); pg.goto(base + "/glyphs.html?profile=personal"); pg.wait_for_timeout(900); pg.evaluate(CRISIS)
        pg.evaluate("() => { window.__out = []; }"); pg.evaluate("() => UGCL.feel('..-', {})"); pg.wait_for_timeout(300)
        out["ugcl_feel_in_crisis_control"] = pg.evaluate("window.__out.map(x => x[0])")
        ctx.close(); return out

    @T("A12_wording")
    def _():
        out = {}
        ctx = b.new_context(); ctx.add_init_script(SPIES)
        for prof in ("personal", "coaching", "performance", "learning", "research", "workplace", "clinical"):
            pg = ctx.new_page(); pg.goto(base + f"/safety.html?profile={prof}"); pg.wait_for_timeout(600)
            t = pg.inner_text("body"); out[prof] = {"advisory": "advisory" in t}
            pg.close()
        pg = ctx.new_page(); pg.goto(base + "/night.html?profile=workplace"); pg.wait_for_timeout(600); t = pg.inner_text("body")
        out["night_workplace_nightmare"] = "nightmare" in t.lower() or "painful memory" in t.lower(); pg.close()
        pg = ctx.new_page(); pg.goto(base + "/therapist.html?profile=workplace"); pg.wait_for_timeout(600); t = pg.inner_text("body")
        out["therapist_workplace_reliving"] = "re-living" in t.lower() or "reliving" in t.lower(); pg.close()
        # escalation message in Performance with a low-mood plan and 3 days
        pg = ctx.new_page(); pg.goto(base + "/safety.html?profile=performance"); pg.wait_for_timeout(600)
        pg.evaluate("() => { const d = 86400000, n = Date.now(); localStorage.setItem('rsos.plan', JSON.stringify({approved: true, nodes: [], intake: {concerns: ['depression']}})); localStorage.setItem('rsos.selfchecks', JSON.stringify([{at: n - 2*d, intensity: 8, sleep_h: null}, {at: n - d, intensity: 8, sleep_h: null}])); }")
        pg.reload(); pg.wait_for_timeout(600); pg.select_option("#sfInt", "8"); pg.click("#sfSave"); pg.wait_for_timeout(300)
        out["perf_escalation_msg"] = pg.inner_text("#sfMsgs")[:300]; pg.close()
        ctx.close(); return out

    @T("A13_observer_nbsp_regression")
    def _():
        ctx, pg = ctxpage("/player.html?profile=workplace"); pg.evaluate(PTSDPLAN); pg.reload(); pg.wait_for_timeout(900)
        r = pg.evaluate("""() => { const res = {};
          $('program').value = 'plan:1'; selectProgram(); const node = $('source').value; res.plan_observer = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          $('program').value = 'node_observer'; selectProgram();
          $('source').value = node.replace('VERSION 1.0', 'VERSION 1.0 # x'); recompile(); res.copy_ascii_space = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          $('source').value = node.replace('MODE "observer"', 'MODE\\u00a0"observer"'); recompile();
          res.copy_nbsp = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}).decision;
          res.compiled_mode = (timeline.events.find(e => e.kind === 'tier') || {}).mode; return res; }""")
        ctx.close(); return r

    @T("A14_device_code_variants_dx")
    def _():
        ctx, pg = ctxpage("/device.html?profile=personal"); pg.evaluate(DXPLAN); pg.reload(); pg.wait_for_timeout(900)
        r = pg.evaluate("""async () => { const res = {}; window.tx = undefined; tx = { send: async l => { window.__sent.push(l); } };
          for (const c of ['..-', '..- ..-', '..- -']) { window.__sent = []; await playCode(c); res[c] = window.__sent.includes('START'); }
          window.__sent = []; const btn = Array.from(document.querySelectorAll('#codes button')).find(b => b.textContent.endsWith('Lion + Dragon')); btn.click(); await new Promise(r => setTimeout(r, 300));
          res['button Lion + Dragon'] = window.__sent.includes('START'); res.buttons = Array.from(document.querySelectorAll('#codes button')).map(b => b.textContent); return res; }""")
        ctx.close(); return r

    b.close()
srv.shutdown()
print(json.dumps({"results": R, "page_errors": errs}, indent=1, ensure_ascii=False))
