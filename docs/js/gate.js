/* The autonomy gate (spec/GATE.md), part of CONTAIN, JavaScript implementation. Mirrors rsso/rsso/gate.py (identical
 * results, tested): each anchor earns its stage (manual, suggest, automatic, under pressure) from manual training,
 * proven strength, few false alarms and no wear-out or contamination, and loses it again when the evidence weakens.
 * Also consent records, the flag for anything below awareness, and the audit log. Needs docs/js/peak.js.
 * Browser: window.RSOSGate; Node: module.exports.
 */
(function (root) {
  "use strict";
  const P = typeof module !== "undefined" && module.exports ? require("./peak.js") : root.RSOSPeak;
  const STAGES = ["manual", "suggest", "auto", "pressure"];
  const STAGE_NAMES = { manual: "Manual", suggest: "Suggest", auto: "Automatic", pressure: "Under pressure" };
  const NEED = {
    suggest: { captures: 5, status: ["strong", "present"] },
    auto: { captures: 8, status: ["strong"], offers: 10, false_alarm_max: 25, wear_max: 25 },
    pressure: { auto_days: 30, offers: 30, false_alarm_max: 15, wear_max: 10 },
  };
  const OUTCOMES = ["helped", "not_needed", "dismissed", "ignored"], WINDOW = 30, WEAR_WARN = 15;
  const CONSENT_SCOPES = ["speech_profiling", "emotion_detection", "night_cueing", "automatic_firing", "research_sharing"];
  const BELOW_AWARENESS = { night_cueing: "Plays while you sleep", blind_probe: "Sham or real is not shown until afterwards",
    automatic_firing: "The device fires without asking", speech_profiling: "Your words are analysed" };
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);

  function recordOffer(offers, anchorId, ts, outcome, stage, stress) {
    if (!OUTCOMES.includes(outcome)) throw new Error("outcome must be one of " + OUTCOMES.join(", "));
    const o = { anchor: anchorId, ts, outcome, stage: stage || "suggest" };
    if (stress !== undefined && stress !== null) o.stress = !!stress;
    offers.push(o); return o;
  }
  function falseAlarms(offers, anchorId) {
    const mine = offers.filter(o => o.anchor === anchorId && o.outcome !== "ignored").slice(-WINDOW);
    const fa = mine.filter(o => o.outcome === "not_needed").length, helped = mine.filter(o => o.outcome === "helped").length;
    return { offers: mine.length, false: fa, helped, rate: mine.length ? r1(fa / mine.length * 100) : null };
  }
  function wear(anchor) {
    const caps = anchor.captures || [], last = caps.length ? Math.max(...caps.map(c => c.ts || 0)) : null;
    const n = (anchor.uses || []).filter(u => last === null || (u.ts || 0) > last).length;
    const level = n >= NEED.auto.wear_max ? "high" : n >= WEAR_WARN ? "medium" : "low";
    const say = { low: "Fresh: recently paired at a peak.",
      medium: "Used " + n + " times since its last pairing. Pair it at a peak again soon.",
      high: "Used " + n + " times since its last pairing: it may be wearing out. Pair it at a peak before automatic use." }[level];
    return { unpaired_uses: n, level, say };
  }
  const chk = (id, name, met, have, need) => ({ id, name, met: !!met, have, need });
  function gate(anchor, offers, now, optins, history) {
    optins = optins || {}; history = history || {}; now = now || 0;
    const s = P.strength(anchor), c = P.contamination(anchor), w = wear(anchor), fa = falseAlarms(offers, anchor.id), caps = (anchor.captures || []).length;
    const checks = {
      suggest: [chk("captures", "Paired at a peak by hand", caps >= NEED.suggest.captures, caps, NEED.suggest.captures),
        chk("strength", "Probes show an effect", NEED.suggest.status.includes(s.status), s.status, "present or strong"),
        chk("clean", "Not taking on stress", c.risk !== "high", c.risk, "not high")],
      auto: [chk("captures", "Paired at a peak by hand", caps >= NEED.auto.captures, caps, NEED.auto.captures),
        chk("strength", "Probes show a strong effect", NEED.auto.status.includes(s.status), s.status, "strong"),
        chk("offers", "Enough confirmed offers", fa.offers >= NEED.auto.offers, fa.offers, NEED.auto.offers),
        chk("false_alarms", "Few false alarms", fa.rate !== null && fa.rate <= NEED.auto.false_alarm_max, fa.rate, "at most " + NEED.auto.false_alarm_max + "%"),
        chk("wear", "Not worn out", w.unpaired_uses < NEED.auto.wear_max, w.unpaired_uses, "under " + NEED.auto.wear_max),
        chk("clean", "Not taking on stress", c.risk === "low", c.risk, "low")],
    };
    const autoDays = history.auto_since !== null && history.auto_since !== undefined ? (now - history.auto_since) / 86400 : 0;
    checks.pressure = [chk("optin", "You chose pressure practice", !!optins.pressure, !!optins.pressure, true),
      chk("auto_days", "Automatic for a month", autoDays >= NEED.pressure.auto_days, r1(autoDays), NEED.pressure.auto_days),
      chk("offers", "Many confirmed offers", fa.offers >= NEED.pressure.offers, fa.offers, NEED.pressure.offers),
      chk("false_alarms", "Very few false alarms", fa.rate !== null && fa.rate <= NEED.pressure.false_alarm_max, fa.rate, "at most " + NEED.pressure.false_alarm_max + "%"),
      chk("wear", "Fresh", w.unpaired_uses < NEED.pressure.wear_max, w.unpaired_uses, "under " + NEED.pressure.wear_max)];
    let stage = "manual";
    for (const st of ["suggest", "auto", "pressure"]) { if (checks[st].every(k => k.met)) stage = st; else break; }
    const nxt = stage !== "pressure" ? STAGES[Math.min(STAGES.indexOf(stage) + 1, 3)] : null;
    const needs = nxt ? checks[nxt].filter(k => !k.met).map(k => k.name) : [];
    const say = { manual: "Manual only: you fire this anchor yourself.", suggest: "The device may suggest this anchor when it detects stress; you confirm.",
      auto: "The device may fire this anchor by itself, within the safety limits.", pressure: "Automatic, including during your pressure practice." }[stage];
    return { anchor: anchor.id, stage, stage_name: STAGE_NAMES[stage], next: nxt, needs, checks, say, strength: s.status, risk: c.risk, wear: w, false_alarms: fa };
  }
  function hasConsent(consents, scope, now) { now = now || 0; return consents.some(c => c.scope === scope && c.given <= now && (c.withdrawn === null || c.withdrawn > now)); }
  function mayFire(anchor, mode, offers, now, optins, history, consents) {
    const g = gate(anchor, offers, now, optins, history);
    let allowed = STAGES.indexOf(g.stage) >= STAGES.indexOf(mode);
    let reasons = allowed ? [] : ["this anchor is at stage " + g.stage_name.toLowerCase() + "; " + mode + " needs: " + g.checks[mode].filter(k => !k.met).map(k => k.name.toLowerCase()).join("; ")];
    if (allowed && (mode === "auto" || mode === "pressure") && !hasConsent(consents || [], "automatic_firing", now)) { allowed = false; reasons = ["automatic firing has no consent on record"]; }
    return { decision: allowed ? "allow" : "deny", mode, stage: g.stage, reasons, flag: mode === "auto" || mode === "pressure" ? BELOW_AWARENESS.automatic_firing : null };
  }
  function giveConsent(consents, scope, by, ts, note) {
    if (!CONSENT_SCOPES.includes(scope)) throw new Error("scope must be one of " + CONSENT_SCOPES.join(", "));
    const c = { scope, by, given: ts, withdrawn: null, note: note || "" }; consents.push(c); return c;
  }
  function withdrawConsent(consents, scope, ts) { let n = 0; consents.forEach(c => { if (c.scope === scope && c.withdrawn === null) { c.withdrawn = ts; n++; } }); return n; }
  const flag = kind => BELOW_AWARENESS[kind] || null;
  function audit(log, ts, actor, action, anchor, decision, reasons, flg) {
    const e = { ts, actor, action, anchor: anchor === undefined ? null : anchor, decision: decision === undefined ? null : decision, reasons: (reasons || []).slice(), flag: flg === undefined ? null : flg };
    log.push(e); return e;
  }
  function auditSummary(log, since) {
    since = since || 0; const rows = log.filter(e => e.ts >= since), by = {};
    rows.forEach(e => { const k = e.action + ":" + (e.decision || "none"); by[k] = (by[k] || 0) + 1; });
    const sorted = {}; Object.keys(by).sort().forEach(k => { sorted[k] = by[k]; });
    return { entries: rows.length, automatic: rows.filter(e => e.actor === "device").length, denied: rows.filter(e => e.decision === "deny").length,
      flagged: rows.filter(e => e.flag).length, by: sorted };
  }
  const api = { STAGES, STAGE_NAMES, NEED, OUTCOMES, CONSENT_SCOPES, BELOW_AWARENESS, recordOffer, falseAlarms, wear, gate, mayFire,
    giveConsent, withdrawConsent, hasConsent, flag, audit, auditSummary };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.RSOSGate = api;
})(typeof self !== "undefined" ? self : this);
