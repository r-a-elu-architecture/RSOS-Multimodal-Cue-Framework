// Helper for test_trial.py
const path = require("path");
const T = require(path.join(__dirname, "..", "..", "docs", "js", "trial.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.schedules = i.schedules.map(([d, b, seed]) => T.schedule(d, b, seed));
  out.sims = i.sims.map(([d, b, seed, eff, o]) => { const t = new T.SimPerson(eff, o).run(T.newTrial(d, b, seed)); return { trial: t, analysis: T.analyze(t) }; });
  out.given = i.given.map(t => T.analyze(t));
  out.pool = T.pool(out.sims.filter(x => x.trial.design === "anchor_vs_sham").map(x => x.analysis), "anchor");
  out.consistency = T.consistency(i.decisions);
  process.stdout.write(JSON.stringify(out));
});
