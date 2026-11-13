// Helper for test_identity.py
const path = require("path");
const I = require(path.join(__dirname, "..", "..", "docs", "js", "identity.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const out = i.profiles.map(p => ({
    issues: I.issues(p), completeness: I.completeness(p), coherence: p.ratings.map(r => I.coherence(r.scores)),
    trend: I.trend(p), drift: I.drift(p), generalisation: I.generalisation(p), walks: I.walksReport(p), rehearsals: I.rehearsalsReport(p),
    diff: p.versions.length > 1 ? I.diff(p.versions[0], p.versions[p.versions.length - 1]) : [],
    day: I.dayRsx(p), night: I.nightRsx(p), seq: I.sequenceRsx(p, "the worry"), week: I.weekPlan(p) }));
  process.stdout.write(JSON.stringify({ profiles: out, library: I.LIBRARY, templates: I.LIBRARY.map(t => I.fromTemplate(t.id, "x" + t.id, 5)),
    switches: I.switchReport(i.log), at: i.minutes.map(m => I.profileAt(i.schedule, m)), dose: [I.dosePlan(), I.dosePlan("07:30", "22:00", 9, 14)],
    evaluate: I.evaluate(30) }));
});
