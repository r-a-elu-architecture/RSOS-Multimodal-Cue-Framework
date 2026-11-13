/* TRIAL — personal randomised experiments, JavaScript implementation (spec/TRIAL.md). Mirrors rsso/rsso/trial.py
 * (identical results, tested): designs, permuted-block schedules, session records, analysis with Welch intervals,
 * permutation p-values, adjustment for session order and sleep, pooling across people, consistency, simulated people.
 * Needs docs/js/peak.js (the shared seeded generator). Browser: window.RSOSTrial; Node: module.exports.
 */
(function (root) {
  "use strict";
  const PEAK = typeof module !== "undefined" && module.exports ? require("./peak.js") : root.RSOSPeak;
  const Rng = PEAK.Rng;
  const DESIGNS = {
    anchor_vs_sham: { title: "Real anchor or sham", arms: ["anchor", "sham"], reference: "sham",
      arm_names: { anchor: "Your anchor's code", sham: "A sham code, never paired" },
      outcome: "Calm, 0-10", items: [1, 33], claims: ["C2", "C10", "C12"],
      do: "Play the code you are given, then rate calm again after a minute." },
    cue_vs_none: { title: "Cue or no cue", arms: ["cue", "none"], reference: "none",
      arm_names: { cue: "Play your anchor when stress starts", none: "Notice the stress, play nothing" },
      outcome: "Calm, 0-10", items: [1, 33], claims: ["C1", "C12"],
      do: "When you notice stress, do what the session says, then rate calm after two minutes." },
    auto_vs_manual: { title: "Automatic or by hand", arms: ["auto", "manual"], reference: "manual",
      arm_names: { auto: "The device fires the anchor", manual: "You fire the anchor yourself" },
      outcome: "Calm, 0-10", items: [26, 33], claims: ["C40"],
      do: "Practise as the session says, then rate calm." },
    order_ct_identity: { title: "Core Transformation and identity: which order", reference: "identity_first",
      arms: ["ct_first", "identity_peak_first", "hybrid", "identity_first"],
      arm_names: { ct_first: "Core Transformation, then identity, future-pacing, action",
        identity_peak_first: "Identity peak, then Core Transformation, future-pacing, action",
        hybrid: "A short Core Transformation, identity, then a deeper Core Transformation",
        identity_first: "Identity fully, then Core Transformation" },
      outcome: "Calm, 0-10", items: [52, 53], claims: ["C85", "C88"],
      do: "Run the session in the order given, then rate calm and how strongly you felt the identity." },
    ssit: { title: "Higher-level imagery (SSIT)", arms: ["higher", "local", "calm"], reference: "calm",
      arm_names: { higher: "Imagery about a level above the problem, flowing down",
        local: "Imagery about the activity itself becoming easy", calm: "General calming imagery" },
      outcome: "Ease of an untrained activity, 0-10", items: [63, 64], claims: ["C97", "C101"],
      do: "Do the imagery you are given for five minutes, then rate how easy an activity you did not imagine feels." },
    identity_language: { title: "An identity in another language", arms: ["other", "own"], reference: "own",
      arm_names: { other: "Practise the identity in its own language (one you are learning)",
        own: "Practise the identity in your first language" },
      outcome: "How true the identity feels, 0-10", items: [24, 51], claims: ["C82"],
      do: "Run the identity session in the language given, then rate how true the identity feels." },
    network_vs_timeline: { title: "Network trance or a timeline", arms: ["network", "timeline"], reference: "timeline",
      arm_names: { network: "The network trance: descend to the strongest trigger and transform it",
        timeline: "A timeline session: float back above the first event and release it" },
      outcome: "Calm while picturing an untreated trigger, 0-10", items: [60, 63], claims: ["C94", "C95"],
      do: "Run the session given, then picture one trigger you did not work on and rate how calm you feel, before and after." },
    rhythm_focus: { title: "A vibration rhythm for focus", arms: ["rhythm", "plain"], reference: "plain",
      arm_names: { rhythm: "Wristband vibration pulsing 12 times a second for five minutes",
        plain: "The same vibration with no rhythm (the motor's own), same strength and time" },
      outcome: "2-back score after five minutes, in tenths (0-10)", items: [29], claims: ["C35"],
      do: "Wear the band during five minutes of reading, then do the 2-back test on the Checks page and enter the score divided by ten, rounded." },
    agent_values: { title: "An agent with values or without", arms: ["gated", "plain"], reference: "plain",
      arm_names: { gated: "The agent checks each action against its values and asks when unsure",
        plain: "The same agent acting without the value check" },
      outcome: "How much you trust the agent, 0-10", items: [42, 44], claims: ["C70", "C72"],
      do: "Work with the agent on the task given for ten minutes, then rate how much you trust it and how much it cared about you." },
    pronunciation_feedback: { title: "Pronunciation feedback or listening only", arms: ["feedback", "listen"], reference: "listen",
      arm_names: { feedback: "Practise drills with the feedback on the Devices page",
        listen: "Practise the same drills by listening and repeating, no feedback" },
      outcome: "Clarity rated by a listener who does not know the arm, 0-10", items: [10], claims: ["C14"],
      do: "Practise for ten minutes as given, then record one test phrase; a listener rates it later without knowing the arm." },
  };
  const COVARIATES = ["sleep_h", "caffeine", "exercise", "hour"], ADJUST = ["sleep_h"], PERMUTATIONS = 1000;
  const T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
    2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042];
  const tcrit = df => (df >= 1 && df <= 30 ? T95[df - 1] : 1.96);
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const r2 = x => (x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100);
  const r3 = x => (x === null || x === undefined ? null : Math.floor(x * 1000 + 0.5) / 1000);
  function num(v) { if (v === null || v === undefined || v === "" || typeof v === "boolean") return null; const x = Number(v); return Number.isFinite(x) ? x : null; }
  const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;
  function variance(xs) { if (xs.length < 2) return 0; const m = mean(xs); return xs.reduce((s, x) => s + (x - m) * (x - m), 0) / (xs.length - 1); }

  function shuffle(xs, rng) {
    xs = xs.slice();
    for (let i = xs.length - 1; i > 0; i--) { const j = Math.floor(rng.u() * (i + 1)); const t = xs[i]; xs[i] = xs[j]; xs[j] = t; }
    return xs;
  }
  function schedule(design, blocks, seed) {
    const arms = DESIGNS[design].arms, rng = new Rng(seed); let out = [];
    for (let b = 0; b < blocks; b++) out = out.concat(shuffle(arms, rng));
    return out;
  }
  function newTrial(design, blocks, seed, id, created) {
    return { schema: "rsos-trial/1", id: id || "t1", design, blocks, seed, created: created || 0, schedule: schedule(design, blocks, seed), sessions: [] };
  }
  function record(trial, before, after, cov, ts) {
    const i = trial.sessions.length;
    if (i >= trial.schedule.length) return null;
    const s = { i, arm: trial.schedule[i], ts: ts || 0, before: r1(Number(before)), after: r1(Number(after)), cov: {} };
    COVARIATES.forEach(k => { const x = num((cov || {})[k]); if (x !== null) s.cov[k] = x; });
    trial.sessions.push(s);
    return s;
  }

  function solve(A, b) {
    const n = A.length, M = A.map((row, i) => row.slice().concat([b[i]]));
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      if (Math.abs(M[p][c]) < 1e-12) return null;
      const t = M[c]; M[c] = M[p]; M[p] = t;
      for (let r = 0; r < n; r++) {
        if (r === c) continue;
        const f = M[r][c] / M[c][c];
        for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k];
      }
    }
    return M.map((row, i) => row[n] / row[i]);
  }
  function ols(X, y) {
    const n = X.length, p = X[0].length;
    if (n <= p) return null;
    const XtX = [], Xty = [];
    for (let i = 0; i < p; i++) { XtX.push([]); for (let j = 0; j < p; j++) { let s = 0; for (let r = 0; r < n; r++) s += X[r][i] * X[r][j]; XtX[i].push(s); } }
    for (let i = 0; i < p; i++) { let s = 0; for (let r = 0; r < n; r++) s += X[r][i] * y[r]; Xty.push(s); }
    const beta = solve(XtX, Xty); if (beta === null) return null;
    let ss = 0; for (let r = 0; r < n; r++) { let f = 0; for (let j = 0; j < p; j++) f += X[r][j] * beta[j]; const e = y[r] - f; ss += e * e; }
    const s2 = ss / (n - p), se = [];
    for (let j = 0; j < p; j++) { const unit = []; for (let k = 0; k < p; k++) unit.push(k === j ? 1 : 0); const col = solve(XtX, unit); se.push(Math.sqrt(Math.max(0, s2 * col[j]))); }
    return { beta, se, df: n - p };
  }
  function permP(a, b, seed) {
    const obs = Math.abs(mean(a) - mean(b)), pool = a.concat(b), na = a.length, rng = new Rng(seed === undefined ? 12345 : seed);
    let hit = 0;
    for (let k = 0; k < PERMUTATIONS; k++) { const sh = shuffle(pool, rng); if (Math.abs(mean(sh.slice(0, na)) - mean(sh.slice(na))) >= obs - 1e-12) hit++; }
    return (hit + 1) / (PERMUTATIONS + 1);
  }
  function fmt(x) {
    const k = Math.floor(Math.abs(x) * 100 + 0.5); let s = Math.floor(k / 100) + "." + String(k % 100).padStart(2, "0");
    s = s.replace(/0+$/, "").replace(/\.$/, "");
    return (x < 0 && k ? "-" : "") + s;
  }
  function analyze(trial) {
    const d = DESIGNS[trial.design], ref = d.reference;
    const S = trial.sessions.filter(s => num(s.before) !== null && num(s.after) !== null);
    const chg = {}; d.arms.forEach(a => { chg[a] = S.filter(s => s.arm === a).map(s => s.after - s.before); });
    const out = { design: trial.design, title: d.title, outcome: d.outcome, reference: ref, sessions: S.length,
      planned: trial.schedule.length, arms: [], contrasts: [], balance: {}, adjusted: null };
    d.arms.forEach(a => { const xs = chg[a]; out.arms.push({ arm: a, name: d.arm_names[a], n: xs.length, mean: xs.length ? r2(mean(xs)) : null, sd: xs.length >= 2 ? r2(Math.sqrt(variance(xs))) : null }); });
    d.arms.forEach(a => {
      if (a === ref) return;
      const xa = chg[a], xr = chg[ref];
      const c = { arm: a, against: ref, n: xa.length, n_ref: xr.length, diff: null, lo: null, hi: null, p: null };
      if (xa.length && xr.length) {
        const diff = mean(xa) - mean(xr); c.diff = r2(diff);
        if (xa.length >= 2 && xr.length >= 2) {
          const va = variance(xa) / xa.length, vr = variance(xr) / xr.length, se = Math.sqrt(va + vr);
          const den = (xa.length > 1 ? va * va / (xa.length - 1) : 0) + (xr.length > 1 ? vr * vr / (xr.length - 1) : 0);
          const df = den > 0 ? Math.floor((va + vr) * (va + vr) / den) : Math.min(xa.length, xr.length) - 1;
          const h = tcrit(Math.max(df, 1)) * se;
          c.lo = r2(diff - h); c.hi = r2(diff + h); c.se = r3(se); c.p = r3(permP(xa, xr));
        }
      }
      if (xa.length < 3 || xr.length < 3) { c.verdict = "too_few"; c.say = "Too few sessions yet: three or more in each arm give an answer."; }
      else if (c.lo !== null && c.lo > 0) { c.verdict = "better"; c.say = d.arm_names[a] + " works better for you, by " + fmt(c.diff) + " points."; }
      else if (c.hi !== null && c.hi < 0) { c.verdict = "worse"; c.say = d.arm_names[ref] + " works better for you, by " + fmt(-c.diff) + " points."; }
      else { c.verdict = "unclear"; c.say = "No clear difference yet. More sessions make the interval narrower."; }
      out.contrasts.push(c);
    });
    const present = COVARIATES.filter(k => S.length && S.every(s => k in s.cov) && new Set(S.map(s => s.cov[k])).size > 1);
    present.forEach(k => { out.balance[k] = {}; d.arms.forEach(a => { const v = S.filter(s => s.arm === a).map(s => s.cov[k]); out.balance[k][a] = chg[a].length ? r2(mean(v)) : null; }); });
    const others = d.arms.filter(a => a !== ref), adjK = ADJUST.filter(k => present.includes(k));
    const X = S.map(s => [1].concat(others.map(a => (s.arm === a ? 1 : 0)), [s.i], adjK.map(k => s.cov[k])));
    const y = S.map(s => s.after - s.before);
    const fit = S.length && d.arms.every(a => chg[a].length) ? ols(X, y) : null;
    if (fit) {
      const adj = others.map((a, j) => { const b = fit.beta[1 + j], h = tcrit(fit.df) * fit.se[1 + j]; return { arm: a, diff: r2(b), lo: r2(b - h), hi: r2(b + h) }; });
      out.adjusted = { for: ["session order"].concat(adjK), contrasts: adj, trend_per_session: r2(fit.beta[1 + others.length]) };
    }
    return out;
  }
  function pool(results, arm) {
    const ds = [], vs = [];
    results.forEach(r => r.contrasts.forEach(c => { if (c.arm === arm && c.se) { ds.push(Number(c.diff)); vs.push(Number(c.se) * Number(c.se)); } }));
    const k = ds.length, out = { arm, people: k, estimate: null, lo: null, hi: null, tau: null };
    if (k < 2) return out;
    const w = vs.map(v => 1 / v), sw = w.reduce((s, x) => s + x, 0);
    let fe = 0; w.forEach((wi, i) => { fe += wi * ds[i]; }); fe /= sw;
    let q = 0; w.forEach((wi, i) => { const e = ds[i] - fe; q += wi * (e * e); });
    let w2 = 0; w.forEach(wi => { w2 += wi * wi; });
    const c = sw - w2 / sw, tau2 = c > 0 ? Math.max(0, (q - (k - 1)) / c) : 0;
    const ws = vs.map(v => 1 / (v + tau2)); let sws = 0, est = 0; ws.forEach((wi, i) => { est += wi * ds[i]; }); ws.forEach(wi => { sws += wi; });
    est /= sws; const se = Math.sqrt(1 / sws);
    return Object.assign(out, { estimate: r2(est), lo: r2(est - 1.96 * se), hi: r2(est + 1.96 * se), tau: r2(Math.sqrt(tau2)) });
  }
  function consistency(decisions) {
    const by = {}; decisions.forEach(x => { const k = String(x.scenario); (by[k] = by[k] || []).push(String(x.choice)); });
    let nu = 0, de = 0; const per = [];
    Object.keys(by).sort().forEach(sc => {
      const cs = by[sc]; if (cs.length < 2) return;
      const counts = {}; cs.forEach(c => { counts[c] = (counts[c] || 0) + 1; });
      let top = null; Object.keys(counts).sort().forEach(c => { if (top === null || counts[c] > counts[top]) top = c; });
      nu += counts[top]; de += cs.length;
      per.push({ scenario: sc, n: cs.length, modal: top, agree: r1(counts[top] / cs.length * 100) });
    });
    return { scenarios: per.length, consistency: de ? r1(nu / de * 100) : null, per };
  }
  function SimPerson(effects, o) {
    o = o || {}; this.effects = effects; this.rng = new Rng(o.seed === undefined ? 1 : o.seed);
    this.noise = o.noise === undefined ? 1.5 : o.noise; this.trend = o.trend === undefined ? 0 : o.trend; this.sleep_effect = o.sleep_effect === undefined ? 0.3 : o.sleep_effect;
  }
  SimPerson.prototype.run = function (trial) {
    trial.schedule.forEach((arm, i) => {
      const sleep = 5 + Math.floor(this.rng.u() * 9) / 2;
      const cov = { sleep_h: sleep, caffeine: this.rng.u() < 0.4 ? 1 : 0, exercise: this.rng.u() < 0.3 ? 1 : 0, hour: 7 + Math.floor(this.rng.u() * 15) };
      const before = 4 + Math.floor(this.rng.u() * 3);
      const change = this.effects[arm] + this.trend * i + this.sleep_effect * (sleep - 7) + this.noise * this.rng.gauss();
      record(trial, before, before + change, cov, i * 86400);
    });
    return trial;
  };
  const api = { DESIGNS, COVARIATES, tcrit, schedule, newTrial, record, analyze, pool, consistency, SimPerson, shuffle };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.RSOSTrial = api;
})(typeof self !== "undefined" ? self : this);
