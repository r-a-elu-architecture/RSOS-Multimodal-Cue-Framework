// Helper for test_fixes_r2.py
const path = require("path"), T = require(path.join(__dirname, "..", "..", "docs", "js", "trial.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  process.stdout.write(JSON.stringify({ sham: i.sham.map(([seed, k, c]) => T.shamCode({ seed }, k, c)),
    evidence: i.evidence.map(([tr, ses]) => T.evidence(tr, ses)) }));
});
