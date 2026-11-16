// Helper for test_fixes_r5.py: the JavaScript side of the parity checks. stdin: {sources, checks, states, texts}.
const path = require("path"), J = n => require(path.join(__dirname, "..", "..", "docs", "js", n));
const W = J("watchdog.js"), S = J("safety.js");
let s = ""; process.stdin.on("data", d => { s += d; });
process.stdin.on("end", () => {
  const i = JSON.parse(s), safe = f => { try { return f(); } catch (e) { return "ERR:" + e.name; } };
  const cues = [{ id: "c1", tier: "414" }, { id: "ид", tier: "414" }];
  process.stdout.write(JSON.stringify({
    level: i.sources.map(x => W.levelOfProgram(x, { cues, edited: true })),
    fold: i.sources.map(x => S.fold(x)),
    ev: i.checks.map(a => safe(() => S.eventFromCheck(a))),
    exit: i.states.map(st => safe(() => S.exit(st, "person", 5))),
    spine: i.texts.map(t => S.spineFlags(t).map(f => f.flag)),
  }));
});
