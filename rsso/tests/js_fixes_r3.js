// Helper for test_fixes_r3.py
const path = require("path"), J = n => require(path.join(__dirname, "..", "..", "docs", "js", n));
const W = J("watchdog.js"), S = J("safety.js");
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  process.stdout.write(JSON.stringify({ level: i.level.map(([src, o]) => W.levelOfProgram(src, o)),
    observe: i.states.map(st => S.observe(st, { clinical_result: "high" }, 5)[0].mode), link: i.states.map(st => W.link({ escalation: { active: true, reasons: ["x"] } }, st, 5)[0].mode) }));
});
