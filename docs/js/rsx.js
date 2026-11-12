/* RSX v2 compiler, JavaScript implementation.
 * Mirrors rsx/rsx/compiler.py statement for statement; rsx/tests/test_conformance.py
 * checks that both produce identical timelines and identical errors.
 * Works in the browser (window.RSX) and in Node (module.exports).
 */
(function (root) {
  "use strict";
  const LANGUAGE_VERSION = "2.0";
  const CHANNELS = ["V", "A", "K", "O", "G"];
  const CHANNEL_NAMES = { V: "visual", A: "auditory", K: "kinesthetic", O: "olfactory", G: "gustatory" };
  const DEFAULT_SAFETY = { max_per_hour: 6, max_per_day: 20, refractory_ms: 90000, haptic_max: 0.4 };
  const DEFAULT_BREATH = { inhale: 4000, exhale: 6000, hold: 0 };
  const SAY_MS = 1500, CUE_MS = 2000;

  class RSXError extends Error {
    constructor(line, message) { super("line " + line + ": " + message); this.line = line; this.rsxMessage = message; }
  }

  const TOKEN = /"(?:[^"\\]|\\.)*"|\S+/g;
  function tokenize(text) { return text.match(TOKEN) || []; }
  function unquote(tok, line) {
    if (tok.length < 2 || tok[0] !== '"' || tok[tok.length - 1] !== '"') throw new RSXError(line, "expected a quoted string, got " + tok);
    return tok.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, "\\");
  }
  function parseDuration(tok, line) {
    const m = /^(\d+(?:\.\d+)?)(ms|s|m)$/.exec(tok);
    if (!m) throw new RSXError(line, "bad duration " + tok + " (use e.g. 300ms, 4s, 1.5s, 2m)");
    return Math.round(parseFloat(m[1]) * { ms: 1, s: 1000, m: 60000 }[m[2]]);
  }
  function parseNumber(tok, line) {
    const s = String(tok).trim();
    const v = Number(s);
    if (s === "" || !isFinite(v)) throw new RSXError(line, "expected a number, got " + tok);
    return v;
  }
  function parseKv(tokens, line) {
    const out = {};
    for (const t of tokens) {
      const i = t.indexOf("=");
      if (i < 0) throw new RSXError(line, "expected key=value, got " + t);
      out[t.slice(0, i)] = t.slice(i + 1);
    }
    return out;
  }
  function firstKey(o) { return Object.keys(o)[0]; }
  function stripComment(raw) {
    let out = "", inq = false;
    for (let i = 0; i < raw.length; i++) {
      const c = raw[i];
      if (c === "\\" && inq && i + 1 < raw.length) { out += raw.slice(i, i + 2); i++; continue; }
      if (c === '"') inq = !inq;
      if (c === "#" && !inq) break;
      out += c;
    }
    return out.trim();
  }
  function splitLines(source) {
    const lines = [];
    source.split(/\r\n|\r|\n/).forEach((raw, k) => {
      const text = stripComment(raw);
      if (!text) return;
      let buf = "", inq = false; const parts = [];
      for (const c of text) {
        if (c === '"') inq = !inq;
        if (c === ";" && !inq) { parts.push(buf); buf = ""; } else buf += c;
      }
      parts.push(buf);
      for (let p of parts) { p = p.trim(); if (p) lines.push({ no: k + 1, text: p }); }
    });
    return lines;
  }
  function parseBlock(lines, i, opener) {
    let depth = 1; const body = [];
    while (i < lines.length) {
      const ln = lines[i];
      if (ln.text === "}") { depth--; if (depth === 0) return [body, i + 1]; }
      if (ln.text.endsWith("{")) depth++;
      body.push(ln); i++;
    }
    throw new RSXError(opener.no, "missing closing }");
  }
  const capitalize = s => s ? s[0].toUpperCase() + s.slice(1).toLowerCase() : s;
  const title = s => s.replace(/[A-Za-z]+/g, w => capitalize(w));

  function compile(source) {
    const lines = splitLines(source);
    const prog = {
      rsx: LANGUAGE_VERSION, protocol: null, title: "", version: "",
      safety: Object.assign({}, DEFAULT_SAFETY), breath: Object.assign({}, DEFAULT_BREATH),
      tiers: {}, futures: [], phases: [], events: [], warnings: [], duration_ms: 0
    };
    const state = { t: 0 };
    let i = 0;
    while (i < lines.length) {
      const ln = lines[i], toks = tokenize(ln.text), kw = toks[0];
      if (kw === "PROTOCOL") {
        if (toks.length < 2) throw new RSXError(ln.no, "PROTOCOL needs an id");
        prog.protocol = toks[1];
        prog.title = toks.length > 2 ? unquote(toks[2], ln.no) : toks[1];
        i++;
      } else if (kw === "VERSION") {
        prog.version = toks.length > 1 ? toks[1] : ""; i++;
      } else if (kw === "SAFETY") {
        const kv = parseKv(toks.slice(1), ln.no);
        for (const k of Object.keys(kv)) {
          const v = kv[k];
          if (k === "max_per_hour" || k === "max_per_day") prog.safety[k] = Math.trunc(parseNumber(v, ln.no));
          else if (k === "refractory") prog.safety.refractory_ms = parseDuration(v, ln.no);
          else if (k === "haptic_max") {
            const a = parseNumber(v, ln.no);
            if (!(a > 0 && a <= 1)) throw new RSXError(ln.no, "haptic_max must be in (0, 1]");
            prog.safety[k] = a;
          } else throw new RSXError(ln.no, "unknown SAFETY key " + k);
        }
        i++;
      } else if (kw === "BREATH") {
        const kv = parseKv(toks.slice(1), ln.no);
        for (const k of Object.keys(kv)) {
          if (!(k in DEFAULT_BREATH)) throw new RSXError(ln.no, "unknown BREATH key " + k);
          prog.breath[k] = parseDuration(kv[k], ln.no);
        }
        i++;
      } else if (kw === "FUTURES") {
        prog.futures = toks.slice(1).filter(t => t !== "|").map(t => unquote(t, ln.no));
        if (!prog.futures.length) throw new RSXError(ln.no, "FUTURES needs at least one quoted context");
        i++;
      } else if (kw === "TIER" && toks.includes("::")) {
        vectorCommand(prog, state, ln, toks); i++;
      } else if (kw === "TIER") {
        if (toks[toks.length - 1] !== "{" || toks.length !== 4) throw new RSXError(ln.no, "tier syntax: TIER <number> <NAME> {");
        const [body, j] = parseBlock(lines, i + 1, ln); i = j;
        tier(prog, ln, toks, body);
      } else if (kw === "PHASE" || kw === "FOR" || kw === "REPEAT") {
        if (toks[toks.length - 1] !== "{") throw new RSXError(ln.no, kw + " must open a block with {");
        const [body, j] = parseBlock(lines, i + 1, ln); i = j;
        block(prog, state, ln, toks, body, {});
      } else throw new RSXError(ln.no, "unknown statement " + kw);
    }
    if (prog.protocol === null) throw new RSXError(1, "missing PROTOCOL statement");
    prog.duration_ms = state.t;
    prog.events.sort((a, b) => a.t - b.t || a.seq - b.seq);
    for (const e of prog.events) delete e.seq;
    return prog;
  }

  function tier(prog, ln, toks, body) {
    if (!/^[+-]?\d+$/.test(toks[1])) throw new RSXError(ln.no, "tier number must be an integer");
    const number = parseInt(toks[1], 10), name = toks[2];
    if (name in prog.tiers) throw new RSXError(ln.no, "tier " + name + " defined twice");
    const t = { number, name, glyph: "", word: "", channels: {} };
    for (const b of body) {
      const bt = tokenize(b.text), key = bt[0];
      if (bt.length !== 2) throw new RSXError(b.no, key + " takes one quoted value");
      const val = unquote(bt[1], b.no);
      if (CHANNELS.includes(key)) t.channels[key] = val;
      else if (key === "GLYPH") t.glyph = val;
      else if (key === "WORD") t.word = val;
      else throw new RSXError(b.no, "unknown tier field " + key);
    }
    const missing = ["V", "A", "K"].filter(c => !(c in t.channels));
    if (missing.length) throw new RSXError(ln.no, "tier " + name + " needs channels V, A and K (missing " + missing.join(", ") + ")");
    prog.tiers[name] = t;
  }

  function emit(prog, t, dur, channel, kind, phase, params) {
    const ev = Object.assign({ t, dur, channel, kind, phase }, params || {});
    ev.seq = prog.events.length;
    prog.events.push(ev);
    return t + dur;
  }
  function subst(text, ctx) {
    if (text.includes("$future")) {
      if (!("future" in ctx)) throw new RSXError(ctx._line || 0, "$future used outside FOR FUTURE");
      text = text.split("$future").join(ctx.future);
    }
    return text;
  }
  function block(prog, state, ln, toks, body, ctx) {
    const kw = toks[0];
    if (kw === "FOR") {
      if (!(toks.length === 3 && toks[1] === "FUTURE" && toks[2] === "{")) throw new RSXError(ln.no, "loop syntax: FOR FUTURE {");
      if (!prog.futures.length) throw new RSXError(ln.no, "FOR FUTURE used before FUTURES");
      prog.futures.forEach((f, k) => runBody(prog, state, body, Object.assign({}, ctx, { future: f, future_index: k })));
    } else if (kw === "REPEAT") {
      if (toks.length !== 3) throw new RSXError(ln.no, "loop syntax: REPEAT <n> {");
      const n = Math.trunc(parseNumber(toks[1], ln.no));
      if (n < 1 || n > 100) throw new RSXError(ln.no, "REPEAT count must be 1..100");
      for (let r = 0; r < n; r++) runBody(prog, state, body, ctx);
    } else phase(prog, state, ln, toks, body, ctx);
  }
  function runBody(prog, state, body, ctx) {
    let j = 0;
    while (j < body.length) {
      const b = body[j], bt = tokenize(b.text);
      if (["PHASE", "FOR", "REPEAT"].includes(bt[0]) && bt[bt.length - 1] === "{") {
        const [inner, k] = parseBlock(body, j + 1, b); j = k;
        block(prog, state, b, bt, inner, ctx);
      } else if (bt[0] === "TIER" && bt.includes("::")) { vectorCommand(prog, state, b, bt); j++; }
      else throw new RSXError(b.no, bt[0] + " must be inside a PHASE");
    }
  }
  function phase(prog, state, ln, toks, body, ctx) {
    if (toks.length < 3) throw new RSXError(ln.no, "phase syntax: PHASE <name> [breath=inhale|exhale|hold|none] [dur=4s] {");
    const name = toks[1];
    const opts = parseKv(toks.slice(2, -1), ln.no);
    const breath = "breath" in opts ? opts.breath : "none"; delete opts.breath;
    let minDur = 0;
    if ("dur" in opts) { minDur = parseDuration(opts.dur, ln.no); delete opts.dur; }
    if (Object.keys(opts).length) throw new RSXError(ln.no, "unknown PHASE option " + firstKey(opts));
    if (!["inhale", "exhale", "hold", "none"].includes(breath)) throw new RSXError(ln.no, "bad breath " + breath);
    const start = state.t, index = prog.phases.length;
    const extra = {};
    if ("future_index" in ctx) extra.future_index = ctx.future_index;
    let end = start;
    if (breath !== "none") end = Math.max(end, emit(prog, start, prog.breath[breath], "breath", breath, name, extra));
    end = Math.max(end, steps(prog, body, name, start, ctx, extra)[0]);
    end = Math.max(end, start + minDur);
    if (end === start) end = start + CUE_MS;
    prog.phases.push(Object.assign({ name, t: start, dur: end - start, breath, index }, extra));
    state.t = end;
  }
  function steps(prog, body, ph, cursor, ctx, extra) {
    let end = cursor, j = 0;
    while (j < body.length) {
      const b = body[j], bt = tokenize(b.text);
      if (bt[0] === "FOR" && bt[bt.length - 1] === "{") {
        if (!(bt.length === 3 && bt[1] === "FUTURE")) throw new RSXError(b.no, "loop syntax: FOR FUTURE {");
        if (!prog.futures.length) throw new RSXError(b.no, "FOR FUTURE used before FUTURES");
        if ("future" in ctx) throw new RSXError(b.no, "FOR FUTURE cannot be nested");
        const [inner, k] = parseBlock(body, j + 1, b); j = k;
        prog.futures.forEach((f, n) => {
          const r = steps(prog, inner, ph, cursor, Object.assign({}, ctx, { future: f, future_index: n }), extra);
          end = Math.max(end, r[0]); cursor = r[1];
        });
        continue;
      }
      end = Math.max(end, step(prog, b, bt, ph, cursor, Object.assign({}, ctx, { _line: b.no }), extra));
      if (bt[0] === "WAIT") { cursor += parseDuration(bt[1], b.no); end = Math.max(end, cursor); }
      j++;
    }
    return [end, cursor];
  }
  const SIMPLE = { SAY: ["A", "say"], SEE: ["V", "see"], FEEL: ["K", "feel"], GESTURE: ["K", "gesture"], SMELL: ["O", "smell"], TASTE: ["G", "taste"] };
  function step(prog, b, bt, ph, t, ctx, extra) {
    const kw = bt[0];
    if (kw in SIMPLE) {
      if (bt.length !== 2) throw new RSXError(b.no, kw + " takes one quoted value");
      const [ch, kind] = SIMPLE[kw];
      return emit(prog, t, kw === "SAY" ? SAY_MS : CUE_MS, CHANNEL_NAMES[ch], kind, ph,
        Object.assign({ text: subst(unquote(bt[1], b.no), ctx) }, extra));
    }
    if (kw === "WAIT") {
      if (bt.length !== 2) throw new RSXError(b.no, "WAIT takes a duration");
      parseDuration(bt[1], b.no); return t;
    }
    if (kw === "HAPTIC") {
      const kv = parseKv(bt.slice(1), b.no);
      const take = (k, d) => { const v = k in kv ? kv[k] : d; delete kv[k]; return v; };
      const on = parseDuration(take("on", "300ms"), b.no), off = parseDuration(take("off", "300ms"), b.no);
      const count = Math.trunc(parseNumber(take("x", "1"), b.no));
      const amp = parseNumber(take("amp", String(prog.safety.haptic_max)), b.no);
      if (Object.keys(kv).length) throw new RSXError(b.no, "unknown HAPTIC key " + firstKey(kv));
      if (amp > prog.safety.haptic_max + 1e-12) throw new RSXError(b.no, "haptic amp " + pyNum(amp) + " exceeds SAFETY haptic_max " + pyNum(prog.safety.haptic_max));
      if (count < 1 || count > 50) throw new RSXError(b.no, "haptic x must be 1..50");
      return emit(prog, t, (on + off) * count, "haptic", "pulse", ph, Object.assign({ on, off, count, amp }, extra));
    }
    if (kw === "TONE") {
      if (bt.length !== 3 || !bt[1].endsWith("Hz")) throw new RSXError(b.no, "TONE syntax: TONE <freq>Hz <duration>");
      const hz = parseNumber(bt[1].slice(0, -2), b.no);
      if (!(hz >= 20 && hz <= 4000)) throw new RSXError(b.no, "tone frequency must be 20..4000 Hz");
      return emit(prog, t, parseDuration(bt[2], b.no), "auditory", "tone", ph, Object.assign({ hz }, extra));
    }
    if (kw === "ACTIVATE") {
      if (bt.length !== 2) throw new RSXError(b.no, "ACTIVATE takes a tier name");
      return activate(prog, findTier(prog, bt[1], b.no), ph, t, extra);
    }
    if (kw === "MARK") {
      if (bt.length !== 2) throw new RSXError(b.no, "MARK takes one quoted label");
      return emit(prog, t, 0, "marker", "mark", ph, Object.assign({ text: unquote(bt[1], b.no) }, extra));
    }
    throw new RSXError(b.no, "unknown step " + kw);
  }
  function pyNum(x) { return Number.isInteger(x) ? x.toFixed(1) : String(x); }
  function findTier(prog, ref, line) {
    if (ref in prog.tiers) return prog.tiers[ref];
    for (const k of Object.keys(prog.tiers)) if (String(prog.tiers[k].number) === ref) return prog.tiers[k];
    throw new RSXError(line, "unknown tier " + ref);
  }
  function activate(prog, t0, ph, t, extra) {
    let end = emit(prog, t, 0, "marker", "tier", ph, Object.assign({ tier: t0.name, number: t0.number, glyph: t0.glyph, word: t0.word }, extra));
    for (const ch of CHANNELS) if (ch in t0.channels)
      end = Math.max(end, emit(prog, t, CUE_MS, CHANNEL_NAMES[ch], "cue", ph, Object.assign({ text: t0.channels[ch], tier: t0.name }, extra)));
    return end;
  }
  function vectorCommand(prog, state, ln, toks) {
    const parts = toks.join(" ").split("::").map(p => p.trim());
    const head = parts[0].split(/\s+/).filter(Boolean);
    if (head.length !== 2 || head[0] !== "TIER") throw new RSXError(ln.no, "vector command must start with TIER <n> ::");
    const number = head[1];
    let arch = null, mode = null; const vectors = [];
    for (const p of parts.slice(1)) {
      if (!p) continue;
      if (p.startsWith("{") && p.endsWith("}")) arch = p.slice(1, -1);
      else if (p.startsWith("(") && p.endsWith(")")) mode = p.slice(1, -1);
      else if (p.startsWith("@")) {
        const m = /^@Vector(\d+):(\w+)(?:\((.*)\))?$/.exec(p);
        if (!m) throw new RSXError(ln.no, "bad vector " + p);
        vectors.push([parseInt(m[1], 10), m[2], m[3] || ""]);
      } else throw new RSXError(ln.no, "unexpected element " + p);
    }
    if (!vectors.length) throw new RSXError(ln.no, "vector command has no @Vector elements");
    if (vectors.length > 17) throw new RSXError(ln.no, "RSX supports at most 17 concurrent vectors");
    const name = "tier-" + number, start = state.t, index = prog.phases.length;
    let end = emit(prog, start, 0, "marker", "vector-command", name, { number, archetype: arch || "", mode: mode || "", vectors: vectors.length });
    for (const [k, op, arg] of vectors) {
      const tag = { vector: k };
      if (op === "BreathOverride") {
        const t1 = emit(prog, start, prog.breath.inhale, "breath", "inhale", name, tag);
        end = Math.max(end, emit(prog, t1, prog.breath.exhale, "breath", "exhale", name, tag));
      } else if (op === "MemoryRecall") {
        const target = arg.includes("=") ? arg.slice(arg.indexOf("=") + 1) : arg;
        const key = capitalize(target) in prog.tiers ? capitalize(target) : target;
        if (key in prog.tiers) end = Math.max(end, activate(prog, prog.tiers[key], name, start, tag));
        else end = Math.max(end, emit(prog, start, CUE_MS, "visual", "see", name, Object.assign({ text: "Recall the " + title(target) + " archetype" }, tag)));
      } else if (op === "EmotionalLock") end = Math.max(end, emit(prog, start, 0, "marker", "state", name, Object.assign({ text: arg }, tag)));
      else if (op === "FutureProjection") end = Math.max(end, emit(prog, start, CUE_MS, "visual", "see", name, Object.assign({ text: ("See your future self " + arg).trim() }, tag)));
      else if (op === "DeviceOutput") end = Math.max(end, emit(prog, start, 0, "device", "output", name, Object.assign({ text: arg }, tag)));
      else if (op === "PostureShift") end = Math.max(end, emit(prog, start, CUE_MS, "kinesthetic", "feel", name, Object.assign({ text: "Shift into an upright, open posture" }, tag)));
      else {
        prog.warnings.push("line " + ln.no + ": @Vector" + k + ":" + op + " has no runtime effect (recorded only)");
        end = Math.max(end, emit(prog, start, 0, "annotation", "vector", name, Object.assign({ text: op }, tag)));
      }
    }
    end = Math.max(end, start + CUE_MS);
    prog.phases.push({ name, t: start, dur: end - start, breath: "none", index });
    state.t = end;
  }

  const api = { compile, RSXError, LANGUAGE_VERSION };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSX = api;
})(typeof self !== "undefined" ? self : this);
