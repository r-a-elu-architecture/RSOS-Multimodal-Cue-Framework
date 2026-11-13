// Helper for test_pron.py
const path = require("path");
const P = require(path.join(__dirname, "..", "..", "docs", "js", "peak.js"));
const R = require(path.join(__dirname, "..", "..", "docs", "js", "pron.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const out = { model: [], compare: [], mouth: [] };
  const rng = new P.Rng(21);
  R.DRILLS.slice(0, 3).forEach(d => {
    const m = R.synth(d.syllables);
    out.model.push([m.length, m.slice(1000, 1010), R.features(m).map(f => [f.db, f.f0]), R.syllablesOf(R.features(m))]);
    ["correct", "melody", "vowels", "rhythm"].forEach(kind => {
      const [x, k] = R.learner(d, kind, rng);
      out.compare.push([k, R.compare(x, m, d.syllables.map(q => q.v))]);
    });
  });
  const mr = new P.Rng(4), d = R.DRILLS[3], vs = d.syllables.map(q => q.v), spans = [[0.1, 0.34], [0.39, 0.63], [0.68, 0.92]];
  out.mouth.push(R.mouthFeedback(R.simMouth(mr, vs, spans, 30, [1, "o"]), spans, vs));
  out.mouth.push(R.mouthFeedback(R.simMouth(mr, vs, spans), spans, vs));
  out.resampled = R.to8k([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 24000);
  process.stdout.write(JSON.stringify(out));
});
