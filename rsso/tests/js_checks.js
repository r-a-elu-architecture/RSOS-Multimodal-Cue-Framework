// Helper for test_checks.py
const path = require("path");
const C = require(path.join(__dirname, "..", "..", "docs", "js", "checks.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = {};
  out.nback = i.nback.map(([seed, pressed]) => { const q = C.genNback(seed); return { seq: q, score: C.scoreNback(q, pressed) }; });
  out.digits = i.digits.map(([seed, n]) => C.genDigits(seed, n));
  out.span = i.span.map(t => [C.scoreSpan(t), C.nextSpan(t)]);
  out.reaction = i.reaction.map(([r, m]) => C.scoreReaction(r, m));
  out.delays = C.genDelays(9);
  out.words = i.words.map(seed => C.genWords(seed));
  out.recall = i.recall.map(([w, a]) => C.scoreRecall(w, a));
  out.reading = i.reading.map(([p, ms, a]) => C.scoreReading(p, ms, a));
  out.dot = i.dot.map(([seed, resp]) => { const t = C.genDotprobe(seed); return { trials: t, score: C.scoreDotprobe(t, resp) }; });
  out.z = i.z.map(C.zq);
  process.stdout.write(JSON.stringify(out));
});
