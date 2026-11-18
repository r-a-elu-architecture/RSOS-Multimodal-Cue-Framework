/* Domain profiles, JavaScript implementation (spec/PROFILES.md). Mirrors rsso/rsso/profiles.py (identical
 * results, tested). A profile changes what people see, never what the engine does: modules keep one canonical
 * vocabulary and this file translates it at display time. In the browser it also adds the domain selector,
 * the home-page chooser and a live translation of each page. Writes only the storage key "rsos.profile".
 * Browser: window.RSOSProfiles; Node: module.exports.
 */
(function (root) {
  "use strict";
  const PROFILES = [
    { id: "personal", name: "Personal", for: "Individuals shaping their own state", max_level: "structured", clinical_module: "none", memory_work: true },
    { id: "coaching", name: "Coaching", for: "Coaches and personal-development practitioners", max_level: "structured", clinical_module: "none", memory_work: true },
    { id: "performance", name: "Performance", for: "Sport, music, stage and executives", max_level: "structured", clinical_module: "none", memory_work: true },
    { id: "learning", name: "Learning", for: "Universities, students, mnemonics and languages", max_level: "structured", clinical_module: "none", memory_work: true },
    { id: "research", name: "Research", for: "Labs, BCI/EEG, haptic devices and trials", max_level: "clinician_led", clinical_module: "study", memory_work: true },
    { id: "workplace", name: "Workplace", for: "Companies and teams; employers see aggregates only", max_level: "structured", clinical_module: "none", memory_work: false },
    { id: "clinical", name: "Clinical", for: "Psychotherapists, psychiatrists and clinics", max_level: "clinician_led", clinical_module: "practitioner", memory_work: true }
  ];
  const IDS = PROFILES.map(p => p.id), DEFAULT = "personal";
  const K = ["rating", "target_state", "memories", "memory", "low_mood", "surges", "ongoing_stress", "changes",
    "person", "persons", "practitioner", "practitioners", "therapy"];
  const ROWS = {
    clinical: ["distress", "negative state", "trauma", "distressing memory", "depression", "anxiety",
      "chronic stress", "symptoms", "client", "clients", "therapist", "therapists", "therapy"],
    personal: ["intensity", "state you want to change", "difficult memories", "difficult memory",
      "low energy or mood", "sudden surges", "ongoing stress", "what you want to change",
      "client", "clients", "practitioner", "practitioners", "guided practice"],
    coaching: ["intensity", "state the client wants to change", "difficult memories", "difficult memory",
      "low energy or mood", "sudden surges", "ongoing stress", "what the client wants to change",
      "client", "clients", "coach", "coaches", "coaching"],
    performance: ["tension", "limiting state", "past setbacks", "past setback", "low drive", "pre-event nerves",
      "ongoing pressure", "performance limiters", "athlete", "athletes", "coach", "coaches", "coaching"],
    learning: ["load", "learning block", "earlier learning experiences", "earlier learning experience",
      "low motivation", "exam nerves", "ongoing study pressure", "learning blocks", "learner", "learners",
      "teacher", "teachers", "tutoring"],
    research: ["intensity", "target state", "aversive memories", "aversive memory", "low affect", "acute arousal",
      "chronic stress", "outcome measures", "participant", "participants", "investigator", "investigators",
      "guided sessions"],
    workplace: ["pressure", "pressure point", "difficult memories", "difficult memory", "low energy",
      "pressure spikes", "ongoing pressure", "focus areas", "team member", "team members", "facilitator",
      "facilitators", "facilitated sessions"]
  };
  const TERMS = {}; K.forEach((k, i) => { TERMS[k] = {}; for (const p of Object.keys(ROWS)) TERMS[k][p] = ROWS[p][i]; });
  const RULES = [
    ["\\bdistress \\(SUDS?\\)", "{rating}"],
    ["\\btherapy sessions?\\b", "{therapy}"],
    ["\\b(?:an? )?(?:anxiety|panic) disorders?\\b", "{surges}"],
    ["\\bclinical judgement\\b", "professional judgement"],
    ["\\bclinical screening\\b", "screening"],
    ["\\bPTSD or trauma\\b", "{memories}"],
    ["\\btrauma symptoms\\b", "{memories}"],
    ["\\btrauma(?:tic)? memories\\b", "{memories}"],
    ["\\b(?:a|an) distressing memory\\b", "{a:memory}"],
    ["\\bdistressing memory\\b", "{memory}"],
    ["\\bthe most distress\\b", "the highest {rating}"],
    ["\\bsymptoms and what they feel like\\b", "{changes} (describe how it feels)"],
    ["\\b(?:a|an) negative state\\b", "{a:target_state}"],
    ["\\bnegative state\\b", "{target_state}"],
    ["\\b(?:a|an) therapist\\b", "{a:practitioner}"],
    ["\\b(?:a|an) (?:client|patient)\\b", "{a:person}"],
    ["\\btherapists\\b", "{practitioners}"],
    ["\\btherapist\\b", "{practitioner}"],
    ["\\b(?:clients|patients)\\b", "{persons}"],
    ["\\b(?:client|patient)\\b", "{person}"],
    ["\\btherapy\\b", "{therapy}"],
    ["\\bchronic stress\\b", "{ongoing_stress}"],
    ["\\bSUDS?\\b", "{rating}"],
    ["\\bdistressing\\b", "intense"],
    ["\\bdistress\\b", "{rating}"],
    ["\\bPTSD\\b", "{memories}"],
    ["\\btrauma\\b", "{memories}"],
    ["\\bdepression\\b", "{low_mood}"],
    ["\\b(?:anxiety|panic)\\b", "{surges}"],
    ["\\bsymptoms\\b", "{changes}"],
    ["\\btherapeutic\\b", "supportive"],
    ["\\btherap\\w+\\b", "{therapy}"],
    ["\\bdiagnosed\\b", "identified"],
    ["\\bdiagnostics\\b", "checks"],
    ["\\bdiagnos\\w*\\b", "assessment"],
    ["\\btraumatic\\b", "difficult"],
    ["\\btrauma\\w+\\b", "{memories}"],
    ["\\bdepress\\w+\\b", "{low_mood}"],
    ["\\bsymptom\\w*\\b", "{changes}"],
    ["\\bdistress\\w+\\b", "intense"],
    ["\\bpanic\\w+\\b", "{surges}"],
    ["\\bpatholog\\w*\\b", "problem pattern"],
    ["\\b(?:C-SSRS|PHQ-9|GAD-7|PCL-5)\\b", "a standard questionnaire"]   // FIXES_WORDING §2
  ];
  const RX = new RegExp(RULES.map(r => "(" + r[0] + ")").join("|"), "gi");
  const SLOT = /\{(a:)?(\w+)\}/g;
  const CLINICAL_WORDS = "\\b(?:SUDS?|PTSD|depress\\w*|trauma\\w*|symptom\\w*|distress\\w*|panic\\w*|anxiety|patients?|therap\\w*" +
    "|clinical screening|clinical judgement|diagnos\\w*|C-SSRS|PHQ-9|GAD-7|PCL-5)\\b";   // FIXES_R1 P-3
  const EXEMPT_PAGES = [];   // FIXES_WORDING §2: research records translated too, wording only

  const valid = p => IDS.includes(p) ? p : DEFAULT;
  const get = p => PROFILES[IDS.indexOf(valid(p))];
  const maxLevel = (p, on) => valid(p) === "research" ? (on ? "clinician_led" : "structured") : get(p).max_level;   // FIXES_R1 W-2
  const LED = /\b(?:therapist|clinician)-led\b/i, THERAPIST = /\btherapist(s?)\b/gi;   // FIXES_R1 P-1
  const clinicianLedText = s => LED.test(s) ? s.replace(THERAPIST, (m, pl) => (m.charAt(0) === "T" ? "Clinician" : "clinician") + pl) : s;
  const clinicalVocab = (p, on) => valid(p) === "clinical" || (valid(p) === "research" && !!on);
  const term = (key, p, on) => TERMS[key][clinicalVocab(p, on) ? "clinical" : valid(p)];
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const article = w => ("aeiou".includes(w.charAt(0).toLowerCase()) ? "an " : "a ") + w;
  const isUp = c => c !== c.toLowerCase();

  function text(s, p, on) {
    if (!s || clinicalVocab(p, on)) return s;
    const id = valid(p);
    s = clinicianLedText(s);
    return s.replace(RX, function () {
      const a = arguments, w = a[0], off = a[RULES.length + 1];
      let g = 1; while (a[g] === undefined) g++;
      let out = RULES[g - 1][1].replace(SLOT, (t, art, k) => art ? article(TERMS[k][id]) : TERMS[k][id]);
      if (isUp(w.charAt(0)) && (w.length === 1 || !isUp(w.charAt(1)) || off === 0)) out = cap(out);
      return out;
    });
  }
  const hasClinicalWords = s => new RegExp(CLINICAL_WORDS, "i").test(s);

  const api = { PROFILES, IDS, DEFAULT, TERMS, RULES, CLINICAL_WORDS, EXEMPT_PAGES, valid, get, maxLevel, clinicalVocab, term, text, hasClinicalWords };

  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }

  /* ---- browser ---- */
  const KEY = "rsos.profile";
  function current() {
    try {
      const q = new URLSearchParams(root.location.search).get("profile");
      if (q && IDS.includes(q)) { localStorage.setItem(KEY, JSON.stringify(q)); return q; }
      return valid(JSON.parse(localStorage.getItem(KEY) || "null"));
    } catch (e) { return DEFAULT; }
  }
  function clinicalOn() { try { return !!(JSON.parse(localStorage.getItem("rsos.clinical") || "{}") || {}).on; } catch (e) { return false; } }
  const P = current();
  // The domain context every gate reads (FIXES_R3 §1), recomputed when the domain or clinical module changes in any
  // tab (FIXES_R4 G2). The page's wording keeps the domain it loaded with until it reloads.
  const domainOf = () => { let p = P; try { p = valid(JSON.parse(localStorage.getItem(KEY) || "null")) || P; } catch (e) {}
    return Object.freeze({ profile: p, max_level: maxLevel(p, clinicalOn()), memory_work_allowed: get(p).memory_work, clinical_vocab: clinicalVocab(p, clinicalOn()) }); };
  root.RSOSDomain = domainOf();
  root.addEventListener("storage", e => { if (!e.key || /rsos\.(profile|clinical)$/.test(e.key)) root.RSOSDomain = domainOf(); });
  const page = (root.location.pathname.split("/").pop() || "index.html");
  const translating = !clinicalVocab(P, clinicalOn()) && !EXEMPT_PAGES.includes(page);
  const SKIP = "script,style,textarea,pre,code,nav,[data-raw],.profilebar";
  const tr = s => text(s, P, clinicalOn());

  function walk(node) {
    if (!translating || !node) return;
    if (node.nodeType === 3) { const el = node.parentElement; if (el && !el.closest(SKIP)) { const v = tr(node.data); if (v !== node.data) node.data = v; } return; }
    if (node.nodeType !== 1 || node.closest(SKIP)) return;
    const els = [node].concat(Array.from(node.querySelectorAll("[placeholder],[title],[aria-label]")));
    for (const e of els) { if (e.closest(SKIP)) continue; for (const at of ["placeholder", "title", "aria-label"]) { const v = e.getAttribute(at); if (v) { const t = tr(v); if (t !== v) e.setAttribute(at, t); } } }
    const w = document.createTreeWalker(node, NodeFilter.SHOW_TEXT); let t;
    while ((t = w.nextNode())) { const el = t.parentElement; if (el && el.closest(SKIP)) continue; const v = tr(t.data); if (v !== t.data) t.data = v; }
  }
  // Switching into the Clinical domain asks first, inline (FIXES_R1 P-5). A link with ?profile=clinical is explicit.
  function choose(id, where) {
    const go = () => { try { localStorage.setItem(KEY, JSON.stringify(id)); } catch (e) {} const u = new URL(root.location.href); u.searchParams.delete("profile"); root.location.replace(u.toString()); };
    if (id !== "clinical" || P === "clinical") return go();
    let c = document.getElementById("profileConfirm");
    if (!c) { c = document.createElement("div"); c.id = "profileConfirm"; c.style.cssText = "margin:8px 0;font-size:14px"; }
    c.replaceChildren(document.createTextNode("The Clinical domain is for clinicians and people working with one. Clinician-led work still needs the clinician present, a recorded screening and, to resume, the clinician's PIN. "));
    const b = document.createElement("button"); b.type = "button"; b.className = "btn"; b.textContent = "Switch to Clinical"; b.addEventListener("click", go);
    const n = document.createElement("button"); n.type = "button"; n.className = "btn quiet"; n.textContent = "Cancel"; n.addEventListener("click", () => { c.remove(); const s = document.getElementById("profileSelect"); if (s) s.value = P; });
    c.append(b, document.createTextNode(" "), n); where.append(c);
  }
  function bar() {
    const h = document.querySelector("header"); if (!h || h.querySelector(".profilebar")) return;
    const d = document.createElement("div"); d.className = "profilebar";
    d.style.cssText = "font-size:13px;margin:6px 0 0;opacity:.85";
    const l = document.createElement("label"); l.textContent = "Domain ";
    const s = document.createElement("select"); s.setAttribute("aria-label", "Domain profile"); s.id = "profileSelect";
    s.style.cssText = "background:transparent;color:inherit;border:1px solid rgba(128,128,128,.45);border-radius:6px;padding:2px 6px;font:inherit;margin-left:4px";
    for (const p of PROFILES) s.append(new Option(p.name, p.id, false, p.id === P));
    s.addEventListener("change", () => choose(s.value, d));
    l.append(s); d.append(l); h.append(d);
  }
  function cards() {
    const box = document.getElementById("profileCards"); if (!box) return;
    box.replaceChildren();
    for (const p of PROFILES) {
      const b = document.createElement("button"); b.type = "button"; b.className = "pcard" + (p.id === P ? " on" : "");
      b.setAttribute("aria-pressed", p.id === P ? "true" : "false");
      const n = document.createElement("b"); n.textContent = p.name; const f = document.createElement("span"); f.textContent = p.for;
      b.append(n, f);
      b.addEventListener("click", () => choose(p.id, box.parentElement || box));
      box.append(b);
    }
  }
  function style() {
    const st = document.createElement("style");
    st.textContent = (clinicalVocab(P, clinicalOn()) ? "[data-hide=clinical]" : "[data-show=clinical]") + "{display:none!important}" +
      (get(P).memory_work ? "" : "[data-memory-work]{display:none!important}");
    document.head.append(st);
  }
  style();
  function init() {
    document.documentElement.setAttribute("data-profile", P);
    bar(); cards();
    if (!translating) return;
    document.title = tr(document.title);
    walk(document.body);
    new MutationObserver(ms => { for (const m of ms) { if (m.type === "characterData") walk(m.target); else m.addedNodes.forEach(walk); if (m.type === "attributes") walk(m.target); } })
      .observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["placeholder", "title", "aria-label"] });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
  root.RSOSProfiles = Object.assign(api, { current: () => P, clinicalOn, translating, t: (key, c) => { const v = term(key, P, clinicalOn()); return c ? cap(v) : v; }, tr });
})(typeof window !== "undefined" ? window : globalThis);
