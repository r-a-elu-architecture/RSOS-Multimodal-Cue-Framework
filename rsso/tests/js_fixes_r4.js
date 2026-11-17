// Helper for test_fixes_r4.py
const path = require("path"), J = n => require(path.join(__dirname, "..", "..", "docs", "js", n));
const W = J("watchdog.js"), S = J("safety.js");
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  process.stdout.write(JSON.stringify({ level: i.sources.map(src => W.levelOfProgram(src, { cues: [{ id: "c1", tier: "414" }] })),
    ev: i.checks.map(a => S.eventFromCheck(a)), exit: i.states.map(st => S.exit(st, "person", 5)) }));
});
