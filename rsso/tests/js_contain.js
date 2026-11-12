// Helper for test_contain.py
const path = require("path");
const C = require(path.join(__dirname, "..", "..", "docs", "js", "contain.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.envelope = i.timelines.map(t => C.checkEnvelope(t));
  out.drift = i.drifts.map(([runs, p, since]) => C.drift(runs, p, since));
  out.escalation = i.escalations.map(([r, a, sc, now]) => C.escalation(r, a, sc, now));
  out.review = i.reviews.map(([st, r, a, sc, now]) => C.review(st, r, a, sc, now));
  out.decide = i.decisions.map(([a, st, tl, now]) => C.decide(a, st, tl, now));
  out.release = i.releases.map(([st, p, by, now]) => C.release(st, p, by, now));
  out.rollback = C.rollback(i.history);
  process.stdout.write(JSON.stringify(out));
});
