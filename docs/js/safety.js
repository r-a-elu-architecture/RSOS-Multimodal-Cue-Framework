/* Session states for people and agents, JavaScript implementation (spec/CONTAIN.md §9 and §10). Mirrors
 * rsso/rsso/safety.py (identical results, tested): screens, fixed responses and messages, the mode machine
 * (shown as Standard, Stabilisation, Paused: practical, Clinician-led protocol), the categories each state allows,
 * guidance levels, the everyday self-check and the clinician-entered screening result,
 * Spine wording flags, the deep-processing gate and medication-stratified effects. Rules are fixed.
 * Browser: window.RSOSSafety; Node: module.exports.
 */
(function (root) {
  "use strict";
  const MODES = ["NORMAL", "STABILISE", "PRACTICAL_CRISIS", "CRISIS"];
  const SEVERITY = { NORMAL: 0, STABILISE: 1, PRACTICAL_CRISIS: 2, CRISIS: 3 };
  const RECOVERY_H = { mild: 0, moderate: 24, intense: 48, highly_destabilising: 96 };
  const WEEKLY_CAP = { self_chosen: 1, clinician_agreed: 3 };
  const FOOTER = "Research and development framework; not a medical device.";
  const clone = o => JSON.parse(JSON.stringify(o));
  const uniq = xs => xs.filter((x, i) => xs.indexOf(x) === i);
  const has = v => v !== null && v !== undefined;

  function screen(ev) {
    const hits = [];
    if (ev.substances && ev.sedative_prescribed) hits.push("sedative_combination");
    if (ev.arrangements_for_after) hits.push("possible_crisis");
    if (ev.self_harm_signal) hits.push("possible_crisis");
    if (ev.job_loss || ev.housing_risk || ev.no_income) hits.push("practical_crisis");
    if (ev.intensity_mechanism) hits.push("intensity_protocol");
    if ((has(ev.distress) ? ev.distress : 0) >= 7 || (has(ev.sleep_h) ? ev.sleep_h : 8) < 4) hits.push("unstable");
    if (ev.clinical_result === "high") hits.push("clinical_high");
    else if (ev.clinical_result === "moderate") hits.push("clinical_moderate");
    if (ev.history_reference && !hits.includes("possible_crisis")) hits.push("history_check_in");
    return uniq(hits);
  }

  const RESPONSES = {
    possible_crisis: ["ask_safety_directly", "crisis_contacts_for_country", "notify_clinician_view", "pause_module_work"],
    sedative_combination: ["state_breathing_risk_plainly", "route_prescriber_or_emergency_if_symptoms", "notify_clinician_view", "pause_module_work"],
    practical_crisis: ["concrete_next_steps", "offer_human_services", "pause_module_work"],
    intensity_protocol: ["block_protocol", "offer_ordinary_regulation"],
    unstable: ["offer_stabilise_mode", "no_deep_processing_today"],
    history_check_in: ["ask_how_they_are_now", "offer_contacts_without_escalation"],
    clinical_high: ["route_to_clinician_led_protocol", "notify_clinician_view", "pause_module_work"],
    clinical_moderate: ["offer_stabilise_mode", "no_deep_processing_today", "notify_clinician_view"],
  };
  const MESSAGES = {
    possible_crisis: "Self-guided practice is paused. The session continues inside a clinician-led protocol: the " +
      "responsible clinician decides the next step and resumes practice.",
    sedative_combination: "Medication interaction flagged. Self-guided practice is paused until the prescribing " +
      "clinician has reviewed it.",
    practical_crisis: "Practical circumstances flagged. Practice is paused so the next practical step comes first; " +
      "resume when you choose.",
    intensity_protocol: "Intensity methods (temperature extremes, pain, extreme breath-holding, sleep loss) are " +
      "outside RSOS. Use a regulation program instead.",
    unstable: "High intensity or short sleep: the session moved to Stabilisation. Regulation programs only today; leave " +
      "Stabilisation when you choose.",
    history_check_in: "Earlier experience noted for the practitioner's review. Nothing changes in the session.",
    clinical_high: "Screening result: high. The session moves to the clinician-led protocol; the responsible " +
      "clinician resumes practice.",
    clinical_moderate: "Screening result: moderate. Stabilisation: regulation programs only, no deep processing " +
      "today; the practitioner is informed.",
  };

  const MODE_ALLOWED = {
    NORMAL: ["module_work", "deep_processing", "override_cue", "regulating_cue", "practical_support", "crisis_response", "review", "logging"],
    STABILISE: ["regulating_cue", "practical_support", "review", "logging", "crisis_response"],
    PRACTICAL_CRISIS: ["practical_support", "regulating_cue", "logging", "crisis_response"],
    CRISIS: ["crisis_response", "logging"],
  };
  const MODE_NAME = { NORMAL: "Standard", STABILISE: "Stabilisation", PRACTICAL_CRISIS: "Paused: practical", CRISIS: "Clinician-led protocol" };
  const MODE_TEXT = {
    NORMAL: "Standard: every program the person's guidance level allows.",
    STABILISE: "Stabilisation: regulation programs and practical steps only, no deep processing. The person " +
      "leaves it when they choose.",
    PRACTICAL_CRISIS: "Paused: practical. Practical steps and regulation only. The person resumes when they choose.",
    CRISIS: "Clinician-led protocol: self-guided practice is paused; the responsible clinician resumes it.",
  };
  const LEVELS = {
    self_guided: "Everyday states (pressure, nerves, low energy, distraction): self-guided.",
    structured: "Recurring strong states, panic, difficult memories: with consent, self-guided or with a " +
      "practitioner the person chooses (therapist, coach).",
    clinician_led: "Trauma processing, depression work and any acute risk to life: only inside a qualified " +
      "clinician's protocol (including a private psychotherapist or psychiatrist).",
  };

  const REGULATING = ["paced_breathing", "interrupt_only", "tier016_stillness"];   // exactly CONTAIN §9.4 (FIXES_R1 S-3)

  function regulating(a) {   // FIXES_R1 S-4b, W-7
    a = a || {};
    if (a.edited || a.therapist_led || a.deep) return false;
    return REGULATING.includes(a.protocol || "");
  }
  function category(a) {
    if (a.category && a.source === "agent") return a.category;   // FIXES_R1 S-4a
    if (a.kind === "plan") return "module_work";
    if (a.therapist_led || a.deep) return "deep_processing";
    if (regulating(a)) return "regulating_cue";
    return "override_cue";
  }
  const newState = () => ({ mode: "NORMAL", history: [], last: null });
  function allowed(state, action) {
    const mode = state && typeof state === "object" && MODES.includes(state.mode) ? state.mode : "NORMAL", cat = category(action);   // FIXES_R1 W-10
    if (MODE_ALLOWED[mode].includes(cat)) return { ok: true, mode, category: cat, reason: "" };
    return { ok: false, mode, category: cat, reason: "session state " + MODE_TEXT[mode] };
  }
  function go(st, mode, why, by, now) {
    const rec = { from: st.mode, to: mode, why, by, at: now };
    st.mode = mode; st.history = st.history.concat([rec]).slice(-50);
    return rec;
  }
  function observe(state, ev, now) {
    now = now || 0; const st = state && typeof state === "object" && MODES.includes(state.mode) ? clone(state) : newState(), hits = screen(ev);   // FIXES_R3 R3-c
    if (!Array.isArray(st.history)) st.history = [];
    let target = "NORMAL";
    if (hits.includes("possible_crisis") || hits.includes("sedative_combination") || hits.includes("clinical_high")) target = "CRISIS";
    else if (hits.includes("practical_crisis")) target = "PRACTICAL_CRISIS";
    else if (hits.includes("unstable") || hits.includes("clinical_moderate")) target = "STABILISE";
    const actions = uniq([].concat(...hits.map(h => RESPONSES[h])));
    let rec = null;
    if (SEVERITY[target] > SEVERITY[st.mode]) rec = go(st, target, hits.join(","), "screen", now);
    st.last = { at: now, screens: hits };
    return [st, { mode: st.mode, screens: hits, actions, transition: rec, messages: hits.map(h => MESSAGES[h]) }];
  }
  function enterStabilise(state, by, now) {
    const st = clone(state || newState());
    if (SEVERITY[st.mode] >= SEVERITY.STABILISE) return [st, { ok: false, why: "already_at_or_above" }];
    return [st, { ok: true, transition: go(st, "STABILISE", "chosen", by || "person", now || 0) }];
  }
  function exit(state, by, now) {
    const st = state && typeof state === "object" && MODES.includes(state.mode) ? clone(state) : newState();   // FIXES_R4 P1
    if (!Array.isArray(st.history)) st.history = [];
    if (st.mode === "NORMAL") return [st, { ok: false, why: "not_in_safety_mode" }];
    if (st.mode === "CRISIS" && !["clinician", "owner"].includes(by)) return [st, { ok: false, why: "crisis_exit_needs_clinician_or_owner" }];
    if ((st.mode === "STABILISE" || st.mode === "PRACTICAL_CRISIS") && !["person", "clinician", "owner"].includes(by)) return [st, { ok: false, why: "exit_is_the_persons_choice" }];
    return [st, { ok: true, transition: go(st, "NORMAL", "exit", by, now || 0) }];
  }

  const SELF_CHECK = [
    { id: "intensity", text: "Intensity of the state right now (0 none, 10 the most)", kind: "scale" },
    { id: "sleep_h", text: "Hours slept last night", kind: "hours" },
  ];
  const CLINICAL_RESULTS = ["none", "low", "moderate", "high"];
  const CLINICAL_FLAGS = { medication: "Medication interaction (substances with a prescribed sedative)",
    practical: "Practical circumstances (work, housing, income)" };
  // fold(text), identical in both languages (spec/FIXES_R5.md §3, FIXES_R6 §3): line ends, zero-width characters removed,
  // each code point through the generated table (js/foldtable.js, pinned to one Unicode version: compatibility forms and
  // look-alike letters to ASCII, nonspacing marks removed), whitespace and controls to a space, spaces collapsed, A-Z lowercased.
  const FT = root.RSOSFoldTable || (typeof require === "function" ? require("./foldtable.js") : null);
  const isMark = cp => { if (!FT) return false; let lo = 0, hi = FT.MARKS.length - 1;
    while (lo <= hi) { const m = (lo + hi) >> 1, r = FT.MARKS[m]; if (cp < r[0]) hi = m - 1; else if (cp > r[1]) lo = m + 1; else return true; } return false; };
  function fold(text) {
    let s = String(text === null || text === undefined ? "" : text).replace(/\r\n?|\u2028|\u2029/g, "\n").replace(/[\u00ad\u200b-\u200d\u2060\ufeff]/g, "");
    let out = "";
    for (const ch of s) { const cp = ch.codePointAt(0); out += cp < 128 ? ch : isMark(cp) ? "" : FT && Object.prototype.hasOwnProperty.call(FT.MAP, cp) ? FT.MAP[cp] : ch; }
    out = out.replace(/[\x00-\x09\x0b-\x1f \u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]/g, " ");
    return out.replace(/ {2,}/g, " ").replace(/[A-Z]/g, c => c.toLowerCase());
  }
  const NUM = /^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/;
  function eventFromCheck(ans) {
    const flags = new Set(ans.flags || []);
    const ev = { substances: flags.has("medication"), sedative_prescribed: flags.has("medication"), job_loss: flags.has("practical"),
      history_reference: !!ans.history };
    if (CLINICAL_RESULTS.includes(ans.clinical_result)) ev.clinical_result = ans.clinical_result;
    // a non-numeric answer is omitted (FIXES_R4 P1)
    const fin = v => typeof v === "number" ? (Number.isFinite(v) ? v : null)   // FIXES_R5 §3: numbers, or plain ASCII decimal strings
      : typeof v === "string" && NUM.test(v.replace(/^[ \t\n\r]+|[ \t\n\r]+$/g, "")) ? Number(v.replace(/^[ \t\n\r]+|[ \t\n\r]+$/g, "")) : null;
    if (fin(ans.intensity) !== null) ev.distress = fin(ans.intensity);
    if (fin(ans.sleep_h) !== null) ev.sleep_h = fin(ans.sleep_h);
    return ev;
  }

  const SPINE_WORDS = {
    temperature_extreme: ["ice[- ]?bath", "ice[- ]?water", "cold[- ]?plunge", "freezing", "scalding", "boiling",
      "burn(?:ing)? (?:yourself|your skin|the skin)", "very hot (?:bath|water|shower)", "hottest (?:bath|water|shower)", "as hot as (?:you|it) can"],
    pain: ["cause (?:yourself )?pain", "until it hurts", "through the pain", "pinch (?:yourself )?hard",
      "snap (?:a|the) (?:rubber )?band", "hurt yourself", "self[- ]?inflicted"],
    breath_holding_extreme: ["hold (?:your|the) breath (?:as long as|until)", "until you (?:almost )?(?:faint|pass out|black out)",
      "(?:hold|holding) (?:your|the) breath for (?:[2-9]|\\d{2,}) ?min"],
    sleep_deprivation: ["without sleep", "no sleep", "stay awake (?:all night|for \\d+)", "skip sleep", "sleep deprivation"],
    rank_claim: ["\\btop \\d+(?:\\.\\d+)? ?%", "\\b\\d+ in (?:a |one )?(?:thousand|million|billion)",
      "\\b\\d+ (?:in|of) \\d+ (?:thousand|million|billion)", "\\bone in a (?:thousand|million|billion)",
      "rarer than", "\\bpercentile\\b", "better than (?:\\d+ ?%|most people|everyone)", "only (?:a few|\\d+) (?:people )?in the world"],
  };
  const SPINE_VIRTUE = { temperature_extreme: "jin", pain: "jin", breath_holding_extreme: "jin", sleep_deprivation: "jin", rank_claim: "makoto" };
  const SPINE_TEXT = {
    temperature_extreme: "release through extreme heat or cold is not used (Jin): keep warmth comfortable",
    pain: "release through pain is not used (Jin)",
    breath_holding_extreme: "extreme breath-holding is not used (Jin): breathe slowly instead",
    sleep_deprivation: "going without sleep is not used (Jin)",
    rank_claim: "no population ranks about the person (Makoto): RSOS reports your own measures",
  };
  const SPINE_RE = {};
  for (const k of Object.keys(SPINE_WORDS)) SPINE_RE[k] = new RegExp(SPINE_WORDS[k].join("|"));   // on folded text (FIXES_R5 §3)
  function spineFlags(text) {
    const t = fold(text), u = t.replace(/\\./g, " ").replace(/[^a-z0-9%. -]+/g, " ").replace(/ {2,}/g, " ");   // escapes and punctuation as spaces too
    return Object.keys(SPINE_WORDS).filter(k => SPINE_RE[k].test(t) || SPINE_RE[k].test(u)).map(k => ({ flag: k, virtue: SPINE_VIRTUE[k], text: SPINE_TEXT[k] }));
  }

  function mayStartDeepSession(nowH, last, check, done7d, tier) {
    if (!(tier in WEEKLY_CAP)) return { ok: false, why: "consent_tier_required" };
    if (done7d >= WEEKLY_CAP[tier]) return { ok: false, why: "weekly_cap" };
    if (last) {
      if (nowH - last.end_h < RECOVERY_H[last.intensity]) return { ok: false, why: "recovery_window" };
      const c = check || {};
      if (!(c.sleep_ok && c.functioning_ok && !c.craving_spike && c.distress_at_baseline)) return { ok: false, why: "stability_check_not_green" };
    }
    return { ok: true };
  }
  function adjustedEffect(records, key) {
    key = key || "outcome"; const strata = {}, order = [];
    for (const r of records) {
      const m = has(r.med_state) ? r.med_state : "none";
      if (!strata[m]) { strata[m] = { t: [], c: [] }; order.push(m); }
      strata[m][r.treated ? "t" : "c"].push(r[key]);
    }
    const used = [], dropped = []; let num = 0, den = 0;
    const mean = xs => xs.reduce((a, b) => a + b, 0) / xs.length;
    for (const name of order) {
      const s = strata[name];
      if (s.t.length && s.c.length) { const n = s.t.length + s.c.length; num += n * (mean(s.t) - mean(s.c)); den += n; used.push(name); }
      else dropped.push(name);
    }
    const t = records.filter(r => r.treated).map(r => r[key]), c = records.filter(r => !r.treated).map(r => r[key]);
    return { adjusted: den ? num / den : null, crude: t.length && c.length ? mean(t) - mean(c) : null, strata_used: used, strata_dropped: dropped };
  }

  const api = { regulating, MODES, SEVERITY, RECOVERY_H, WEEKLY_CAP, FOOTER, RESPONSES, MESSAGES, MODE_ALLOWED, MODE_NAME, MODE_TEXT, LEVELS, REGULATING,
    SELF_CHECK, CLINICAL_RESULTS, CLINICAL_FLAGS, screen, category, newState, allowed, observe, enterStabilise, exit, eventFromCheck, spineFlags, fold,
    mayStartDeepSession, adjustedEffect };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSSafety = api;
})(typeof self !== "undefined" ? self : this);
