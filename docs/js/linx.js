/* LINX — the AI interface and routing layer, JavaScript implementation (spec/LINX.md).
 * Mirrors rsso/rsso/linx.py (identical results, tested): understand, converse, suggestFrames, modelPrompt, route, offer.
 * LINX only proposes; the planner builds, the person approves and starts every run.
 * Browser: window.RSOSLinx (needs RSOSNodes); Node: module.exports.
 */
(function (root) {
  "use strict";
  const N = typeof module !== "undefined" && module.exports ? require("./nodes.js") : root.RSOSNodes;
  const SCHEMA = "rsos-linx-proposal/1";
  const LIMITS = { nodes: 6, frames: 5, contexts: 3, triggers: 10, notes: 5, text: 160, frame: 120, sense: 80, note: 240 };
  const CONCERN_WORDS = [
    ["ptsd", ["ptsd", "trauma", "flashback", "nightmare"]],
    ["depression", ["depress", "hopeless", "low mood", "emptiness"]],
    ["anxiety", ["anxi", "panic", "worr"]],
    ["chronic_stress", ["chronic stress", "burnout", "burned out", "burnt out", "exhaust"]],
    ["stress", ["stress", "tense", "tension", "overwhelm"]],
    ["habits", ["scroll", "procrastinat", "habit", "smok", "social media"]],
    ["confidence", ["confiden", "boundar", "saying no", "say no", "assert", "shy"]],
    ["focus", ["focus", "concentrat", "distract"]]];
  const OBSERVER_WORDS = ["observer", "no ego", "nothing binds", "from outside", "from the outside", "detached", "watch it from"];
  const OWN_SYMBOLS = ["wolf", "rabbit", "hero", "owl", "phoenix", "horse", "shark", "warrior", "oak", "mountain", "ocean", "sun",
    "falcon", "hawk", "panther", "elephant", "dolphin", "tree", "river", "star"];
  const CONTEXT_RE = /\b(at|in|during|before|while|after) (work|home|meetings?|the office|school|the gym|bed|sleep|night|the morning|the evening|driving|exams?|presentations?|training|lunch|a conflict|conflicts)\b/g;
  const END = "(?=[.,;!?]| and | when | while | at | in | for |$)";
  const SENSE_RES = [
    ["O", new RegExp("\\b(?:smell|scent|aroma) of ([a-z][a-z ]{1,30}?)" + END)],
    ["O", new RegExp("\\bsmells like ([a-z][a-z ]{1,30}?)" + END)],
    ["G", new RegExp("\\btaste of ([a-z][a-z ]{1,30}?)" + END)],
    ["G", new RegExp("\\btastes like ([a-z][a-z ]{1,30}?)" + END)],
    ["A", new RegExp("\\b(?:sound|song|melody|music) of ([a-z][a-z ]{1,30}?)" + END)],
    ["A", new RegExp("\\blistening to ([a-z][a-z ]{1,30}?)" + END)],
    ["V", new RegExp("\\b(?:image|picture|colou?r) of ([a-z][a-z ]{1,30}?)" + END)],
    ["V", /\b(golden light|white light|blue light|a sphere of [a-z]+ light)\b/],
    ["K", new RegExp("\\bfeeling of ([a-z][a-z ]{1,30}?)" + END)]];
  const STATE_RE = /\b(?:wants? to|wish(?:es)? to|would like to|needs? to) (?:feel|be|become|stay) (?:more )?([a-z][a-z ,]{1,40}?)(?=[.;!?]| when | while | at | in | so |$)/;
  const STATE2_RE = /\b(?:i|she|he|they|we) (?:wants?|need|needs) (?!to |a |an |the |my |her |his |their |our |it )([a-z][a-z ]{1,40}?)(?=[.,;!?]| when | while | at | in | so | like |$)/;
  const TRIGGER_RE = /\b(?:when|whenever|every time|each time|triggered by) ([a-z][a-z' ]{2,50}?)(?=[.,;!?]| i | and i |$)/g;
  const QUOTE_RE = /["“”«»]([^"“”«»]{3,120})["“”«»]/g;
  const QUOTE_ONE = /["“”«»]([^"“”«»]{3,120})["“”«»]/;
  const FRAME_RE = /\b(?:frame|statement|affirmation|i say|i tell myself)(?: is)?:? ([A-Za-z][^.!?"“”]{3,110})/i;
  const ANTONYM = { afraid: "calm", scared: "steady", anxious: "calm", nervous: "steady", weak: "strong", stressed: "calm",
    tired: "awake", lazy: "active", confused: "clear", alone: "connected", angry: "calm", sad: "open",
    distracted: "focused", small: "whole", stuck: "free", lost: "clear", overwhelmed: "steady", tense: "relaxed" };
  const GERUND = { seeing: "see", focusing: "focus", speaking: "speak", learning: "learn", listening: "listen", leading: "lead",
    thinking: "think", remembering: "remember", moving: "move", breathing: "breathe", deciding: "decide", acting: "act",
    holding: "hold", standing: "stand", staying: "stay", saying: "say", choosing: "choose", keeping: "keep" };
  const NARROW_STRIP = /\b(only|just|a bit|a little|somewhat|try to|trying to)\s+/gi;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const len = s => [...s].length;
  const clone = o => JSON.parse(JSON.stringify(o));
  const empty = v => v === null || v === undefined || v === "" || (Array.isArray(v) && !v.length);

  function fmt1(x, sign) {
    const k = Math.floor(x * 10 + 0.5), a = Math.abs(k);
    return (sign ? (k >= 0 ? "+" : "-") : (k < 0 ? "-" : "")) + Math.floor(a / 10) + "." + (a % 10);
  }
  const clean = s => s.replace(/\s+/g, " ").replace(/^[ ,.;]+|[ ,.;]+$/g, "");
  const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  const sentences = text => text.split(/[.!?]+\s+|\n+/).filter(s => s.trim());
  function concerns(low) {
    const out = [];
    for (const [key, stems] of CONCERN_WORDS) if (stems.some(st => new RegExp("\\b" + esc(st)).test(low))) out.push(key);
    if (out.includes("chronic_stress") && out.includes("stress")) out.splice(out.indexOf("stress"), 1);
    return out;
  }
  function symbol(low) {
    for (const a of Object.keys(N.ARCHETYPES)) if (a !== "OBSERVER" && new RegExp("\\b" + a.toLowerCase() + "s?\\b").test(low)) return [a, ""];
    if (OBSERVER_WORDS.some(w => low.includes(w))) return ["OBSERVER", ""];
    for (const w of OWN_SYMBOLS) if (new RegExp("\\b(?:a|an|the|my|like|as) " + w + "\\b").test(low)) return ["", cap(w)];
    return ["", ""];
  }
  function understand(text) {
    const out = { concerns: [], nodes: [], triggers: [], physiology: {}, dose: {}, author: "" };
    const lowAll = text.toLowerCase();
    out.concerns = concerns(lowAll);
    if (/\bmy (?:client|patient)s?\b/.test(lowAll)) out.author = "therapist";
    let m = /\bresting (?:heart rate|hr|pulse)(?: is| of|:)? ?(\d{2,3})/.exec(lowAll); if (m) out.physiology.resting_hr = +m[1];
    m = /\b(?:hrv|rmssd)(?: is| of|:)? ?(\d{1,3})/.exec(lowAll); if (m) out.physiology.rmssd = +m[1];
    m = /\b(\d{1,3}) (?:times|runs|repetitions) (?:a|per) day\b/.exec(lowAll); if (m) out.dose.per_day = +m[1];
    m = /\bfor (\d{1,2}) days\b/.exec(lowAll); if (m) out.dose.days = +m[1];
    let current = null, pending = {};
    const nodeFor = (arch, own) => {
      for (const n of out.nodes) if ((arch && n.archetype === arch) || (own && n.name === own)) return n;
      const n = arch ? { archetype: arch } : { name: own }; out.nodes.push(n); return n;
    };
    const addTo = (t, k, v) => { if (!(k in t)) t[k] = []; if (!t[k].includes(v)) t[k].push(v); };
    for (const sent of sentences(text)) {
      const low = sent.toLowerCase(), [arch, own] = symbol(low);
      if (arch || own) {
        current = nodeFor(arch, own);
        if (Object.keys(pending).length) {
          for (const [k, v] of Object.entries(pending)) {
            if (k === "frames" || k === "contexts") { if (!(k in current)) current[k] = []; for (const x of v) if (!current[k].includes(x)) current[k].push(x); }
            else if (!(k in current)) current[k] = v;
          }
          pending = {};
        }
      }
      const target = current !== null ? current : pending;
      const sm = STATE_RE.exec(low) || STATE2_RE.exec(low); if (sm && !("state" in target)) target.state = clean(sm[1]);
      for (const qm of sent.matchAll(QUOTE_RE)) addTo(target, "frames", clean(qm[1]));
      const fm = FRAME_RE.exec(sent); if (fm && !QUOTE_ONE.test(sent)) addTo(target, "frames", clean(fm[1]));
      for (const [ch, rx] of SENSE_RES) { const x = rx.exec(low); if (x && !target[ch]) target[ch] = cap(clean(x[1])); }
      for (const cm of low.matchAll(CONTEXT_RE)) addTo(target, "contexts", cap(cm[0]));
      for (const tm of low.matchAll(TRIGGER_RE)) { const t = cap(clean(tm[1])); if (t && !out.triggers.includes(t)) out.triggers.push(t); }
      if (arch === "OBSERVER" && current !== null) current.mode = "observer";
    }
    if (Object.keys(pending).length) out.nodes.push(Object.assign({ archetype: "" }, pending));
    return out;
  }
  function merge(intake, patch) {
    const it = clone(intake || {});
    for (const k of ["concerns", "triggers"]) { if (!it[k]) it[k] = []; for (const v of patch[k] || []) if (!it[k].includes(v)) it[k].push(v); }
    for (const k of ["physiology", "dose"]) if (patch[k] && Object.keys(patch[k]).length) it[k] = Object.assign(it[k] || {}, patch[k]);
    if (patch.author) it.author = patch.author;
    if (!it.nodes) it.nodes = [];
    const nodes = it.nodes;
    for (const pn of patch.nodes || []) {
      const ref = pn.ref; let tgt = null;
      if (Number.isInteger(ref) && ref >= 0 && ref < nodes.length) tgt = nodes[ref];
      else for (const n of nodes) if ((pn.archetype && n.archetype === pn.archetype) || (pn.name && n.name === pn.name)) { tgt = n; break; }
      if (tgt === null) { tgt = {}; nodes.push(tgt); }
      for (const [k, v] of Object.entries(pn)) {
        if (k === "ref" || empty(v)) continue;
        if (k === "frames" || k === "contexts" || k === "rules") { if (!tgt[k]) tgt[k] = []; for (const x of v) if (!tgt[k].includes(x)) tgt[k].push(x); }
        else tgt[k] = v;
      }
    }
    return it;
  }
  const QUESTIONS = {
    concerns: "What is happening that you want to change? For example stress at work, flashbacks, or scrolling instead of working.",
    symbol: "Which symbol should hold the state you want: a lion for courage and boundaries, a raven for the wide view, the observer for no ego where nothing binds, or a symbol of your own?",
    state: "What state should the {name} hold? For example calm confidence, or clear focus.",
    frame: "What do you say to yourself in that state? A short sentence in the present tense, like “I breathe fully and completely, and I hold my ground”.",
    senses: "What do you see, hear, smell or taste in that state? Name any you like: a colour, a song, a scent, a taste.",
    contexts: "Where will you use the {name}? Up to three situations, for example at work, before sleep.",
    triggers: "What usually sets off the state you want to change? For example raised voices, or opening social media." };
  const SKIP = /^\s*(no|none|nothing|skip|pass|not sure|don't know|dont know|-)\s*[.!]?\s*$/i;
  const nameOf = n => n.name || (n.archetype ? n.archetype.charAt(0) + n.archetype.slice(1).toLowerCase() : "node");
  function next(intake, asked) {
    const nodes = intake.nodes || [];
    if (!(intake.concerns || []).length && !asked.includes("concerns")) return ["concerns", -1];
    if (!nodes.length) return asked.includes("symbol") ? [null, -1] : ["symbol", -1];
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i], A = N.ARCHETYPES[n.archetype || ""];
      if (!n.state && !asked.includes("state:" + i) && !(A && A.meaning)) return ["state", i];
      if (!(n.frames || []).length && !asked.includes("frame:" + i)) return ["frame", i];
      if (!["A", "O", "G"].some(c => n[c]) && !asked.includes("senses:" + i)) return ["senses", i];
      if (!(n.contexts || []).length && !asked.includes("contexts:" + i)) return ["contexts", i];
    }
    if (!(intake.triggers || []).length && !asked.includes("triggers")) return ["triggers", -1];
    return [null, -1];
  }
  function heard(patch, intake) {
    const said = [];
    if ((patch.concerns || []).length) said.push("what is happening: " + patch.concerns.map(c => N.CONCERNS[c].toLowerCase()).join(", "));
    for (const n of patch.nodes || []) {
      const bits = [];
      if (n.state) bits.push("the state " + n.state);
      if ((n.frames || []).length) bits.push("the frame “" + n.frames[0] + "”");
      for (const [ch, word] of [["V", "seen:"], ["A", "heard:"], ["O", "smell:"], ["G", "taste:"], ["K", "felt:"]]) if (n[ch]) bits.push(word + " " + n[ch].toLowerCase());
      if ((n.contexts || []).length) bits.push("for " + n.contexts.map(c => c.toLowerCase()).join(", "));
      const nodes = intake.nodes || [];
      const who = Number.isInteger(n.ref) && n.ref >= 0 && n.ref < nodes.length ? nameOf(nodes[n.ref]) : nameOf(n);
      said.push(who + (bits.length ? ": " + bits.join("; ") : ""));
    }
    if ((patch.triggers || []).length) said.push("triggers: " + patch.triggers.map(t => t.toLowerCase()).join(", "));
    return said;
  }
  const SENSE_WORDS = [["O", ["cedar", "lavender", "rose", "citrus", "sandalwood", "pine", "vanilla", "eucalyptus", "jasmine", "incense", "scent", "smell", "perfume"]],
    ["G", ["mint", "chocolate", "lemon", "honey", "ginger", "salt", "taste", "tea", "coffee"]],
    ["A", ["song", "music", "drum", "bell", "waves", "rain", "melody", "voice", "piano", "guitar", "sound", "hum"]],
    ["V", ["gold", "golden", "light", "blue", "white", "red", "green", "sun", "fire", "colour", "color", "sphere", "image"]]];
  function sensesFromList(raw) {
    const out = {};
    for (const item of raw.split(/,|;| and /).map(x => x.trim()).filter(Boolean)) {
      const low = item.toLowerCase();
      const hit = SENSE_WORDS.find(([, ws]) => ws.some(w => new RegExp("\\b" + w).test(low)));
      const ch = hit ? hit[0] : "K";
      if (!(ch in out)) out[ch] = cap([...item].slice(0, LIMITS.sense).join(""));
    }
    return out;
  }
  function converse(state, text) {
    const st = clone(state || { intake: {}, asked: [], pending: null });
    const patch = understand(text), slot = st.pending;
    if (slot && !SKIP.test(text)) {
      const [kind, idx] = slot.split(":"), i = idx !== undefined ? +idx : -1;
      const nodes = st.intake.nodes || [], node = i >= 0 && i < nodes.length ? nodes[i] : null, raw = clean(text);
      if (kind === "concerns" && !patch.concerns.length) st.intake.symptoms = ((st.intake.symptoms || "") + " " + raw).trim();
      else if (kind === "symbol" && !patch.nodes.length && raw) patch.nodes = [{ name: cap(raw.split(" ").pop()) }];
      else if (kind === "triggers" && !patch.triggers.length) patch.triggers = raw.split(/,| and |\n/).map(c => c.trim()).filter(Boolean).map(cap).slice(0, 5);
      else if (node !== null) {
        for (const p of patch.nodes) if (!p.archetype && !p.name) p.ref = i;
        const have = key => patch.nodes.some(p => !empty(p[key]));
        if (kind === "state" && !have("state")) patch.nodes.push({ ref: i, state: [...raw].slice(0, 60).join("") });
        else if (kind === "frame" && !have("frames")) patch.nodes.push({ ref: i, frames: [[...raw].slice(0, LIMITS.frame).join("")] });
        else if (kind === "contexts" && !have("contexts")) patch.nodes.push({ ref: i, contexts: raw.split(/,| and /).map(c => c.trim()).filter(Boolean).map(cap).slice(0, 3) });
        else if (kind === "senses") patch.nodes.push(Object.assign(sensesFromList(raw), { ref: i }));
      }
    }
    const known = st.intake.nodes || [], target = slot && slot.includes(":") ? +slot.split(":")[1] : known.length - 1;
    patch.nodes = patch.nodes.filter(p => {
      if (!("ref" in p) && !p.archetype && !p.name) { if (known.length) p.ref = target; else if (!(p.state || (p.frames || []).length)) return false; }
      return true;
    });
    st.intake = merge(st.intake, patch);
    if (slot) st.asked.push(slot);
    const h = heard(patch, st.intake);
    const [kind, i] = next(st.intake, st.asked);
    const noted = h.length ? "Noted " + h.join("; ") + ". " : "";
    if (kind === null) { st.pending = null; return { state: st, reply: noted + "Your plan is ready on the right. Read every node; change anything in the form, or tell me more.", done: true }; }
    st.pending = i < 0 ? kind : kind + ":" + i;
    return { state: st, reply: noted + QUESTIONS[kind].replace("{name}", i >= 0 ? nameOf(st.intake.nodes[i]).toLowerCase() : "node"), done: false };
  }
  function suggestFrames(text, mode) {
    mode = mode || "associated";
    const base = N.frameCheck(text, mode), cands = [], t = clean(text);
    const m = /^i (?:will not|won't|am not|do not|don't|will never|never) (?:be |feel |get )?([a-z]+)(.*)$/i.exec(t);
    if (m && m[1].toLowerCase() in ANTONYM) { const rest = clean(m[2]); cands.push("I am " + ANTONYM[m[1].toLowerCase()] + (rest ? " " + rest : "") + " and I breathe fully"); }
    let s = t.replace(NARROW_STRIP, "");
    s = s.replace(/\bi will be\b/gi, "I am").replace(/\bi will (?!not\b|never\b)/gi, "I ");
    const gm = /\bi am good at ([a-z]+ing)\b/i.exec(s);
    if (gm && gm[1].toLowerCase() in GERUND) {
      s = s.slice(0, gm.index) + "I " + GERUND[gm[1].toLowerCase()] + s.slice(gm.index + gm[0].length);
      s = s.replace(/\bsee things\b/gi, "see broadly and clearly");
    } else s = s.replace(/\bi am good at\b/gi, "I am skilled at");
    if (s !== t) cands.push(s);
    if (/\bsee\b/i.test(s) && !/\b(broadly|clearly|whole|from above)\b/i.test(s)) cands.push(s.replace(/\bsee\b/i, "see broadly"));
    const chk = N.frameCheck(s, mode);
    if (chk.flags.includes("trait only")) cands.push(s.replace(/[ .]+$/, "") + ", and I breathe fully and completely");
    if (mode === "associated" && chk.scope === "neutral" && !chk.flags.includes("trait only")) cands.push(s.replace(/[ .]+$/, "") + ", fully and completely");
    const out = [], seen = new Set([text.trim().toLowerCase()]);
    for (let c of cands) {
      c = cap(clean(c));
      if (seen.has(c.toLowerCase())) continue;
      seen.add(c.toLowerCase());
      const fc = N.frameCheck(c, mode);
      if (fc.flags.includes("negation") || fc.flags.includes("future")) continue;
      if (fc.score > base.score || (fc.score === base.score && fc.broad.length > base.broad.length)) out.push({ text: c, score: fc.score, scope: fc.scope, kind: fc.kind });
    }
    out.sort((a, b) => b.score - a.score);
    return out.slice(0, 3);
  }
  function modelPrompt(ctx) {
    const it = ctx.intake || {}, plan = ctx.plan || {}, runs = ctx.runs || [];
    const L = ["You are LINX, the AI layer of RSOS (https://r-a-elu-architecture.github.io/RSOS-Multimodal-Cue-Framework/).",
      "RSOS installs resourceful states as nodes: a state held as one unit, with cues on every sense (V seen, A heard, K felt, O smell, G taste), " +
      "a vibration code, a glyph, a mode (associated: in the body; observer: nothing binds, only observed) and the mental frame said in that state.",
      "Rules: propose only; the person approves and starts every run. Do not diagnose. Frames are short, present tense, about what the person does " +
      "(I breathe, I see), broad rather than narrow, and believable. Use the person's own words where you can. Point out anything a therapist should review.",
      "", "Current state of this person's system:"];
    if ((it.concerns || []).length) L.push("- What is happening: " + it.concerns.map(c => N.CONCERNS[c] || c).join(", "));
    if ((it.triggers || []).length) L.push("- Triggers: " + it.triggers.join("; "));
    const nodes = (plan.nodes && plan.nodes.length ? plan.nodes : null) || it.nodes || [];
    nodes.forEach((n, i) => {
      const ch = n.channels && Object.keys(n.channels).length ? n.channels : Object.fromEntries([..."VAKOG"].filter(k => n[k]).map(k => [k, n[k]]));
      L.push("- Node " + i + " " + (n.name || n.archetype || "own") + " (" + (n.mode || "associated") + "): state " + (n.meaning || n.state || "-") +
        "; frames " + JSON.stringify(n.frames || []) + "; cues " + JSON.stringify(Object.fromEntries(Object.entries(ch).filter(([, v]) => v))) +
        "; contexts " + JSON.stringify(n.contexts || []));
    });
    if ((plan.tiers || []).length) L.push("- Ledger tiers in use: " + plan.tiers.join(", "));
    if (runs.length) {
      const by = {};
      for (const r of runs) if (!empty(r.sud_before) && !empty(r.sud_after)) (by[r.protocol || "?"] = by[r.protocol || "?"] || []).push(Number(r.sud_after) - Number(r.sud_before));
      L.push("- Practice so far: " + runs.length + " runs" + Object.keys(by).sort().map(p => "; " + p + ": " + by[p].length + " rated, mean change in distress " + fmt1(by[p].reduce((a, b) => a + b, 0) / by[p].length, true)).join(""));
    }
    L.push("", "Reply with JSON only, in this form (leave out anything you do not change):",
      JSON.stringify({ schema: SCHEMA, nodes: [{ ref: "index of an existing node, or omit for a new node", name: "", archetype: "LION|RAVEN|EAGLE|LEOPARD|TIGER|BEAR|DRAGON|OBSERVER|",
        mode: "associated|observer", state: "", frames: [""], V: "", A: "", K: "", O: "", G: "", contexts: [""] }],
      concerns: Object.keys(N.CONCERNS), triggers: [""], notes_for_therapist: [""] }));
    return L.join("\n") + "\n";
  }
  const UNSAFE = /\b(kill|die|dying|suicid\w*|self-harm|harm myself|hurt myself|starve|purge|worthless|hate myself)\b/i;
  const ACTIONS = /^(auto_?)?(start|run|execute|play|fire|trigger)(_now)?$|_now$/;   // field names that would act instead of propose
  const NODE_KEYS = ["ref", "name", "archetype", "mode", "state", "frames", "V", "A", "K", "O", "G", "contexts"];
  function route(proposal, intake) {
    const rejected = [], applied = [];
    if (!proposal || typeof proposal !== "object" || Array.isArray(proposal)) return { intake: clone(intake || {}), applied: [], rejected: [{ path: "", reason: "not a JSON object" }] };
    if (proposal.schema !== SCHEMA) return { intake: clone(intake || {}), applied: [], rejected: [{ path: "schema", reason: "expected " + SCHEMA }] };
    for (const k of Object.keys(proposal).sort()) {
      if (ACTIONS.test(k.toLowerCase())) rejected.push({ path: k, reason: "LINX may only propose: the person starts every run" });
      else if (!["schema", "nodes", "concerns", "triggers", "notes_for_therapist"].includes(k)) rejected.push({ path: k, reason: "unknown field" });
    }
    const patch = { concerns: [], triggers: [], nodes: [] };
    const textOk = (path, v, limit) => {
      if (typeof v !== "string" || !v.trim()) return null;
      if (len(v) > limit) { rejected.push({ path, reason: "longer than " + limit + " characters" }); return null; }
      if (UNSAFE.test(v)) { rejected.push({ path, reason: "unsafe wording: held for the person and their therapist" }); return null; }
      return v.trim();
    };
    for (const c of proposal.concerns || []) { if (c in N.CONCERNS) patch.concerns.push(c); else rejected.push({ path: "concerns", reason: "unknown concern '" + c + "'" }); }
    (proposal.triggers || []).slice(0, LIMITS.triggers).forEach((t, j) => { const v = textOk("triggers." + j, t, LIMITS.text); if (v) patch.triggers.push(v); });
    const nodes = (intake || {}).nodes || [];
    (proposal.nodes || []).slice(0, LIMITS.nodes).forEach((pn, j) => {
      const p = "nodes." + j;
      if (!pn || typeof pn !== "object" || Array.isArray(pn)) { rejected.push({ path: p, reason: "not an object" }); return; }
      const out = {};
      if (Number.isInteger(pn.ref)) {
        if (pn.ref >= 0 && pn.ref < nodes.length) out.ref = pn.ref;
        else { rejected.push({ path: p + ".ref", reason: "no such node" }); return; }
      }
      for (const k of Object.keys(pn).sort()) {
        if (ACTIONS.test(k.toLowerCase())) rejected.push({ path: p + "." + k, reason: "LINX may only propose: the person starts every run" });
        else if (!NODE_KEYS.includes(k)) rejected.push({ path: p + "." + k, reason: "unknown field" });
      }
      const arch = pn.archetype || "";
      if (arch) { if (arch in N.ARCHETYPES) out.archetype = arch; else rejected.push({ path: p + ".archetype", reason: "unknown archetype '" + arch + "'" }); }
      if (pn.mode) { if (pn.mode === "associated" || pn.mode === "observer") out.mode = pn.mode; else rejected.push({ path: p + ".mode", reason: "mode is associated or observer" }); }
      for (const [k, lim] of [["name", 40], ["state", 60], ["V", LIMITS.sense], ["A", LIMITS.sense], ["K", LIMITS.sense], ["O", LIMITS.sense], ["G", LIMITS.sense]]) {
        const v = textOk(p + "." + k, pn[k], lim); if (v) out[k] = v;
      }
      const nodeMode = out.mode || ("ref" in out ? nodes[out.ref].mode : null) || (N.ARCHETYPES[arch] || {}).mode || "associated";
      const frames = [];
      (pn.frames || []).slice(0, LIMITS.frames).forEach((f, q) => {
        const v = textOk(p + ".frames." + q, f, LIMITS.frame); if (!v) return;
        const fc = N.frameCheck(v, nodeMode);
        if (fc.score < 70 || fc.flags.includes("negation")) { rejected.push({ path: p + ".frames." + q, reason: "frame check " + fc.score + "/100: " + fc.flags.join(", ") }); return; }
        frames.push(v);
      });
      if (frames.length) out.frames = frames;
      const ctx = []; (pn.contexts || []).slice(0, LIMITS.contexts).forEach((c, q) => { const v = textOk(p + ".contexts." + q, c, LIMITS.text); if (v) ctx.push(v); });
      if (ctx.length) out.contexts = ctx;
      if (Object.keys(out).length > ("ref" in out ? 1 : 0)) { patch.nodes.push(out); applied.push(p + ": " + Object.keys(out).filter(k => k !== "ref").join(", ")); }
    });
    if (patch.concerns.length) applied.push("concerns: " + patch.concerns.join(", "));
    if (patch.triggers.length) applied.push("triggers: " + patch.triggers.length);
    const notes = []; (proposal.notes_for_therapist || []).slice(0, LIMITS.notes).forEach((n, q) => { const v = textOk("notes_for_therapist." + q, n, LIMITS.note); if (v) notes.push(v); });
    const res = merge(intake || {}, patch);
    if (notes.length) { res.notes_for_therapist = (res.notes_for_therapist || []).concat(notes); applied.push("notes for the therapist: " + notes.length); }
    return { intake: res, applied, rejected };
  }
  const STOP = new Set(["the", "and", "with", "for", "from", "when", "into"]);
  const words = s => new Set(((s || "").toLowerCase().match(/[a-z]+/g) || []).filter(w => w.length > 2 && !STOP.has(w)));
  function offer(event, plan, runs, gov, now) {
    if (!plan || !(plan.nodes || []).length) return { node: null, reason: "no node plan" };
    if (!plan.approved) return { node: null, reason: "the plan is not approved yet" };
    gov = gov || {}; now = now || 0;
    const starts = (gov.starts || []).filter(s => now - s < 86400);
    if (gov.last_start !== null && gov.last_start !== undefined && now - gov.last_start < 90) return { node: null, reason: "wait: at least 90 s between runs" };
    if (starts.filter(s => now - s < 3600).length >= 6) return { node: null, reason: "limit: 6 device-offered runs an hour" };
    if (starts.length >= 20) return { node: null, reason: "limit: 20 device-offered runs a day" };
    const src = event.source || "hr", ev = words(event.text || ""), trig = new Set();
    for (const t of (plan.intake || {}).triggers || plan.triggers || []) for (const w of words(t)) trig.add(w);
    let best = null, bestScore = null, why = "";
    plan.nodes.forEach((n, i) => {
      let score = 0; const reasons = [], ctx = new Set();
      for (const c of n.contexts || []) for (const w of words(c)) ctx.add(w);
      const hit = [...ev].filter(w => ctx.has(w)).sort();
      if (hit.length) { score += 2 * hit.length; reasons.push("its context matches " + hit.join(", ")); }
      if ([...ev].some(w => trig.has(w)) && n.mode === "associated") { score += 1; reasons.push("a known trigger"); }
      if (src === "memory" && n.mode === "observer") { score += 3; reasons.push("a memory: observed, not relived"); }
      if ((src === "hr" || src === "eeg") && n.mode === "associated") { score += 1; reasons.push(src === "hr" ? "the body signals stress" : "the brain signals arousal"); }
      const proto = "node_" + String(n.key || "").toLowerCase();
      const ch = (runs || []).filter(r => r.protocol === proto && !empty(r.sud_before) && !empty(r.sud_after)).map(r => Number(r.sud_after) - Number(r.sud_before));
      if (ch.length >= 3) {
        const mean = ch.reduce((a, b) => a + b, 0) / ch.length;
        score += Math.max(-2, Math.min(2, -mean / 2));
        if (mean < 0) reasons.push("it lowered your distress by " + fmt1(-mean) + " on average");
      }
      if (bestScore === null || score > bestScore) { best = i; bestScore = score; why = reasons.join("; "); }
    });
    const n = plan.nodes[best];
    return { node: best, name: n.name, protocol: "node_" + String(n.key || "").toLowerCase(), reason: why || "your first node" };
  }
  const api = { SCHEMA, LIMITS, understand, merge, converse, sensesFromList, suggestFrames, modelPrompt, route, offer, fmt1 };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSLinx = api;
})(typeof self !== "undefined" ? self : this);
