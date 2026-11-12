// Helper for test_contribution.py: {inputs:[...], timeline} -> JS results (sealed contributions, errors, BIDS events)
const path = require("path");
const C = require(path.join(__dirname, "..", "..", "docs", "js", "contribution.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", async () => {
  const i = JSON.parse(s), out = { built: [], errors: [] };
  for (const inp of i.inputs) {
    try { out.built.push(await C.seal(C.build(inp))); out.errors.push(null); } catch (e) { out.built.push(null); out.errors.push(e.message); }
  }
  out.bids = C.bidsEvents(i.timeline);
  out.check = await C.check(out.built.find(Boolean));
  out.fnv = C.fnv1a(i.text);
  process.stdout.write(JSON.stringify(out));
});
