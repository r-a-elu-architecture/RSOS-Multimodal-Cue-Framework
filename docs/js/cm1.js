/* CM1 — the compression layer, JavaScript implementation (spec/CM1.md). Mirrors rsso/rsso/cm1.py (identical results,
 * tested): signature, assign, suggest, describe, pack and unpack. Profiles and patterns come from docs/data/cm1.json.
 * Browser: window.RSOSCM1; Node: module.exports.
 */
(function (root) {
  "use strict";
  const FAMILIES = ["associated", "observer", "override", "breathing", "other"];
  const CHANNELS = ["V", "A", "K", "O", "G", "thought", "memory"];
  const SHRINK = 3.0, CODEC_VERSION = 1;
  const r3 = x => Math.floor(x * 1000 + 0.5) / 1000;
  function num(v) { if (v === null || v === undefined || v === "" || typeof v === "boolean") return null; const x = Number(v); return Number.isFinite(x) ? x : null; }
  function family(r) {
    const p = String(r.protocol || ""), mode = r.node_mode || "";
    if (p.startsWith("node_") || p.startsWith("plan") || mode) return mode === "observer" || p.includes("observer") ? "observer" : "associated";
    if (["override", "interrupt_only", "swish"].includes(p) || p.startsWith("tier")) return "override";
    if (p === "paced_breathing") return "breathing";
    return "other";
  }
  function signature(runs) {
    const v = [], n = [];
    for (const f of FAMILIES) {
      const xs = runs.filter(r => family(r) === f && num(r.sud_before) !== null && num(r.sud_after) !== null).map(r => num(r.sud_before) - num(r.sud_after));
      v.push(xs.length ? r3(xs.reduce((a, b) => a + b, 0) / (xs.length + SHRINK)) : 0); n.push(xs.length);
    }
    for (const c of CHANNELS) {
      const ls = runs.filter(r => String(r.trigger_channel || "") === c && num(r.latency_s) !== null).map(r => num(r.latency_s));
      v.push(ls.length ? r3(ls.filter(x => x <= 3).length / (ls.length + SHRINK)) : 0); n.push(ls.length);
    }
    const done = runs.filter(r => !(r.completed === undefined || r.completed === null || r.completed === ""));
    const comp = done.map(r => ["1", "1.0", "True", "true"].includes(String(r.completed)) ? 1 : 0);
    v.push(comp.length ? r3((comp.reduce((a, b) => a + b, 0) + SHRINK * 0.9) / (comp.length + SHRINK)) : 0.9); n.push(comp.length);
    return { v, n };
  }
  function d2(a, b, scale) { let s = 0; for (let i = 0; i < a.length; i++) { const d = scale ? (a[i] - b[i]) / scale[i] : a[i] - b[i]; s += d * d; } return s; }
  const FAMILY_WORDS = { associated: "an associated node (in the body)", observer: "the observer (nothing binds)", override: "the Override Protocol", breathing: "paced breathing", other: "other programs" };
  const CHANNEL_WORDS = { V: "something seen", A: "a sound", K: "a feeling in the body", O: "a scent", G: "a taste", thought: "a thought", memory: "a memory" };
  function argmax(xs) { let b = 0; for (let i = 1; i < xs.length; i++) if (xs[i] > xs[b]) b = i; return b; }
  function describe(c) {
    const helps = c.slice(0, FAMILIES.length), speed = c.slice(FAMILIES.length, FAMILIES.length + CHANNELS.length);
    const best = argmax(helps), out = [helps[best] >= 0.5 ? "helped most by " + FAMILY_WORDS[FAMILIES[best]] : "little change from any program yet"];
    const fast = argmax(speed);
    if (speed[fast] >= 0.2) out.push(CHANNEL_WORDS[CHANNELS[fast]] + " starts the state fastest");
    if (c[c.length - 1] < 0.75) out.push("often stops runs early: worth a session with a therapist");
    return out.join("; ");
  }
  function assign(sig, profiles) {
    const d = profiles.map((p, i) => [d2(sig.v, p.centroid, p.scale), i]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const best = profiles[d[0][1]];
    const margin = d.length > 1 && d[1][0] + d[0][0] > 0 ? (d[1][0] - d[0][0]) / (d[1][0] + d[0][0]) : 1.0;
    const runs = sig.n.slice(0, FAMILIES.length).reduce((a, b) => a + b, 0);
    return { profile: best.id, text: best.text, distance: r3(Math.sqrt(d[0][0])), confidence: r3(margin * runs / (runs + 10)), runs };
  }
  function suggest(sig, profiles) {
    const a = assign(sig, profiles), cent = profiles.find(p => p.id === a.profile).centroid;
    const blend = sig.v.map((own, i) => { const w = sig.n[i] / (sig.n[i] + 5.0); return r3(w * own + (1 - w) * cent[i]); });
    const helps = blend.slice(0, FAMILIES.length), speed = blend.slice(FAMILIES.length, FAMILIES.length + CHANNELS.length);
    const fam = argmax(helps.slice(0, 3)), ch = argmax(speed.slice(0, 5));
    const rec = ["Start with " + FAMILY_WORDS[FAMILIES[fam]] + ".", "Put the strongest cue on " + CHANNEL_WORDS[CHANNELS[ch]] + " (" + CHANNELS[ch] + ")."];
    if (blend[blend.length - 1] < 0.75) rec.push("Runs are often stopped early: keep them short and review the plan with a therapist.");
    return { assign: a, family: FAMILIES[fam], channel: CHANNELS[ch], values: blend, recommendations: rec };
  }
  const SYMS = { ".": 0, "-": 1, " ": 2 }, REV = [".", "-", " ", "."];
  function fletcher(b) { let s1 = 0, s2 = 0; for (const x of b) { s1 = (s1 + x) % 255; s2 = (s2 + s1) % 255; } return (s2 << 8) | s1; }
  const toB64 = b => typeof Buffer !== "undefined" ? Buffer.from(b).toString("base64") : btoa(String.fromCharCode(...b));
  const fromB64 = s => typeof Buffer !== "undefined" ? Uint8Array.from(Buffer.from(s, "base64")) : Uint8Array.from(atob(s), c => c.charCodeAt(0));
  function utf8Slice(s, n) { return new TextEncoder().encode(s).slice(0, n); }
  function pack(plan, glyphChars, containState, envelope) {
    const env = envelope || { haptic_amp_max: 0.6, refractory_ms_min: 90000, max_per_hour: 6, max_per_day: 20 };
    const nodes = (plan || {}).nodes || [], sched = ((plan || {}).schedule && plan.schedule.length ? plan.schedule : [{}])[0];
    const q = (containState || {}).quarantine || {};
    const out = [67, 49, CODEC_VERSION, Math.min(nodes.length, 8)]; let mask = 0;
    nodes.slice(0, 8).forEach((n, i) => {
      out.push(n.mode === "observer" ? 1 : 0);
      const gi = n.glyph && glyphChars.includes(n.glyph) ? glyphChars.indexOf(n.glyph) : 0xffff;
      out.push(gi >> 8, gi & 0xff);
      const code = [...String(n.tacton || "")].slice(0, 20); out.push(code.length);
      let bits = 0, nb = 0;
      for (const ch of code) { bits = (bits << 2) | (SYMS[ch] === undefined ? 0 : SYMS[ch]); nb += 2; if (nb === 8) { out.push(bits); bits = nb = 0; } }
      if (nb) out.push((bits << (8 - nb)) & 0xff);
      const name = utf8Slice(String(n.name || ""), 16); out.push(name.length, ...name);
      if (("node_" + String(n.key || "").toLowerCase()) in q) mask |= 1 << i;
    });
    out.push(Math.min(255, Math.trunc(Number(sched.per_day) || 0)), Math.min(255, Math.trunc(Number(sched.days) || 0)), Math.floor(env.haptic_amp_max * 100 + 0.5));
    const rs = Math.floor(env.refractory_ms_min / 1000);
    out.push(rs >> 8, rs & 0xff, env.max_per_hour, env.max_per_day, mask, ((containState || {}).escalation || {}).active ? 1 : 0);
    const c = fletcher(out); out.push(c >> 8, c & 0xff);
    return toB64(Uint8Array.from(out));
  }
  function unpack(b64, glyphChars) {
    const b = fromB64(b64);
    if (b[0] !== 67 || b[1] !== 49 || b[2] !== CODEC_VERSION) throw new Error("not a CM1 bundle");
    if (fletcher(b.slice(0, -2)) !== ((b[b.length - 2] << 8) | b[b.length - 1])) throw new Error("CM1 bundle checksum does not match");
    let i = 4; const nodes = [];
    for (let k = 0; k < b[3]; k++) {
      const mode = b[i] ? "observer" : "associated", gi = (b[i + 1] << 8) | b[i + 2], ln = b[i + 3]; i += 4;
      let code = ""; const nbytes = Math.floor((ln * 2 + 7) / 8);
      for (let j = 0; j < ln; j++) { const byte = b[i + Math.floor((j * 2) / 8)]; code += REV[(byte >> (6 - (j * 2) % 8)) & 3]; }
      i += nbytes;
      const nl = b[i], name = new TextDecoder().decode(b.slice(i + 1, i + 1 + nl)); i += 1 + nl;
      nodes.push({ name, mode, glyph: gi < glyphChars.length ? glyphChars[gi] : "", tacton: code });
    }
    const mask = b[i + 7];
    nodes.forEach((n, k) => { n.paused = !!((mask >> k) & 1); });
    return { nodes, dose: { per_day: b[i], days: b[i + 1] }, envelope: { haptic_amp_max: b[i + 2] / 100, refractory_ms_min: ((b[i + 3] << 8) | b[i + 4]) * 1000, max_per_hour: b[i + 5], max_per_day: b[i + 6] },
      escalation: !!b[i + 8], bytes: b.length };
  }
  const api = { FAMILIES, CHANNELS, family, signature, describe, assign, suggest, pack, unpack };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSCM1 = api;
})(typeof self !== "undefined" ? self : this);
