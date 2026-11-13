/* CHECKS — built-in cognitive tests, JavaScript implementation (spec/CHECKS.md). Mirrors rsso/rsso/checks.py
 * (identical sequences and scores, tested): n-back, digit span, reaction time, word recall, reading, and dot-probe
 * attention to threat. Needs docs/js/peak.js (the shared seeded generator). Research measures, not diagnostic tests.
 * Browser: window.RSOSChecks; Node: module.exports.
 */
(function (root) {
  "use strict";
  const PEAK = typeof module !== "undefined" && module.exports ? require("./peak.js") : root.RSOSPeak;
  const Rng = PEAK.Rng;
  const DATA = {"LETTERS": "BCDFGHJKLMNPQRSTVWXZ", "WORDS": ["anchor", "basket", "candle", "garden", "harbor", "island", "jacket", "kettle", "ladder", "marble", "napkin", "orchard", "pencil", "quarry", "ribbon", "saddle", "tunnel", "violin", "window", "yogurt", "bridge", "carpet", "falcon", "glacier", "hammer", "lantern", "meadow", "needle", "pepper", "rocket", "silver", "timber", "valley", "walnut", "zipper", "button", "copper", "feather", "orange", "pillow"], "THREAT": ["danger", "attack", "failure", "reject", "panic", "threat", "injury", "shame", "abandon", "collapse", "assault", "terror", "humiliate", "disaster", "betray", "hostile", "punish", "fear", "violent", "ruin"], "NEUTRAL": ["window", "garden", "pencil", "cabinet", "lantern", "harbor", "teacup", "meadow", "notebook", "staircase", "blanket", "kettle", "orchard", "library", "ribbon", "carpet", "basket", "pillow", "candle", "button"], "PASSAGES": [{"id": "bees", "title": "How bees share a map", "text": "A honeybee that finds a good patch of flowers returns to the hive and dances. On the vertical comb, the angle of her waggle run from straight up matches the angle between the sun and the flowers. The length of the run tells the distance: a longer waggle means a farther patch. Other bees follow her closely, feeling the vibrations in the dark, and then fly out on the bearing she showed. Because the sun moves across the sky, a dancer who keeps dancing for an hour slowly turns her run to keep the bearing true. Scouts that find poor patches dance briefly or not at all, so the colony sends most foragers to the richest flowers without any bee ever seeing the whole field.", "questions": [["What does the angle of the waggle run show?", ["The direction relative to the sun", "The number of flowers", "The time of day", "The danger on the way"], 0], ["What does a longer waggle run mean?", ["Better nectar", "A farther patch", "Rain is coming", "More bees are needed"], 1], ["Why do most foragers go to the richest flowers?", ["The queen chooses", "Scouts from poor patches dance briefly", "The richest flowers are nearest", "Bees follow the scent trail"], 1]]}, {"id": "tides", "title": "Why there are two tides a day", "text": "Most coasts see two high tides and two low tides each day. The moon's gravity pulls the ocean toward it, raising a bulge of water on the side of the earth that faces the moon. A second bulge forms on the far side, because there the moon pulls the solid earth slightly more than the distant water, leaving the water behind. As the earth turns, a coast passes through both bulges, so it meets two high tides. The moon also moves along its orbit, which is why the tides arrive about fifty minutes later each day. When the sun and the moon line up, at new and full moon, their pulls add together and the tides are largest.", "questions": [["Why is there a bulge on the side facing away from the moon?", ["The sun pushes it there", "The moon pulls the earth more than the far water", "Wind piles the water up", "The earth spins faster there"], 1], ["Why do tides come about fifty minutes later each day?", ["The moon moves along its orbit", "The oceans slow down", "The earth's day is getting longer", "Clocks are adjusted"], 0], ["When are tides largest?", ["At half moon", "When the sun and moon line up", "In winter only", "When the moon is farthest away"], 1]]}, {"id": "lighthouse", "title": "How a lighthouse is recognised", "text": "At night every lighthouse looks like a point of light, so sailors tell them apart by their rhythm. Each light has its own character, written on charts: a single flash every ten seconds, for example, or two quick flashes and a long pause, or a steady light that is briefly cut off. Some lights show different colours in different directions, so a ship that sees red knows it is heading toward rocks and should turn until the light shows white. Before electricity, keepers wound clockwork that turned the lens through the night. Today most lights run automatically, but the rhythms have stayed the same, because the charts still use them.", "questions": [["How do sailors tell lighthouses apart at night?", ["By their height", "By their rhythm of flashes", "By radio only", "By the keeper's signal"], 1], ["What should a ship do if it sees a red sector?", ["Keep its course", "Turn until the light shows white", "Stop and anchor", "Signal back in red"], 1], ["Why have the rhythms stayed the same?", ["The charts still use them", "The lenses cannot change", "Law forbids changes", "Keepers prefer them"], 0]]}]};
  const { LETTERS, WORDS, THREAT, NEUTRAL, PASSAGES } = DATA;
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const r2 = x => (x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100);
  const pick = (rng, n) => Math.floor(rng.u() * n);
  function shuffle(xs, rng) { xs = xs.slice(); for (let i = xs.length - 1; i > 0; i--) { const j = pick(rng, i + 1); const t = xs[i]; xs[i] = xs[j]; xs[j] = t; } return xs; }
  function zq(p) {
    const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.3577518672690, -30.66479806614716, 2.506628277459239];
    const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
    const c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
    const d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
    const lo = 0.02425;
    if (p < lo) { const q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    if (p > 1 - lo) { const q = Math.sqrt(-2 * Math.log(1 - p)); return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    const q = p - 0.5, r = q * q;
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  function genNback(seed, n, length, targets) {
    n = n === undefined ? 2 : n; length = length === undefined ? 24 : length; targets = targets === undefined ? 8 : targets;
    const rng = new Rng(seed), idx = []; for (let i = n; i < length; i++) idx.push(i);
    const pos = shuffle(idx, rng).slice(0, targets).sort((x, y) => x - y), seq = [];
    for (let i = 0; i < length; i++) {
      if (pos.includes(i)) seq.push(seq[i - n]);
      else { let ch; while (true) { ch = LETTERS[pick(rng, LETTERS.length)]; if (i < n || ch !== seq[i - n]) break; } seq.push(ch); }
    }
    return seq.map((ch, i) => ({ i, letter: ch, target: i >= n && ch === seq[i - n] }));
  }
  function scoreNback(seq, pressed) {
    const pr = {}; pressed.forEach(p => { pr[Math.trunc(p.i)] = p.rt === undefined ? null : p.rt; });
    const has = i => Object.prototype.hasOwnProperty.call(pr, i);
    const t = seq.filter(s => s.target).length, hits = seq.filter(s => s.target && has(s.i)).length;
    const fa = seq.filter(s => !s.target && has(s.i)).length, nt = seq.length - t;
    const hr = (hits + 0.5) / (t + 1), fr = (fa + 0.5) / (nt + 1);
    const rts = seq.filter(s => s.target && has(s.i) && pr[s.i] !== null).map(s => Number(pr[s.i]));
    return { task: "nback", hits, targets: t, false_alarms: fa, non_targets: nt, accuracy: seq.length ? r1((hits + nt - fa) / seq.length * 100) : null,
      d_prime: r2(zq(hr) - zq(fr)), rt: rts.length ? r1(rts.reduce((s, x) => s + x, 0) / rts.length) : null };
  }
  function genDigits(seed, length) { const rng = new Rng(seed); let out = ""; while (out.length < length) { const d = String(pick(rng, 10)); if (!out || d !== out[out.length - 1]) out += d; } return out; }
  function scoreSpan(trials) { let best = 0, total = 0; trials.forEach(t => { if (t.correct) { total++; best = Math.max(best, Math.trunc(t.length)); } }); return { task: "span", span: best, correct: total, trials: trials.length }; }
  function nextSpan(trials, start, top) {
    start = start || 3; top = top || 10;
    if (!trials.length) return start;
    const last = Math.trunc(trials[trials.length - 1].length), at = trials.filter(t => Math.trunc(t.length) === last);
    if (at.length < 2) return last;
    if (!at.some(t => t.correct)) return null;
    return last < top ? last + 1 : null;
  }
  function scoreReaction(rts, misses) {
    const xs = rts.filter(x => x !== null && x !== undefined).map(Number).sort((a, b) => a - b), valid = xs.filter(x => x >= 150);
    const out = { task: "reaction", n: xs.length, anticipations: xs.length - valid.length, lapses: valid.filter(x => x > 500).length, misses: Math.trunc(misses || 0), median: null, mean: null, sd: null };
    if (valid.length) {
      const k = valid.length, h = Math.floor(k / 2), med = k % 2 ? valid[h] : (valid[h - 1] + valid[h]) / 2, m = valid.reduce((s, x) => s + x, 0) / k;
      out.median = r1(med); out.mean = r1(m); out.sd = k > 1 ? r1(Math.sqrt(valid.reduce((s, x) => s + (x - m) * (x - m), 0) / (k - 1))) : null;
    }
    return out;
  }
  function genDelays(seed, n, lo, hi) { n = n || 15; lo = lo || 1500; hi = hi || 4000; const rng = new Rng(seed), out = []; for (let i = 0; i < n; i++) out.push(lo + pick(rng, hi - lo)); return out; }
  function genWords(seed, n) { return shuffle(WORDS, new Rng(seed)).slice(0, n || 12); }
  function scoreRecall(words, answer) {
    const said = Array.from(String(answer).toLowerCase()).map(ch => (/\p{L}/u.test(ch) ? ch : " ")).join("").split(/\s+/).filter(Boolean);
    const seen = new Set(), target = new Set(words.map(w => w.toLowerCase())); let correct = 0, intr = 0, rep = 0;
    said.forEach(w => { if (seen.has(w)) { rep++; return; } seen.add(w); if (target.has(w)) correct++; else intr++; });
    return { task: "recall", correct, of: words.length, intrusions: intr, repeats: rep, percent: words.length ? r1(correct / words.length * 100) : null };
  }
  const passage = pid => PASSAGES.find(p => p.id === pid);
  const wordCount = text => text.split(/\s+/).filter(Boolean).length;
  function scoreReading(pid, ms, answers) {
    const p = passage(pid), words = wordCount(p.text);
    let right = 0; p.questions.forEach((q, k) => { const a = answers[k]; if (a !== null && a !== undefined && Math.trunc(a) === q[2]) right++; });
    const wpm = ms && ms > 0 ? words / (Number(ms) / 60000) : null, comp = right / p.questions.length;
    return { task: "reading", passage: pid, words, wpm: wpm ? r1(wpm) : null, correct: right, of: p.questions.length, comprehension: r1(comp * 100), effective_wpm: wpm ? r1(wpm * comp) : null };
  }
  function genDotprobe(seed, n) {
    n = n || 32; const rng = new Rng(seed), th = shuffle(THREAT, rng), ne = shuffle(NEUTRAL, rng);
    const sidesIn = [], congIn = []; for (let k = 0; k < n; k++) { sidesIn.push(k < Math.floor(n / 2) ? "left" : "right"); congIn.push(k < Math.floor(n / 2)); }
    const sides = shuffle(sidesIn, rng), cong = shuffle(congIn, rng), out = [];
    for (let k = 0; k < n; k++) { const ts = sides[k], probe = cong[k] ? ts : (ts === "left" ? "right" : "left");
      out.push({ k, threat: th[k % th.length], neutral: ne[k % ne.length], threat_side: ts, probe_side: probe, congruent: cong[k] }); }
    return out;
  }
  function scoreDotprobe(trials, responses) {
    const by = {}; responses.forEach(r => { by[Math.trunc(r.k)] = r; });
    const con = [], inc = []; let wrong = 0;
    trials.forEach(t => { const r = by[t.k]; if (!r) return; if (r.side !== t.probe_side) { wrong++; return; } const rt = Number(r.rt); if (rt >= 200 && rt <= 1500) (t.congruent ? con : inc).push(rt); });
    const mc = con.length ? con.reduce((s, x) => s + x, 0) / con.length : null, mi = inc.length ? inc.reduce((s, x) => s + x, 0) / inc.length : null;
    return { task: "dotprobe", congruent_rt: mc !== null ? r1(mc) : null, incongruent_rt: mi !== null ? r1(mi) : null,
      bias: mc !== null && mi !== null ? r1(mi - mc) : null, errors: wrong, n: con.length + inc.length };
  }
  const api = { LETTERS, WORDS, THREAT, NEUTRAL, PASSAGES, zq, genNback, scoreNback, genDigits, scoreSpan, nextSpan, scoreReaction, genDelays, genWords, scoreRecall, passage, wordCount, scoreReading, genDotprobe, scoreDotprobe };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.RSOSChecks = api;
})(typeof self !== "undefined" ? self : this);
