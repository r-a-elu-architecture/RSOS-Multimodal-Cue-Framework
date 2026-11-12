// Helper for test_metrics.py: [{runs, srbai, settings}] on stdin -> JS metric values
const path = require("path");
const X = require(path.join(__dirname, "..", "..", "docs", "js", "metrics.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  process.stdout.write(JSON.stringify(JSON.parse(s).map(c => X.compute(c.runs, c.srbai, c.settings))));
});
