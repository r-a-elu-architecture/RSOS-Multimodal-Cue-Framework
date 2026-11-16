"""Review R6 (review/r6 branch): adversarial browser scenarios against docs/ served locally, through the real page paths
(program menu, editor typing, Start and Begin, the device page's buttons).
python3 -I review/r6/attacks.py <docs_dir> [chrome] [comma-separated scenario prefixes, e.g. C1,C3]
Spies are installed below the output gate (as in scripts/check_outlet.py and review/r5/attacks.py), so __out lists only
what passed the gate. The device page's transport is a fake that applies the same START gate as docs/js/rdp.js:28.
Needs Playwright, Chrome and node (plans come from docs/js/nodes.js through review/r6/plans.js)."""
import functools, http.server, json, os, socketserver, subprocess, sys, threading
from playwright.sync_api import sync_playwright
DOCS = os.path.abspath(sys.argv[1]); CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__))
SPIES = """(() => { window.__out = []; window.__hold = 0; window.addEventListener('rsos-outlet-hold', () => { window.__hold++; });
  Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', JSON.stringify(p), Date.now()]); return true; };
  SpeechSynthesis.prototype.speak = function (u) { window.__out.push(['speak', u.text, Date.now()]); };
  const st = AudioScheduledSourceNode.prototype.start; AudioScheduledSourceNode.prototype.start = function () { window.__out.push(['sound', 1, Date.now()]); return st.apply(this, arguments); };
})();"""
# the same START gate as rdp.js:28, on a fake transport
FAKETX = """() => { window.__sent = []; tx = { kind: 'fake', send: async l => { if (/^\\s*START\\b/im.test(String(l)) && !(window.RSOSOutlet && RSOSOutlet.permit('wristband'))) return; window.__sent.push(l); } };
  for (const id of ['stop', 'check', 'play', 'run']) $(id).disabled = false; }"""
STATE = "(m) => { localStorage.setItem('rsos.safety', JSON.stringify({mode: m, history: [{from: 'NORMAL', to: m, why: 't', by: 't', at: 1}], last: null})); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'})); }"
PLANS = json.loads(subprocess.run(["node", os.path.join(HERE, "plans.js"), os.path.join(DOCS, "js", "nodes.js")], capture_output=True, text=True, check=True).stdout)
SETPLAN = "(p) => { localStorage.setItem('rsos.plan', JSON.stringify(p)); }"

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=DOCS)); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
R, errs = {}, []

def T(name):
    def deco(fn):
        if ONLY and not any(name.startswith(o) for o in ONLY): return fn
        try: R[name] = fn()
        except Exception as e: R[name] = "could not run: " + str(e)[:400]
        return fn
    return deco

