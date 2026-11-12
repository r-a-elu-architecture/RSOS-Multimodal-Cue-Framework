/* RSOS nodes, JavaScript implementation. Mirrors rsso/rsso/nodes.py (identical results, tested in
 * rsso/tests/test_nodes.py): the archetype vibration alphabet, frame check, the planner (intake -> plan with
 * RSX programs) and channel opening. Browser: window.RSOSNodes; Node: module.exports.
 */
(function (root) {
  "use strict";
  const PLANNER = "rsos-planner/1", SHORT = 100, LONG = 300, GAP = 100;
  const ARCHETYPES = {
    LION: { tacton: "..-", glyph: "🦁", mode: "associated", meaning: "Courage and boundaries", frame: "I breathe fully and completely, and I hold my ground", source: "Tier 001" },
    RAVEN: { tacton: ".-.", glyph: "", mode: "associated", meaning: "Intelligence and the wide view", frame: "I am intelligent and I see broadly, from above", source: "" },
    EAGLE: { tacton: "-..", glyph: "", mode: "associated", meaning: "Overview and precision", frame: "I see the whole field clearly and choose my moment", source: "" },
    LEOPARD: { tacton: "...", glyph: "", mode: "associated", meaning: "Agility and focus", frame: "I move lightly and stay fully focused", source: "" },
    TIGER: { tacton: "-.-", glyph: "", mode: "associated", meaning: "Power and drive", frame: "I move with power toward what I choose", source: "" },
    BEAR: { tacton: "--", glyph: "", mode: "associated", meaning: "Strength and stability", frame: "I stand steady and strong", source: "" },
    DRAGON: { tacton: "---", glyph: "🐉", mode: "associated", meaning: "Strength and shadow held together", frame: "I hold my strength and my shadow in one breath", source: "Tier 013" },
    OBSERVER: { tacton: "-", glyph: "∅", mode: "observer", meaning: "No ego: nothing binds, only observed", frame: "Nothing binds. Nothing holds. Only observed", source: "∅ in the tier ledger" }
  };
  const CODE_POOL = [".", "..", ".-", "-.", "....", ".--", "--.", "..--", "-.-.", ".-..", "--..", "...-", "-...", ".---"];
  const CONCERNS = { ptsd: "PTSD or trauma", depression: "Depression", chronic_stress: "Chronic stress", stress: "Stress", anxiety: "Anxiety",
    habits: "Unwanted habits (for example scrolling)", confidence: "Confidence and boundaries", focus: "Focus and work" };
  const TIER_SETS = { associated: ["T001", "T003", "T006", "T014"], calm: ["T012", "T016", "T513", "T576"], observer: ["T016", "T578", "T581", "T433"],
    memory: ["T444"], habits: ["T422", "T441"], futures: ["T535"], reflex: ["T587"] };
  const CHANNEL_DEVICE = { V: "Screen or VR: the node's glyph and representation", A: "Earbuds: the node's sound and spoken frames",
    K: "Wristband: the node's vibration code; posture and gesture", O: "Scent module: the node's scent", G: "Taste cue the person brings (for example a specific mint)" };
  const PROCESS = new Set(["breathe", "breathes", "see", "sees", "move", "moves", "act", "acts", "hold", "holds", "notice", "choose", "stand", "speak", "walk",
    "listen", "observe", "observed", "let", "return", "step", "focus", "say", "feel", "rise", "keep"]);
  const BROAD = ["broadly", "whole", "all", "everything", "from above", "wide", "widely", "clearly", "fully", "completely", "every", "big picture", "the field"];
  const NARROW = ["only", "just", "a bit", "a little", "good at", "try", "trying", "somewhat"];
  const NEGATION = new Set(["not", "no", "never", "don't", "dont", "won't", "can't", "cannot", "stop", "without"]);
  const ABSOLUTE = new Set(["always", "never", "exceptional", "perfect", "perfectly", "best", "unlimited", "infinite", "flawless"]);

  function tactonPulses(code) {
    const out = [];
    for (const c of code || "") { if (c === " ") { if (out.length) out[out.length - 1][1] = 400; continue; } out.push([c === "." ? SHORT : LONG, GAP]); }
    if (out.length) out[out.length - 1][1] = 0; return out;
  }
  const words = t => (String(t).toLowerCase().match(/[a-z']+/g) || []);
  const has = (t, p) => (" " + words(t).join(" ") + " ").indexOf(" " + p + " ") >= 0;

  function frameCheck(text, mode, believability) {
    mode = mode || "associated";
    const w = words(text);
    const trait = has(text, "i am") || has(text, "i'm"), proc = w.some(x => PROCESS.has(x));
    const kind = trait && proc ? "process and trait" : trait ? "trait" : proc ? "process" : "statement";
    const broad = BROAD.filter(p => has(text, p)), narrow = NARROW.filter(p => has(text, p));
    const scope = broad.length && narrow.length ? "mixed" : broad.length ? "broad" : narrow.length ? "narrow" : "neutral";
    const flags = [], tips = [];
    if (narrow.length && mode === "associated") { flags.push("narrowing"); tips.push("Narrowing words (" + narrow.join(", ") + ") shrink the frame. Say what you see or do in full."); }
    if (mode === "associated" && w.some(x => NEGATION.has(x))) { flags.push("negation"); tips.push("Say what you do, not what you don't: the mind has to picture the thing a negation names."); }
    const abs = w.filter(x => ABSOLUTE.has(x));
    if (abs.length) { flags.push("absolute"); tips.push("Absolutes (" + abs.join(", ") + ") are easy to doubt. A process frame such as “I breathe fully and see clearly” is easier to believe."); }
    if (w.includes("will")) { flags.push("future"); tips.push("Use the present tense: the frame describes the state you are in now."); }
    if (w.length > 16) { flags.push("long"); tips.push("Keep a frame under 16 words so it can be said on one exhale."); }
    if (trait && !proc) { flags.push("trait only"); tips.push("Add what you do in that state (I see, I breathe, I move): process frames hold up better than claims about who you are."); }
    if (believability !== null && believability !== undefined && believability < 6) { flags.push("low believability"); tips.push("You rated it " + believability + " of 10. Choose a wording you can believe today; it can grow later."); }
    if (scope === "neutral" && mode === "associated") tips.push("To widen perception, add how far you see or feel: broadly, from above, the whole field.");
    return { text, kind, scope, broad, narrow, flags, tips, score: Math.max(0, 100 - 15 * flags.length) };
  }
  const q = s => '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, "'").replace(/\n/g, " ").trim() + '"';
  const slug = n => (String(n).trim().replace(/[^A-Za-z0-9]+/g, "_").replace(/^_+|_+$/g, "").toUpperCase()) || "NODE";

  function nodeProgram(n, inhale, exhale) {
    inhale = inhale || 4; exhale = exhale || 6;
    const name = n.key, mode = n.mode;
    const L = ["# Node " + n.name + " (" + mode + "), generated by the RSOS planner from an intake (spec/NODES.md).",
      "PROTOCOL node_" + name.toLowerCase() + " " + q("Node: " + n.name), "VERSION 1.0",
      "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4", "BREATH inhale=" + inhale + "s exhale=" + exhale + "s", "", "TIER 1 " + name + " {"];
    for (const ch of ["V", "A", "K", "O", "G"]) if (n.channels[ch]) L.push("  " + ch + " " + q(n.channels[ch]));
    if (n.glyph) L.push("  GLYPH " + q(n.glyph));
    L.push("  WORD " + q(n.meaning));
    for (const f of n.frames) L.push("  FRAME " + q(f));
    L.push("  MODE " + q(mode), "  TACTON " + q(n.tacton), "}", "");
    if (n.contexts.length) L.push("FUTURES " + n.contexts.slice(0, 3).map(q).join(" | "), "");
    const phases = [];
    if (mode === "associated") phases.push(["interrupt", "", ['  SAY "I move, I act"', '  GESTURE "Spine straight, head up, clench your fist"']]);
    else phases.push(["stillness", "dur=3s", ['  FEEL "Stillness. The body stays still"']]);
    phases.push(["inhale", "breath=inhale", ["  ACTIVATE " + name, "  SEE " + q(n.representation)]]);
    n.frames.forEach((f, i) => phases.push(["frame" + (i + 1), "breath=exhale", ["  SAY " + q(f)]]));
    if (mode === "observer") phases.push(["position", "dur=4s", ['  SEE "See it from another position: nothing binds, only observed"']]);
    if (n.contexts.length) phases.push(["futures", "breath=exhale", ["  FEEL " + q("Hold the " + n.name.toLowerCase() + " in you as you enter"),
      "  FOR FUTURE {", '    SEE "$future"', "    WAIT 1s", "  }"]]);
    phases.push(["seal", "breath=exhale", [mode === "associated" ? '  SAY "I own"' : '  FEEL "Let it settle"', '  MARK "installed"']]);
    let prev = "", k = 0;
    for (const [pname, attr, body] of phases) {
      if (attr === "breath=exhale" && prev === "breath=exhale") { k++; L.push("PHASE breathe" + k + " breath=inhale {", '  FEEL "Breathe in"', "}"); }
      L.push(attr ? "PHASE " + pname + " " + attr + " {" : "PHASE " + pname + " {", ...body, "}");
      prev = attr;
    }
    return L.join("\n") + "\n";
  }

  function plan(intake) {
    const concerns = (intake.concerns || []).filter(c => c in CONCERNS), devices = intake.devices || {};
    const used = new Set(), nodes = [], archCodes = Object.values(ARCHETYPES).map(a => a.tacton);
    for (const raw of (intake.nodes || [])) {
      const arch = String(raw.archetype || "").toUpperCase(), base = ARCHETYPES[arch] || {};
      let code;
      if (raw.tacton) code = raw.tacton;
      else if (base.tacton && !used.has(base.tacton)) code = base.tacton;
      else code = CODE_POOL.concat(CODE_POOL.map(x => x + ".")).find(c => !used.has(c) && !archCodes.includes(c));
      used.add(code);
      const mode = raw.mode || base.mode || "associated";
      const name = raw.name || (arch ? arch.charAt(0) + arch.slice(1).toLowerCase() : "") || "Node";
      let frames = (raw.frames || []).map(f => f.trim()).filter(Boolean).slice(0, 5);
      if (!frames.length) frames = base.frame ? [base.frame] : [];
      const rep = raw.representation || (mode === "associated" ? "A sphere of golden light" : "A clear, empty space around you");
      const ch = {}; for (const k of ["V", "A", "K", "O", "G"]) ch[k] = String(raw[k] || "").trim();
      ch.V = ch.V || rep;
      ch.A = ch.A || (frames.length ? frames[0] : "Your own sound");
      ch.K = ch.K || (mode === "associated" ? "Spine straight, warmth in the belly" : "The body still, nothing held");
      const n = { name, key: slug(name), archetype: arch in ARCHETYPES ? arch : "", mode, meaning: raw.state || base.meaning || "", representation: rep,
        channels: ch, glyph: raw.glyph || base.glyph || "", tacton: code, tacton_pulses: tactonPulses(code), frames,
        contexts: (raw.contexts || []).map(c => c.trim()).filter(Boolean).slice(0, 3), rules: (raw.rules || []).map(r => r.trim()).filter(Boolean),
        frame_checks: frames.map(f => frameCheck(f, mode, raw.believability)) };
      n.program = nodeProgram(n, intake.inhale || 4, intake.exhale || 6);
      nodes.push(n);
    }
    const tiers = [], add = k => { for (const t of TIER_SETS[k]) if (!tiers.includes(t)) tiers.push(t); };
    const hasMode = m => nodes.some(n => n.mode === m), inC = (...cs) => cs.some(c => concerns.includes(c));
    if (hasMode("associated")) add("associated");
    if (hasMode("observer")) add("observer");
    if (inC("stress", "chronic_stress", "anxiety")) add("calm");
    if (inC("habits")) add("habits");
    if (inC("ptsd") && hasMode("observer")) add("memory");
    if (nodes.some(n => n.contexts.length)) add("futures");
    add("reflex");
    const metrics = ["SAR", "RSF", "CRI", "ERV", "MCRAL", "PRM", "SEP", "RIF", "LAW"];
    if (intake.author === "therapist") metrics.push("MCI");
    const dose = intake.dose || {}, perDay = Math.trunc(dose.per_day === undefined ? 50 : dose.per_day), days = Math.trunc(dose.days === undefined ? 4 : dose.days);
    const schedule = [{ phase: "Massed practice", per_day: perDay, days, note: "Self-started runs, spread over the waking day, each node in turn." },
      { phase: "Maintenance", per_day: 5, days: 21, note: "Spaced practice, plus every real trigger." },
      { phase: "On triggers", per_day: 0, days: 0, note: "Start the node when the trigger comes; device offers only with consent." }];
    const safety = ["Every node runs with the person's consent; the person can stop any run at once."];
    const therapistLed = inC("ptsd") && hasMode("observer");
    if (therapistLed) safety.push("Observer work with trauma memories is therapist-led: a therapist is present and the screening question is answered before the session.");
    if (inC("ptsd", "depression")) safety.push("Ask the screening question before the first session: Right now, are you in crisis, or having thoughts of harming yourself or not wanting to live?");
    if (nodes.some(n => n.channels.O) || nodes.some(n => n.channels.G)) safety.push("Confirm there is no allergy to the scent or taste before it is used.");
    if (perDay > 20) safety.push("More than 20 a day are self-started; device-triggered offers stay within the safety limits (20 a day, 90 s apart).");
    if (nodes.some(n => n.frame_checks.some(fc => fc.flags.includes("negation") || fc.flags.includes("low believability")))) safety.push("Some frames need rewording before practice (see the frame checks).");
    const phys = intake.physiology || {};
    let detector = null;
    if (phys.resting_hr) detector = { resting_hr: phys.resting_hr, rmssd: phys.rmssd === undefined ? null : phys.rmssd,
      note: "Heart-rate trigger: the detector learns this person's baseline and offers the first node when heart rate rises and variability falls without movement." };
    const devs = ["V", "A", "K", "O", "G"].filter(c => nodes.some(n => n.channels[c]) && devices[c] !== false).map(c => CHANNEL_DEVICE[c]);
    if (devices.hr) devs.push("Heart-rate strap or watch: triggers and the node's body signature");
    if (devices.eeg) devs.push("EEG headset: early detection and the node's signature");
    return { planner: PLANNER, person: intake.person || "me", author: intake.author || "self", concerns: concerns.map(c => CONCERNS[c]),
      symptoms: intake.symptoms || "", triggers: intake.triggers || [], nodes, tiers, metrics, schedule, devices: devs, detector,
      safety, therapist_led: therapistLed, approved: false };
  }

  function median(xs) { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; }
  function channelOpening(runs) {
    const out = {};
    for (const ch of ["V", "A", "K", "O", "G", "thought", "memory"]) {
      const rs = runs.filter(r => String(r.trigger_channel || "").trim() === ch);
      if (!rs.length) continue;
      const done = rs.filter(r => ["1", "1.0", "True", "true"].includes(String(r.completed === undefined ? "1" : r.completed)));
      const lats = done.map(r => (r.latency_s === null || r.latency_s === undefined || r.latency_s === "" ? NaN : Number(r.latency_s))).filter(Number.isFinite);
      out[ch] = { runs: rs.length, completed: done.length, median_latency: lats.length ? median(lats) : null,
        within_3s: lats.length ? Math.floor(1000 * lats.filter(x => x <= 3).length / lats.length + 0.5) / 10 : null };
    }
    return out;
  }
  const api = { PLANNER, ARCHETYPES, CONCERNS, TIER_SETS, tactonPulses, frameCheck, nodeProgram, plan, channelOpening };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSNodes = api;
})(typeof self !== "undefined" ? self : this);
