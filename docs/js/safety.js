/* Safety modes for people and agents, JavaScript implementation (spec/CONTAIN.md §9, S1). Mirrors
 * rsso/rsso/safety.py (identical results, tested): screens, fixed responses and messages, the mode machine
 * (NORMAL, STABILISE, PRACTICAL_CRISIS, CRISIS), the categories each mode allows, the structured check-in,
 * Spine wording flags, the deep-processing gate and medication-stratified effects. Rules are fixed.
 * Browser: window.RSOSSafety; Node: module.exports.
 */
(function (root) {
  "use strict";
  const MODES = ["NORMAL", "STABILISE", "PRACTICAL_CRISIS", "CRISIS"];
  const SEVERITY = { NORMAL: 0, STABILISE: 1, PRACTICAL_CRISIS: 2, CRISIS: 3 };
  const RECOVERY_H = { mild: 0, moderate: 24, intense: 48, highly_destabilising: 96 };
  const WEEKLY_CAP = { self_chosen: 1, clinician_agreed: 3 };
  const HELP = "If you might act on these thoughts, contact local emergency services now. You can also reach a crisis line: " +
    "find one for your country at https://findahelpline.com.";
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
  };
  const MESSAGES = {
    possible_crisis: "Are you safe right now? Practice is paused, because what you said matters more than any " +
      "exercise. " + HELP + " If you have a therapist or doctor, tell them today.",
    sedative_combination: "Alcohol or other drugs together with a prescribed sedative can slow or stop breathing. " +
      "If you feel very sleepy or confused, or your breathing is slow or shallow, call " +
      "emergency services now. Otherwise do not take more, and ask your prescriber or a " +
      "pharmacist today. Practice is paused.",
    practical_crisis: "Losing work, a home or income is a crisis of its own. Practice is paused so you can deal " +
      "with it: write down the one next step for today, and contact local social, housing or " +
      "employment services, or someone you trust, to help with it.",
    intensity_protocol: "This uses heat or cold, pain, holding the breath or going without sleep to force a " +
      "change. RSOS does not run that. Use ordinary regulation instead: slow breathing, " +
      "warmth that is comfortable, rest.",
    unstable: "Today looks like a day for stabilising: high distress or very little sleep. No deep work today. " +
      "Stabilise mode offers only calming and practical steps; you can leave it when you choose.",
    history_check_in: "You mentioned a hard time in the past. How are you now? If any of it is close again, " +
      "talk to someone you trust or a crisis line (https://findahelpline.com). Nothing else " +
      "changes.",
  };
  const MODE_ALLOWED = {
    NORMAL: ["module_work", "deep_processing", "override_cue", "regulating_cue", "practical_support", "crisis_response", "review", "logging"],
    STABILISE: ["regulating_cue", "practical_support", "review", "logging", "crisis_response"],
    PRACTICAL_CRISIS: ["practical_support", "regulating_cue", "logging", "crisis_response"],
    CRISIS: ["crisis_response", "logging"],
  };
  const MODE_TEXT = {
    NORMAL: "Normal: everything the Spine allows.",
    STABILISE: "Stabilise: calming and practical steps only, no deep work. You can leave when you choose.",
    PRACTICAL_CRISIS: "Practical crisis: practical support and calming only. You can leave when you choose.",
    CRISIS: "Crisis: practice is paused; only crisis help. Leaving needs your clinician.",
  };
  const REGULATING = ["paced_breathing", "interrupt_only", "tier016_stillness", "tier012_breath_anchor"];

  function category(a) {
    if (a.category) return a.category;
    if (a.kind === "plan") return "module_work";
    if (a.therapist_led || a.deep) return "deep_processing";
    if (REGULATING.includes(a.protocol || "")) return "regulating_cue";
    return "override_cue";
  }
  const newState = () => ({ mode: "NORMAL", history: [], last: null });
  function allowed(state, action) {
    const mode = (state || newState()).mode, cat = category(action);
    if (MODE_ALLOWED[mode].includes(cat)) return { ok: true, mode, category: cat, reason: "" };
    return { ok: false, mode, category: cat, reason: "the safety mode is " + mode + ": " + MODE_TEXT[mode] };
  }
  function go(st, mode, why, by, now) {
    const rec = { from: st.mode, to: mode, why, by, at: now };
    st.mode = mode; st.history = st.history.concat([rec]).slice(-50);
    return rec;
  }
  function observe(state, ev, now) {
    now = now || 0; const st = clone(state || newState()), hits = screen(ev);
    let target = "NORMAL";
    if (hits.includes("possible_crisis") || hits.includes("sedative_combination")) target = "CRISIS";
    else if (hits.includes("practical_crisis")) target = "PRACTICAL_CRISIS";
    else if (hits.includes("unstable")) target = "STABILISE";
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
    const st = clone(state || newState());
    if (st.mode === "NORMAL") return [st, { ok: false, why: "not_in_safety_mode" }];
    if (st.mode === "CRISIS" && !["clinician", "owner"].includes(by)) return [st, { ok: false, why: "crisis_exit_needs_clinician_or_owner" }];
    if ((st.mode === "STABILISE" || st.mode === "PRACTICAL_CRISIS") && !["person", "clinician", "owner"].includes(by)) return [st, { ok: false, why: "exit_is_the_persons_choice" }];
    return [st, { ok: true, transition: go(st, "NORMAL", "exit", by, now || 0) }];
  }

  const CHECKIN = [
    { id: "now", text: "Right now, are you having thoughts of harming yourself or of not wanting to live?" },
    { id: "after", text: "Have you been putting things in order or making arrangements for after you are gone?" },
    { id: "sedative", text: "Today, have you had alcohol or other drugs while taking a prescribed sedative " +
      "(for example a sleeping pill, a benzodiazepine or an opioid)?" },
    { id: "practical", text: "Are you losing your job, your home or all income right now?" },
    { id: "past", text: "Have you had such thoughts in the past, even if they are not here now?" },
  ];
  function eventFromCheckin(ans) {
    const yes = k => ans[k] === "yes";
    const ev = { self_harm_signal: yes("now") || yes("screen"), arrangements_for_after: yes("after"), substances: yes("sedative"),
      sedative_prescribed: yes("sedative"), job_loss: yes("practical"), history_reference: yes("past") };
    if (has(ans.distress) && ans.distress !== "") ev.distress = Number(ans.distress);
    if (has(ans.sleep_h) && ans.sleep_h !== "") ev.sleep_h = Number(ans.sleep_h);
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
  for (const k of Object.keys(SPINE_WORDS)) SPINE_RE[k] = new RegExp(SPINE_WORDS[k].join("|"), "i");
  function spineFlags(text) {
    const t = String(has(text) ? text : "");
    return Object.keys(SPINE_WORDS).filter(k => SPINE_RE[k].test(t)).map(k => ({ flag: k, virtue: SPINE_VIRTUE[k], text: SPINE_TEXT[k] }));
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

  const api = { MODES, SEVERITY, RECOVERY_H, WEEKLY_CAP, HELP, RESPONSES, MESSAGES, MODE_ALLOWED, MODE_TEXT, REGULATING, CHECKIN,
    screen, category, newState, allowed, observe, enterStabilise, exit, eventFromCheckin, spineFlags, mayStartDeepSession, adjustedEffect };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSSafety = api;
})(typeof self !== "undefined" ? self : this);
