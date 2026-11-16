/* The RSIA Watchdog on the person side, JavaScript implementation (spec/WATCHDOG.md). Mirrors rsso/rsso/watchdog.py
 * (identical results, tested): one decision for every action that acts on a person (allow, ask or hold), each reason
 * naming the Spine virtue or precept that decided it, and a hash-chained audit log with a synchronous SHA-256.
 * It asks CONTAIN (which asks the session state) and never loosens a rule. Needs contain.js and safety.js.
 * Browser: window.RSOSWatchdog; Node: module.exports.
 */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const C = node ? require("./contain.js") : root.RSOSContain;
  const S = node ? require("./safety.js") : root.RSOSSafety;
  const LEVEL_RANK = { self_guided: 0, structured: 1, clinician_led: 2 };
  const LEVEL_NAME = { self_guided: "self-guided", structured: "structured", clinician_led: "clinician-led" };
  const CLINICIAN_TIERS = ["414", "420", "439", "440"];
  const MAP_SOURCES = ["cm1", "atlas", "map"];
  const CLINICIAN_SESSIONS = ["session_low_mood"];   // depression work (CONTAIN §10.2; FIXES_R1 W-9)
  const LOG_MAX = 500, ZERO = "0".repeat(64);
  const clone = o => JSON.parse(JSON.stringify(o));

  function level(action) {
    const a = action || {}, m = /^tier(\d{3})/.exec(String(a.protocol || ""));
    if (a.therapist_led || a.deep || (m && CLINICIAN_TIERS.includes(m[1])) || CLINICIAN_SESSIONS.includes(a.protocol)) return "clinician_led";
    if (["plan", "session"].includes(a.kind) || a.programmed || ["device", "agent"].includes(a.trigger) || ["practitioner", "agent"].includes(a.source)) return "structured";
    return "self_guided";
  }
  const consent = (cs, scope, now) => (cs || []).some(c => c.scope === scope && (c.given || 0) <= now && (c.withdrawn === null || c.withdrawn === undefined || c.withdrawn > now));
  const state = (v, key, allowed) => (v && typeof v === "object" && !Array.isArray(v) && key in v && (!allowed || allowed.includes(v[key])) ? v : null);   // FIXES_R1 W-10
  const R = (rule, virtue, text, resolve) => ({ rule, virtue, text, resolve });

  function watch(action, ctx) {
    const a = action || {}, x = ctx || {}, now = x.now || 0;
    if (a.kind === "stop") return { decision: "allow", level: "self_guided", reasons: [], resolve: null, contain: null };
    const lvl = level(a), holds = [], asks = [];
    for (const f of S.spineFlags(a.text || "")) holds.push(R("spine:" + f.flag, f.virtue, f.text, "none"));
    const d = C.decide(Object.assign({}, a, { therapist_present: !!x.clinician_present }), state(x.contain, "quarantine"), x.timeline || null, now, state(x.safety, "mode", S.MODES));
    for (const t of d.reasons) holds.push(R("contain", "jin", t, "safety_page"));
    const regulating = S.regulating(a) && lvl !== "clinician_led";       // FIXES_R1 W-7
    if (a.memory_work && x.memory_work_allowed === false) holds.push(R("memory", "gi", "Difficult-memory work is not offered in this domain.", "none"));   // FIXES_R1 P-2
    if (!regulating) {
      let top = x.max_level || "clinician_led";
      if (!Object.prototype.hasOwnProperty.call(LEVEL_RANK, top)) top = "structured";                        // FIXES_R1 W-8
      if (LEVEL_RANK[lvl] > LEVEL_RANK[top])
        holds.push(R("level", "gi", "This is " + LEVEL_NAME[lvl] + " work; this domain allows up to " + LEVEL_NAME[top] + ". It runs in the Clinical domain, or in Research with a study clinician.", "none"));
      else if (lvl === "clinician_led" && !(x.clinician_present && x.screening_recorded))
        holds.push(R("clinician", "gi", "Clinician-led work starts only with the clinician present and the screening result recorded.", "clinician"));
      const plan = x.plan_protocols;
      if (["device", "agent"].includes(a.trigger) && plan !== null && plan !== undefined && a.protocol && !plan.includes(a.protocol))
        holds.push(R("plan", "chugi", a.protocol + " is not in the person's plan; a device or agent offers only what the person chose.", "none"));
    }
    const auto = !!a.auto && a.source !== "agent" && a.trigger !== "agent";
    if (auto && !consent(x.consents, "automatic_firing", now)) asks.push(R("consent", "rei", "Automatic firing has no consent on record, so the device asks instead.", "person"));
    if (a.auto && new Set(a.signals || []).size < 2) asks.push(R("p3", "p3", "Fewer than two independent signals: never act on a partial impression, so the device asks instead.", "person"));
    if (a.source === "agent" || a.trigger === "agent") asks.push(R("agent", "rei", "An agent proposed this; the person starts every run.", "person"));
    else if (a.trigger === "device" && !a.auto) asks.push(R("offer", "rei", "A device offer: the person confirms before it runs.", "person"));
    if (MAP_SOURCES.includes(a.justified_by)) asks.push(R("p15", "p15", "Recommended from population data: maps inform, the person decides.", "person"));
    if (holds.length) {
      const rs = holds.map(h => h.resolve);
      return { decision: "hold", level: lvl, reasons: holds.concat(asks), resolve: rs.includes("none") ? "none" : rs.includes("clinician") ? "clinician" : "safety_page", contain: d };
    }
    if (asks.length) return { decision: "ask", level: lvl, reasons: asks, resolve: "person", contain: d };
    return { decision: "allow", level: lvl, reasons: [], resolve: null, contain: d };
  }

  function link(contain, safety, now) {
    let st = clone(safety || S.newState());
    const esc = (contain || {}).escalation || {};
    if (esc.active && S.SEVERITY[st.mode] < S.SEVERITY.STABILISE) {
      st = S.enterStabilise(st, "contain", now || 0)[0];
      st.history[st.history.length - 1].why = "practice paused: " + (esc.reasons || []).join("; ");
      return [st, true];
    }
    return [st, false];
  }

  /* ---- audit log ---- */
  function canonical(o) {
    if (Array.isArray(o)) return "[" + o.map(canonical).join(",") + "]";
    if (o && typeof o === "object") return "{" + Object.keys(o).sort().map(k => JSON.stringify(k) + ":" + canonical(o[k])).join(",") + "}";
    return JSON.stringify(o === undefined ? null : o);
  }
  const K = new Uint32Array([0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);
  function sha256(text) {
    const msg = new TextEncoder().encode(text), len = msg.length, n = ((len + 9 + 63) >> 6) << 6, b = new Uint8Array(n);
    b.set(msg); b[len] = 0x80;
    const bits = len * 8; for (let i = 0; i < 8; i++) b[n - 1 - i] = Math.floor(bits / Math.pow(2, 8 * i)) & 0xff;
    const H = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]), W = new Uint32Array(64);
    const rot = (x, r) => (x >>> r) | (x << (32 - r));
    for (let o = 0; o < n; o += 64) {
      for (let i = 0; i < 16; i++) W[i] = (b[o + 4 * i] << 24) | (b[o + 4 * i + 1] << 16) | (b[o + 4 * i + 2] << 8) | b[o + 4 * i + 3];
      for (let i = 16; i < 64; i++) {
        const s0 = rot(W[i - 15], 7) ^ rot(W[i - 15], 18) ^ (W[i - 15] >>> 3), s1 = rot(W[i - 2], 17) ^ rot(W[i - 2], 19) ^ (W[i - 2] >>> 10);
        W[i] = (W[i - 16] + s0 + W[i - 7] + s1) >>> 0;
      }
      let [a, bb, c, d, e, f, g, h] = H;
      for (let i = 0; i < 64; i++) {
        const t1 = (h + (rot(e, 6) ^ rot(e, 11) ^ rot(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + W[i]) >>> 0;
        const t2 = ((rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)) + ((a & bb) ^ (a & c) ^ (bb & c))) >>> 0;
        h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = bb; bb = a; a = (t1 + t2) >>> 0;
      }
      H[0] += a; H[1] += bb; H[2] += c; H[3] += d; H[4] += e; H[5] += f; H[6] += g; H[7] += h;
    }
    return Array.from(H).map(x => x.toString(16).padStart(8, "0")).join("");
  }
  function record(log, action, result, ts) {
    const a = action || {}, nul = v => (v === undefined ? null : v);
    // FIXES_R1 W-1: the number follows the previous record, so trimming keeps the chain valid
    const body = { n: log.length ? log[log.length - 1].n + 1 : 0, ts: Math.trunc(ts), kind: nul(a.kind), protocol: nul(a.protocol), trigger: nul(a.trigger), source: nul(a.source),
      decision: result.decision, level: result.level, rules: result.reasons.map(r => r.rule), virtues: result.reasons.map(r => r.virtue),
      prev: log.length ? log[log.length - 1].hash : ZERO };
    const rec = Object.assign({}, body, { hash: sha256(canonical(body)) });
    log.push(rec);
    return rec;
  }
  const trim = log => log.slice(-LOG_MAX);
  function verify(log) {
    return (log || []).every((r, i) => {
      const body = Object.assign({}, r); delete body.hash;
      if (r.hash !== sha256(canonical(body))) return false;
      if (i && r.prev !== log[i - 1].hash) return false;
      if (i && r.n !== (log[i - 1].n === undefined ? -2 : log[i - 1].n) + 1) return false;
      return true;
    });
  }

  const api = { LEVEL_RANK, LEVEL_NAME, CLINICIAN_TIERS, LOG_MAX, level, watch, link, canonical, sha256, record, trim, verify };
  if (node) module.exports = api; else root.RSOSWatchdog = api;
})(typeof window !== "undefined" ? window : globalThis);
