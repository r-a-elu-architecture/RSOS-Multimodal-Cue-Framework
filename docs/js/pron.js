/* PRON — pronunciation feedback from sound and, optionally, the camera (spec/MACHINES.md §4).
 * Identical to rsso/rsso/pron.py (tested). Needs docs/js/peak.js for the seeded generator.
 * Browser: window.RSOSPron; Node: module.exports. */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const P = node ? require("./peak.js") : root.RSOSPeak;

  const SR = 8000, FRAME = 200, HOP = 160, NFFT = 256;
  const VOWELS = { a: [730, 1090], e: [530, 1840], i: [270, 2290], o: [570, 840], u: [300, 870] };
  const MOUTH = { a: { open: 0.62, round: 0.2 }, e: { open: 0.38, round: 0.1 }, i: { open: 0.18, round: 0.05 }, o: { open: 0.45, round: 0.7 }, u: { open: 0.2, round: 0.85 } };
  const THRESH = { melody: 2.0, vowels: 5.5, rhythm: 0.36 };
  const KEYS = ["melody", "vowels", "rhythm"];
  const DRILLS = [
    {
      "id": "question",
      "title": "A rising question",
      "syllables": [
        {
          "v": "e",
          "ms": 160,
          "f0": [
            120,
            124
          ]
        },
        {
          "v": "a",
          "ms": 230,
          "f0": [
            126,
            120
          ]
        },
        {
          "v": "i",
          "ms": 170,
          "f0": [
            119,
            118
          ]
        },
        {
          "v": "o",
          "ms": 280,
          "f0": [
            126,
            182
          ]
        }
      ]
    },
    {
      "id": "statement",
      "title": "A falling statement",
      "syllables": [
        {
          "v": "a",
          "ms": 200,
          "f0": [
            150,
            160
          ]
        },
        {
          "v": "o",
          "ms": 260,
          "f0": [
            165,
            150
          ]
        },
        {
          "v": "e",
          "ms": 160,
          "f0": [
            140,
            128
          ]
        },
        {
          "v": "u",
          "ms": 260,
          "f0": [
            122,
            95
          ]
        }
      ]
    },
    {
      "id": "stress",
      "title": "Stress on the second syllable",
      "syllables": [
        {
          "v": "o",
          "ms": 140,
          "f0": [
            130,
            130
          ]
        },
        {
          "v": "e",
          "ms": 320,
          "f0": [
            150,
            165
          ]
        },
        {
          "v": "a",
          "ms": 150,
          "f0": [
            135,
            125
          ]
        }
      ]
    },
    {
      "id": "i_e",
      "title": "i against e",
      "syllables": [
        {
          "v": "i",
          "ms": 240,
          "f0": [
            140,
            135
          ]
        },
        {
          "v": "e",
          "ms": 240,
          "f0": [
            135,
            130
          ]
        },
        {
          "v": "i",
          "ms": 240,
          "f0": [
            132,
            120
          ]
        }
      ]
    },
    {
      "id": "u_o",
      "title": "u against o",
      "syllables": [
        {
          "v": "u",
          "ms": 240,
          "f0": [
            140,
            135
          ]
        },
        {
          "v": "o",
          "ms": 240,
          "f0": [
            135,
            130
          ]
        },
        {
          "v": "u",
          "ms": 240,
          "f0": [
            132,
            120
          ]
        }
      ]
    }
  ];
  const EDGES = []; for (let k = 0; k < 15; k++) EDGES.push(200 * Math.pow(3600 / 200, k / 14));

  const r1 = x => x == null ? null : Math.floor(x * 10 + 0.5) / 10;
  const r2 = x => x == null ? null : Math.floor(x * 100 + 0.5) / 100;
  const argmax = xs => { let b = 0; for (let i = 1; i < xs.length; i++) if (xs[i] > xs[b]) b = i; return b; };
  const median = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };

  // ------------------------------------------------------------ synthesis
  function reson(f, bw) { const c = -Math.exp(-2 * Math.PI * bw / SR), b = 2 * Math.exp(-Math.PI * bw / SR) * Math.cos(2 * Math.PI * f / SR); return [1 - b - c, b, c]; }

  function synth(syllables, rng, f0Scale, formantScale, tempo, noise) {
    rng = rng || new P.Rng(1); f0Scale = f0Scale == null ? 1 : f0Scale; formantScale = formantScale == null ? 1 : formantScale;
    tempo = tempo == null ? 1 : tempo; noise = noise == null ? 0.01 : noise;
    const out = new Array(Math.trunc(0.08 * SR)).fill(0);
    syllables.forEach((s, k) => {
      const n = Math.trunc(s.ms / tempo * SR / 1000), F = VOWELS[s.v];
      const res = [reson(F[0] * formantScale, 90), reson(F[1] * formantScale, 110), reson(2500 * formantScale, 150)];
      const st = [[0, 0], [0, 0], [0, 0]];
      let phase = 0;
      for (let i = 0; i < n; i++) {
        const f0 = (s.f0[0] + (s.f0[1] - s.f0[0]) * i / Math.max(1, n - 1)) * f0Scale;
        phase += f0 / SR;
        let x = phase >= 1 ? 1 : 0;
        if (phase >= 1) phase -= 1;
        x += (rng.u() - 0.5) * noise;
        for (let j = 0; j < 3; j++) { const [a, b, c] = res[j]; const y = a * x + b * st[j][0] + c * st[j][1]; st[j][1] = st[j][0]; st[j][0] = y; x = y; }
        const env = Math.min(1, i / (0.02 * SR), (n - i) / (0.02 * SR));
        out.push(x * env);
      }
      if (k < syllables.length - 1) { const g = Math.trunc(0.05 / tempo * SR); for (let i = 0; i < g; i++) out.push((rng.u() - 0.5) * noise); }
    });
    for (let i = 0; i < Math.trunc(0.08 * SR); i++) out.push(0);
    return out;
  }

  // ------------------------------------------------------------ features
  function fftPower(w) {
    const n = NFFT, re = w.slice(), im = new Array(n).fill(0);
    while (re.length < n) re.push(0);
    let j = 0;
    for (let i = 1; i < n; i++) { let bit = n >> 1; while (j & bit) { j ^= bit; bit >>= 1; } j |= bit; if (i < j) { const t = re[i]; re[i] = re[j]; re[j] = t; } }
    for (let size = 2; size <= n; size *= 2) {
      const ang = -2 * Math.PI / size;
      for (let start = 0; start < n; start += size) for (let k = 0; k < size / 2; k++) {
        const c = Math.cos(ang * k), s = Math.sin(ang * k), a = start + k, b = start + k + size / 2;
        const tr = re[b] * c - im[b] * s, ti = re[b] * s + im[b] * c;
        re[b] = re[a] - tr; im[b] = im[a] - ti; re[a] = re[a] + tr; im[a] = im[a] + ti;
      }
    }
    const out = []; for (let k = 0; k <= n / 2; k++) out.push(re[k] * re[k] + im[k] * im[k]);
    return out;
  }
  function smooth(pw, h) {
    h = h || 4; const n = pw.length, out = [];
    for (let k = 0; k < n; k++) { const a = Math.max(0, k - h), b = Math.min(n, k + h + 1); let s = 0; for (let i = a; i < b; i++) s += pw[i]; out.push(s / (b - a)); }
    return out;
  }
  function pitch(fr) {
    let top = 0; for (const v of fr) top = Math.max(top, Math.abs(v));
    if (top === 0) return null;
    const cl = 0.3 * top, y = fr.map(v => v > cl ? v - cl : (v < -cl ? v + cl : 0));
    const r = L => { let num = 0, a = 0, b = 0; for (let i = 0; i < FRAME - L; i++) { const u = y[i], v = y[i + L]; num += u * v; a += u * u; b += v * v; } return a > 0 && b > 0 ? num / Math.sqrt(a * b) : 0; };
    const lo = Math.floor(SR / 400), hi = Math.floor(SR / 70), rs = {};
    let best = -Infinity, bl = lo;
    for (let L = lo; L <= hi; L++) { rs[L] = r(L); if (rs[L] > best) { best = rs[L]; bl = L; } }
    if (best < 0.5) return null;
    for (let L = lo + 1; L < hi; L++)
      if (rs[L] >= 0.7 * best && rs[L] > 0.45 && rs[L] >= rs[L - 1] && rs[L] >= rs[L + 1])
        if (2 * L + 1 > hi || Math.max(rs[2 * L - 1], rs[2 * L], rs[2 * L + 1]) >= 0.6 * best) return SR / L;
    return SR / bl;
  }
  function features(x) {
    const out = [], win = [];
    for (let i = 0; i < FRAME; i++) win.push(0.5 - 0.5 * Math.cos(2 * Math.PI * i / (FRAME - 1)));
    const bins = []; for (let b = 0; b < 14; b++) { const bb = []; for (let k = 0; k <= NFFT / 2; k++) if (EDGES[b] <= k * SR / NFFT && k * SR / NFFT < EDGES[b + 1]) bb.push(k); bins.push(bb); }
    for (let s0 = 0; s0 + FRAME <= x.length; s0 += HOP) {
      const fr = x.slice(s0, s0 + FRAME);
      let e = 0; for (const v of fr) e += v * v; e /= FRAME;
      const pw = smooth(fftPower(fr.map((v, i) => v * win[i])));
      const prof = bins.map(bb => { let s = 0; for (const k of bb) s += pw[k]; return 10 * Math.log10(s / bb.length + 1e-12); });
      const m = prof.reduce((a, b) => a + b, 0) / prof.length;
      out.push({ db: 10 * Math.log10(e + 1e-12), f0: pitch(fr), prof: prof.map(q => q - m) });
    }
    const raw = out.map(f => f.f0);
    for (let i = 0; i < out.length; i++) { const w = raw.slice(Math.max(0, i - 1), i + 2).filter(v => v); out[i].f0 = raw[i] && w.length >= 2 ? median(w) : raw[i]; }
    return out;
  }
  function syllablesOf(F) {
    let top = -Infinity; for (const f of F) top = Math.max(top, f.db);
    const quiet = F.map(f => f.db).filter(d => d > -100).sort((a, b) => a - b);
    const floor = quiet.length ? quiet[Math.floor(quiet.length / 10)] : top - 60;
    const thr = Math.max(top - 32, floor + 0.4 * (top - floor));
    const on = F.map(f => f.db > thr).concat([false]), out = [];
    let start = null;
    on.forEach((v, i) => { if (v && start === null) start = i; else if (!v && start !== null) { if (i - start >= 3) out.push([start, i]); start = null; } });
    return out;
  }

  // ------------------------------------------------------------ comparison
  const dist = (p, q) => { let s = 0; for (let i = 0; i < p.length; i++) s += (p[i] - q[i]) * (p[i] - q[i]); return Math.sqrt(s / p.length); };
  const st = (f, ref) => 12 * Math.log(f / ref) / Math.log(2);
  function detrend(p) {
    const n = p.length, mx = (n - 1) / 2, my = p.reduce((a, b) => a + b, 0) / n;
    let sxx = 0, sxy = 0; for (let k = 0; k < n; k++) { sxx += (k - mx) * (k - mx); sxy += (k - mx) * (p[k] - my); }
    const b = sxy / sxx; return p.map((v, k) => v - my - b * (k - mx));
  }
  function shifted(p, sh) {
    const n = p.length, out = [];
    for (let k = 0; k < n; k++) { const x = Math.min(n - 1, Math.max(0, k + sh)), i = Math.min(n - 2, Math.trunc(x)), f = x - i; out.push(p[i] * (1 - f) + p[i + 1] * f); }
    return detrend(out);
  }
  function tractShift(model, learner) {
    let best = null, bs = 0;
    for (let k = -12; k <= 12; k++) { const sh = k / 10, d = median(model.map((m, i) => dist(m, shifted(learner[i], sh)))); if (best === null || d < best - 1e-12) { best = d; bs = sh; } }
    return bs;
  }
  function sylView(F, syl) {
    const voiced = []; syl.forEach(([a, b]) => { for (let i = a; i < b; i++) if (F[i].f0) voiced.push(F[i].f0); });
    const ref = voiced.length ? median(voiced) : null;
    const fold = f => { while (f > 1.6 * ref) f /= 2; while (f < ref / 1.6) f *= 2; return f; };
    return syl.map(([a, b]) => {
      const n = b - a, pts = [];
      [0.1, 0.3, 0.5, 0.7, 0.9].forEach(q => {
        const i = a + Math.min(n - 1, Math.trunc(q * n)), near = [];
        for (let j = Math.max(a, i - 1); j < Math.min(b, i + 2); j++) if (F[j].f0) near.push(fold(F[j].f0));
        pts.push(near.length && ref ? st(median(near), ref) : null);
      });
      const m0 = a + Math.trunc(0.2 * n), m1 = Math.max(a + Math.trunc(0.2 * n) + 1, a + Math.trunc(0.8 * n)), prof = [];
      for (let k = 0; k < 14; k++) { let s = 0; for (let i = m0; i < m1; i++) s += F[i].prof[k]; prof.push(s / (m1 - m0)); }
      return { n, pts, prof: detrend(prof) };
    });
  }
  function feedback(worst, k, vowels) {
    if (worst == null) return "Close to the model. Try it a little faster, or try the next drill.";
    const where = k != null ? "syllable " + (k + 1) + (vowels && k < vowels.length ? " ('" + vowels[k] + "')" : "") : "the phrase";
    return { melody: "The melody differs most on " + where + ": listen to whether the voice rises or falls there, and copy it.",
      vowels: "The vowel sound differs most on " + where + ": listen to the model's vowel there and shape your mouth to match.",
      rhythm: "The rhythm differs most on " + where + ": make it as long, compared with the others, as in the model." }[worst];
  }
  function compare(learner, model, vowels) {
    const FL = features(learner), FM = features(model), sl = syllablesOf(FL), sm = syllablesOf(FM);
    const none = () => { const o = {}; KEYS.forEach(k => { o[k] = null; }); return o; };
    if (sl.length !== sm.length)
      return { scores: none(), measured: none(), at: none(), syllables: [sm.length, sl.length], worst: "count",
        say: "The model has " + sm.length + " syllables and this recording " + sl.length + ": say each vowel clearly, with a short break between." };
    const VM = sylView(FM, sm), VL = sylView(FL, sl);
    const sh = tractShift(VM.map(v => v.prof), VL.map(v => v.prof));
    VL.forEach(v => { v.prof = shifted(v.prof, sh); });
    const tm = VM.reduce((a, v) => a + v.n, 0), tl = VL.reduce((a, v) => a + v.n, 0), per = { melody: [], vowels: [], rhythm: [] };
    VM.forEach((m, i) => {
      const l = VL[i], d = [];
      m.pts.forEach((x, j) => { const y = l.pts[j]; if (x != null && y != null) d.push(Math.abs(x - y)); });
      per.melody.push(d.length ? d.reduce((a, b) => a + b, 0) / d.length : 0);
      per.vowels.push(dist(m.prof, l.prof));
      per.rhythm.push(Math.abs(Math.log((l.n / tl) / (m.n / tm))));
    });
    const meas = {}, at = {}, score = {}, measured = {}, over = {};
    KEYS.forEach(k => { meas[k] = Math.max(...per[k]); at[k] = argmax(per[k]); score[k] = r1(Math.max(0, 100 * (1 - meas[k] / (2 * THRESH[k])))); measured[k] = r2(meas[k]); if (meas[k] > THRESH[k]) over[k] = meas[k] / THRESH[k]; });
    let worst = null; Object.keys(over).forEach(k => { if (worst === null || over[k] > over[worst]) worst = k; });
    return { scores: score, measured, at, syllables: [sm.length, sl.length], worst, say: feedback(worst, worst ? at[worst] : null, vowels) };
  }

  // ------------------------------------------------------------ the camera (optional)
  function mouthFeedback(trace, spans, vowels) {
    const rows = []; let worst = null;
    spans.forEach(([t0, t1], k) => {
      const fr = trace.filter(p => t0 <= p.t && p.t < t1);
      if (!fr.length) { rows.push({ syllable: k + 1, vowel: vowels[k], open: null, round: null, ok: null }); return; }
      const o = median(fr.map(p => p.open)), r = median(fr.map(p => p.round)), tg = MOUTH[vowels[k]];
      const dOpen = o - tg.open, dRound = r - tg.round, miss = Math.max(Math.abs(dOpen) / 0.15, Math.abs(dRound) / 0.25);
      rows.push({ syllable: k + 1, vowel: vowels[k], open: r2(o), round: r2(r), ok: miss <= 1 });
      if (miss > 1 && (worst === null || miss > worst[0])) worst = [miss, k, Math.abs(dOpen) / 0.15 >= Math.abs(dRound) / 0.25 ? "open" : "round", dOpen, dRound];
    });
    let say;
    if (worst === null) say = rows.some(r => r.ok) ? "Mouth shapes match the vowels." : "No face seen; check the light and the camera.";
    else { const [, k, what, dOpen, dRound] = worst, v = vowels[k];
      say = "On '" + v + "' (syllable " + (k + 1) + "), " + (what === "open" ? (dOpen < 0 ? "open your mouth more" : "open your mouth less") : (dRound < 0 ? "round your lips more" : "spread your lips, less rounded")) + "."; }
    return { rows, say };
  }
  function simMouth(rng, vowels, spans, fps, wrong) {
    fps = fps || 30; const out = [], end = spans[spans.length - 1][1] + 0.1;
    for (let t = 0; t < end; t += 1 / fps) {
      let v = null; spans.forEach(([a, b], k) => { if (a <= t && t < b) v = wrong && wrong[0] === k ? wrong[1] : vowels[k]; });
      const tg = v ? MOUTH[v] : { open: 0.05, round: 0.1 };
      out.push({ t, open: Math.max(0, tg.open + rng.gauss() * 0.08), round: Math.min(1, Math.max(0, tg.round + rng.gauss() * 0.12)) });
    }
    return out;
  }
  function learner(drill, kind, rng) {
    const syl = drill.syllables.map(s => Object.assign({}, s, { f0: s.f0.slice() }));
    let k = null;
    if (kind === "melody") { k = syl.length - 1; const [a, b] = syl[k].f0; syl[k].f0 = [a, a * Math.pow(2, (b > a ? -4 : 4) / 12)]; }
    else if (kind === "vowels") { k = Math.trunc(rng.u() * syl.length) % syl.length; syl[k].v = { a: "i", e: "u", i: "a", o: "i", u: "e" }[syl[k].v]; }
    else if (kind === "rhythm") { k = 0; for (let i = 1; i < syl.length; i++) if (syl[i].ms < syl[k].ms) k = i; syl[k].ms = Math.trunc(syl[k].ms * 2.2); }
    const f0s = Math.pow(2, (-3 + rng.u() * 9) / 12), fs = 0.92 + rng.u() * 0.2, tempo = 0.85 + rng.u() * 0.35;
    return [synth(syl, rng, f0s, fs, tempo, 0.02), k];
  }
  /* Resample browser audio (any rate, Float32Array) to 8 kHz by averaging: what the page passes to compare(). */
  function to8k(samples, rate) {
    const ratio = rate / SR, n = Math.floor(samples.length / ratio), out = new Array(n);
    for (let i = 0; i < n; i++) { const a = Math.floor(i * ratio), b = Math.max(a + 1, Math.floor((i + 1) * ratio)); let s = 0; for (let j = a; j < b; j++) s += samples[j]; out[i] = s / (b - a); }
    return out;
  }

  const api = { SR, VOWELS, MOUTH, THRESH, DRILLS, synth, features, syllablesOf, compare, feedback, mouthFeedback, simMouth, learner, to8k };
  if (node) module.exports = api; else root.RSOSPron = api;
})(typeof self !== "undefined" ? self : this);
