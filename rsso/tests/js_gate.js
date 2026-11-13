// Helper for test_gate.py
const path = require("path");
const G = require(path.join(__dirname, "..", "..", "docs", "js", "gate.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const out = i.cases.map(c => ({ gate: G.gate(c.anchor, c.offers, c.now, c.optins, c.history), wear: G.wear(c.anchor),
    fa: G.falseAlarms(c.offers, c.anchor.id),
    fire: ["suggest", "auto", "pressure"].map(m => G.mayFire(c.anchor, m, c.offers, c.now, c.optins, c.history, c.consents)) }));
  process.stdout.write(JSON.stringify({ cases: out, summary: G.auditSummary(i.log, 5), has: i.consents.map(([cs, sc, now]) => G.hasConsent(cs, sc, now)) }));
});
