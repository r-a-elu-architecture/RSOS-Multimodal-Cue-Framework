// Helper for test_cm1.py
const path = require("path");
const C = require(path.join(__dirname, "..", "..", "docs", "js", "cm1.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const sigs = i.people.map(C.signature);
  process.stdout.write(JSON.stringify({ sigs, assign: sigs.map(x => C.assign(x, i.profiles)), suggest: sigs.map(x => C.suggest(x, i.profiles)),
    describe: i.profiles.map(p => C.describe(p.centroid)), packs: i.plans.map(([p, st]) => C.pack(p, i.glyphs, st)),
    unpacked: i.bundles.map(b => C.unpack(b, i.glyphs)) }));
});
