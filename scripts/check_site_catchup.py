"""Browser acceptance for spec/SITE_CATCHUP.md, Steps 6 to 8.
python3 scripts/check_site_catchup.py [docs_dir] [chrome_path] [screenshot_dir]      Needs Playwright and Chrome.
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
DOCS = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
SHOTS = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None


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

        def page(url, w=1280):
            ctx = b.new_context(viewport={"width": w, "height": 900}); pg = ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(url + ": " + str(e)))
            pg.on("console", lambda m: errs.append(url + ": console " + m.text) if m.type == "error" and "net::ERR_" not in m.text and "Failed to load resource" not in m.text else None)
            pg.goto(base + url); pg.wait_for_timeout(900); return ctx, pg

        def step6():
            ctx, pg = page("/system.html")
            drawn = pg.evaluate("() => [document.querySelectorAll('#map g.node').length, Object.keys(NODES).length, document.querySelectorAll('#map path.edge').length, EDGES.length]")
            expect("S6 every box and edge drawn", [drawn[0] == drawn[1], drawn[2] == drawn[3], pg.is_visible("#n-rsxv")], [True, True, True])
            pg.click("#n-rsxv"); pg.wait_for_timeout(200); panel = pg.inner_text("body")
            expect("S6.2 RSX-V panel", ["RSX-V commands" in panel, "none comes from people" in panel, "0 tier records" in panel], [True, True, False])
            pg.click("#n-gate"); pg.wait_for_timeout(200); panel = pg.inner_text("body")
            expect("S6.1 Safety panel", ["Watchdog and CONTAIN" in panel, "Paused: practical" in panel, "Output gate on every page" in panel, "tier records" in panel], [True, True, True, True])
            pg.click("#n-devices"); pg.wait_for_timeout(200)
            expect("S6.3 Devices panel names pairing", "two-minute window" in pg.inner_text("body"), True)
            if SHOTS:
                SHOTS.mkdir(parents=True, exist_ok=True); pg.locator("#map").screenshot(path=str(SHOTS / "system_map.png"))
            ctx.close()
            ctx, pg = page("/system.html", 390)   # phone width: the map still fits its container
            expect("S6.5 map fits a phone screen", pg.evaluate("() => { const m = document.getElementById('map').getBoundingClientRect(); return m.width <= window.innerWidth; }"), True)
            ctx.close()

        def step7():
            ctx, pg = page("/rsxv.html"); pg.wait_for_timeout(500)
            got = pg.evaluate("() => ['fCommand', 'fCue', 'fDevice'].map(id => document.getElementById(id).textContent.split('\\n')[0])")
            expect("S7.2 three forms shown", got, ["RSX-V TIER 8 :: {DRAGON} :: (OVERRIDE)", 'PROTOCOL dragon "steady identity under pressure"', "LOAD 15 0.40"])
            expect("S7.2 status and links", ["none comes from people" in pg.inner_text("body"), pg.evaluate("() => ['agents.html', 'results.html'].every(h => !!document.querySelector('a[href=\"' + h + '\"]'))")], [True, True])
            if SHOTS:
                pg.screenshot(path=str(SHOTS / "rsxv_page.png"), full_page=False)
            ctx.close()
            ctx, pg = page("/")
            pg.click('nav a[href="rsxv.html"]'); pg.wait_for_timeout(500)
            expect("S7.1/S7.4 menu entry from the home page", [pg.url.endswith("rsxv.html"), pg.evaluate("document.querySelector('nav a[aria-current]').textContent")], [True, "RSX-V"])
            ctx.close()
            ctx, pg = page("/")
            expect("S7.1 home page names RSX-V", "RSX-V, above RSX" in pg.inner_text("body"), True)
            ctx.close()

        def step8():
            ctx, pg = page("/results.html"); pg.wait_for_timeout(500)
            fams = pg.evaluate("() => Array.from(document.querySelectorAll('.fam')).map(f => [f.dataset.family, f.querySelectorAll('.lk').length])")
            total = sum(n for _, n in fams)
            expect("S8.3 families and every test in them", [[f for f, _ in fams], total == pg.evaluate("document.querySelectorAll('#rows tr').length")],
                   [["transfer", "repurposing", "lineage", "person model", "agents"], True])
            chain = pg.evaluate("() => Array.from(document.querySelectorAll('.fam[data-family=\"repurposing\"] .chain')[0].querySelectorAll('.lk')).map(x => x.textContent)")
            expect("S8.2 repurposing chain in order", chain, ["W5-R", "W5-R2", "W5-R3", "W5-R4", "W5-R5", "W5-R6"])
            body = pg.inner_text("body")
            ceil = pg.evaluate("() => { const x = Array.from(document.querySelectorAll('.lk')).find(e => e.textContent === 'W5-CEILING'); return x ? x.className : null; }")
            expect("FIXES_P2 C3 W5-CEILING shown as an analysis", ceil, "lk analysis")
            expect("S8.4/S8.5 context line; wording", ["tests are registered so far" in body, "past-crisis" in body], [True, False])
            if SHOTS:
                pg.locator("#families").screenshot(path=str(SHOTS / "results_families.png"))
            ctx.close()

        def step10():
            ctx = b.new_context(viewport={"width": 1280, "height": 900})
            ctx.add_init_script("""(() => { window.__out = [];
              Navigator.prototype.vibrate = function (p) { window.__out.push(['vibrate', p]); return true; };
              SpeechSynthesis.prototype.speak = function (u) { window.__out.push(['speak', u.text]); };
              const st = AudioScheduledSourceNode.prototype.start; AudioScheduledSourceNode.prototype.start = function () { window.__out.push(['sound', 1]); return st.apply(this, arguments); };
            })();""")
            pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append("agents.html: " + str(e)))
            pg.goto(base + "/agents.html"); pg.wait_for_timeout(1200)
            d = json.loads((DOCS / "data" / "agents_proven.json").read_text(encoding="utf-8"))
            first = pg.inner_text("#pvTrial")
            pg.click("#pvNext"); second = pg.inner_text("#pvTrial"); pg.click("#pvPrev")
            meta = pg.inner_text("#pvOut"); pg.click('#pvRepair [data-arm="local"]'); local = pg.inner_text("#pvOut")
            t0 = d["w1"]["trials"][0]
            expect("S10 repair panel steps and arms", [first.startswith("Trial 1 of 40"), second.startswith("Trial 2 of 40"),
                   ("fixed" if t0["meta"]["fixed"] else "not fixed") in meta, ("not fixed" if not t0["local"]["fixed"] else "fixed") in local,
                   pg.evaluate("document.querySelectorAll('#pvGraph rect').length"), pg.evaluate("document.querySelectorAll('#pvSteps li').length")],
                   [True, True, True, True, 6, len(t0["local"]["repairs"])])
            F = d["w1"]["fixed"]
            expect("S10 counts match the file", f"meta repair fixed {F['meta']['all']}, local retry {F['local']['all']}" in pg.inner_text("#pvCount"), True)
            w1m = d["register"]["W1 repair"]["meaning"]
            import re as _re
            # RELEASE_1 A1 F1: compare after the page's own wording rule (profiles.js shows clinical words in the
            # current profile's vocabulary), not with the raw register text.
            shown = lambda t: pg.evaluate("t => RSOSProfiles.text(t, RSOSProfiles.current(), RSOSProfiles.clinicalOn())", t)
            expect("FIXES_P2 A1/A2 W1 caveat and heading", [shown(_re.sub(r"<[^>]+>", "", w1m))[:40] in pg.inner_text("#pvW1Meaning"), pg.inner_text("#pvTitle")],
                   [True, "Tested in simulation: the RSX-V agents"])
            A = d["audit"]
            expect("BASELINE_AUDIT §7 T3 audit line counts", f"{A['holds']} of {A['n']} audited results" in pg.inner_text("#pvAudit"), True)
            hsm = shown(_re.sub(r"<[^>]+>", "", d["register"]["H-CFIT / H-SWITCH"]["meaning"]))[:40]
            expect("BASELINE_AUDIT Q3 H-SWITCH meaning shown", hsm in pg.inner_text("#pvHsMeaning"), True)
            expect("S10 five bars, three cards", [pg.evaluate("document.querySelectorAll('#pvBars i').length"), pg.evaluate("document.querySelectorAll('#pvCards .pv-box').length")], [5, 3])
            expect("S10 no output to the person", pg.evaluate("window.__out.length"), 0)
            if SHOTS:
                pg.locator("#proven").screenshot(path=str(SHOTS / "agents_proven.png"))
            ctx.close()

        steps = [("Step 6", step6), ("Step 7", step7), ("Step 8", step8), ("Step 10", step10)]
        for name, fn in steps:
            try:
                fn()
            except Exception as e:
                fails.append(f"{name}: could not run ({str(e)[:200]})")
        b.close()
    srv.shutdown()
    print(json.dumps({"results": out, "page_errors": errs, "fails": fails}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
