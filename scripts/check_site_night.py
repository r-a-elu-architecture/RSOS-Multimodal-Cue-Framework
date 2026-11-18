"""Browser acceptance for spec/SITE_NIGHT.md §2 (C1–C5): the World page shows the Person Lab and tonight's results.
python3 scripts/check_site_night.py [docs_dir] [chrome_path]      Needs Playwright and Chrome.
"""
import functools
import http.server
import json
import pathlib
import re
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"
sys.path.insert(0, str(ROOT / "rsxv"))
from rsxv import site_findings as SF  # noqa: E402

NUM = re.compile(r"[−+-]?\d[\d,]*(?:\.\d+)?")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def nums(text):
    return [x.replace("−", "-").replace(",", "") for x in NUM.findall(text or "")]


def main():
    F = json.loads((DOCS / "data/world_findings.json").read_text(encoding="utf-8"))
    out, fails, errs = {}, [], []

    def expect(name, got, want):
        out[name] = got
        if got != want:
            fails.append(f"{name}: got {got!r}, expected {want!r}")

    # C2, Python side: the data file equals what the result files give.
    expect("C2 findings file equals the result files", F == json.loads(json.dumps(SF.build(), ensure_ascii=False)), True)

    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for label, vp in (("desktop", {"width": 1280, "height": 800}), ("phone", {"width": 390, "height": 844})):
            pg = b.new_page(viewport=vp)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + "/world.html", wait_until="networkidle")
            pg.wait_for_function("document.getElementById('findTurn').textContent.length > 40")
            expect(f"C1 {label} h1 names the Person Lab", "Person Lab" in pg.text_content("h1"), True)
            expect(f"C1 {label} jump link to #lab", pg.locator('a[href="#lab"]').count() >= 1 and pg.locator("#lab").count() == 1, True)
            shown = {
                "findTurn": pg.text_content("#findTurn"), "findCue": pg.text_content("#findCue"),
                "lookFind": pg.text_content("#lookFind"), "labFind": pg.text_content("#labFind"),
                "pBear": pg.text_content("#pBear"),
            }
            expect(f"C2 {label} findings equal the data",
                   [nums(shown["findTurn"]), nums(shown["findCue"])], [nums(F["turn"]), nums(F["cue"])])
            expect(f"C2 {label} 'What you are looking at' carries the CUE_RESOLVE line", F["cue"] in shown["lookFind"], True)
            expect(f"C2 {label} Person Lab note carries the TURN_RATINGS line", shown["labFind"], F["lab_note"])
            expect(f"C2 {label} run note from data", F["run_note"] in shown["pBear"], True)
            expect(f"C4 {label} one current navigation item", pg.locator('nav a[aria-current="page"]').count(), 1)
            expect(f"C5 {label} effect values kept",
                   pg.eval_on_selector_all("#labE option", "o => o.map(x => x.value)"), ["placeholder", "illustrative"])
            sp = b.new_page(viewport=vp)
            sp.on("pageerror", lambda e: errs.append(str(e)))
            sp.goto(base + "/system.html", wait_until="networkidle")
            sp.evaluate("show('personlab')")
            hrefs = sp.eval_on_selector_all("a.open", "a => a.map(x => x.getAttribute('href'))")
            expect(f"C3 {label} System box opens the Person Lab", any(h.endswith("world.html#lab") for h in hrefs), True)
            pg.close(); sp.close()
        b.close()
    srv.shutdown()
    expect("C5 page errors", errs, [])
    print(json.dumps({"checks": len(out), "fails": fails}, indent=1, ensure_ascii=False))
    print(f"{len(out) - len(fails)}/{len(out)} checks pass")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
