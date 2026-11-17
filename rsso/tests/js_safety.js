// Helper for test_safety.py
const path = require("path");
const S = require(path.join(__dirname, "..", "..", "docs", "js", "safety.js"));
const C = require(path.join(__dirname, "..", "..", "docs", "js", "contain.js"));
const L = require(path.join(__dirname, "..", "..", "docs", "js", "linx.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.screen = i.events.map(e => S.screen(e));
  out.sequences = i.sequences.map(seq => { let st = S.newState(); const r = []; seq.forEach(([op, arg, t]) => {
    let res; if (op === "observe") [st, res] = S.observe(st, arg, t); else if (op === "exit") [st, res] = S.exit(st, arg, t); else [st, res] = S.enterStabilise(st, arg, t);
    r.push([st, res]); }); return r; });
  out.category = i.actions.map(a => S.category(a));
  out.allowed = i.allowed.map(([st, a]) => S.allowed(st, a));
  out.check = i.checks.map(a => S.eventFromCheck(a));
  out.spine = i.texts.map(t => S.spineFlags(t));
  out.deep = i.deep.map(a => S.mayStartDeepSession(...a));
  out.adjusted = S.adjustedEffect(i.records);
  out.decide = i.decisions.map(([a, st, tl, now, sf]) => C.decide(a, st, tl, now, sf));
  out.route = i.routes.map(([p, intake]) => L.route(p, intake));
  process.stdout.write(JSON.stringify(out));
});
