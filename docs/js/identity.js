/* IDENTITY, identity profiles level by level (spec/IDENTITY.md), JavaScript implementation. Mirrors
 * rsso/rsso/identity.py (identical results, tested): a profile headed by a symbol and a login code, seven levels from
 * mission to environment, each with a statement, an image and a code; versions, coherence and its trend, drift while
 * mirroring others, generalisation, the anchor tree and recall walks, value-conflict rehearsals, switching between
 * profiles, programs (day, night, four steps, the prepared week, dose) and a library. Needs docs/js/peak.js and
 * docs/js/trial.js. Browser: window.RSOSIdentity; Node: module.exports. The library
 * is the same as LIBRARY in identity.py (tested).
 */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const P = node ? require("./peak.js") : root.RSOSPeak;
  const T = node ? require("./trial.js") : root.RSOSTrial;
  const LEVELS = ["mission", "identity", "values", "beliefs", "skills", "behaviour", "environment"];
  const LEVEL_NAMES = { mission: "Mission", identity: "Identity", values: "Values", beliefs: "Beliefs", skills: "Skills",
    behaviour: "Behaviour", environment: "Environment" };
  const LEVEL_ASK = { mission: "What is it for, beyond you?", identity: "Who are you, in this?", values: "What matters most here?",
    beliefs: "What do you know to be true?", skills: "What can you do?", behaviour: "What do you do, and when?",
    environment: "Where, and with what around you?" };
  const ENV_KEYS = ["clothing", "scent", "music", "space"], CONTEXTS = ["baseline", "after_mirroring"];
  const SWITCH_BY = ["login", "schedule", "interrupt", "person"], REACTION = -10, DOSE = { per_day: 12, days: 30 };
  const LIBRARY = [
    {
      "id": "steady",
      "name": "Steady under pressure",
      "symbol": "🦁",
      "code": "..-",
      "levels": {
        "mission": "People around me are safer because I stay clear when it counts.",
        "identity": "I am the one who stays steady.",
        "values": "Clarity, courage, care.",
        "beliefs": "Pressure is information. I can feel it and still choose.",
        "skills": "I can slow my breath, name what is happening and choose the next step.",
        "behaviour": "When pressure rises I breathe out long, lower my voice and act on one thing.",
        "environment": "A clear desk, a grounded stance, cedar on the wrist."
      },
      "environment": {
        "clothing": "Something with structure",
        "scent": "Cedar",
        "music": "Low strings",
        "space": "A clear desk"
      }
    },
    {
      "id": "learner",
      "name": "Focused learner",
      "symbol": "🦉",
      "code": ".-.",
      "levels": {
        "mission": "What I learn I pass on, so others start further ahead.",
        "identity": "I am a learner who finishes.",
        "values": "Curiosity, patience, precision.",
        "beliefs": "Not knowing yet is the beginning of knowing.",
        "skills": "I can break a subject into steps and test myself on each.",
        "behaviour": "I start with the hardest twenty minutes, then test myself before I stop.",
        "environment": "One window, phone in another room, rosemary nearby."
      },
      "environment": {
        "clothing": "Comfortable, the same each session",
        "scent": "Rosemary",
        "music": "None, or steady rain",
        "space": "One window, nothing else open"
      }
    },
    {
      "id": "maker",
      "name": "Creative maker",
      "symbol": "🐉",
      "code": "-..",
      "levels": {
        "mission": "I make things that did not exist and leave the world more alive.",
        "identity": "I am a maker.",
        "values": "Play, craft, courage to show.",
        "beliefs": "The first version is supposed to be rough.",
        "skills": "I can generate many options fast and then choose one to finish.",
        "behaviour": "I make something every day, and I show it before it feels ready.",
        "environment": "Tools within reach, music on, space to move."
      },
      "environment": {
        "clothing": "Clothes I can get dirty",
        "scent": "Orange peel",
        "music": "Fast, without words",
        "space": "Tools within reach"
      }
    },
    {
      "id": "calm_parent",
      "name": "Calm parent",
      "symbol": "🌳",
      "code": "--.",
      "levels": {
        "mission": "My children grow up knowing that strong feelings can be held.",
        "identity": "I am the calm in the house.",
        "values": "Warmth, patience, honesty.",
        "beliefs": "A child's storm is not about me; it is a moment to help.",
        "skills": "I can notice my rising heat, pause and kneel to their level.",
        "behaviour": "When voices rise I lower mine, breathe out and name the feeling.",
        "environment": "Soft light in the evening, a quiet corner, lavender."
      },
      "environment": {
        "clothing": "Soft",
        "scent": "Lavender",
        "music": "Quiet",
        "space": "A quiet corner"
      }
    },
    {
      "id": "athlete",
      "name": "Athlete at rest",
      "symbol": "🐆",
      "code": ".--",
      "levels": {
        "mission": "I show what a trained body and a quiet mind can do together.",
        "identity": "I am an athlete, also when I rest.",
        "values": "Discipline, recovery, joy in effort.",
        "beliefs": "Rest is training. The body adapts while I sleep.",
        "skills": "I can switch from full effort to full rest on one breath.",
        "behaviour": "After hard effort I breathe out long, stretch and stop thinking about it.",
        "environment": "Kit ready the night before, cool room, eucalyptus."
      },
      "environment": {
        "clothing": "Training kit",
        "scent": "Eucalyptus",
        "music": "A pre-start track",
        "space": "Kit ready the night before"
      }
    },
    {
      "id": "speaker",
      "name": "Clear speaker",
      "symbol": "🦅",
      "code": "-.-",
      "levels": {
        "mission": "What matters gets said clearly, so people can act on it.",
        "identity": "I am someone worth listening to.",
        "values": "Truth, clarity, respect for the listener.",
        "beliefs": "Nerves are energy for the room.",
        "skills": "I can open with one sentence, pause and look at one person at a time.",
        "behaviour": "Before I speak I plant my feet, breathe out and say the first sentence slowly.",
        "environment": "Feet on the floor, water at hand, peppermint."
      },
      "environment": {
        "clothing": "What I would wear to be taken seriously",
        "scent": "Peppermint",
        "music": "One track before",
        "space": "Standing, feet planted"
      }
    }
  ];

  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const mean = xs => xs.reduce((a, b) => a + b, 0) / xs.length;
  const sd = xs => { const m = mean(xs); return Math.sqrt(xs.reduce((a, x) => a + (x - m) * (x - m), 0) / xs.length); };
  const vr = xs => { if (xs.length < 2) return 0; const m = mean(xs); return xs.reduce((a, x) => a + (x - m) * (x - m), 0) / (xs.length - 1); };
  const median = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
  const isNum = x => x !== null && x !== undefined;

  function welch(a, b) {
    const va = vr(a), vb = vr(b), se = Math.sqrt(va / a.length + vb / b.length), d = mean(b) - mean(a);
    if (se === 0) return [d, d, d];
    const num = Math.pow(va / a.length + vb / b.length, 2);
    const den = Math.pow(va / a.length, 2) / (a.length - 1) + Math.pow(vb / b.length, 2) / (b.length - 1);
    const df = den > 0 ? Math.max(1, Math.floor(num / den)) : a.length + b.length - 2;
    const t = T.tcrit(df); return [d, d - t * se, d + t * se];
  }
  function paired(ds) {
    if (ds.length < 3) return null;
    const m = mean(ds), se = Math.sqrt(vr(ds) / ds.length), t = T.tcrit(ds.length - 1);
    return { difference: r1(m), lo: r1(m - t * se), hi: r1(m + t * se), n: ds.length };
  }
  function slope(xs, ys) {
    const n = xs.length, mx = mean(xs), my = mean(ys);
    let sxx = 0, sxy = 0; for (let i = 0; i < n; i++) { sxx += (xs[i] - mx) * (xs[i] - mx); }
    if (sxx === 0) return [0, 0, 0];
    for (let i = 0; i < n; i++) sxy += (xs[i] - mx) * (ys[i] - my);
    const b = sxy / sxx; let res = 0;
    for (let i = 0; i < n; i++) res += Math.pow(ys[i] - my - b * (xs[i] - mx), 2);
    const se = n > 2 ? Math.sqrt(res / (n - 2) / sxx) : 0, t = n > 2 ? T.tcrit(n - 2) : 0;
    return [b, b - t * se, b + t * se];
  }

  // ------------------------------------------------------------ the profile
  function makeProfile(id, name, symbol, code, language, created) {
    const levels = {}; LEVELS.forEach(l => { levels[l] = { text: "", image: "", code: "" }; });
    const environment = {}; ENV_KEYS.forEach(k => { environment[k] = ""; });
    return { schema: "rsos-identity/1", id, name, symbol, code, language: language || "", created: created || 0, levels, environment,
      futures: [], policy: { anchors: [], max_stage: "suggest", night_chain: false }, tree: { center: "", parts: [] },
      versions: [], ratings: [], contexts: [], walks: [], rehearsals: [] };
  }
  function setLevel(p, level, text, image, code) {
    if (!LEVELS.includes(level)) throw new Error("level must be one of " + LEVELS.join(", "));
    const L = p.levels[level];
    if (isNum(text)) L.text = text; if (isNum(image)) L.image = image; if (isNum(code)) L.code = code;
    return L;
  }
  function codeOk(c) {
    if (!c || !c.trim() || ![...c].every(ch => ".- ".includes(ch))) return false;
    const w = c.trim().split(/\s+/); return w.length <= 3 && w.every(x => x.length <= 6);
  }
  function issues(p) {
    const out = [];
    if (!p.symbol) out.push({ field: "symbol", say: "Choose a symbol to head the profile." });
    if (!codeOk(p.code || "")) out.push({ field: "code", say: "The login code needs dots and dashes only, up to three groups." });
    LEVELS.forEach(l => { if (!p.levels[l].text.trim()) out.push({ field: l, say: LEVEL_NAMES[l] + ": not written yet. " + LEVEL_ASK[l] }); });
    const seen = new Map(); if (p.code) seen.set(p.code, "the login code");
    const ns = s => s.split(" ").join("");
    LEVELS.forEach(l => {
      const c = p.levels[l].code; if (!c) return;
      if (!codeOk(c)) out.push({ field: l, say: LEVEL_NAMES[l] + ": the code needs dots and dashes only, up to three groups." });
      else if (seen.has(c)) out.push({ field: l, say: LEVEL_NAMES[l] + ": the same code as " + seen.get(c) + "; the body cannot tell them apart." });
      else {
        for (const [other, who] of seen) {
          if (ns(c).startsWith(ns(other)) || ns(other).startsWith(ns(c))) {
            out.push({ field: l, say: LEVEL_NAMES[l] + ": the code starts like " + who + "; make it differ in the first pulses." }); break;
          }
        }
        seen.set(c, LEVEL_NAMES[l].toLowerCase());
      }
    });
    return out;
  }
  function completeness(p) {
    const filled = LEVELS.filter(l => p.levels[l].text.trim()), coded = LEVELS.filter(l => p.levels[l].code);
    const env = ENV_KEYS.filter(k => p.environment[k]);
    return { levels: filled.length, codes: coded.length, environment: env.length, of: LEVELS.length,
      ready: filled.length === LEVELS.length && !issues(p).some(i => i.field === "code" || i.field === "symbol") };
  }

  // ------------------------------------------------------------ versions
  function saveVersion(p, ts, note) {
    const levels = {}; LEVELS.forEach(l => { levels[l] = p.levels[l].text; });
    const v = { v: p.versions.length + 1, ts, note: note || "", symbol: p.symbol, code: p.code, levels, environment: Object.assign({}, p.environment) };
    p.versions.push(v); return v;
  }
  function diff(a, b) {
    const out = [];
    ["symbol", "code"].forEach(f => { if (a[f] !== b[f]) out.push({ field: f, before: a[f], after: b[f] }); });
    LEVELS.forEach(l => { const x = a.levels[l] || "", y = b.levels[l] || ""; if (x !== y) out.push({ field: l, before: x, after: y }); });
    ENV_KEYS.forEach(k => { const x = a.environment[k] || "", y = b.environment[k] || ""; if (x !== y) out.push({ field: "environment." + k, before: x, after: y }); });
    return out;
  }

  // ------------------------------------------------------------ coherence and drift
  function rate(p, ts, scores, context) {
    context = context || "baseline";
    if (!CONTEXTS.includes(context)) throw new Error("context must be one of " + CONTEXTS.join(", "));
    const s = {}; LEVELS.forEach(l => { if (isNum(scores[l])) s[l] = scores[l]; });
    const r = { ts, context, scores: s }; p.ratings.push(r); return r;
  }
  function coherence(scores) {
    const ls = LEVELS.filter(l => isNum(scores[l])), vals = ls.map(l => Number(scores[l]));
    if (vals.length < 3) return null;
    const m = mean(vals), s = sd(vals);
    let weakest = ls[0]; ls.forEach(l => { if (scores[l] < scores[weakest]) weakest = l; });
    return { score: r1(Math.max(0, Math.min(10, m - s))), mean: r1(m), spread: r1(s), weakest };
  }
  function trend(p, context) {
    context = context || "baseline";
    const rows = p.ratings.filter(r => r.context === context).sort((a, b) => a.ts - b.ts);
    const pts = rows.map(r => [(r.ts - rows[0].ts) / 86400, coherence(r.scores)]).filter(x => x[1]).map(x => [x[0], x[1].score]);
    if (pts.length < 4 || pts[pts.length - 1][0] - pts[0][0] < 7)
      return { n: pts.length, per_month: null, lo: null, hi: null, verdict: "too_few", say: "Rate the levels at least four times over a week or more to see a trend." };
    const [b, lo, hi] = slope(pts.map(x => x[0]), pts.map(x => x[1]));
    const verdict = lo > 0 ? "rising" : hi < 0 ? "falling" : "no_clear_change";
    const say = { rising: "Coherence is rising", falling: "Coherence is falling", no_clear_change: "No clear change in coherence yet" }[verdict];
    return { n: pts.length, per_month: r1(b * 30), lo: r1(lo * 30), hi: r1(hi * 30), verdict, first: pts[0][1], last: pts[pts.length - 1][1],
      say: say + ": " + r1(b * 30) + " points a month [" + r1(lo * 30) + ", " + r1(hi * 30) + "]." };
  }
  function drift(p, margin) {
    margin = margin === undefined ? 1 : margin;
    const sc = ctx => p.ratings.filter(r => r.context === ctx).map(r => coherence(r.scores)).filter(c => c).map(c => c.score);
    const a = sc("baseline"), b = sc("after_mirroring");
    if (a.length < 3 || b.length < 3) return { n_baseline: a.length, n_after: b.length, difference: null, lo: null, hi: null, verdict: "too_few",
      say: "Rate the levels at least three times on ordinary days and three times right after time with other people." };
    const [d, lo, hi] = welch(a, b);
    const verdict = hi < 0 ? "drifts" : lo > -margin && hi < margin ? "holds" : "unclear";
    const say = { drifts: "Mirroring others pulls you away from this profile", holds: "You keep this profile while mirroring others",
      unclear: "Not clear yet whether mirroring others moves you" }[verdict];
    return { n_baseline: a.length, n_after: b.length, difference: r1(d), lo: r1(lo), hi: r1(hi), verdict,
      say: say + ": " + r1(d) + " points [" + r1(lo) + ", " + r1(hi) + "]." };
  }

  // ------------------------------------------------------------ generalisation
  function addContext(p, ts, context, trained, fired, latency_s) {
    const c = { ts, context, trained: !!trained, fired: !!fired, latency_s: isNum(latency_s) ? latency_s : null };
    p.contexts.push(c); return c;
  }
  function generalisation(p) {
    const tr = p.contexts.filter(c => c.trained), un = p.contexts.filter(c => !c.trained);
    const rt = tr.length ? tr.filter(c => c.fired).length / tr.length * 100 : null;
    const ru = un.length ? un.filter(c => c.fired).length / un.length * 100 : null;
    const lat = p.contexts.filter(c => c.fired && isNum(c.latency_s)).map(c => c.latency_s);
    const score = rt === null || rt === 0 || ru === null ? null : Math.min(100, ru / rt * 100);
    const names = [...new Set(un.filter(c => c.fired).map(c => c.context))].sort();
    const say = score === null ? "Log contexts where you meant to act, trained and new, to see whether the behaviour travels."
      : "The behaviour started in " + r1(ru) + "% of new contexts and " + r1(rt) + "% of trained ones: it travels " +
        (score >= 75 ? "well." : score >= 40 ? "partly." : "little so far; train it in more places.");
    return { trained: tr.length, new: un.length, trained_rate: r1(rt), new_rate: r1(ru), score: r1(score),
      median_latency_s: lat.length ? r1(median(lat)) : null, travelled_to: names, say };
  }

  // ------------------------------------------------------------ the anchor tree and recall walks
  function setTree(p, center, parts) {
    if (parts.length > 5) throw new Error("an anchor tree holds up to five parts");
    p.tree = { center, parts: parts.map(x => ({ part: x.part || "", context: x.context || "", code: x.code || "" })) }; return p.tree;
  }
  function addWalk(p, ts, kind, results) {
    if (kind !== "tree" && kind !== "single") throw new Error("kind must be tree or single");
    const w = { ts, kind, results: results.map(r => ({ part: r.part || "", ok: !!r.ok, ms: isNum(r.ms) ? r.ms : null })) };
    p.walks.push(w); return w;
  }
  function walksReport(p) {
    const out = {};
    ["tree", "single"].forEach(kind => {
      const ws = p.walks.filter(w => w.kind === kind).sort((a, b) => a.ts - b.ts);
      const cyc = ws.map((w, i) => {
        const n = w.results.length, ok = w.results.filter(r => r.ok).length, ms = w.results.filter(r => r.ok && isNum(r.ms)).map(r => r.ms);
        return { cycle: i + 1, accuracy: n ? r1(ok / n * 100) : null, median_ms: ms.length ? r1(median(ms)) : null };
      });
      const timed = cyc.filter(c => c.median_ms !== null);
      const sl = timed.length >= 3 ? slope(timed.map(c => c.cycle), timed.map(c => c.median_ms))[0] : null;
      const last = cyc.slice(-3).filter(c => c.accuracy !== null).map(c => c.accuracy);
      out[kind] = { walks: ws.length, cycles: cyc, ms_per_cycle: r1(sl), recent_accuracy: last.length ? r1(mean(last)) : null };
    });
    const t = out.tree.cycles, s = out.single.cycles, k = Math.min(t.length, s.length);
    out.compare = null;
    if (k >= 3) {
      const da = [], dm = [];
      for (let i = 0; i < k; i++) {
        if (t[i].accuracy !== null && s[i].accuracy !== null) da.push(t[i].accuracy - s[i].accuracy);
        if (t[i].median_ms !== null && s[i].median_ms !== null) dm.push(t[i].median_ms - s[i].median_ms);
      }
      out.compare = { cycles: k, accuracy: paired(da), ms: paired(dm) };
      const a = out.compare.accuracy, m = out.compare.ms, parts = [];
      if (a && a.lo > 0) parts.push("recalled better from the tree (" + a.difference + " points [" + a.lo + ", " + a.hi + "])");
      else if (a && a.hi < 0) parts.push("recalled better from one image (" + a.difference + " points [" + a.lo + ", " + a.hi + "])");
      if (m && m.hi < 0) parts.push("recalled faster from the tree (" + m.difference + " ms [" + m.lo + ", " + m.hi + "])");
      else if (m && m.lo > 0) parts.push("recalled faster from one image (" + m.difference + " ms)");
      out.say = parts.length ? "Contexts are " + parts.join(" and ") + "." : "No clear difference between the tree and one image after " + k + " walks of each.";
    } else out.say = "Walk the tree and a single image three times each to compare them.";
    return out;
  }

  // ------------------------------------------------------------ value-conflict rehearsal
  function addRehearsal(p, ts, value, kind, before, during, after, distress) {
    if (kind !== "violation" && kind !== "neutral") throw new Error("kind must be violation or neutral");
    const r = { ts, value, kind, before, during, after, distress: isNum(distress) ? distress : null }; p.rehearsals.push(r); return r;
  }
  function reaction(r) {
    const b = r.before, d = r.during, a = r.after;
    if (!b || !isNum(d)) return { reaction: null, recovery: null, reacted: null };
    const rc = (d - b) / b * 100, rv = isNum(a) ? (a - d) / b * 100 : null;
    return { reaction: r1(rc), recovery: r1(rv), reacted: rc <= REACTION };
  }
  function rehearsalsReport(p) {
    const per = {}, neutral = [];
    p.rehearsals.forEach(r => {
      const x = reaction(r); if (x.reaction === null) return;
      if (r.kind === "neutral") { neutral.push(x); return; }
      (per[r.value] = per[r.value] || []).push(x);
    });
    const values = Object.keys(per).sort().map(v => {
      const xs = per[v], rec = xs.filter(x => x.recovery !== null).map(x => x.recovery);
      return { value: v, n: xs.length, reaction: r1(mean(xs.map(x => x.reaction))), recovery: rec.length ? r1(mean(rec)) : null,
        reacted: r1(xs.filter(x => x.reacted).length / xs.length * 100) };
    });
    let strongest = null; values.forEach(v => { if (strongest === null || v.reaction < strongest.reaction) strongest = v; });
    strongest = strongest ? strongest.value : null;
    return { values, neutral: neutral.length, neutral_reacted: neutral.length ? r1(neutral.filter(x => x.reacted).length / neutral.length * 100) : null,
      strongest, say: values.length ? "Your body reacts most to a conflict with " + strongest + "."
        : "Rehearse a value conflict and an ordinary situation, with the heart measured, to see which value the body defends." };
  }

  // ------------------------------------------------------------ switching between profiles
  function switchTo(log, ts, to, by) {
    by = by || "person"; if (!SWITCH_BY.includes(by)) throw new Error("by must be one of " + SWITCH_BY.join(", "));
    const e = { ts, to, by, settled: null }; log.push(e); return e;
  }
  function settle(log, ts) {
    if (!log.length || log[log.length - 1].settled !== null) return null;
    const e = log[log.length - 1]; e.settled = ts - e.ts; return e;
  }
  const interrupt = (log, ts, base) => switchTo(log, ts, base, "interrupt");
  const current = (log, base) => (log.length ? log[log.length - 1].to : base);
  const minutes = hhmm => { const [h, m] = hhmm.split(":"); return parseInt(h, 10) * 60 + parseInt(m, 10); };
  function profileAt(schedule, minute) {
    for (const s of schedule) {
      const a = minutes(s.from), b = minutes(s.to);
      if (a <= b ? (a <= minute && minute < b) : (minute >= a || minute < b)) return s.profile;
    }
    return null;
  }
  function switchReport(log) {
    const by = {}; SWITCH_BY.forEach(k => { by[k] = log.filter(e => e.by === k).length; });
    const lat = log.filter(e => e.settled !== null).map(e => e.settled);
    return { switches: log.length, by, settled: lat.length, median_settle_s: lat.length ? r1(median(lat)) : null };
  }

  // ------------------------------------------------------------ programs
  const q = s => '"' + String(s).split('"').join("'").split("\n").join(" ") + '"';
  const head = (pid, title, perDay) => ["PROTOCOL " + pid + " " + q(title), "VERSION 1.0",
    "SAFETY max_per_hour=6 max_per_day=" + (perDay || 20) + " refractory=90s haptic_max=0.4", "BREATH inhale=4s exhale=6s", ""];
  const slug = p => ("id_" + [...String(p.id || "identity").toLowerCase()].map(ch => (/[\p{L}\p{N}]/u.test(ch) ? ch : "_")).join("")).slice(0, 40);
  function symbolTier(p, n) {
    const who = p.levels.identity.text || p.name;
    return ["TIER " + (n || 1) + " SYMBOL {", "  GLYPH " + q(p.symbol), "  V " + q(p.levels.identity.image || ("see " + p.symbol + " in front of you")),
      "  A " + q(who), "  K " + q("feel the code " + p.code), "  WORD " + q(p.name)]
      .concat(p.environment.scent ? ["  O " + q(p.environment.scent)] : []).concat(["  TACTON " + q(p.code), "}"]);
  }
  function levelTier(p, l, n) {
    const L = p.levels[l];
    return ["TIER " + n + " " + l.toUpperCase() + " {", "  V " + q(L.image || ("see " + LEVEL_NAMES[l].toLowerCase())), "  A " + q(L.text || LEVEL_NAMES[l]),
      "  K " + q("feel " + LEVEL_NAMES[l].toLowerCase() + " in the body")].concat(L.code ? ["  TACTON " + q(L.code)] : []).concat(["}"]);
  }
  const futuresOf = p => ((p.futures && p.futures.length) ? p.futures : p.tree.parts.map(x => x.context)).filter(f => f);
  function dayRsx(p) {
    return head(slug(p) + "_day", p.name + ": the symbol").concat(symbolTier(p), ["", "PHASE login breath=inhale {", "  ACTIVATE SYMBOL", "}",
      "PHASE seal breath=exhale {", "  SAY " + q(p.levels.identity.text || p.name), "  MARK " + q("login " + p.id), "}"]).join("\n") + "\n";
  }
  function nightRsx(p) {
    let L = head(slug(p) + "_night", p.name + ": the whole chain").concat(symbolTier(p));
    LEVELS.forEach((l, i) => { L = L.concat(levelTier(p, l, i + 2)); });
    L = L.concat(["", "PHASE symbol breath=inhale {", "  ACTIVATE SYMBOL", "}"]);
    LEVELS.forEach(l => { L = L.concat(["PHASE " + l + " breath=exhale {", "  ACTIVATE " + l.toUpperCase(), "}"]); });
    return L.concat(["PHASE close breath=inhale {", "  ACTIVATE SYMBOL", "  MARK " + q("chain " + p.id), "}"]).join("\n") + "\n";
  }
  function sequenceRsx(p, state) {
    state = state === undefined ? "the old state" : state;
    let fut = futuresOf(p).slice(0, 3); if (!fut.length) fut = ["The next time it starts"];
    return head(slug(p) + "_seq", p.name + ": four steps").concat(symbolTier(p), [
      "", "FUTURES " + fut.map(q).join(" | "), "",
      "PHASE peak breath=inhale {", "  ACTIVATE SYMBOL", "  SAY " + q(p.levels.identity.text || p.name), "}",
      "PHASE core dur=20s {", "  FEEL " + q("Notice " + state + " and ask it what it wants for you"), "  WAIT 6s",
      '  FEEL "Ask what that would give you, and again, until you reach a core state"', "  WAIT 6s",
      '  FEEL "Let the core state flow back through the old state"', "}",
      "PHASE future breath=exhale {", "  FOR FUTURE {", "    SEE " + q("$future, as " + p.name), "    WAIT 1s", "  }", "}",
      "PHASE movement dur=6s {", '  GESTURE "Move: stand, breathe out, fist or step forward"', "  ACTIVATE SYMBOL",
      "  MARK " + q("sequence " + p.id), "}"]).join("\n") + "\n";
  }
  function levelRsx(p, level, day) {
    let fut = futuresOf(p).slice(0, 1); if (!fut.length) fut = ["Tomorrow"];
    return head(slug(p) + "_d" + day, p.name + ": day " + day + ", " + LEVEL_NAMES[level].toLowerCase()).concat(symbolTier(p), levelTier(p, level, 2), [
      "", "FUTURES " + q(fut[0]), "", "PHASE symbol breath=inhale {", "  ACTIVATE SYMBOL", "}",
      "PHASE " + level + " breath=exhale {", "  ACTIVATE " + level.toUpperCase(), "}",
      "PHASE future breath=exhale {", "  FOR FUTURE {", "    SEE " + q("$future, living this"), "  }", "  MARK " + q("day " + day), "}"]).join("\n") + "\n";
  }
  function installRsx(p) {
    const fut = futuresOf(p).slice(0, 3);
    while (fut.length < 3) fut.push(["At work", "At home", "Under pressure"][fut.length]);
    return head(slug(p) + "_install", p.name + ": installing the symbol").concat(symbolTier(p), [
      "", "FUTURES " + fut.map(q).join(" | "), "",
      "PHASE settle dur=20s {", '  FEEL "Let the eyes close; each breath out a little heavier"', "  TONE 110Hz 18s", "}",
      "PHASE descend breath=exhale {", '  FEEL "Counting down from five, down a little more with each number"', "}",
      "PHASE install breath=inhale {", "  ACTIVATE SYMBOL", "  SAY " + q("All seven levels, gathered in " + p.symbol), "}",
      "PHASE future dur=12s {", "  FOR FUTURE {", "    SEE " + q("$future: " + p.symbol + " is there and you act from it"), "    WAIT 3s", "  }", "}",
      "PHASE return dur=8s {", '  SAY "Counting up from one to five, eyes open, awake and clear"', "  MARK " + q("installed " + p.id), "}"]).join("\n") + "\n";
  }
  function weekPlan(p) {
    const days = LEVELS.map((l, i) => ({ day: i + 1, level: l, title: LEVEL_NAMES[l], practice: p.levels[l].text || LEVEL_ASK[l], rsx: levelRsx(p, l, i + 1) }));
    days.push({ day: 8, level: "symbol", title: "The symbol", practice: "Install " + p.symbol + " in a light trance, with three future situations.", rsx: installRsx(p) });
    return days;
  }
  function dosePlan(start, end, perDay, days) {
    start = start || "08:00"; end = end || "21:00"; perDay = perDay || DOSE.per_day; days = days || DOSE.days;
    const a = minutes(start), b = minutes(end), step = perDay > 1 ? (b - a) / (perDay - 1) : 0, times = [];
    for (let i = 0; i < perDay; i++) { const m = Math.floor(a + i * step + 0.5); times.push(String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0")); }
    return { per_day: perDay, days, total: perDay * days, times,
      say: perDay + " short practices a day for " + days + " days, " + (perDay * days) + " in all; the symbol by day and the whole chain once at night." };
  }
  function fromTemplate(tid, id, created) {
    const t = LIBRARY.find(x => x.id === tid), p = makeProfile(id || t.id, t.name, t.symbol, t.code, "", created || 0);
    LEVELS.forEach(l => { p.levels[l].text = t.levels[l]; }); p.environment = Object.assign({}, t.environment); return p;
  }

  // ------------------------------------------------------------ simulation with known answers
  function SimIdentity(seed, growth, pull, noise, start) {
    this.rng = new P.Rng(seed === undefined ? 1 : seed);
    this.growth = growth === undefined ? 1 : growth; this.pull = pull || 0; this.noise = noise === undefined ? 1 : noise;
    start = start === undefined ? 4 : start; this.base = LEVELS.map(() => start + this.rng.u() * 2);
  }
  SimIdentity.prototype.truth = function (day) { return this.base.map(b => Math.min(9, b + this.growth * day / 30)); };
  SimIdentity.prototype.rate = function (day, mirrored) {
    const out = {};
    LEVELS.forEach((l, i) => {
      const t = this.truth(day)[i] - (mirrored ? this.pull * (1 + 0.5 * (i % 2)) : 0);
      out[l] = Math.max(0, Math.min(10, Math.floor(t + this.rng.gauss() * this.noise + 0.5)));
    });
    return out;
  };
  function simTrend(seed, growth, weeks) {
    const s = new SimIdentity(seed, growth), p = makeProfile("s", "Sim", "🦁", "..-");
    for (let w = 0; w < weeks; w++) rate(p, w * 7 * 86400, s.rate(w * 7));
    return trend(p).verdict;
  }
  function simDrift(seed, pull, n) {
    n = n || 10; const s = new SimIdentity(seed, 0, pull), p = makeProfile("s", "Sim", "🦁", "..-");
    for (let k = 0; k < n; k++) { rate(p, k * 86400, s.rate(30), "baseline"); rate(p, k * 86400 + 3600, s.rate(30, true), "after_mirroring"); }
    return drift(p).verdict;
  }
  function simWalks(seed, advantage, cycles, parts) {
    cycles = cycles || 6; parts = parts || 5;
    const rng = new P.Rng(seed), p = makeProfile("s", "Sim", "🦁", "..-");
    for (let c = 0; c < cycles; c++) {
      ["tree", "single"].forEach(kind => {
        const base = 0.35 + 0.3 * (1 - Math.pow(0.8, c));
        const pr = Math.min(0.97, kind === "tree" ? 1 - Math.pow(1 - base, 1 + advantage) : base), res = [];
        for (let k = 0; k < parts; k++) {
          const ok = rng.u() < pr;
          const ms = Math.floor(2600 * Math.pow(c + 1, -0.35) * (kind === "tree" ? 1 - 0.2 * advantage : 1) * (1 + 0.15 * rng.gauss()) + 0.5);
          res.push({ part: "p" + k, ok, ms });
        }
        addWalk(p, c * 86400 + (kind === "tree" ? 0 : 1), kind, res);
      });
    }
    const c = walksReport(p).compare;
    return [c.accuracy !== null && c.accuracy.lo > 0, c.ms !== null && c.ms.hi < 0];
  }
  function simRehearsal(seed, trueDrop, noise) {
    const rng = new P.Rng(seed), b = 40 + rng.u() * 30;
    const v = reaction({ before: b, during: b * (1 + (trueDrop + rng.gauss() * noise) / 100), after: b });
    const n = reaction({ before: b, during: b * (1 + (rng.gauss() * noise) / 100), after: b });
    return [v.reacted, n.reacted];
  }
  function evaluate(n) {
    n = n || 200; const res = {}, pct = k => r1(k / n * 100);
    [1, 0].forEach(g => [8, 26].forEach(w => {
      const vs = []; for (let i = 0; i < n; i++) vs.push(simTrend(1000 + i, g, w));
      res["trend:" + g + ":" + w] = { rising: pct(vs.filter(v => v === "rising").length), falling: pct(vs.filter(v => v === "falling").length) };
    }));
    [1.5, 0].forEach(pull => {
      const vs = []; for (let i = 0; i < n; i++) vs.push(simDrift(2000 + i, pull));
      res["drift:" + pull] = { drifts: pct(vs.filter(v => v === "drifts").length), holds: pct(vs.filter(v => v === "holds").length), unclear: pct(vs.filter(v => v === "unclear").length) };
    });
    [1, 0].forEach(adv => [6, 12].forEach(cyc => {
      const xs = []; for (let i = 0; i < n; i++) xs.push(simWalks(3000 + i, adv, cyc));
      res["walks:" + adv + ":" + cyc] = { better: pct(xs.filter(x => x[0]).length), faster: pct(xs.filter(x => x[1]).length) };
    }));
    [[4, "chest"], [8, "camera"]].forEach(([noise, label]) => {
      const xs = []; for (let i = 0; i < n; i++) xs.push(simRehearsal(4000 + i, -18, noise));
      res["rehearsal:" + label] = { sensitivity: pct(xs.filter(x => x[0]).length), false: pct(xs.filter(x => x[1]).length) };
    });
    return { n, res };
  }

  const api = { LEVELS, LEVEL_NAMES, LEVEL_ASK, ENV_KEYS, CONTEXTS, SWITCH_BY, REACTION, DOSE, LIBRARY, makeProfile, setLevel, issues, completeness,
    saveVersion, diff, rate, coherence, trend, drift, addContext, generalisation, setTree, addWalk, walksReport, addRehearsal, reaction,
    rehearsalsReport, switchTo, settle, interrupt, current, profileAt, switchReport, dayRsx, nightRsx, sequenceRsx, levelRsx, installRsx,
    weekPlan, dosePlan, fromTemplate, SimIdentity, evaluate };
  if (node) module.exports = api; else root.RSOSIdentity = api;
})(typeof self !== "undefined" ? self : this);
