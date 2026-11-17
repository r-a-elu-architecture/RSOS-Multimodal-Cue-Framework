// Helper for test_watchdog.py
const path = require("path");
const W = require(path.join(__dirname, "..", "..", "docs", "js", "watchdog.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.watch = i.cases.map(([a, c]) => W.watch(a, c));
  out.level = i.cases.map(([a]) => W.level(a));
  out.link = i.links.map(([c, st, t]) => W.link(c, st, t));
  out.sha = i.texts.map(t => W.sha256(t));
  const log = []; i.cases.slice(0, 300).forEach(([a, c], k) => W.record(log, a, W.watch(a, c), 1700000000000 + k));
  out.log = log; out.verify = W.verify(log);
  process.stdout.write(JSON.stringify(out));
});
