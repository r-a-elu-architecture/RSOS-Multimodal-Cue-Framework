/* CONTAIN — the safety layer, JavaScript implementation (spec/CONTAIN.md). Mirrors rsso/rsso/contain.py (identical
 * results, tested): the device safety envelope, drift detection, escalation, review, the decide() gate, release and
 * rollback. Runs carry `timestamp` in seconds; adverse events and screening answers carry `ts` in milliseconds.
 * Browser: window.RSOSContain; Node: module.exports.
 */
(function (root) {
  "use strict";
  const ENVELOPE = { haptic_amp_max: 0.6, haptic_pulse_ms_max: 1000, haptic_burst_ms_max: 6000, haptic_on_ms_per_run: 20000,
    tone_hz_min: 60, tone_hz_max: 2000, tone_ms_max: 10000, tone_ms_per_run: 60000, scent_per_run: 3, scent_gap_ms: 20000,
    taste_per_run: 2, run_ms_max: 900000, max_per_hour: 6, max_per_day: 20, refractory_ms_min: 90000 };
  const DAY = 86400, WEEK = 7 * 86400;
  const clone = o => JSON.parse(JSON.stringify(o));
  function num(v) { if (v === null || v === undefined || v === "" || typeof v === "boolean") return null; const x = Number(v); return Number.isFinite(x) ? x : null; }
  const r1 = x => Math.floor(x * 10 + 0.5) / 10;
  function t1(x) { const k = Math.floor(Math.abs(x) * 10 + 0.5); return (x < 0 && k ? "-" : "") + Math.floor(k / 10) + "." + (k % 10); }
  function checkEnvelope(tl, env) {
    env = env || ENVELOPE; const out = [], s = tl.safety || {};
    if ((s.max_per_hour || 0) > env.max_per_hour) out.push({ rule: "max_per_hour", value: s.max_per_hour, limit: env.max_per_hour });
    if ((s.max_per_day || 0) > env.max_per_day) out.push({ rule: "max_per_day", value: s.max_per_day, limit: env.max_per_day });
    if ((s.refractory_ms || 0) < env.refractory_ms_min) out.push({ rule: "refractory_ms_min", value: s.refractory_ms === undefined ? null : s.refractory_ms, limit: env.refractory_ms_min });
    if ((s.haptic_max || 0) > env.haptic_amp_max) out.push({ rule: "haptic_amp_max", value: s.haptic_max, limit: env.haptic_amp_max });
    if ((tl.duration_ms || 0) > env.run_ms_max) out.push({ rule: "run_ms_max", value: tl.duration_ms, limit: env.run_ms_max });
    let hapOn = 0, toneMs = 0, tastes = 0; const scents = [];
    (tl.events || []).forEach((e, i) => {
      if (e.channel === "haptic") {
        const on = Math.trunc(e.on || 0), off = Math.trunc(e.off || 0), n = Math.trunc(e.count || 1), amp = Number(e.amp || 0);
        if (amp > env.haptic_amp_max) out.push({ rule: "haptic_amp_max", event: i, value: amp, limit: env.haptic_amp_max });
        if (on > env.haptic_pulse_ms_max) out.push({ rule: "haptic_pulse_ms_max", event: i, value: on, limit: env.haptic_pulse_ms_max });
        if (n * (on + off) > env.haptic_burst_ms_max) out.push({ rule: "haptic_burst_ms_max", event: i, value: n * (on + off), limit: env.haptic_burst_ms_max });
        hapOn += n * on;
      } else if (e.channel === "auditory" && e.kind === "tone") {
        const hz = Number(e.hz || 0), dur = Math.trunc(e.dur || 0);
        if (!(env.tone_hz_min <= hz && hz <= env.tone_hz_max)) out.push({ rule: "tone_hz", event: i, value: hz, limit: env.tone_hz_min + "-" + env.tone_hz_max });
        if (dur > env.tone_ms_max) out.push({ rule: "tone_ms_max", event: i, value: dur, limit: env.tone_ms_max });
        toneMs += dur;
      } else if (e.channel === "olfactory") {
        if (scents.length && e.t - scents[scents.length - 1] < env.scent_gap_ms) out.push({ rule: "scent_gap_ms", event: i, value: e.t - scents[scents.length - 1], limit: env.scent_gap_ms });
        scents.push(e.t);
      } else if (e.channel === "gustatory") tastes++;
    });
    if (hapOn > env.haptic_on_ms_per_run) out.push({ rule: "haptic_on_ms_per_run", value: hapOn, limit: env.haptic_on_ms_per_run });
    if (toneMs > env.tone_ms_per_run) out.push({ rule: "tone_ms_per_run", value: toneMs, limit: env.tone_ms_per_run });
    if (scents.length > env.scent_per_run) out.push({ rule: "scent_per_run", value: scents.length, limit: env.scent_per_run });
    if (tastes > env.taste_per_run) out.push({ rule: "taste_per_run", value: tastes, limit: env.taste_per_run });
    return out;
  }
  const rated = r => num(r.sud_before) !== null && num(r.sud_after) !== null;
  const mean = xs => xs.reduce((a, b) => a + b, 0) / xs.length;
  const ts = r => num(r.timestamp) || 0;
  function drift(runs, protocol, since) {
    const rs = runs.filter(r => r.protocol === protocol && (since === null || since === undefined || ts(r) > since)).sort((a, b) => ts(a) - ts(b));
    const rt = rs.filter(rated), sig = [], last = rt.slice(-5);
    if (last.length >= 4) {
      const ch = mean(last.map(r => num(r.sud_after) - num(r.sud_before)));
      if (ch >= 0.5) sig.push({ signal: "worse after", value: r1(ch), text: "distress rose by " + t1(ch) + " on average over the last " + last.length + " rated runs" });
      const ag = last.filter(r => num(r.agency_after) !== null && num(r.agency_before) !== null).map(r => num(r.agency_after) - num(r.agency_before));
      if (ag.length >= 4 && mean(ag) <= -1) sig.push({ signal: "agency falls", value: r1(mean(ag)), text: "agency fell by " + t1(-mean(ag)) + " on average" });
    }
    if (rt.length >= 8) {
      const a = mean(rt.slice(-5).map(r => num(r.sud_after))), b = mean(rt.slice(-10, -5).map(r => num(r.sud_after)));
      if (a - b >= 1.5) sig.push({ signal: "rising distress", value: r1(a - b), text: "distress after a run is " + t1(a - b) + " higher than in the runs before" });
    }
    const recent = rs.slice(-6);
    if (recent.length >= 6) {
      const stopped = recent.filter(r => ["0", "0.0", "False", "false"].includes(String(r.completed))).length;
      if (stopped >= 4) sig.push({ signal: "stopped often", value: stopped, text: "stopped " + stopped + " of the last 6 times" });
    }
    const names = new Set(sig.map(s => s.signal));
    const status = names.has("worse after") || names.has("agency falls") || sig.length >= 2 ? "drift" : sig.length ? "watch" : "ok";
    return { status, signals: sig, runs: rs.length };
  }
  function escalation(runs, adverse, screens, now) {
    const reasons = [], age = a => now - (num(a.ts) || 0) / 1000;
    if ((adverse || []).some(a => a.severity === "serious" && age(a) <= 30 * DAY)) reasons.push("a serious adverse event in the last 30 days");
    const mod = (adverse || []).filter(a => a.severity === "moderate" && (a.related === "possible" || a.related === "likely") && age(a) <= 14 * DAY);
    if (mod.length >= 2) reasons.push(mod.length + " moderate adverse events possibly related to practice in 14 days");
    if ((screens || []).some(s => s.answer === "yes" && age(s) <= WEEK)) reasons.push("the screening question was answered yes in the last 7 days");
    const week = runs.filter(r => rated(r) && now - ts(r) <= WEEK).sort((a, b) => ts(a) - ts(b));
    const high = week.slice(-5).filter(r => num(r.sud_after) >= 8).length;
    if (high >= 3) reasons.push("distress stayed at 8 or more after " + high + " of the last 5 runs");
    return { active: reasons.length > 0, reasons };
  }
  const newState = () => ({ quarantine: {}, released: {}, escalation: { active: false, reasons: [] } });
  function review(state, runs, adverse, screens, now) {
    const st = clone(state || newState()), changes = [];
    const protos = [...new Set(runs.map(r => r.protocol).filter(Boolean))].sort();
    for (const p of protos) {
      if (p in st.quarantine) continue;
      const rel = st.released[p], d = drift(runs, p, rel ? rel.at : null);
      if (d.status === "drift") {
        st.quarantine[p] = { since: now, reason: d.signals.map(s => s.text).join("; "), signals: d.signals.map(s => s.signal), therapist: false };
        changes.push({ kind: "quarantine", protocol: p, text: st.quarantine[p].reason });
      }
    }
    for (const a of adverse || []) {
      const p = a.protocol;
      if (p && (a.related === "possible" || a.related === "likely") && (a.severity === "moderate" || a.severity === "serious") && !(p in st.quarantine)) {
        const rel = st.released[p];
        if (!rel || (num(a.ts) || 0) / 1000 > rel.at) {
          st.quarantine[p] = { since: now, reason: "a " + a.severity + " adverse event " + a.related + "ly related to it", signals: ["adverse"], therapist: true };
          changes.push({ kind: "quarantine", protocol: p, text: st.quarantine[p].reason });
        }
      }
    }
    const esc = escalation(runs, adverse || [], screens || [], now);
    if (esc.active !== st.escalation.active) changes.push({ kind: esc.active ? "escalation" : "escalation ended", text: esc.reasons.join("; ") });
    st.escalation = esc;
    return [st, changes];
  }
  function decide(action, state, timeline, now) {
    const st = state || newState(), reasons = [];
    if (timeline) for (const v of checkEnvelope(timeline)) reasons.push("outside the device safety envelope: " + v.rule + " is " + v.value + ", the limit is " + v.limit);
    const p = action.protocol;
    if (p && p in st.quarantine) { const q = st.quarantine[p]; reasons.push("paused by CONTAIN: " + q.reason + ". It can be restored on the safety page" + (q.therapist ? " with your therapist" : "")); }
    const esc = st.escalation;
    if (esc.active) {
      if (action.kind === "offer" || action.trigger === "device") reasons.push("device offers are paused: " + esc.reasons.join("; "));
      if (action.therapist_led && !action.therapist_present) reasons.push("therapist-led work is paused unless a therapist is present: " + esc.reasons.join("; "));
      if (action.kind === "plan" && !action.therapist_present) reasons.push("a new plan needs a therapist present while practice is paused: " + esc.reasons.join("; "));
    }
    return { decision: reasons.length ? "block" : "allow", reasons };
  }
  function release(state, protocol, by, now) {
    const st = clone(state), q = st.quarantine[protocol];
    if (!q) return [st, "not paused"];
    if ((q.therapist || st.escalation.active) && by !== "therapist") return [st, "needs the therapist: this pause involved an adverse event or practice is paused"];
    delete st.quarantine[protocol]; st.released[protocol] = { at: now, by };
    return [st, "restored"];
  }
  function rollback(history) { const ap = (history || []).filter(h => h.approved); return ap.length >= 2 ? clone(ap[ap.length - 2]) : null; }
  const api = { ENVELOPE, checkEnvelope, drift, escalation, newState, review, decide, release, rollback, r1, t1 };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSContain = api;
})(typeof self !== "undefined" ? self : this);
