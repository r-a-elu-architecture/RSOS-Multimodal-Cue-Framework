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
            expect("S8.4/S8.5 context line; wording", ["tests are registered so far" in body, "past-crisis" in body], [True, False])
            if SHOTS:
                pg.locator("#families").screenshot(path=str(SHOTS / "results_families.png"))
            ctx.close()

        steps = [("Step 6", step6), ("Step 7", step7), ("Step 8", step8)]
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
