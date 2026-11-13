// Helper for test_ppg.py
const path = require("path");
const G = require(path.join(__dirname, "..", "..", "docs", "js", "ppg.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  process.stdout.write(JSON.stringify(JSON.parse(s).map(G.analyze)));
});
