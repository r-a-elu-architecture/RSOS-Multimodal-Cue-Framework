// Helper for test_fixes_r1.py
const path = require("path"), J = n => require(path.join(__dirname, "..", "..", "docs", "js", n));
const S = J("safety.js"), W = J("watchdog.js"), P = J("profiles.js");
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.allowed = i.allowed.map(([st, a]) => S.allowed(st, a));
  out.watch = i.watch.map(([a, c]) => W.watch(a, c));
  out.text = i.text.map(([t, p]) => P.text(t, p));
  out.max = i.max.map(([p, on]) => P.maxLevel(p, on));
  const log = []; for (let k = 0; k < 1200; k++) { W.record(log, { kind: "run" }, { decision: "allow", level: "self_guided", reasons: [] }, 1000 + k); log.splice(0, Math.max(0, log.length - W.LOG_MAX)); }
  out.trimmed = { verify: W.verify(log), n0: log[0].n, len: log.length };
  process.stdout.write(JSON.stringify(out));
});
