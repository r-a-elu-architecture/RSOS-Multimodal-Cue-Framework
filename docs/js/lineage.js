/* Level from content, wherever it goes (spec/FIXES_R5.md §2, amended by FIXES_R6 §2). A saved program with a level above
 * self-guided (a plan node, a saved therapist program, a programmed cue) is an origin. A run inherits an origin's flags
 * when it has one of the origin's distinctive elements (an element no built-in program has; a distinctive text also as
 * whole words in the run's joined text, unless a built-in's joined text has it too), or when it contains at least 80%
 * of the origin's elements. Elements are read from the compiled program, so comments, separators, spacing and look-alike
 * letters do not change them. Used by the player and the device page. Browser: window.RSOSLineage.
 * Needs rsx.js, safety.js (fold), watchdog.js and consent.js.
 */
(function (root) {
  "use strict";
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const BUILTINS = ["interrupt_only", "legacy_vector", "node_lion", "node_observer", "override", "paced_breathing", "ssit_calm", "ssit_higher",
    "ssit_local", "swish", "tier003_command_stack", "tier012_breath_anchor", "tier013_lion_dragon", "tier014_seal", "tier016_stillness",
    "tier406_release", "tier579_glyph"];   // docs/protocols (rsso/tests/test_fixes_r5.py checks the list)
  const TEXT_KINDS = new Set(["say", "see", "cue", "feel", "gesture"]);
  const SHARE = 0.8, LONG = 8;
  const key = t => root.RSOSSafety.fold(t).replace(/[^a-z0-9]+/g, " ").trim();
  const unite = (f, g) => { if (g && g.therapist_led) f.therapist_led = true; if (g && g.memory_work) f.memory_work = true; return f; };
  const some = f => !!(f.therapist_led || f.memory_work);

  function compile(src) { try { return root.RSX.compile(String(src || "")); } catch (e) { return null; } }
  function elements(tl) {
    const s = new Set(); if (!tl) return s;
    const text = t => { const k = key(t); if (k) s.add("t:" + k); };
    for (const e of tl.events || []) {
      if (TEXT_KINDS.has(e.kind) && e.text) text(String(e.text).replace(/\$future/g, " "));   // FIXES_R6 §2: removed, not skipped
      if (e.kind === "tier") { s.add("tier:" + key(e.tier) + ":" + key(e.mode || "")); if (e.word) text(e.word); for (const f of e.frames || []) text(f); if (e.tacton) s.add("code:" + e.tacton); }
      if (e.kind === "pulse") s.add("p:" + e.on + "/" + e.off + "/" + e.count);
    }
    for (const f of tl.futures || []) text(f);
    return s;
  }
  // Built-in elements: loaded once; until then every element of an origin counts as distinctive (stricter).
  let builtin = null, builtinTexts = [];
  const ready = (typeof fetch === "function" ? Promise.all(BUILTINS.map(p => fetch("protocols/" + p + ".rsx").then(r => (r.ok ? r.text() : "")).catch(() => "")))
    .then(srcs => {
      const u = new Set(); for (const s of srcs) { const tl = compile(s); for (const e of elements(tl)) u.add(e); builtinTexts.push(joined(tl)); }
      if (srcs.every(Boolean)) builtin = u; else api.strict = true;   // FIXES_R6 §2 (R6-9): strict, and the page says so
    }) : Promise.resolve())
    .then(() => { api.loaded = true; });
  // The run's texts joined in event order, as keys (FIXES_R6 §2: a sentence split over events still counts).
  function joined(tl) {
    const out = []; if (!tl) return "";
    for (const e of tl.events || []) {
      if (TEXT_KINDS.has(e.kind) && e.text) out.push(key(String(e.text).replace(/\$future/g, " ")));
      if (e.kind === "tier") { if (e.word) out.push(key(e.word)); for (const f of e.frames || []) out.push(key(f)); }
    }
    for (const f of tl.futures || []) out.push(key(f));
    return " " + out.filter(Boolean).join(" ") + " ";
  }

  // A plan node's flags (FIXES_R4 LM1, spec/LOW_MOOD.md).
  function planFlags(plan, i) {
    const f = {}, n = plan && plan.nodes ? plan.nodes[i] : null; if (!n) return f;
    const dx = (plan.dx || []).includes("depression"), memory = (((plan.intake || {}).concerns) || []).includes("ptsd") || (!!plan.therapist_led && !dx);
    if (memory) { f.memory_work = true; if (plan.therapist_led && n.mode === "observer") f.therapist_led = true; }
    if (dx) f.therapist_led = true;
    return f;
  }
  const cache = new Map();
  function origin(id, flags, src, code) {
    if (!some(flags)) return null;
    let els = cache.get(src); if (!els) { els = elements(compile(src)); cache.set(src, els); }
    const distinct = Array.from(els).filter(e => !builtin || !builtin.has(e));
    return { id, flags, els, distinct, code: code || null };
  }
  function origins() {
    const out = [], cues = get("rsos.cues", []) || [], plan = get("rsos.plan", null), W = root.RSOSWatchdog, C = root.RSOSConsent;
    if (plan && Array.isArray(plan.nodes)) plan.nodes.forEach((n, i) => out.push(origin("plan:" + i, planFlags(plan, i), n.program || "", n.tacton)));
    for (const it of get("rsos.thera.programs", []) || []) {
      const f = {}; if (it.level === "clinician_led") f.therapist_led = true; if (it.memory) f.memory_work = true;
      if (W) unite(f, W.levelOfProgram(it.program || "", { cues }));
      out.push(origin("thera:" + it.key, f, it.program || ""));
    }
    if (C && W) for (const c of cues) { const src = C.cueProgram(c); out.push(origin("cue:" + c.id, W.levelOfProgram(src, { cues: [c] }), src)); }
    return out.filter(Boolean);
  }
  // Share of the origin's elements the run contains (FIXES_R6 §2: shared / |origin|).
  const share = (run, o) => { if (!o.size) return 0; let n = 0; for (const x of o) if (run.has(x)) n++; return n / o.size; };
  function has(E, all, d) {
    if (E.has(d)) return true;
    if (!d.startsWith("t:") || d.length - 2 < LONG) return false;
    const w = " " + d.slice(2) + " ";
    if (builtinTexts.some(b => b.includes(w))) return false;   // inside a built-in's text: exact only (R6-4)
    return all.includes(w);
  }
  // The flags a source inherits (FIXES_R5 §2); opts.edited: the text differs from its slot's built-in.
  function flags(source, opts) {
    const o = opts || {}, tl = compile(source), E = elements(tl), all = joined(tl);
    const f = { from: [] };
    for (const g of origins()) if (g.distinct.some(d => has(E, all, d)) || share(E, g.els) >= SHARE) { unite(f, g.flags); f.from.push(g.id); }
    if (o.edited && tl && (tl.events || []).some(e => e.kind === "tier" && key(e.mode || "") === "observer")) { f.therapist_led = true; f.memory_work = true; }
    return f;
  }
  // Codes on the band (R5-11): a sequence is held when any of its codes belongs to a held plan node.
  function codeFlags(code) {
    const toks = String(code || "").trim().split(/\s+/), f = { from: [] };
    for (const g of origins()) if (g.code && toks.includes(g.code)) { unite(f, g.flags); f.from.push(g.id); }
    return f;
  }
  // The words a compiled program actually says and shows (escapes resolved), for the Spine check.
  function texts(tl) {
    if (!tl) return "";
    const out = []; for (const e of tl.events || []) { if (e.text) out.push(e.text); if (e.word) out.push(e.word); for (const f of e.frames || []) out.push(f); }
    for (const f of tl.futures || []) out.push(f);
    return out.join(" ");
  }
  const api = { BUILTINS, ready, loaded: false, strict: false, joined, elements, compile, texts, planFlags, origins, flags, codeFlags, unite };
  root.RSOSLineage = api;
})(typeof window !== "undefined" ? window : globalThis);
