/* RSOS operational metrics, JavaScript implementation. Mirrors rsso/rsso/metrics.py `compute`
 * (identical results, tested in rsso/tests/test_metrics.py). Needs RSOSMemstack (docs/js/memstack.js).
 * Browser: window.RSOSMetrics; Node: module.exports.
 */
(function (root) {
  "use strict";
  const M = typeof module !== "undefined" && module.exports ? require("./memstack.js") : root.RSOSMemstack;
  const REFLEX_LATENCY = 3.0, KINDS = ["V", "A", "K", "O", "G", "thought", "memory"];
  const num = v => { if (v === null || v === undefined || v === "" || typeof v === "boolean") return null; const f = Number(v); return Number.isFinite(f) ? f : null; };
  const r1 = x => Math.floor(x * 10 + 0.5) / 10;
  const median = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; if (!n) return null; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
  const done = r => ["1", "1.0", "True", "true"].includes(String(r.completed === undefined ? "1" : r.completed));
  const isTrigger = r => Boolean(String(r.trigger_channel || "").trim()) || r.trigger === "device";
  const pct = (a, b) => b ? r1(100 * a / b) : null;
  function fmtG(x) { return String(x); }

  function compute(runs, srbai, settings, now) {
    const rows = runs.slice().sort((a, b) => (num(a.timestamp) || 0) - (num(b.timestamp) || 0));
    settings = settings || {};
    const out = {}, n = rows.length;
    const dn = rows.filter(done), trig = dn.filter(isTrigger);
    const lats = trig.map(r => num(r.latency_s)).filter(x => x !== null);
    out.CRI = pct(n - dn.length, n);
    out.RSF = pct(dn.length, n);
    out.SPV = pct(trig.length, dn.length);
    const chans = new Set(trig.map(r => String(r.trigger_channel || "").trim()).filter(c => KINDS.includes(c)));
    out.SEP = trig.length ? pct(chans.size, KINDS.length) : null;
    out.SAR = pct(lats.filter(x => x <= REFLEX_LATENCY).length, lats.length);
    out.RAI = pct(trig.filter(r => r.trigger !== "device").length, trig.length);
    const days = [...new Set(rows.map(r => Math.floor((num(r.timestamp) || 0) / 86400)))].sort((a, b) => a - b);
    const last = Math.floor((now !== undefined && now !== null ? now : (rows.length ? (num(rows[rows.length - 1].timestamp) || 0) : 0)) / 86400);
    out.SRI = rows.length ? pct(days.filter(d => d >= last - 13 && d <= last).length, 14) : null;
    let streak = 0;
    if (days.length) { const s = new Set(days); let d = days[days.length - 1]; while (s.has(d)) { streak++; d--; } }
    out.SRCD = rows.length ? streak : null;
    if (lats.length >= 10) { const first = median(lats.slice(0, 5)), latest = median(lats.slice(-5)); out.ARC = first ? r1(100 * (1 - latest / first)) : null; }
    else out.ARC = null;
    const pairs = dn.map(r => [num(r.sud_before), num(r.sud_after)]).filter(([a, b]) => a !== null && b !== null);
    out.MCI = pct(pairs.length, n);
    const recent = pairs.slice(-10), before = recent.reduce((s, [a]) => s + a, 0);
    out.ERV = recent.length && before ? r1(100 * recent.reduce((s, [a, b]) => s + (a - b), 0) / before) : null;
    const inh = num(settings.inhale), exh = num(settings.exhale);
    out.SBB = inh && exh ? "1:" + fmtG(Math.floor(exh / inh * 100 + 0.5) / 100) : null;
    const summ = rows.length ? M.summarize(rows, srbai || []) : { tiers: {}, srbai: [] };
    const tiers = Object.values(summ.tiers);
    out.SME = rows.length ? tiers.length : null;
    let main = null; for (const t of tiers) if (!main || t.runs > main.runs) main = t;
    out.LAW = main ? r1(100 * main.bundle_strength) : null;
    out.RIF = main && main.habit ? (main.habit.runs_to_reflex === undefined ? null : main.habit.runs_to_reflex) : null;
    out.PRM = main ? Boolean(main.reflex.met) : null;
    const weeks = summ.srbai;
    out.MCRAL = weeks.length ? weeks[weeks.length - 1].srbai : null;
    const signals = [];
    if (lats.length >= 10) signals.push(median(lats.slice(-5)) < median(lats.slice(0, 5)));
    if (weeks.length >= 2) signals.push(weeks[weeks.length - 1].srbai > weeks[0].srbai);
    if (main && main.distress_drop_first !== null && main.distress_drop_latest !== null && pairs.length >= 10) signals.push(main.distress_drop_latest >= main.distress_drop_first);
    out.MMR = signals.length ? pct(signals.filter(Boolean).length, signals.length) : null;
    out.HSC = rows.length ? [trig.length > 0, lats.some(x => x <= 10), lats.some(x => x <= REFLEX_LATENCY), weeks.some(w => w.srbai >= 4), Boolean(main && main.reflex.met)].filter(Boolean).length : null;
    if (weeks.length && lats.length >= 3) {
      const felt = (weeks[weeks.length - 1].srbai - 1) / 4 * 100, speed = Math.max(0, 1 - Math.min(1, median(lats.slice(-5)) / 60)) * 100;
      out.EDA = r1(Math.abs(felt - speed));
    } else out.EDA = null;
    return out;
  }
  const api = { compute };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSMetrics = api;
})(typeof self !== "undefined" ? self : this);
