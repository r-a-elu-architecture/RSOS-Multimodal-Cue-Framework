"""Browser acceptance for spec/PERSONLAB.md §7d D-E: the Person Lab on the World page and its box on the System page.
python3 scripts/check_personlab.py [docs_dir] [chrome_path]      Needs Playwright and Chrome.
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
sys.path.insert(0, str(ROOT / "rsxv"))
from rsxv.personlab import lab as LB  # noqa: E402


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    mirrors = json.loads((DOCS / "data/personlab_persons.json").read_text(encoding="utf-8"))
    lab = json.loads((DOCS / "data/personlab_lab.json").read_text(encoding="utf-8"))
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
            pg.goto(base + url); pg.wait_for_timeout(1500); return ctx, pg

        for q in ("", "?profile=performance", "?profile=clinical"):
            ctx, pg = page("/world.html" + q)
            expect(f"D1 100 lab persons listed {q}", pg.locator("#labP option").count(), 100)
            note = pg.inner_text("#labNote")
            expect(f"D2 the page says invented and not validated {q}", ["invented" in note, "failed its validation" in note, "no effect" in note], [True, True, True])
            rows = pg.evaluate("() => [...document.querySelectorAll('#labPop tr')].slice(1).map(r => [...r.cells].map(c => c.textContent))")
            want = []
            for eff in LB.EFFECTS:
                for pol in LB.POLICIES:
                    s = lab["population"][eff][pol]
                    want.append([f"{s['mean_final_I']:.2f}", f"{round(s['mean_final_g'] * 100)}%"])
            expect(f"D3 population table equals the published data {q}", [r[2:4] for r in rows], want)
            ctx.close()

        ctx, pg = page("/world.html")
        for idx in (0, 41, 99):
            for eff in LB.EFFECTS:
                for pol in LB.POLICIES:
                    pg.select_option("#labP", str(idx)); pg.select_option("#labE", eff); pg.select_option("#labPol", pol); pg.wait_for_timeout(80)
                    got = pg.evaluate("() => [...document.querySelectorAll('#labTicks tr')].slice(1).map(r => [r.cells[3].textContent, r.cells[4].textContent, r.cells[6].textContent])")
                    py = LB.session(mirrors["persons"][idx], idx + 1, pol, eff)
                    want = [[r["target"] or "—", f"{r['I']:.2f}", str(r["feedback"])] for r in py["ticks"]]
                    expect(f"D4 session {mirrors['persons'][idx]['id']} {eff} {pol} equals Python", got, want)
        pg.select_option("#labP", "0"); pg.select_option("#labPol", "agents"); pg.wait_for_timeout(80)
        pg.locator("#labTicks tr").nth(3).click(); pg.wait_for_timeout(100)
        prog = pg.inner_text("#labProg")
        expect("D5 the selected tick shows its RSX-V program with TARGET", ["TARGET " in prog, "@Vector7:EthicsContain(CONTAIN)" in prog], [True, True])
        tree = pg.inner_text("#labTree")
        expect("D6 the identity tree shows six levels, top to bottom", [tree.index("Purpose and mission") < tree.index("Environment"), pg.locator("#labTree > li").count()], [True, 6])
        ctx.close()

        ctx, pg = page("/world.html", 390)
        expect("D7 the section fits a phone screen", pg.evaluate("() => [...document.querySelectorAll('#lab .pane')].every(p => p.getBoundingClientRect().right <= window.innerWidth + 1)"), True)
        ctx.close()

        ctx, pg = page("/system.html")
        pg.click("#n-personlab"); pg.wait_for_timeout(200)
        panel = pg.inner_text("#panel")
        expect("E1 System page: Person Lab box and its evidence", ["Person Lab" in panel, "invented" in panel, "failed validation" in panel, "TARGET" in panel], [True, True, True, True])
        ctx.close()
        b.close()
    srv.shutdown()
    for f in fails:
        print("FAIL", f)
    for e in errs:
        print("PAGE ERROR", e)
    print(f"{len(out) - len(fails)}/{len(out)} checks pass; {len(errs)} page errors")
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
