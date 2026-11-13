/* PEAK — anchors as measured objects, JavaScript implementation (spec/PEAK.md). Mirrors rsso/rsso/peak.py (identical
 * results, tested): the anchor object, composites, capture at a peak, probe trials against sham, strength with a 95%
 * interval, contamination and restoration, chains (and their RSX program), and the seeded simulated body.
 * Browser: window.RSOSPeak; Node: module.exports.
 */
(function (root) {
  "use strict";
  const ROLES = ["healing", "stability", "redirection", "lockin"];
  const ROLE_ORDER = { healing: 0, stability: 1, redirection: 2, lockin: 3 };
  const ROLE_NAMES = { healing: "Healing", stability: "Stability", redirection: "Redirection", lockin: "Lock-in" };
  const METRICS = ["rmssd_pct", "hr_delta", "calm"];
  const METRIC_NAMES = { rmssd_pct: "heart rate variability (RMSSD), % change", hr_delta: "heart rate fall, bpm", calm: "calm rating change, 0-10" };
  const THRESHOLD = { rmssd_pct: 5.0, hr_delta: 2.0, calm: 1.0 };
  const WINDOW = 8;
  const CODE_RE = /^[.\-]{1,6}( [.\-]{1,6}){0,2}$/;
  const T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
    2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042];
  const r1 = x => x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10;
  const r2 = x => x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100;
  const tcrit = df => (df >= 1 && df <= 30 ? T95[df - 1] : 1.96);
  function num(v) { if (v === null || v === undefined || v === "" || typeof v === "boolean") return null; const x = Number(v); return Number.isFinite(x) ? x : null; }
  const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;
  function variance(xs) { if (xs.length < 2) return 0; const m = mean(xs); return xs.reduce((s, x) => s + (x - m) * (x - m), 0) / (xs.length - 1); }
  function slope(ys) {
    const n = ys.length; if (n < 2) return 0;
    const mx = (n - 1) / 2, my = mean(ys); let nu = 0, de = 0;
    ys.forEach((y, k) => { nu += (k - mx) * (y - my); }); for (let k = 0; k < n; k++) de += (k - mx) * (k - mx);
    return nu / de;
  }
  function fmt(x) { const k = Math.floor(Math.abs(x) * 10 + 0.5); return (x < 0 && k ? "-" : "") + Math.floor(k / 10) + "." + (k % 10); }
  const byTs = arr => arr.slice().sort((a, b) => (a.ts || 0) - (b.ts || 0));

  function makeAnchor(id, name, glyph, code, role, scent, light, phrase, created) {
    role = role || "stability";
    if (!ROLES.includes(role)) throw new Error("role must be one of " + ROLES.join(", "));
    if (!CODE_RE.test(code || "")) throw new Error('code is 1 to 6 dots and dashes, up to three joined by spaces, e.g. "..-"');
    return { schema: "rsos-anchor/1", id, name, glyph, code, role,
      channels: { vibration: code, scent: scent == null ? null : scent, light: light == null ? null : light, phrase: phrase == null ? null : phrase, glyph },
      parts: [], created: created || 0, captures: [], probes: [], uses: [] };
  }
  function composite(a, b, id, role, created) {
    const code = a.code + " " + b.code;
    if (!CODE_RE.test(code)) throw new Error("the joined code is too long; use shorter codes");
    const pick = k => a.channels[k] || b.channels[k] || null;
    const ph = [a.channels.phrase, b.channels.phrase].filter(Boolean).join(" ") || null;
    const out = makeAnchor(id || (a.id + "+" + b.id), a.name + " + " + b.name, a.glyph + " + " + b.glyph, code, role || a.role, pick("scent"), pick("light"), ph, created || 0);
    out.parts = [a.id, b.id];
    return out;
  }
  function captureCheck(sample, baseline) {
    baseline = baseline || {};
    const src = sample.source || "self_tap", sig = {};
    ["hr", "rmssd", "alpha_theta", "intensity"].forEach(k => { if (num(sample[k]) !== null) sig[k] = r1(num(sample[k])); });
    if (src === "self_tap") return { ok: true, source: src, reason: "marked by the person", signature: sig };
    if (src === "hrv") {
      const rm = num(sample.rmssd), bRm = num(baseline.rmssd), hr = num(sample.hr), bHr = num(baseline.hr);
      if (rm === null || !bRm) return { ok: false, source: src, reason: "needs RMSSD now and at baseline", signature: sig };
      const up = (rm - bRm) / bRm * 100; sig.rmssd_up_pct = r1(up);
      if (hr !== null && bHr !== null && hr - bHr > 10) return { ok: false, source: src, reason: "heart rate rose more than 10 bpm (likely movement or effort)", signature: sig };
      const ok = up >= 15;
      return { ok, source: src, reason: "HRV " + (ok ? "up " : "only up ") + fmt(r1(up)) + "% over baseline", signature: sig };
    }
    if (src === "eeg") {
      const at = num(sample.alpha_theta), bAt = num(baseline.alpha_theta);
      if (at === null || !bAt) return { ok: false, source: src, reason: "needs alpha+theta power now and at baseline", signature: sig };
      const up = (at - bAt) / bAt * 100; sig.alpha_theta_up_pct = r1(up);
      const ok = up >= 20;
      return { ok, source: src, reason: "alpha+theta " + (ok ? "up " : "only up ") + fmt(r1(up)) + "%", signature: sig };
    }
    return { ok: false, source: src, reason: "unknown source", signature: sig };
  }
  function addCapture(anchor, sample, baseline, ts) {
    const c = captureCheck(sample, baseline);
    if (c.ok) anchor.captures.push({ ts: ts || 0, source: c.source, signature: c.signature });
    return c;
  }
  function addProbe(anchor, probe) {
    const p = { ts: probe.ts || 0, kind: probe.kind || "cue" };
    ["hr_before", "hr_after", "rmssd_before", "rmssd_after", "calm_before", "calm_after"].forEach(k => { const x = num(probe[k]); if (x !== null) p[k] = r1(x); });
    anchor.probes.push(p);
    return p;
  }
  function addUse(anchor, ts, duringStress) { anchor.uses.push({ ts: ts || 0, during_stress: !!duringStress }); }

  function probeEffect(p, metric) {
    if (metric === "rmssd_pct") { const b = num(p.rmssd_before), a = num(p.rmssd_after); return b === null || a === null || b <= 0 ? null : (a - b) / b * 100; }
    if (metric === "hr_delta") { const b = num(p.hr_before), a = num(p.hr_after); return b === null || a === null ? null : b - a; }
    const b = num(p.calm_before), a = num(p.calm_after); return b === null || a === null ? null : a - b;
  }
  function chooseMetric(probes) {
    let best = "calm", most = -1;
    for (const m of METRICS) {
      const n = probes.filter(p => p.kind === "cue" && probeEffect(p, m) !== null).length;
      if (n >= 3) return m;
      if (n > most) { best = m; most = n; }
    }
    return best;
  }
  function strength(anchor, window) {
    window = window || WINDOW;
    const probes = byTs(anchor.probes || []), metric = chooseMetric(probes), thr = THRESHOLD[metric];
    const eff = kind => probes.filter(p => p.kind === kind).map(p => probeEffect(p, metric)).filter(e => e !== null).slice(-window);
    const cue = eff("cue"), sham = eff("sham");
    const out = { metric, metric_name: METRIC_NAMES[metric], threshold: thr, n_cue: cue.length, n_sham: sham.length,
      effects: cue.map(r1), estimate: null, lo: null, hi: null, trend: 0, status: "building", against: sham.length >= 3 ? "sham" : "zero" };
    if (!cue.length) { out.say = "No probes yet. Run a probe after a few captures."; return out; }
    let est, se, df;
    if (sham.length >= 3) {
      est = mean(cue) - mean(sham); const va = variance(cue) / cue.length, vs = variance(sham) / sham.length; se = Math.sqrt(va + vs);
      const den = (cue.length > 1 ? va * va / (cue.length - 1) : 0) + vs * vs / (sham.length - 1);
      df = den > 0 ? Math.floor((va + vs) * (va + vs) / den) : Math.min(cue.length, sham.length) - 1;
    }
    else { est = mean(cue); se = Math.sqrt(variance(cue) / cue.length); df = cue.length - 1; }
    out.estimate = r1(est);
    if (cue.length >= 2) { const half = tcrit(Math.max(df, 1)) * se; out.lo = r1(est - half); out.hi = r1(est + half); }
    const tr = cue.length >= 4 ? slope(cue.slice(-6)) : 0;
    out.trend = r2(tr);
    const lo = cue.length >= 2 ? est - tcrit(Math.max(df, 1)) * se : null, hi = cue.length >= 2 ? est + tcrit(Math.max(df, 1)) * se : null;
    let st, say;
    const early = cue.slice(0, -3).length ? cue.slice(0, -3) : cue;
    if (cue.length < 3) { st = "building"; say = "Too few probes to judge. Three or more give an answer."; }
    else if (hi < 0) { st = "contaminated"; say = "The cue now makes things worse than no cue. Restore it before using it again."; }
    else if (tr <= -thr / 2 && mean(cue.slice(-3)) < mean(early) - thr / 2) { st = "weakening"; say = "The effect is falling with each probe. Re-pair it at a peak, and use it less outside practice."; }
    else if (lo > 0 && est >= thr) { st = "strong"; say = "The cue alone changes the body, clearly more than " + (sham.length >= 3 ? "a sham cue." : "nothing."); }
    else if (lo > 0) { st = "present"; say = "There is an effect, but smaller than the threshold. Keep pairing it at peaks."; }
    else { st = "unclear"; say = "No clear effect yet. Keep pairing at peaks and probing."; }
    out.status = st; out.say = say;
    return out;
  }
  function contamination(anchor) {
    const s = strength(anchor), metric = s.metric, thr = THRESHOLD[metric];
    const cue = byTs(anchor.probes || []).filter(p => p.kind === "cue").map(p => probeEffect(p, metric)).filter(e => e !== null);
    const uses = byTs(anchor.uses || []).slice(-10);
    const share = uses.length ? uses.filter(u => u.during_stress).length / uses.length : 0;
    const reasons = []; let risk = "low";
    if (s.status === "contaminated") { reasons.push("the cue alone now makes things worse than no cue"); risk = "high"; }
    else if (cue.length >= 3 && mean(cue.slice(-3)) < -thr) { reasons.push("the last three probes were negative"); risk = "high"; }
    if (uses.length >= 4 && share >= 0.5) {
      reasons.push("used during stress in " + r1(share * 100) + "% of recent uses");
      if (risk === "low") risk = (s.trend || 0) <= -thr / 4 || s.status === "weakening" || s.status === "unclear" ? "medium" : "low";
    }
    return { contaminated: risk === "high", risk, reasons, stress_share: r1(share * 100), status: s.status };
  }
  function restorationPlan(anchor, resource) {
    const c = contamination(anchor), w = resource ? resource.name : "a higher-order resource state";
    const steps = [
      "Pause automatic use of " + anchor.name + " (the autonomy gate keeps it manual until restored).",
      "Do not use it during stress for now: use another anchor, or none.",
      "Re-pair it in calm, at a measured peak, together with " + w + ", for at least 5 sessions.",
      "Run probes after the re-pairing: it is restored after 3 positive probes in a row with the interval above zero."];
    if (resource) steps.splice(3, 0, "Consider holding both as one anchor: " + anchor.glyph + " + " + resource.glyph + ".");
    return { anchor: anchor.id, needed: c.risk !== "low", risk: c.risk, reasons: c.reasons, steps, resource: resource ? resource.id : null,
      restored_when: "3 positive probes in a row, interval above zero" };
  }
  function chain(anchors) {
    return anchors.slice().sort((a, b) => ROLE_ORDER[a.role] - ROLE_ORDER[b.role] || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)).map(a => ({
      anchor: a.id, role: a.role, role_name: ROLE_NAMES[a.role], glyph: a.glyph, code: a.code, scent: a.channels.scent || null,
      light: a.channels.light || null, phrase: a.channels.phrase || null, check: "Did this phase do its job? (calm 0-10 after it)" }));
  }
  const q = s => '"' + String(s).replace(/"/g, "'") + '"';
  function chainRsx(anchors, name) {
    name = name || "anchor_chain";
    const L = ["PROTOCOL " + name + ' "Anchor chain"', "VERSION 1.0", "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4", ""];
    const ph = chain(anchors);
    ph.forEach((p, k) => {
      L.push("TIER " + (k + 1) + " a" + (k + 1) + " {", "  GLYPH " + q(p.glyph), "  V " + q("see " + (p.light || "the light") + " around " + p.glyph),
        "  A " + q(p.phrase || p.role_name), "  K " + q("feel the code " + p.code));
      if (p.scent) L.push("  O " + q(p.scent));
      L.push("  TACTON " + q(p.code), "}");
    });
    L.push("");
    ph.forEach((p, k) => L.push("PHASE " + p.role + (k + 1) + " dur=8s {", "  ACTIVATE a" + (k + 1), "  MARK " + q("check " + p.role), "}"));
    return L.join("\n") + "\n";
  }
  function chainReport(results) {
    let worked = 0;
    const out = results.map(r => { const b = num(r.calm_before), a = num(r.calm_after), d = b === null || a === null ? null : a - b, ok = d !== null && d >= 1;
      if (ok) worked++; return { role: r.role === undefined ? null : r.role, change: d === null ? null : r1(d), worked: ok }; });
    let weakest = null; out.filter(x => x.change !== null).forEach(x => { if (weakest === null || x.change < weakest.change) weakest = x; });
    return { phases: out, worked, of: out.length, weakest: weakest && !weakest.worked ? weakest.role : null };
  }

  function Rng(seed) { this.x = seed % 4294967296; }
  Rng.prototype.u = function () { this.x = (1664525 * this.x + 1013904223) % 4294967296; return this.x / 4294967296; };
  Rng.prototype.gauss = function () { let s = 0; for (let i = 0; i < 12; i++) s += this.u(); return s - 6; };
  function SimBody(o) {
    o = o || {};
    this.rng = new Rng(o.seed === undefined ? 1 : o.seed);
    this.ceiling = o.ceiling === undefined ? 20 : o.ceiling; this.alpha = o.alpha === undefined ? 0.3 : o.alpha;
    this.fade = o.fade === undefined ? 0.98 : o.fade; this.beta = o.beta === undefined ? 0.25 : o.beta;
    this.stress_pull = o.stress_pull === undefined ? -15 : o.stress_pull; this.noise = o.noise === undefined ? 4 : o.noise;
    this.placebo = o.placebo === undefined ? 1 : o.placebo; this.v = 0; this.t = 0;
  }
  SimBody.prototype.pair = function () { this.v += this.alpha * (this.ceiling - this.v); };
  SimBody.prototype.wait = function (days) { for (let i = 0; i < days; i++) this.v *= this.fade; this.t += days * 86400; };
  SimBody.prototype.stressUse = function () { this.v += this.beta * (this.stress_pull - this.v); };
  SimBody.prototype.probe = function (kind) {
    kind = kind || "cue"; this.t += 600;
    const before = 40 + 6 * this.rng.gauss(), eff = (kind === "cue" ? this.v : this.placebo) + this.noise * this.rng.gauss();
    const after = before * (1 + eff / 100), hb = 72 + 4 * this.rng.gauss(), ha = hb - eff / 10;
    return { ts: this.t, kind, rmssd_before: r1(before), rmssd_after: r1(after), hr_before: r1(hb), hr_after: r1(ha) };
  };
  function scenario(kind, seed, probes, shams) {
    probes = probes === undefined ? 8 : probes; shams = shams === undefined ? 4 : shams;
    const b = new SimBody({ seed, ceiling: { strong: 22, weak: 4, none: 0, contaminated: 22 }[kind] });
    const a = makeAnchor("sim" + seed, "Simulated " + kind, "🦁", "..-", "redirection");
    for (let i = 0; i < 8; i++) { b.pair(); addCapture(a, { source: "self_tap", intensity: 8 }, null, b.t); b.wait(1); }
    const total = probes + shams, order = [];
    for (let k = 0; k < total; k++) order.push(Math.floor((k + 1) * shams / total) > Math.floor(k * shams / total) ? "sham" : "cue");
    order.forEach((kd, k) => {
      if (kind === "contaminated" && k >= 2 && kd === "cue") for (let i = 0; i < 3; i++) { b.stressUse(); addUse(a, b.t, true); }
      addProbe(a, b.probe(kd)); b.wait(1);
    });
    return { anchor: a, truth: kind, true_strength: r1(b.v) };
  }

  const api = { ROLES, ROLE_NAMES, METRICS, METRIC_NAMES, THRESHOLD, makeAnchor, composite, captureCheck, addCapture, addProbe, addUse,
    probeEffect, chooseMetric, strength, contamination, restorationPlan, chain, chainRsx, chainReport, Rng, SimBody, scenario, r1 };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.RSOSPeak = api;
})(typeof self !== "undefined" ? self : this);
