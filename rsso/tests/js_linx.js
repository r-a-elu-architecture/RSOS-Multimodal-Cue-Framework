// Helper for test_linx.py: runs the same cases through docs/js/linx.js
const path = require("path");
const L = require(path.join(__dirname, "..", "..", "docs", "js", "linx.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.understand = i.texts.map(L.understand);
  out.conversations = i.conversations.map(msgs => { let st = null; return msgs.map(m => { const r = L.converse(st, m); st = r.state; return r; }); });
  out.frames = i.frames.map(([t, m]) => L.suggestFrames(t, m));
  out.prompt = L.modelPrompt(i.ctx);
  out.routes = i.proposals.map(p => L.route(p, i.ctx.intake));
  out.offers = i.events.map(e => L.offer(e, i.plan, i.runs, i.gov, i.now));
  out.senses = i.senseLists.map(L.sensesFromList);
  process.stdout.write(JSON.stringify(out));
});
