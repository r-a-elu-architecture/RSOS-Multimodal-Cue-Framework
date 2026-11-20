"""spec/SITE_FAMILY.md F2 checks T1-T3 and T5, in Chrome: white ground and the ribbon, text contrast, overflow, screenshots.
Usage: python3 scripts/check_family.py [shots_dir]"""
import functools
import http.server
import json
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SHOTS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
CHROME = "/usr/bin/google-chrome"

MEASURE = r"""() => {
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(Number);
                       return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = c => { const f = x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
                     return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const NAVY = {r: 21, g: 27, b: 47, a: 1};
  const bgOf = el => {
    for (let e = el; e; e = e.parentElement) {
      if (e.matches && e.matches('.ribbon, header.top, aside .top')) return NAVY;
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0.5) return c;
      if (getComputedStyle(e).backgroundImage !== 'none' && e !== document.body && e !== document.documentElement) return null; // image or gradient: not measurable
    }
    return parse(getComputedStyle(document.body).backgroundColor);
  };
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const el = n.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    if (cs.visibility === 'hidden' || cs.display === 'none' || r.width === 0 || r.height === 0 || parseFloat(cs.opacity) < 0.3) continue;
    if (el.closest('pre, code, svg, .orb, .stage, [aria-hidden=true]')) continue;   // code panes keep their dark style; decorative
    const fg = parse(cs.color), bg = bgOf(el); if (!fg || !bg) continue;
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
    const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
    const cr = ratio(fg, bg);
    if (cr < need) out.push({text: n.textContent.trim().slice(0, 50), ratio: Math.round(cr * 100) / 100, need, color: cs.color,
                             bg: `rgb(${bg.r}, ${bg.g}, ${bg.b})`, tag: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '')});
  }
  const body = parse(getComputedStyle(document.body).backgroundColor);
  const header = document.querySelector('.ribbon, header.top, aside .top');
  return {low: out, bodyLum: Math.round(lum(body) * 100) / 100, ribbon: !!header &&
          getComputedStyle(header).backgroundColor === 'rgb(21, 27, 47)'};
}"""


def main():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(DOCS))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    report, errs = {}, []
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        for f in sorted(DOCS.glob("*.html")):
            row = {}
            for w, h in ((1280, 900), (375, 800)):
                pg = b.new_page(viewport={"width": w, "height": h})
                pg.on("pageerror", lambda e, n=f.name: errs.append(f"{n}: {e}"))
                pg.goto(f"{base}/{f.name}"); pg.wait_for_timeout(700)
                row[f"overflow_{w}"] = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                if w == 1280:
                    row.update(pg.evaluate(MEASURE))
                    if SHOTS:
                        pg.screenshot(path=str(SHOTS / f"{f.stem}.png"))
                pg.close()
            report[f.name] = row
        b.close()
    srv.shutdown()
    RETIRED = {"architecture-benchmark.html", "cue-lab.html", "cue-lab-v13.html", "invariance-v14.html"}   # "page retired" notices: no header
    fails = {n: r for n, r in report.items() if r["low"] or r["bodyLum"] < 0.85 or r["overflow_1280"] > 0 or r["overflow_375"] > 0
             or (not r["ribbon"] and n not in RETIRED)}
    summary = {n: {"low": len(r["low"]), "bodyLum": r["bodyLum"], "ribbon": r["ribbon"], "overflow": [r["overflow_1280"], r["overflow_375"]]}
               for n, r in report.items()}
    print(json.dumps({"summary": summary, "fails": {n: r["low"][:8] for n, r in fails.items()}, "page_errors": errs}, indent=1, ensure_ascii=False))
    return 1 if fails or errs else 0


if __name__ == "__main__":
    sys.exit(main())