def outs(pg, n=12):
    return pg.evaluate("window.__out.map(x => x[0] + ':' + String(x[1]).slice(0, 60))")[:n]

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    def page(url, plan=None, ctx=None, route=None):
        ctx = ctx or b.new_context(); ctx.add_init_script(SPIES)
        if route: ctx.route(route[0], route[1])
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(url + ": " + str(e)))
        pg.goto(base + url); pg.wait_for_timeout(600)
        if plan is not None:
            pg.evaluate(SETPLAN, plan); pg.reload(); pg.wait_for_timeout(900)
        return ctx, pg
    def begin(pg):
        """Start and Begin, as a person clicks them."""
        pg.evaluate("() => { $('optVib').checked = true; $('optVoice').checked = true; }")
        pg.click("#start"); pg.wait_for_timeout(500)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(300)
        return pg.evaluate("() => ({running: !!run, msg: $('compileMsg').textContent.slice(0, 160)})")
    def typed(pg, text):
        """Type into the editor (fill fires the input event; the page recompiles after 250 ms)."""
        pg.fill("#source", text); pg.wait_for_timeout(500)
    def node_src(pg, i):
        return pg.evaluate("(i) => { $('program').value = 'plan:' + i; $('program').dispatchEvent(new Event('change')); return $('source').value; }", i)
    def decide(pg):
        return pg.evaluate("() => { const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}); return [d.decision, d.watchdog.level, d.watchdog.reasons.map(r => r.rule), RSOSLineage.flags(effectiveSource(), {}).from]; }")

    # ---------------------------------------------------------------- C1: the program changes under a running session
    @T("C1a_midrun_menu_switch_to_held_dx_node_personal")
    def _():
        ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
        held = (node_src(pg, 0), decide(pg))[1]
        pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
        allowed = decide(pg); st = begin(pg)
        pg.evaluate("() => { window.__out = []; }")
        pg.select_option("#program", "plan:0")            # the menu, during the run
        pg.wait_for_timeout(12000)
        r = {"plan0_alone": held, "ssit_calm": allowed, "started": st, "still_running": pg.evaluate("!!run"),
             "timeline_now": pg.evaluate("timeline.protocol"), "hold_events": pg.evaluate("window.__hold"),
             "session_action": pg.evaluate("RSOSOutlet.sessions().map(s => s.action.protocol + (s.held ? ' held' : ''))"),
             "outputs_after_switch": outs(pg, 14)}
        ctx.close(); return r

    @T("C1b_midrun_typing_observer_node_workplace")
    def _():
        ctx, pg = page("/player.html?profile=workplace", PLANS["ptsd"])
        obs = node_src(pg, 1); held = decide(pg)
        pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
        st = begin(pg); pg.evaluate("() => { window.__out = []; }")
        typed(pg, obs)                                      # the editor, during the run
        pg.wait_for_timeout(9000)
        r = {"plan1_alone": held, "started": st, "still_running": pg.evaluate("!!run"), "timeline_now": pg.evaluate("timeline.protocol"),
             "mode_now": pg.evaluate("(timeline.events.find(e => e.kind === 'tier') || {}).mode"), "hold_events": pg.evaluate("window.__hold"),
             "outputs_after_typing": outs(pg, 14)}
        ctx.close(); return r

    @T("C1c_midrun_menu_switch_in_crisis_control")
    def _():
        # control: CRISIS set during the run is caught (the session state is re-read), unlike C1a/C1b
        ctx, pg = page("/player.html?profile=personal")
        pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300); st = begin(pg)
        pg.evaluate(STATE, "CRISIS"); pg.wait_for_timeout(1500)
        r = {"started": st, "still_running": pg.evaluate("!!run"), "hold_events": pg.evaluate("window.__hold")}
        ctx.close(); return r

    # ---------------------------------------------------------------- C2: a superset of the held node (Jaccard)
    @T("C2_superset_of_dx_lion_node_personal")
    def _():
        ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
        node = node_src(pg, 0); r = {"plan0": decide(pg)}
        pg.select_option("#program", "ssit_calm"); pg.wait_for_timeout(300)
        typed(pg, node); r["exact_copy"] = decide(pg)
        # the node's only distinctive element (the planner's default K text) reworded; everything else kept, own lines added
        node = node.replace("warmth in the belly", "warmth in the chest")
        steps = {}
        for k in range(0, 9):
            extra = "".join('PHASE mine%d {\n  SAY "My own line number %d"\n}\n' % (i, i) for i in range(k))
            typed(pg, node + extra); steps[k] = decide(pg)
            if steps[k][0] == "allow": break
        r["appended_own_lines"] = steps
        r["run"] = begin(pg); pg.wait_for_timeout(9000)
        r["outputs"] = outs(pg, 16)
        r["node_frame_spoken"] = pg.evaluate("window.__out.some(x => x[0] === 'speak' && /hold my ground/.test(x[1]))")
        ctx.close(); return r

    @T("C2b_superset_of_ptsd_observer_node_workplace")
    def _():
        ctx, pg = page("/player.html?profile=workplace", PLANS["ptsd"])
        node = node_src(pg, 1); r = {"plan1": decide(pg)}
        pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
        steps = {}
        for k in range(0, 9):
            extra = "".join('PHASE mine%d {\n  SAY "My own line number %d"\n}\n' % (i, i) for i in range(k))
            typed(pg, node + extra); steps[k] = decide(pg)
            if steps[k][0] == "allow": break
        r["appended_own_lines"] = steps
        ctx.close(); return r

    # ---------------------------------------------------------------- C3: the person's own node, small spelling changes
    @T("C3_own_dx_node_accents_and_unlisted_lookalikes")
    def _():
        ctx, pg = page("/player.html?profile=personal", PLANS["dxOwn"])
        node = node_src(pg, 0); r = {"plan0": decide(pg)}
        pg.fill("#f0", "At my d\u0119sk"); pg.wait_for_timeout(400)   # the futures field as typed (it replaces the FUTURES line)
        pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
        typed(pg, node); r["exact_copy"] = decide(pg)
        # same words: one accent per distinctive text, Latin alpha (U+0251) and Armenian o (U+0585) are not in the fold list,
        # the tier renamed and its code changed
        v = (node.replace("I am steady and I choose my next step", "I am stéady and I choose my next stép")
                 .replace("A warm blue lake", "A wɑrm blue lake").replace("At my desk", "At my dеsk")
                 .replace("Spine straight, warmth in the belly", "Spine straïght, warmth in the belly")
                 .replace("Hold the anchor in you as you enter", "Hold the anchօr in you as you enter")
                 .replace("ANCHOR", "ANKER").replace('TACTON "."', 'TACTON ".."'))
        typed(pg, v); r["accents_lookalikes_renamed_tier"] = decide(pg)
        typed(pg, v.replace("I am stéady and I choose my next stép", "I am steady and I choose my next step")); r["control_frame_restored"] = decide(pg)
        typed(pg, v); r["run"] = begin(pg); pg.wait_for_timeout(9000); r["outputs"] = outs(pg, 12)
        ctx.close(); return r

    # ---------------------------------------------------------------- C4: one sentence split over two events
    @T("C4_own_dx_node_split_sentences")
    def _():
        ctx, pg = page("/player.html?profile=personal", PLANS["dxOwn"])
        node = node_src(pg, 0)
        pg.fill("#f0", "At my"); pg.fill("#f1", "desk"); pg.wait_for_timeout(400)   # the futures fields, as typed
        pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
        v = (node.replace('  SAY "I am steady and I choose my next step"', '  SAY "I am steady and"\n  SAY "I choose my next step"')
                 .replace('  A "I am steady and I choose my next step"', '  A "I am steady"')
                 .replace('  FRAME "I am steady and I choose my next step"', '  FRAME "I choose"')
                 .replace('  V "A warm blue lake"', '  V "A warm"').replace('SEE "A warm blue lake"', 'SEE "A warm"\n  SEE "blue lake"')
                 .replace('FUTURES "At my desk"', 'FUTURES "At my" | "desk"')
                 .replace('"Spine straight, warmth in the belly"', '"Spine straight,"')
                 .replace('FEEL "Hold the anchor in you as you enter"', 'FEEL "Hold the anchor"\n  FEEL "in you as you enter"')
                 .replace("ANCHOR", "ANKER").replace('TACTON "."', 'TACTON ".."'))
        typed(pg, v); r = {"split": decide(pg)}
        r["run"] = begin(pg); pg.wait_for_timeout(8000); r["outputs"] = outs(pg, 12)
        ctx.close(); return r

    @T("C5_future_placeholder_hides_text_from_lineage")
    def _():
        ctx, pg = page("/player.html?profile=personal", PLANS["dxOwn"])
        node = node_src(pg, 0)
        pg.fill("#f0", "$future"); pg.fill("#f1", ""); pg.fill("#f2", ""); pg.wait_for_timeout(400)   # the futures fields, as typed
        pg.select_option("#program", "swish"); pg.wait_for_timeout(300)
        # every distinctive text moved inside FOR FUTURE with a future whose text is the placeholder itself
        v = (node.replace('FUTURES "At my desk"', 'FUTURES "$future"')
                 .replace('PHASE frame1 breath=exhale {\n  SAY "I am steady and I choose my next step"\n}',
                          'PHASE frame1 breath=exhale {\n  FOR FUTURE {\n    SAY "I am steady and I choose my next step $future"\n    SEE "A warm blue lake $future"\n  }\n}')
                 .replace('  SEE "A warm blue lake"\n', '').replace('  V "A warm blue lake"\n', '  V "Blue"\n').replace('  A "I am steady and I choose my next step"\n', '  A "Hum"\n')
                 .replace('  FRAME "I am steady and I choose my next step"\n', '').replace('  K "Spine straight, warmth in the belly"\n', '  K "Calm"\n')
                 .replace('  FEEL "Hold the anchor in you as you enter"\n', '').replace("ANCHOR", "ANKER").replace('TACTON "."', 'TACTON ".."'))
        typed(pg, v); r = {"compiled": pg.evaluate("$('compileMsg').textContent"), "decision": decide(pg),
             "said": pg.evaluate("timeline ? timeline.events.filter(e => e.kind === 'say').map(e => e.text) : null")}
        r["run"] = begin(pg); pg.wait_for_timeout(9000); r["outputs"] = outs(pg, 12)
        ctx.close(); return r

    # ---------------------------------------------------------------- C6/C7: over-blocking
    @T("C6_builtins_with_dx_plan_frame_I_am_steady")
    def _():
        ctx, pg = page("/player.html?profile=personal", PLANS["dxSteady"])
        r = {}
        for p in ["ssit_higher", "ssit_calm", "ssit_local", "swish", "override", "interrupt_only", "node_lion", "tier013_lion_dragon"]:
            pg.select_option("#program", p); pg.wait_for_timeout(250); r[p] = decide(pg)[:2]
        r["own_program_saying_I_am_steady_today"] = (typed(pg, 'PROTOCOL mine "Mine"\nPHASE a {\n  SAY "I am steady today"\n}\n'), decide(pg)[:2])[1]
        ctx.close(); return r

    @T("C7_one_protocol_fetch_fails")
    def _():
        out = {}
        for plan in ["dx", "ptsd"]:
            ctx, pg = page("/player.html?profile=personal", PLANS[plan], route=("**/protocols/tier579_glyph.rsx", lambda rt: rt.fulfill(status=404, body="")))
            pg.wait_for_timeout(500); r = {"loaded": pg.evaluate("RSOSLineage.loaded")}
            for p in ["interrupt_only", "override", "ssit_calm", "swish"]:
                pg.select_option("#program", p); pg.wait_for_timeout(250); r[p] = decide(pg)[:2]
            out[plan] = r; ctx.close()
        ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
        out["control_all_fetched"] = {}
        for p in ["interrupt_only", "override", "ssit_calm", "swish"]:
            pg.select_option("#program", p); pg.wait_for_timeout(250); out["control_all_fetched"][p] = decide(pg)[:2]
        ctx.close(); return out

    # ---------------------------------------------------------------- C8: held sessions that nothing closes
    @T("C8_device_held_run_blocks_codes_after_state_returns")
    def _():
        ctx, pg = page("/device.html?profile=personal")
        pg.evaluate(FAKETX); pg.select_option("#prog", "override"); pg.click("#run"); pg.wait_for_timeout(800)
        a = pg.evaluate("window.__sent.includes('START')")
        pg.evaluate(STATE, "CRISIS"); pg.wait_for_timeout(1500)
        pg.evaluate(STATE, "NORMAL"); pg.evaluate("() => { localStorage.removeItem('rsos.safety'); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'})); }")
        pg.wait_for_timeout(500); pg.evaluate("() => { window.__sent = []; }")
        pg.fill("#code", "-.-"); pg.click("#play"); pg.wait_for_timeout(600)
        r = {"run_started": a, "after_NORMAL_code_sent": pg.evaluate("window.__sent"), "msg": pg.evaluate("$('msg').textContent"),
             "sessions": pg.evaluate("RSOSOutlet.sessions().map(s => s.action.protocol + (s.held ? ' held' : ''))")}
        ctx.close()
        ctx, pg = page("/device.html?profile=personal"); pg.evaluate(FAKETX)
        pg.fill("#code", "-.-"); pg.click("#play"); pg.wait_for_timeout(600); r["control_fresh_page_code_sent"] = pg.evaluate("window.__sent.includes('START')"); ctx.close()
        return r

    @T("C8b_player_held_after_stabilise_then_normal")
    def _():
        # a run session that turns held is closed by finish(); this is the control for the device page in C8
        ctx, pg = page("/player.html?profile=personal")
        pg.select_option("#program", "override"); pg.wait_for_timeout(300); st = begin(pg)
        pg.evaluate(STATE, "CRISIS"); pg.wait_for_timeout(1500)
        pg.evaluate("() => { localStorage.removeItem('rsos.safety'); }"); pg.wait_for_timeout(200)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(300); st2 = begin(pg); pg.wait_for_timeout(2500)
        r = {"first": st, "second": st2, "second_running": pg.evaluate("!!run"), "outputs": outs(pg, 4)}
        ctx.close(); return r

    # ---------------------------------------------------------------- C9: Python/JavaScript fold parity in Chrome (Unicode versions)
    @T("C9_fold_parity_chrome_vs_python")
    def _():
        ctx, pg = page("/safety.html")
        samples = ["ice bath", "\U0001CCDE\U0001CCD8\U0001CCDA bath", "PROTOCOL tier414", "PROTOCOL tier\U0001CCF4\U0001CCF1\U0001CCF4" , "MODE \"\U0001CCE4bserver\"",
                   "Ᲊce bath", "ıce bath", "\U0001D422ce bath", "ice᠎bath", "ice\u0085bath"]
        js = pg.evaluate("(xs) => xs.map(x => [RSOSSafety.fold(x), RSOSSafety.spineFlags(x).map(f => f.flag), RSOSWatchdog.levelOfProgram(x, {}).therapist_led || false, RSOSWatchdog.levelOfProgram(x, {}).memory_work || false])", samples)
        py = json.loads(subprocess.run([sys.executable, "-I", "-c", """import json, sys
sys.path.insert(0, sys.argv[1])
from rsso import safety as S, watchdog as W
xs = json.loads(sys.stdin.read())
print(json.dumps([[S.fold(x), [f['flag'] for f in S.spine_flags(x)], bool(W.level_of_program(x, {}).get('therapist_led')), bool(W.level_of_program(x, {}).get('memory_work'))] for x in xs]))""",
                                         os.path.join(os.path.dirname(DOCS), "rsso")], input=json.dumps(samples), capture_output=True, text=True, check=True).stdout)
        diffs = [{"input": s.encode("unicode_escape").decode(), "chrome": j, "python": p} for s, j, p in zip(samples, js, py) if j != p]
        r = {"chrome_ua": pg.evaluate("navigator.userAgent"), "differences": diffs, "n": len(samples)}
        ctx.close(); return r

    @T("C10_device_dx_plan_builtin_lion_node_vs_its_code")
    def _():
        ctx, pg = page("/device.html?profile=personal", PLANS["dx"]); pg.evaluate(FAKETX)
        pg.select_option("#prog", "node_lion"); pg.click("#run"); pg.wait_for_timeout(800)
        r = {"builtin_lion_node_program_START": pg.evaluate("window.__sent.includes('START')"), "msg": pg.evaluate("$('msg').textContent")[:100]}
        pg.evaluate("() => { RSOSOutlet.close(); window.__sent = []; }")
        pg.fill("#code", "..-"); pg.click("#play"); pg.wait_for_timeout(600)
        r["its_code_alone_START"] = pg.evaluate("window.__sent.includes('START')"); r["code_msg"] = pg.evaluate("$('msg').textContent")[:100]
        ctx.close()
        ctx, pg = page("/player.html?profile=personal", PLANS["dx"])
        pg.select_option("#program", "node_lion"); pg.wait_for_timeout(300); r["player_builtin_node_lion"] = decide(pg)
        ctx.close(); return r

    b.close()
print(json.dumps({"results": R, "page_errors": errs}, indent=1, ensure_ascii=False))
