"""Review R6 check: probes of the run lock (F1-F3), lineage over-blocking (share = shared/|origin|), fold perf.
python3 -I probe.py <docs_dir> [chrome] [P1,P2,...]"""
import functools, http.server, json, os, socketserver, subprocess, sys, threading, time
from playwright.sync_api import sync_playwright
DOCS = os.path.abspath(sys.argv[1]); CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else None
HERE = os.path.dirname(os.path.abspath(__file__))
SPIES = """(() => { window.__out = []; window.addEventListener('rsos-outlet-hold', () => {});
  Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', JSON.stringify(p), Date.now()]); return true; };
  SpeechSynthesis.prototype.speak = function (u) { window.__out.push(['speak', u.text, Date.now()]); };
})();"""
P6 = json.loads(subprocess.run(["node", os.path.join(HERE, "plans.js"), os.path.join(DOCS, "js", "nodes.js")], capture_output=True, text=True, check=True).stdout)
PALL = json.loads(subprocess.run(["node", os.path.join(HERE, "plans_all.js"), os.path.join(DOCS, "js", "nodes.js")], capture_output=True, text=True, check=True).stdout)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=DOCS)); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"; R, errs = {}, []
def T(name):
    def deco(fn):
        if ONLY and not any(name.startswith(o) for o in ONLY): return fn
        try: R[name] = fn()
        except Exception as e: R[name] = "could not run: " + str(e)[:300]
        return fn
    return deco
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    def page(url, plan=None):
        ctx = b.new_context(); ctx.add_init_script(SPIES); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(url + ": " + str(e)))
        pg.goto(base + url); pg.wait_for_timeout(600)
        if plan is not None: pg.evaluate("(p) => localStorage.setItem('rsos.plan', JSON.stringify(p))", plan); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("() => RSOSLineage.ready"); return ctx, pg
    outs = lambda pg: pg.evaluate("window.__out.map(x => x[0] + ':' + String(x[1]).slice(0, 70))")
    st = lambda pg: pg.evaluate("() => ({running: !!run, playing: run ? (run.tl.protocol) : null, msg: $('compileMsg').textContent.slice(0, 120), locked: ['program','source','f0','inhale'].map(i => $(i).disabled)})")
    def sel(pg, v): pg.evaluate("(v) => { $('program').value = v; $('program').dispatchEvent(new Event('change')); }", v); pg.wait_for_timeout(200)
    def begin(pg):
        pg.evaluate("() => { $('optVib').checked = true; $('optVoice').checked = true; }"); pg.click("#start"); pg.wait_for_timeout(400)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(300)
    DEC = "() => { if (!timeline) return ['nocompile', '', []]; const d = safetyDecide({kind: 'run', protocol: timeline.protocol, trigger: 'self'}); return [d.decision, d.watchdog.level, RSOSLineage.flags(effectiveSource(), {}).from]; }"

    @T("P1a_script_menu_change_midrun")
    def _():
        ctx, pg = page("/player.html?profile=personal", P6["dx"]); sel(pg, "ssit_calm"); begin(pg); s0 = st(pg)
        pg.evaluate("() => { window.__out = []; }"); sel(pg, "plan:0"); pg.wait_for_timeout(4000)
        r = {"before": s0, "after": st(pg), "outputs_after_change": outs(pg)}; ctx.close(); return r
    @T("P1b_script_source_recompile_midrun_and_cue_load_path")
    def _():
        ctx, pg = page("/player.html?profile=personal", P6["dx"]); sel(pg, "plan:0"); held = pg.evaluate("$('source').value"); sel(pg, "ssit_calm"); begin(pg)
        pg.evaluate("() => { window.__out = []; }")
        pg.evaluate("(s) => { loadOrigin = null; $('source').value = s; recompile(); }", held); pg.wait_for_timeout(4000)
        r = {"after": st(pg), "outputs_after_change": outs(pg)}; ctx.close(); return r
    @T("P1c_debounce_race_editor_allowed_while_timeline_held")
    def _():
        # editor shows held plan:0 (compiled); replace the text with ssit_calm and press Start+Begin before the 250 ms debounce
        ctx, pg = page("/player.html?profile=personal", P6["dx"]); sel(pg, "ssit_calm"); calm = pg.evaluate("$('source').value"); sel(pg, "plan:0")
        pg.evaluate("() => { $('optVib').checked = true; $('optVoice').checked = true; window.__out = []; }")
        r = pg.evaluate("""async (calm) => { const s = $('source'); s.value = calm; s.dispatchEvent(new Event('input'));
            const p = start('self'); await new Promise(r => setTimeout(r, 30)); const go = $('checkinGo'); if (go && go.offsetParent !== null) go.click();
            const rr = await p; const m0 = $('compileMsg').textContent.slice(0, 140); const playing = run ? run.tl.protocol : null; await new Promise(r => setTimeout(r, 2500));
            return { m0, playing_at_start: playing, now: run ? run.tl.protocol : null, msg: $('compileMsg').textContent.slice(0, 100), out: window.__out.map(x => x[0] + ':' + String(x[1]).slice(0, 60)) }; }""", calm)
        ctx.close(); return r
    @T("P1d_device_offer_start_locks_and_stop_unlocks")
    def _():
        ctx, pg = page("/player.html?profile=personal"); sel(pg, "ssit_calm")
        pg.evaluate("() => { offerShownAt = performance.now(); start('device'); }"); pg.wait_for_timeout(400)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(300); a = st(pg); pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        if pg.is_visible("#checkinGo"): pg.click("#checkinGo")
        pg.wait_for_timeout(300); r = {"during": a, "after_escape": st(pg)}
        sel(pg, "override"); begin(pg); r["second_run"] = st(pg); ctx.close(); return r
    @T("P1e_hold_mid_run_unlocks")
    def _():
        ctx, pg = page("/player.html?profile=personal"); sel(pg, "ssit_calm"); begin(pg); a = st(pg)
        pg.evaluate("() => { localStorage.setItem('rsos.safety', JSON.stringify({mode: 'CRISIS', history: [{from: 'NORMAL', to: 'CRISIS', why: 't', by: 't', at: 1}], last: null})); window.dispatchEvent(new StorageEvent('storage', {key: 'rsos.safety'})); }")
        pg.wait_for_timeout(1800); r = {"during": a, "after_hold": st(pg)}; ctx.close(); return r

    @T("P2_lineage_builtins_by_plan")
    def _():
        ctx, pg = page("/player.html?profile=personal"); progs = pg.evaluate("PROTOCOLS.filter(p => p in sources)")
        own = ['PROTOCOL mine "Mine"\nVERSION 1.0\nPHASE settle {\n  SAY "I breathe slowly and I am here"\n  HAPTIC on=300ms off=300ms x=6 amp=0.4\n}\nPHASE b breath=exhale {\n  FEEL "Feet on the floor; long exhale"\n}',
               'PROTOCOL mine2 "Mine 2"\nVERSION 1.0\nPHASE a {\n  SAY "I move, I act"\n  SAY "I hold my ground"\n  FEEL "Spine straight, warmth in the belly"\n}']
        def run_all(pg):
            out = {}
            for p in progs: sel(pg, p); out[p] = pg.evaluate(DEC)
            for i, s in enumerate(own):
                pg.evaluate("(s) => { $('program').value = 'ssit_calm'; $('source').value = s; recompile(); }", s); out["own%d" % i] = pg.evaluate(DEC)
            return out
        base_ = run_all(pg); ctx.close(); res = {"n_programs": len(progs), "baseline_blocked": [k for k, v in base_.items() if v[0] != "allow"], "by_plan": {}}
        for name, plan in PALL.items():
            ctx, pg = page("/player.html?profile=personal", plan); o = run_all(pg); ctx.close()
            res["by_plan"][name] = {k: [v[0], v[1], v[2]] for k, v in o.items() if v[2] and k not in res["baseline_blocked"]}
        return res

    @T("P3_fold_perf_and_parity_chrome")
    def _():
        ctx, pg = page("/player.html?profile=personal")
        perf = pg.evaluate("""() => { const mk = n => { let s = ''; const parts = ['I am stéady ', 'ɑnd ', '𝐢ce bath ', 'Ꮃord ', '你好 ', 'plain ascii text ']; while (s.length < n) s += parts[s.length % parts.length]; return s; };
            const r = {}; for (const n of [20000, 200000, 1000000]) { const s = mk(n); const t = performance.now(); const f = RSOSSafety.fold(s); r[n] = Math.round(performance.now() - t); }
            const s = mk(200000); let t = performance.now(); RSOSWatchdog.levelOfProgram('PROTOCOL x\\nPHASE a 5s\\nSAY "' + s.replace(/"/g, '') + '"', {}); r.levelOfProgram_200k = Math.round(performance.now() - t);
            t = performance.now(); RSOSLineage.flags('PROTOCOL x\\nPHASE a 5s\\nSAY "' + s.replace(/"/g, '') + '"', {}); r.lineage_flags_200k = Math.round(performance.now() - t); return r; }""")
        # parity: every code point 0..0x3FFFF (except surrogates) through fold in Chrome vs Python
        cps = [c for c in range(0, 0x40000) if not (0xD800 <= c <= 0xDFFF)]
        chunks = ["".join(chr(c) + "|" for c in cps[i:i + 20000]) for i in range(0, len(cps), 20000)]
        js = [pg.evaluate("(s) => RSOSSafety.fold(s)", ch) for ch in chunks]
        py = json.loads(subprocess.run([sys.executable, "-I", "-c", "import json,sys\nsys.path.insert(0, sys.argv[1])\nfrom rsso import safety as S\nprint(json.dumps([S.fold(x) for x in json.loads(sys.stdin.read())]))",
                                        os.path.join(os.path.dirname(DOCS), "rsso")], input=json.dumps(chunks), capture_output=True, text=True, check=True).stdout)
        diff = [i for i, (a, c) in enumerate(zip(js, py)) if a != c]
        ctx.close(); return {"perf_ms": perf, "parity_chunks": len(chunks), "chunks_differing": diff}
    b.close()
print(json.dumps({"results": R, "page_errors": errs}, indent=1, ensure_ascii=False))
