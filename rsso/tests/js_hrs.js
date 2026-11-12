// Helper for test_hrs.py: reads JSON {packets:[[bytes]], rec:{t,rr,motion}} on stdin, prints JS results.
const path = require("path");
const H = require(path.join(__dirname, "..", "..", "docs", "js", "hrs.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const inp = JSON.parse(s);
  const parsed = inp.packets.map(p => H.parseHeartRateMeasurement(p));
  const det = inp.rec ? H.StressDetector.detect(inp.rec, inp.opts || {}) : [];
  process.stdout.write(JSON.stringify({ parsed, det }));
});
