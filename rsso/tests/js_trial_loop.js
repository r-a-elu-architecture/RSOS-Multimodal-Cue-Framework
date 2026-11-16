// Helper for test_trial_loop.py
const path = require("path");
const T = require(path.join(__dirname, "..", "..", "docs", "js", "trial.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.sham = i.sham.map(([seed, k, code]) => T.shamCode({ seed }, k, code));
  out.trials = i.trials.map(t => {
    const tr = T.newTrial(t.design, t.blocks, t.seed, "t", 0), ev = [];
    t.sessions.forEach(([b, a, cov, ts, detail]) => { const x = T.record(tr, b, a, cov, ts, detail); ev.push(x ? T.evidence(tr, x) : null); });
    return { trial: tr, evidence: ev };
  });
  process.stdout.write(JSON.stringify(out));
});
