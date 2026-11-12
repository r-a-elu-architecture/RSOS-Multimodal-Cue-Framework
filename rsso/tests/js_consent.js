// Helper for test_consent.py: {cases:[{c, now}], progs:[c]} -> JS results
const path = require("path");
const C = require(path.join(__dirname, "..", "..", "docs", "js", "consent.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const inp = JSON.parse(s);
  process.stdout.write(JSON.stringify({ checks: inp.cases.map(x => C.check(x.c, x.now)), progs: inp.progs.map(c => C.cueProgram(c, 4, 6)) }));
});
