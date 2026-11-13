// Helper for test_peak.py
const path = require("path");
const P = require(path.join(__dirname, "..", "..", "docs", "js", "peak.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.captures = i.captures.map(([smp, base]) => P.captureCheck(smp, base));
  out.scenarios = i.scenarios.map(([k, seed, n, sh]) => { const sc = P.scenario(k, seed, n, sh);
    return { anchor: sc.anchor, true_strength: sc.true_strength, strength: P.strength(sc.anchor), contamination: P.contamination(sc.anchor) }; });
  out.anchors = i.anchors.map(a => ({ strength: P.strength(a), contamination: P.contamination(a), plan: P.restorationPlan(a, i.resource) }));
  const mk = i.make.map(m => P.makeAnchor(...m));
  out.composite = P.composite(mk[0], mk[1]);
  out.chain = P.chain(mk);
  out.rsx = P.chainRsx(mk);
  out.report = P.chainReport(i.report);
  process.stdout.write(JSON.stringify(out));
});
