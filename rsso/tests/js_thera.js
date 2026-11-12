// Helper for test_thera.py
const path = require("path");
const T = require(path.join(__dirname, "..", "..", "docs", "js", "thera.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), P = i.protocols;
  const plans = i.cases.map(([id, plan]) => T.sessionPlan(P, id, plan));
  const sessions = i.events.map(([k, evs]) => evs.reduce((ses, [step, vals, at]) => T.record(ses, step, vals, at), plans[k]));
  process.stdout.write(JSON.stringify({ plans, checks: sessions.map(T.check), summaries: sessions.map(x => T.summary(x, i.runs, i.started, i.ended)),
    homework: i.cases.map(([id, plan], k) => T.homework(plan, plans[k])) }));
});
