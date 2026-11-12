/* MEMSTACK in the browser: tier memory and progress toward a reflex.
 * Mirrors rsso/rsso/memstack.py; rsso/tests/test_memstack.py checks both give the same numbers.
 * Browser: window.RSOSMemstack; Node: module.exports.
 */
(function (root) {
  "use strict";
  const SCHEMA = "rsos-memstack/1";
  const ALPHA = { V: 0.30, A: 0.25, K: 0.30, trigger: 0.30 }, BETA = 0.5;
  const LAT_MIN = 1.0, REFLEX_LATENCY = 3.0;
  const ETA_GRID = [], L0_GRID = [];
  for (let k = 1; k <= 60; k++) ETA_GRID.push(Math.round(0.005 * k * 1000) / 1000);
  for (let k = 0; k <= 30; k++) L0_GRID.push(5.0 * Math.pow(1.15, k));

  const num = v => { if (v === null || v === undefined || v === "") return null; const f = Number(v); return isFinite(f) ? f : null; };
  const mean = xs => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
  const median = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : null; };

  function fitHabit(latencies) {
    const lat = latencies.map(x => Math.max(x, 0.5));
    if (lat.length < 5) return null;
    let best = null;
    for (const eta of ETA_GRID) for (const L0 of L0_GRID) {
      let sse = 0;
      for (let n = 0; n < lat.length; n++) { const pred = LAT_MIN + (L0 - LAT_MIN) * Math.pow(1 - eta, n); sse += (Math.log(lat[n]) - Math.log(pred)) ** 2; }
      if (best === null || sse < best[0] - 1e-12) best = [sse, eta, L0];
    }
    const [sse, eta, L0] = best, nNow = lat.length;
    const predNow = LAT_MIN + (L0 - LAT_MIN) * Math.pow(1 - eta, nNow);
    let remaining = 0;
    if (predNow > REFLEX_LATENCY) remaining = Math.max(0, Math.ceil(Math.log((REFLEX_LATENCY - LAT_MIN) / (L0 - LAT_MIN)) / Math.log(1 - eta) - nNow));
    return { eta, L0, predicted_latency_now: predNow, runs_to_reflex: remaining, rmse_log: Math.sqrt(sse / nNow) };
  }

  function summarize(runs, srbai) {
    const rows = runs.slice().sort((a, b) => (num(a.timestamp) || 0) - (num(b.timestamp) || 0));
    const groups = {}, order = [];
    for (const r of rows) {
      const key = String(r.tier || "").trim() || (r.protocol || "unknown");
      if (!(key in groups)) { groups[key] = []; order.push(key); }
      groups[key].push(r);
    }
    const tiers = {};
    for (const key of order) {
      const rs = groups[key], V = { V: 0, A: 0, K: 0, trigger: -0.8 };
      let practice = 0, paired = 0, completed = 0; const drops = [], gains = [], lats = [];
      for (const r of rs) {
        const done = ["1", "1.0", "True", "true"].includes(String(r.completed === undefined ? "1" : r.completed));
        completed += done ? 1 : 0;
        const isTrigger = !!String(r.trigger_channel || "").trim() || r.trigger === "device";
        if (done) {
          const present = ["V", "A", "K"].concat(isTrigger ? ["trigger"] : []);
          const err = 1 - present.reduce((s, c) => s + V[c], 0);
          for (const c of present) V[c] += ALPHA[c] * BETA * err;
          if (isTrigger) paired++; else practice++;
        }
        const sb = num(r.sud_before), sa = num(r.sud_after), ab = num(r.agency_before), aa = num(r.agency_after);
        if (done && sb !== null && sa !== null) drops.push(sb - sa);
        if (done && ab !== null && aa !== null) gains.push(aa - ab);
        const lat = num(r.latency_s);
        if (done && isTrigger && lat !== null) lats.push(lat);
      }
      const k = Math.min(5, drops.length);
      tiers[key] = {
        runs: rs.length, completed, practice, trigger_runs: paired,
        distress_drop_first: k ? mean(drops.slice(0, k)) : null,
        distress_drop_latest: k ? mean(drops.slice(-k)) : null,
        agency_gain_latest: gains.length ? mean(gains.slice(-Math.min(5, gains.length))) : null,
        bundle_strength: Math.min(1, Math.max(0, V.V + V.A + V.K)),
        trigger_value: V.trigger,
        median_latency_last10: lats.length ? median(lats.slice(-10)) : null,
        real_triggers: lats.length,
        habit: fitHabit(lats),
      };
    }
    const weeks = (srbai || []).filter(w => num(w.srbai) !== null).map(w => [Math.trunc(num(w.week)), num(w.srbai)]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    let srbaiOk = false;
    for (let i = 0; i + 1 < weeks.length; i++) if (weeks[i][1] >= 4 && weeks[i + 1][1] >= 4 && weeks[i + 1][0] === weeks[i][0] + 1) srbaiOk = true;
    for (const t of Object.values(tiers)) {
      const latOk = t.real_triggers >= 10 && t.median_latency_last10 !== null && t.median_latency_last10 <= REFLEX_LATENCY;
      t.reflex = { srbai_two_weeks_at_4: srbaiOk, latency_at_or_below_3s: latOk, met: srbaiOk && latOk };
    }
    return { schema: SCHEMA, tiers, srbai: weeks.map(([week, s]) => ({ week, srbai: s })) };
  }

  function canonical(o) {
    if (Array.isArray(o)) return "[" + o.map(canonical).join(",") + "]";
    if (o && typeof o === "object") return "{" + Object.keys(o).sort().map(k => JSON.stringify(k) + ":" + canonical(o[k])).join(",") + "}";
    return JSON.stringify(o);
  }
  async function sha256Hex(text) {
    if (typeof crypto !== "undefined" && crypto.subtle) {
      const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    }
    return require("crypto").createHash("sha256").update(text, "utf8").digest("hex");
  }
  async function snapshot(runs, srbai) {
    const body = { schema: SCHEMA, runs, srbai: srbai || [] };
    return Object.assign({}, body, { sha256: await sha256Hex(canonical(body)) });
  }
  async function restore(snap) {
    if (!snap || snap.schema !== SCHEMA) throw new Error("This file is not an RSOS memory snapshot.");
    const body = { schema: snap.schema, runs: snap.runs, srbai: snap.srbai };
    if (await sha256Hex(canonical(body)) !== snap.sha256) throw new Error("The snapshot's checksum doesn't match: the file was changed or damaged.");
    return [snap.runs, snap.srbai];
  }
  function merge(a, b) {
    const seen = new Set(), out = [];
    for (const r of a.concat(b).sort((x, y) => (num(x.timestamp) || 0) - (num(y.timestamp) || 0))) {
      const k = String(r.timestamp) + "|" + r.protocol + "|" + r.participant;
      if (!seen.has(k)) { seen.add(k); out.push(r); }
    }
    return out;
  }

  const api = { SCHEMA, summarize, fitHabit, snapshot, restore, merge, canonical };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSMemstack = api;
})(typeof self !== "undefined" ? self : this);
