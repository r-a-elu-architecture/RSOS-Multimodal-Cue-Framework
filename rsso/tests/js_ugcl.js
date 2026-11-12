// Helper for test_ugcl.py: {glyphs, bt:[{n,comps,scores}]} on stdin -> JS outputs for comparison with Python
const path = require("path");
const U = require(path.join(__dirname, "..", "..", "docs", "js", "ugcl.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const inp = JSON.parse(s);
  const glyphs = inp.glyphs.map(g => ({ id: g.id, svg: U.svg(g, 96), svg_bg: U.svg(g, 40, "#fff", "#000"), haptic: U.hapticSignature(g), tone: U.toneMotif(g), code: U.encode(g), back: U.svg(U.decode(U.encode(g)), 96) }));
  const bt = inp.bt.map(c => ({ scores: U.btFit(c.n, c.comps, 60), next: U.nextPair(c.n, c.comps, c.scores) }));
  process.stdout.write(JSON.stringify({ glyphs, bt }));
});
