/* ATLAS, the trigger atlas and the transfer engine (spec/ATLAS.md), JavaScript implementation. Mirrors
 * rsso/rsso/atlas.py (identical results, tested): a person's triggers as a weighted network fitted by least squares
 * over sampled moments, with combinations, readiness, out-of-sample prediction, rerouting through the autonomy gate,
 * transfer to untreated triggers against a repeat mapping, the level sweep, and the glyph route. Needs
 * docs/js/peak.js, docs/js/trial.js and docs/js/gate.js. Browser: window.RSOSAtlas; Node: module.exports.
 */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const P = node ? require("./peak.js") : root.RSOSPeak;
  const T = node ? require("./trial.js") : root.RSOSTrial;
  const G = node ? require("./gate.js") : root.RSOSGate;
  const SENSES = ["sight", "sound", "smell", "taste", "touch", "place", "thought", "symbol", "person"];
  const SENSE_NAMES = { sight: "Sight", sound: "Sound", smell: "Smell", taste: "Taste", touch: "Touch", place: "Place", thought: "Thought",
    symbol: "Symbol", person: "Person", combo: "Combination", higher: "Higher node" };
  const PHASES = ["map", "map2", "after"], METHODS = ["network", "timeline", "sham", "none"], MARGIN = 1, READY = 1;
  const HIGHER = [
    { id: "words", dim: "abstraction", rank: 1, label: "The words for the feeling" },
    { id: "agency", dim: "abstraction", rank: 2, label: "The one who chooses" },
    { id: "identity", dim: "abstraction", rank: 3, label: "Who you are" },
    { id: "values", dim: "abstraction", rank: 4, label: "What matters to you" },
    { id: "meaning", dim: "abstraction", rank: 5, label: "What your life is for" },
    { id: "room", dim: "scope", rank: 1, label: "The room you are in" },
    { id: "city", dim: "scope", rank: 2, label: "The whole city" },
    { id: "country", dim: "scope", rank: 3, label: "The whole country" },
    { id: "world", dim: "scope", rank: 4, label: "The whole world" },
    { id: "all", dim: "scope", rank: 5, label: "All living things" },
  ];
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const r2 = x => (x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100);
  const sum = xs => { let s = 0; for (const x of xs) s += x; return s; };
  const mean = xs => sum(xs) / xs.length;
  const vr = xs => { if (xs.length < 2) return 0; const m = mean(xs); let s = 0; for (const x of xs) s += (x - m) * (x - m); return s / (xs.length - 1); };
  function ciDiff(a, b) {
    const d = mean(a) - mean(b);
    if (a.length < 2 || b.length < 2) return [d, null, null];
    const va = vr(a) / a.length, vb = vr(b) / b.length, se = Math.sqrt(va + vb);
    if (se === 0) return [d, d, d];
    const den = va * va / (a.length - 1) + vb * vb / (b.length - 1);
    const df = den > 0 ? Math.max(1, Math.floor((va + vb) * (va + vb) / den)) : a.length + b.length - 2;
    const h = T.tcrit(df) * se; return [d, d - h, d + h];
  }

  // ------------------------------------------------------------ the atlas
  const makeAtlas = (id, state, created) => ({ schema: "rsos-atlas/1", id, state: state || "Stress", created: created || 0, nodes: [], exposures: [], treatments: [], sweep: [], routes: [] });
  function addNode(a, id, label, sense) {
    if (!SENSES.includes(sense)) throw new Error("sense must be one of " + SENSES.join(", "));
    if (a.nodes.some(n => n.id === id)) throw new Error("a node with this id exists");
    const n = { id, label, sense }; a.nodes.push(n); return n;
  }
  function addCombo(a, id, of, label) {
    const ids = new Set(a.nodes.filter(n => n.sense !== "combo").map(n => n.id));
    if (of.length < 2 || of.some(x => !ids.has(x))) throw new Error("a combination joins two or more existing nodes");
    const n = { id, label: label || of.join(" + "), sense: "combo", of: of.slice() }; a.nodes.push(n); return n;
  }
  function expose(a, ts, nodes, before, after, phase) {
    phase = phase || "map"; if (!PHASES.includes(phase)) throw new Error("phase must be one of " + PHASES.join(", "));
    const e = { ts, nodes: nodes.slice(), before, after, phase }; a.exposures.push(e); return e;
  }
  const shift = e => e.after - e.before;
  const present = (e, n) => (n.sense === "combo" ? n.of.every(x => e.nodes.includes(x)) : e.nodes.includes(n.id));

  function inverse(M) {
    const n = M.length;
    let A = M.map((row, i) => row.map((x, j) => x + (i === j ? 1e-6 : 0)).concat(Array.from({ length: n }, (_, k) => (k === i ? 1 : 0))));
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      const tmp = A[c]; A[c] = A[p]; A[p] = tmp;
      const piv = A[c][c]; A[c] = A[c].map(x => x / piv);
      for (let r = 0; r < n; r++) if (r !== c && A[r][c] !== 0) { const f = A[r][c], rc = A[c]; A[r] = A[r].map((x, j) => x - f * rc[j]); }
    }
    return A.map(row => row.slice(n));
  }
  function fit(a, phase) {
    phase = phase || "map";
    const ex = a.exposures.filter(e => e.phase === phase), cols = a.nodes.filter(n => ex.some(e => present(e, n)));
    const X = ex.map(e => [1].concat(cols.map(n => (present(e, n) ? 1 : 0)))), y = ex.map(e => shift(e));
    const p = cols.length + 1, m = ex.length;
    if (m < p + 2) return { cols, beta: null, se: null, df: m - p, loo: null, y, base: null };
    const XtX = [], Xty = [];
    for (let i = 0; i < p; i++) { XtX.push([]); for (let j = 0; j < p; j++) { let s = 0; for (let k = 0; k < m; k++) s += X[k][i] * X[k][j]; XtX[i].push(s); } }
    for (let i = 0; i < p; i++) { let s = 0; for (let k = 0; k < m; k++) s += X[k][i] * y[k]; Xty.push(s); }
    const inv = inverse(XtX), beta = [];
    for (let i = 0; i < p; i++) { let s = 0; for (let j = 0; j < p; j++) s += inv[i][j] * Xty[j]; beta.push(s); }
    const res = []; for (let k = 0; k < m; k++) { let s = 0; for (let i = 0; i < p; i++) s += X[k][i] * beta[i]; res.push(y[k] - s); }
    const df = m - p; let ss = 0; for (const r of res) ss += r * r; const s2 = ss / df;
    const se = []; for (let i = 0; i < p; i++) se.push(Math.sqrt(Math.max(0, s2 * inv[i][i])));
    const loo = [];
    for (let k = 0; k < m; k++) {
      let h = 0; for (let i = 0; i < p; i++) { let s = 0; for (let j = 0; j < p; j++) s += inv[i][j] * X[k][j]; h += X[k][i] * s; }
      loo.push(h < 0.999 ? y[k] - res[k] / (1 - h) : null);
    }
    return { cols, beta, se, df, loo, y, base: beta[0], ex };
  }
  function raw(a, phase) {
    const F = fit(a, phase), out = {}; if (F.beta === null) return out;
    F.cols.forEach((n, k) => { out[n.id] = [F.beta[k + 1], F.se[k + 1], F.df]; }); return out;
  }
  function weights(a, phase) {
    phase = phase || "map";
    const F = fit(a, phase), ex = a.exposures.filter(e => e.phase === phase), out = {};
    a.nodes.forEach(n => {
      const cnt = ex.filter(e => present(e, n)).length, i = F.beta === null ? -1 : F.cols.indexOf(n);
      if (i < 0) { out[n.id] = { n: cnt, weight: null, lo: null, hi: null, verdict: "too_few", ready: false, need: 3 }; return; }
      const w = F.beta[i + 1], se = F.se[i + 1], t = T.tcrit(F.df), lo = w - t * se, hi = w + t * se;
      const verdict = cnt < 3 ? "too_few" : lo > 0 ? "trigger" : hi < 0 ? "soothing" : (lo > -MARGIN && hi < MARGIN) ? "none" : "unclear";
      const need = t * se <= READY ? cnt : Math.ceil(cnt * (t * se / READY) * (t * se / READY));
      out[n.id] = { n: cnt, weight: r1(w), lo: r1(lo), hi: r1(hi), verdict, ready: cnt >= 3 && t * se <= READY, need: Math.max(3, need) };
    });
    return out;
  }
  function combos(a, phase) {
    const W = weights(a, phase), out = [];
    a.nodes.forEach(n => {
      if (n.sense !== "combo") return;
      const w = W[n.id], res = { id: n.id, of: n.of, n: w.n, interaction: w.weight, lo: w.lo, hi: w.hi, verdict: "too_few" };
      if (w.verdict !== "too_few") {
        const partsTrigger = n.of.some(x => W[x].verdict === "trigger");
        res.verdict = w.lo > 0 ? (partsTrigger ? "together_more" : "only_together") : w.hi < 0 ? "together_less" : "additive";
      }
      out.push(res);
    });
    return out;
  }
  function edges(a, phase, minShare) {
    phase = phase || "map"; minShare = minShare === undefined ? 0.2 : minShare;
    const ids = a.nodes.filter(n => n.sense !== "combo").map(n => n.id);
    const ex = a.exposures.filter(e => e.phase === phase && e.nodes.length).map(e => new Set(e.nodes)), out = [];
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
      const x = ids[i], y = ids[j]; let both = 0, either = 0;
      ex.forEach(s => { if (s.has(x) && s.has(y)) both++; if (s.has(x) || s.has(y)) either++; });
      if (both && both / either >= minShare) out.push({ a: x, b: y, share: r2(both / either), n: both });
    }
    return out;
  }
  function readiness(a, phase) {
    phase = phase || "map";
    const W = weights(a, phase), real = a.nodes.filter(n => n.sense !== "combo"), ex = a.exposures.filter(e => e.phase === phase);
    const by = {}; SENSES.forEach(s => { let c = 0; ex.forEach(e => real.forEach(n => { if (n.sense === s && e.nodes.includes(n.id)) c++; })); by[s] = c; });
    const ready = real.filter(n => W[n.id].ready).map(n => n.id);
    const nxt = real.filter(n => !W[n.id].ready).sort((p, q) => {
      const a1 = W[p.id].n - W[p.id].need, b1 = W[q.id].n - W[q.id].need; return a1 !== b1 ? a1 - b1 : (p.id < q.id ? -1 : p.id > q.id ? 1 : 0); }).slice(0, 5);
    const controls = ex.filter(e => !e.nodes.length).length;
    const say = ready.length + " of " + real.length + " nodes have a stable weight. " +
      (controls < 5 ? "Add control moments (nothing in particular present): at least five. " : "") +
      (nxt.length ? "Sample next: " + nxt.map(n => n.label).join(", ") + "." : "The map is ready.");
    return { nodes: real.length, ready: ready.length, moments: ex.length, controls, by_sense: by, missing_senses: SENSES.filter(s => by[s] === 0),
      next: nxt.map(n => n.id), say };
  }
  function predict(a, phase) {
    const F = fit(a, phase || "map");
    if (F.beta === null || F.y.length < 10) return { n: F.y.length, r: null, mae: null, mae_null: null, verdict: "too_few",
      say: "More sampled moments are needed to test the map: at least two more than its nodes, and ten in all." };
    const m = F.y.length, tot = sum(F.y), real = [], pred = [], nul = [];
    for (let k = 0; k < m; k++) { if (F.loo[k] === null) continue; real.push(F.y[k]); pred.push(F.loo[k]); nul.push((tot - F.y[k]) / (m - 1)); }
    const mae = mean(real.map((x, i) => Math.abs(x - pred[i]))), mae0 = mean(real.map((x, i) => Math.abs(x - nul[i])));
    const mx = mean(real), my = mean(pred); let sxy = 0, sxx = 0, syy = 0;
    for (let i = 0; i < real.length; i++) sxy += (real[i] - mx) * (pred[i] - my);
    for (const x of real) sxx += (x - mx) * (x - mx);
    for (const y of pred) syy += (y - my) * (y - my);
    const r = sxx > 0 && syy > 0 ? sxy / Math.sqrt(sxx * syy) : 0;
    const verdict = mae <= 0.9 * mae0 && r >= 0.3 ? "predicts" : "does_not_predict";
    const say = verdict === "predicts" ? "The map predicts moments it has not seen: error " + r1(mae) + " points against " + r1(mae0) + " without it (r = " + r2(r) + ")."
      : "The map does not yet predict new moments better than the average (error " + r1(mae) + " against " + r1(mae0) + ").";
    return { n: real.length, r: r2(r), mae: r1(mae), mae_null: r1(mae0), verdict, say };
  }

  // ------------------------------------------------------------ rerouting
  function reroute(a, presentIds, anchors, offers, now, optins, history, consents, threshold) {
    threshold = threshold === undefined ? 2 : threshold;
    const W = weights(a);
    const hits = presentIds.filter(n => W[n] && W[n].verdict === "trigger" && W[n].weight >= threshold)
      .sort((p, q) => (W[q].weight - W[p].weight) || (p < q ? -1 : p > q ? 1 : 0));
    if (!hits.length) return { action: "none", trigger: null, weight: null, anchor: null, reasons: ["no high-weight trigger present"] };
    const trig = hits[0], ranked = [];
    anchors.forEach(an => { const s = P.strength(an); if (s.status === "strong" || s.status === "present") ranked.push([-(s.estimate || 0), an.id, an]); });
    ranked.sort((p, q) => (p[0] - q[0]) || (p[1] < q[1] ? -1 : p[1] > q[1] ? 1 : 0));
    if (!ranked.length) return { action: "none", trigger: trig, weight: W[trig].weight, anchor: null, reasons: ["no anchor with a proven effect"] };
    const reasons = [];
    for (const [, aid, an] of ranked) {
      const h = (history || {})[aid]; let d = null;
      for (const mode of ["auto", "suggest"]) {
        d = G.mayFire(an, mode, offers || [], now || 0, optins, h, consents);
        if (d.decision === "allow") return { action: mode === "auto" ? "fire" : "suggest", trigger: trig, weight: W[trig].weight, anchor: aid, reasons: [], flag: d.flag };
      }
      reasons.push(aid + ": " + d.reasons.join("; "));
    }
    return { action: "none", trigger: trig, weight: W[trig].weight, anchor: null, reasons };
  }

  // ------------------------------------------------------------ the transfer engine
  function chooseNode(a, by, phase) {
    if (by === "level") return sweepReport(a).best;
    const W = weights(a, phase || "map");
    const cand = a.nodes.filter(n => n.sense !== "combo" && W[n.id].verdict === "trigger").map(n => n.id)
      .sort((p, q) => (W[q].weight - W[p].weight) || (p < q ? -1 : p > q ? 1 : 0));
    return cand.length ? cand[0] : null;
  }
  function addTreatment(a, ts, nodeId, method, note) {
    method = method || "network"; if (!METHODS.includes(method)) throw new Error("method must be one of " + METHODS.join(", "));
    const t = { ts, node: nodeId, method, note: note || "" }; a.treatments.push(t); return t;
  }
  function transfer(a, treated) {
    const W0 = weights(a, "map"), R0 = raw(a, "map"), R2 = raw(a, "map2"), R3 = raw(a, "after");
    const controlled = a.exposures.some(e => e.phase === "map2"), base = controlled ? R2 : R0;
    const reactive = a.nodes.filter(n => n.sense !== "combo" && W0[n.id].verdict === "trigger").map(n => n.id);
    const pairs = reactive.filter(i => i in R0 && i in R2).map(i => [R0[i][0], R2[i][0]]);
    const sx = sum(pairs.map(p => p[0])), sy = sum(pairs.map(p => p[1]));
    let drift = controlled && pairs.length && sx > 0 ? sy / sx : 1; drift = Math.max(0, Math.min(1.5, drift));
    const change = i => (!(i in base) || !(i in R3) ? null
      : [R3[i][0] - base[i][0] * drift, R3[i][1] * R3[i][1] + (drift * base[i][1]) * (drift * base[i][1]), Math.min(R3[i][2], base[i][2])]);
    const tc = treated in W0 ? change(treated) : null, tr = tc ? tc[0] : null;
    const un = reactive.filter(i => i !== treated).map(i => [i, change(i)]).filter(x => x[1] !== null);
    const out = { treated, controlled, drift: r2(drift), treated_change: r1(tr), untreated: un.map(([i, c]) => ({ id: i, change: r1(c[0]) })),
      mean: null, lo: null, hi: null, ratio: null, verdict: "too_few" };
    if (tr === null || un.length < 2) { out.say = "Map before treatment, ideally twice, then again after it, with at least two other triggers in the map."; return out; }
    const m = mean(un.map(x => x[1][0])), se = Math.sqrt(sum(un.map(x => x[1][1]))) / un.length;
    const t = T.tcrit(Math.max(1, Math.min(...un.map(x => x[1][2])))), lo = m - t * se, hi = m + t * se;
    out.mean = r1(m); out.lo = r1(lo); out.hi = r1(hi);
    if (tr < 0) out.ratio = r2(m / tr);
    let say;
    if (tr >= -MARGIN) { out.verdict = "no_change"; say = "The treated node itself did not change by a point or more."; }
    else if (hi < 0) { out.verdict = "spreads"; say = "The change spread: untreated triggers fell by " + r1(-m) + (r1(-m) === 1 ? " point" : " points") + " on average [" + r1(-hi) + ", " + r1(-lo) + "], " + r1(m / tr * 100) + "% of the treated node's change."; }
    else if (lo > -MARGIN / 2 && hi < MARGIN / 2) { out.verdict = "stays"; say = "The change stayed on the treated node: untreated triggers moved by less than half a point."; }
    else { out.verdict = "unclear"; say = "Not clear yet whether the change spread; map more moments after treatment."; }
    out.say = say + (controlled ? "" : " Without a repeat mapping before treatment, part of this may be habituation.");
    return out;
  }

  // ------------------------------------------------------------ the level sweep
  function addSweep(a, ts, higher, change) {
    if (!HIGHER.some(h => h.id === higher)) throw new Error("unknown higher node");
    const s = { ts, higher, change }; a.sweep.push(s); return s;
  }
  function sweepReport(a) {
    const out = { dims: {}, best: null }; let best = null;
    const above = (p, q) => { const c = ciDiff(p.xs, q.xs); return c[1] !== null && c[1] > 0; };
    const pub = p => ({ id: p.id, rank: p.rank, n: p.n, benefit: p.benefit });
    ["abstraction", "scope"].forEach(dim => {
      const pts = HIGHER.filter(h => h.dim === dim).map(h => {
        const xs = a.sweep.filter(s => s.higher === h.id).map(s => -s.change);
        return { id: h.id, rank: h.rank, n: xs.length, benefit: xs.length ? r1(mean(xs)) : null, xs };
      });
      const ok = pts.filter(p => p.n >= 2); let shape = "too_few";
      if (ok.length >= 3) {
        let top = ok[0]; ok.forEach(p => { const a1 = mean(p.xs), b1 = mean(top.xs); if (a1 > b1 || (a1 === b1 && -p.rank > -top.rank)) top = p; });
        let loEnd = ok[0], hiEnd = ok[0]; ok.forEach(p => { if (p.rank < loEnd.rank) loEnd = p; if (p.rank > hiEnd.rank) hiEnd = p; });
        if (best === null || mean(top.xs) > best[0]) best = [mean(top.xs), top.id];
        if (top === hiEnd && above(top, loEnd)) shape = "rises";
        else if (top === loEnd && above(top, hiEnd)) shape = "falls";
        else if (top !== loEnd && top !== hiEnd && above(top, loEnd) && above(top, hiEnd)) shape = "peaks";
        else shape = "flat";
        out.dims[dim] = { points: pts.map(pub), shape, top: top.id };
      } else out.dims[dim] = { points: pts.map(pub), shape, top: null };
    });
    const dimOf = s => HIGHER.find(h => h.id === s.higher).dim;
    const ab = a.sweep.filter(s => dimOf(s) === "abstraction").map(s => -s.change), sc = a.sweep.filter(s => dimOf(s) === "scope").map(s => -s.change);
    if (ab.length >= 2 && sc.length >= 2) { const [d, lo, hi] = ciDiff(ab, sc); out.abstraction_minus_scope = { difference: r1(d), lo: r1(lo), hi: r1(hi) }; }
    else out.abstraction_minus_scope = null;
    out.best = best ? best[1] : null;
    const names = { rises: "rises with the level", falls: "falls as the level rises", peaks: "peaks in the middle", flat: "shows no clear shape yet",
      too_few: "needs two sessions at three or more levels" };
    out.say = "By abstraction, the benefit " + names[out.dims.abstraction.shape] + "; by scope, it " + names[out.dims.scope.shape] + ".";
    return out;
  }

  // ------------------------------------------------------------ the glyph route
  const glyphRoute = (glyphs, start, length) => glyphs.slice(start || 0, (start || 0) + (length === undefined ? 12 : length));
  function addRouteWalk(a, ts, start, length, results) {
    const w = { ts, start, length, results: results.map(r => ({ pos: r.pos, ok: !!r.ok, ms: r.ms === undefined ? null : r.ms })) }; a.routes.push(w); return w;
  }
  function routeReport(a) {
    const ws = a.routes.slice().sort((p, q) => p.ts - q.ts);
    const walks = ws.map((w, i) => {
      const n = w.results.length, ok = w.results.filter(r => r.ok).length, ms = w.results.filter(r => r.ok && r.ms !== null).map(r => r.ms).sort((p, q) => p - q);
      const med = !ms.length ? null : ms.length % 2 ? ms[(ms.length - 1) / 2] : (ms[ms.length / 2 - 1] + ms[ms.length / 2]) / 2;
      return { walk: i + 1, accuracy: n ? r1(ok / n * 100) : null, median_ms: r1(med) };
    });
    const acc = walks.filter(w => w.accuracy !== null).map(w => w.accuracy);
    const say = !walks.length ? "Walk the route to start." : walks.length + " walks; the last recalled " + acc[acc.length - 1] + "% of the route" + (acc.length > 1 ? ", up from " + acc[0] + "% on the first." : ".");
    return { walks, say };
  }

  // ------------------------------------------------------------ simulation with known answers
  function SimWorld(seed, nNodes, nTriggers, strength, noise, interaction) {
    this.rng = new P.Rng(seed === undefined ? 1 : seed); this.n = nNodes || 12; this.noise = noise === undefined ? 1.5 : noise;
    nTriggers = nTriggers === undefined ? 4 : nTriggers; strength = strength === undefined ? 3 : strength;
    this.w = []; for (let i = 0; i < this.n; i++) this.w.push(i < nTriggers ? strength * (0.6 + 0.8 * this.rng.u()) : 0);
    this.pair = [nTriggers, nTriggers + 1]; this.inter = interaction === undefined ? 3 : interaction;
  }
  SimWorld.prototype.atlas = function () {
    const a = makeAtlas("sim", "Stress");
    for (let i = 0; i < this.n; i++) addNode(a, "n" + i, "Node " + i, SENSES[i % SENSES.length]);
    addCombo(a, "pair", ["n" + this.pair[0], "n" + this.pair[1]]); return a;
  };
  SimWorld.prototype.moment = function (a, ts, phase, scale) {
    const u = this.rng.u(); let nodes;
    if (u < 0.2) nodes = [];
    else if (u < 0.32) nodes = this.pair.slice();
    else {
      const k = Math.floor(this.rng.u() * this.n); nodes = [k];
      if (this.rng.u() < 0.3) { const j = Math.floor(this.rng.u() * this.n); if (j !== k) nodes.push(j); }
    }
    let sh = 0; for (const k of nodes) sh += this.w[k] * (scale ? scale[k] : 1);
    if (nodes.includes(this.pair[0]) && nodes.includes(this.pair[1])) sh += this.inter * (scale ? scale[this.pair[0]] : 1);
    const before = 2 + Math.floor(this.rng.u() * 4);
    const after = Math.max(0, Math.min(10, Math.floor(before + sh + this.rng.gauss() * this.noise + 0.5)));
    expose(a, ts, nodes.map(k => "n" + k), before, after, phase);
  };
  SimWorld.prototype.sample = function (a, days, perDay, phase, t0, scale) {
    perDay = perDay || 10; phase = phase || "map"; t0 = t0 || 0;
    for (let d = 0; d < days; d++) for (let k = 0; k < perDay; k++) this.moment(a, t0 + d * 86400 + k * 5400, phase, scale);
  };
  function simDemo(seed, days) { const s = new SimWorld(seed); const a = s.atlas(); s.sample(a, days || 14); return { atlas: a, truth: s.w.slice(), pair: s.pair.slice(), interaction: s.inter }; }

  const api = { SENSES, SENSE_NAMES, PHASES, METHODS, MARGIN, READY, HIGHER, makeAtlas, addNode, addCombo, expose, fit, weights, combos, edges,
    readiness, predict, reroute, chooseNode, addTreatment, transfer, addSweep, sweepReport, glyphRoute, addRouteWalk, routeReport, SimWorld, simDemo };
  if (node) module.exports = api; else root.RSOSAtlas = api;
})(typeof self !== "undefined" ? self : this);
