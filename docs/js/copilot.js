/* THERA and LINX extensions (spec/COPILOT.md), JavaScript implementation. Mirrors rsso/rsso/copilot.py (identical
 * results, tested): the therapist's decision matrix and the copilot on a live transcript with agreement, levels of a
 * sentence and the five-step chain, typologies from speech as plug-ins, craving context triggers and cue-reactivity,
 * Core Transformation one question at a time, rescripting with a symbol and light, the life timeline, overrides and
 * OXQ with DOL-9, perceptual events routed to escalation, speech contexts, the four-day block, the timed burst, and
 * the setting. Needs docs/js/peak.js and docs/js/trial.js. Browser: window.RSOSCopilot; Node: module.exports.
 */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const P = node ? require("./peak.js") : root.RSOSPeak;
  const T = node ? require("./trial.js") : root.RSOSTrial;
  const UNSAFE = /\b(kill|die|dying|suicid\w*|self-harm|harm myself|hurt myself|starve|purge|worthless|hate myself)\b/i;
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const r2 = x => (x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100);
  const sum = xs => { let s = 0; for (const x of xs) s += x; return s; };
  const mean = xs => sum(xs) / xs.length;
  const vr = xs => { if (xs.length < 2) return 0; const m = mean(xs); let s = 0; for (const x of xs) s += (x - m) * (x - m); return s / (xs.length - 1); };
  const median = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
  function ciDiff(a, b) {
    const d = mean(a) - mean(b); if (a.length < 2 || b.length < 2) return [d, null, null];
    const va = vr(a) / a.length, vb = vr(b) / b.length, se = Math.sqrt(va + vb); if (se === 0) return [d, d, d];
    const den = va * va / (a.length - 1) + vb * vb / (b.length - 1);
    const df = den > 0 ? Math.max(1, Math.floor((va + vb) * (va + vb) / den)) : a.length + b.length - 2;
    const h = T.tcrit(df) * se; return [d, d - h, d + h];
  }
  function slope(xs, ys) {
    const n = xs.length, mx = mean(xs), my = mean(ys); let sxx = 0; for (const x of xs) sxx += (x - mx) * (x - mx);
    if (sxx === 0 || n < 3) return [0, null, null];
    let sxy = 0; for (let i = 0; i < n; i++) sxy += (xs[i] - mx) * (ys[i] - my); const b = sxy / sxx;
    let res = 0; for (let i = 0; i < n; i++) { const e = ys[i] - my - b * (xs[i] - mx); res += e * e; }
    const se = Math.sqrt(res / (n - 2) / sxx), t = T.tcrit(n - 2); return [b, b - t * se, b + t * se];
  }
  const words = text => (String(text || "").toLowerCase().match(/[a-z']+/g) || []);
  function hits(text, lexicon) {
    const ws = words(text), joined = " " + ws.join(" ") + " ", out = [];
    lexicon.forEach(e => {
      if (e.endsWith("*")) { if (ws.some(w => w.startsWith(e.slice(0, -1)))) out.push(e); }
      else if (e.includes(" ")) { if (joined.includes(" " + e + " ")) out.push(e); }
      else if (ws.includes(e)) out.push(e);
    });
    return out;
  }
  function kappa(pairs) {
    const n = pairs.length; if (!n) return { n: 0, agree: null, kappa: null };
    const cats = [...new Set(pairs.map(p => p[0]).concat(pairs.map(p => p[1])))].sort();
    const po = pairs.filter(p => p[0] === p[1]).length / n;
    let pe = 0; cats.forEach(c => { pe += (pairs.filter(p => p[0] === c).length / n) * (pairs.filter(p => p[1] === c).length / n); });
    const k = pe < 1 ? (po - pe) / (1 - pe) : 1;
    return { n, agree: r1(po * 100), kappa: r2(k) };
  }
  const D = {
    "EXAMPLE_MATRIX": {
      "schema": "rsos-matrix/1",
      "id": "safety",
      "center": "Safety is here, now",
      "branches": [
        {
          "id": "blame",
          "cue": "Self-blame",
          "words": [
            "my fault",
            "blame*",
            "should have",
            "stupid",
            "idiot",
            "failed",
            "ruin*"
          ],
          "response": "Slow down. Name one thing you did that kept you or someone else safe.",
          "code": "..-"
        },
        {
          "id": "flood",
          "cue": "Overwhelm",
          "words": [
            "too much",
            "overwhelm*",
            "can't cope",
            "cannot cope",
            "everything",
            "drown*",
            "panic*"
          ],
          "response": "Feet on the floor. Breathe out longer than in. Name three things you can see.",
          "code": "-.-"
        },
        {
          "id": "withdraw",
          "cue": "Withdrawal",
          "words": [
            "give up",
            "alone",
            "no point",
            "leave",
            "hide",
            "nothing matters",
            "shut down"
          ],
          "response": "Stay with me for one breath. What is one small thing that still matters today?",
          "code": "--."
        }
      ]
    },
    "LEVELS": [
      "environment",
      "behaviour",
      "skills",
      "beliefs",
      "identity",
      "mission"
    ],
    "LEVEL_NAMES": {
      "environment": "Environment",
      "behaviour": "Behaviour",
      "skills": "Skills",
      "beliefs": "Beliefs and values",
      "identity": "Identity",
      "mission": "Mission"
    },
    "LEVEL_WORDS": {
      "mission": [
        "for others",
        "for my family",
        "my purpose",
        "purpose",
        "meaning",
        "the world",
        "legacy",
        "bigger than",
        "serve*",
        "mission",
        "calling",
        "for the people"
      ],
      "identity": [
        "i am",
        "i'm a",
        "i'm an",
        "i'm the",
        "kind of person",
        "who i am",
        "myself as",
        "i'm not a",
        "i am not",
        "loser",
        "failure",
        "type of person"
      ],
      "beliefs": [
        "i believe",
        "believe",
        "should",
        "must",
        "have to",
        "important",
        "matters",
        "because",
        "always",
        "never",
        "it's wrong",
        "it's right",
        "value*",
        "deserve*"
      ],
      "skills": [
        "i can",
        "i can't",
        "i cannot",
        "able to",
        "unable",
        "know how",
        "don't know how",
        "learn*",
        "skill*",
        "good at",
        "bad at",
        "capable"
      ],
      "behaviour": [
        "i did",
        "i do",
        "i went",
        "i said",
        "i shout*",
        "i ran",
        "i keep",
        "i stopped",
        "i started",
        "i yell*",
        "i drink",
        "i scroll*",
        "i eat",
        "i smoke"
      ],
      "environment": [
        "at work",
        "at home",
        "in the office",
        "here",
        "there",
        "the room",
        "the city",
        "the weather",
        "the noise",
        "the traffic",
        "when he",
        "when she",
        "they",
        "people around"
      ]
    },
    "ORDER": [
      "mission",
      "identity",
      "beliefs",
      "skills",
      "behaviour",
      "environment"
    ],
    "ABOVE": {
      "environment": "behaviour",
      "behaviour": "skills",
      "skills": "beliefs",
      "beliefs": "identity",
      "identity": "mission",
      "mission": "mission"
    },
    "QUESTION": {
      "environment": "In that place, what is one thing you can do differently?",
      "behaviour": "What would you need to be able to do, so that this changes?",
      "skills": "What do you believe about yourself when you can do that?",
      "beliefs": "Who are you, when that belief is true for you?",
      "identity": "What is that for, beyond you?",
      "mission": "How will that show up tomorrow, in one small act?"
    },
    "PLUGINS": {
      "senses": {
        "title": "Sensory words",
        "types": {
          "visual": [
            "see*",
            "look*",
            "picture*",
            "clear*",
            "bright*",
            "view*",
            "focus*",
            "show*",
            "imagine*",
            "colour*",
            "watch*",
            "vision*"
          ],
          "auditory": [
            "hear*",
            "sound*",
            "listen*",
            "tell*",
            "said",
            "say*",
            "loud*",
            "quiet*",
            "voice*",
            "tune*",
            "ring*",
            "talk*"
          ],
          "kinesthetic": [
            "feel*",
            "felt",
            "touch*",
            "grasp*",
            "heavy",
            "warm*",
            "solid*",
            "pressure*",
            "smooth*",
            "handle*",
            "tight*",
            "hold*"
          ]
        }
      },
      "time": {
        "title": "Time orientation",
        "types": {
          "past": [
            "was",
            "were",
            "used to",
            "back then",
            "remember*",
            "before",
            "had",
            "ago",
            "last year",
            "childhood"
          ],
          "present": [
            "now",
            "today",
            "is",
            "am",
            "right now",
            "currently",
            "these days",
            "this week",
            "at the moment"
          ],
          "future": [
            "will",
            "going to",
            "plan*",
            "tomorrow",
            "next",
            "soon",
            "hope*",
            "someday",
            "future",
            "later"
          ]
        }
      }
    },
    "NEUTRAL": [
      "we",
      "met",
      "about",
      "the",
      "week",
      "and",
      "my",
      "sister",
      "for",
      "a",
      "walk",
      "it",
      "got",
      "okay",
      "then",
      "dinner",
      "with",
      "friends",
      "work",
      "brother",
      "called",
      "nothing",
      "special",
      "slept",
      "fine",
      "the",
      "bus",
      "late"
    ],
    "CORE_WORDS": [
      "peace*",
      "oneness",
      "one with",
      "being",
      "love",
      "loved",
      "okay-ness",
      "ok-ness",
      "whole*",
      "free*",
      "home",
      "still*",
      "light"
    ],
    "CT_FIRST": "Notice the part of you that brings {state}. Thank it. What does it want for you?",
    "CT_NEXT": "And if you have that, fully and completely, what do you want through having it, that is even more important?",
    "OVERRIDE_KINDS": [
      "fear",
      "craving",
      "thought",
      "perceptual"
    ],
    "SETTING_FACTORS": [
      "warmth",
      "music",
      "imagery"
    ],
    "LEVEL_TEST": [
      [
        "The traffic on the way to work makes me tense.",
        "environment"
      ],
      [
        "At work the noise is constant.",
        "environment"
      ],
      [
        "When he raises his voice I freeze.",
        "environment"
      ],
      [
        "The room is too small and too hot.",
        "environment"
      ],
      [
        "There is never a quiet corner at home.",
        "environment"
      ],
      [
        "People around me are always rushing.",
        "environment"
      ],
      [
        "The weather gets me down every November.",
        "environment"
      ],
      [
        "The city is loud at night.",
        "environment"
      ],
      [
        "I shouted at my son this morning.",
        "behaviour"
      ],
      [
        "I scroll my phone until two in the morning.",
        "behaviour"
      ],
      [
        "I keep checking my email.",
        "behaviour"
      ],
      [
        "I drink too much coffee before meetings.",
        "behaviour"
      ],
      [
        "I went home early again.",
        "behaviour"
      ],
      [
        "I stopped going to the gym.",
        "behaviour"
      ],
      [
        "I said yes when I wanted to say no.",
        "behaviour"
      ],
      [
        "I eat when I am bored.",
        "behaviour"
      ],
      [
        "I can't speak in front of a group.",
        "skills"
      ],
      [
        "I don't know how to calm down.",
        "skills"
      ],
      [
        "I'm good at planning but bad at finishing.",
        "skills"
      ],
      [
        "I'm unable to sleep after a fight.",
        "skills"
      ],
      [
        "I want to learn to say no.",
        "skills"
      ],
      [
        "I can focus for ten minutes at most.",
        "skills"
      ],
      [
        "I never learned to swim.",
        "skills"
      ],
      [
        "I'm not capable of keeping a routine.",
        "skills"
      ],
      [
        "I believe people will leave if I am honest.",
        "beliefs"
      ],
      [
        "You should never show weakness.",
        "beliefs"
      ],
      [
        "Family matters more than work.",
        "beliefs"
      ],
      [
        "I have to be perfect or it doesn't count.",
        "beliefs"
      ],
      [
        "It's wrong to ask for help.",
        "beliefs"
      ],
      [
        "Honesty is important to me.",
        "beliefs"
      ],
      [
        "I don't deserve a break.",
        "beliefs"
      ],
      [
        "Things always go wrong because of me.",
        "beliefs"
      ],
      [
        "I am a failure.",
        "identity"
      ],
      [
        "I'm not the kind of person who speaks up.",
        "identity"
      ],
      [
        "I am a calm person underneath.",
        "identity"
      ],
      [
        "I see myself as a fighter.",
        "identity"
      ],
      [
        "I'm an anxious type of person.",
        "identity"
      ],
      [
        "Who I am changed after the accident.",
        "identity"
      ],
      [
        "I am not a leader.",
        "identity"
      ],
      [
        "I'm a loser at heart.",
        "identity"
      ],
      [
        "My purpose is to protect my family.",
        "mission"
      ],
      [
        "I want my life to mean something for others.",
        "mission"
      ],
      [
        "It's bigger than me; I do it for my children.",
        "mission"
      ],
      [
        "I want to serve the people in my town.",
        "mission"
      ],
      [
        "My work should leave a legacy.",
        "mission"
      ],
      [
        "I feel a calling to teach.",
        "mission"
      ],
      [
        "I am here to make the world a little kinder.",
        "mission"
      ],
      [
        "Meaning matters more to me than money.",
        "mission"
      ]
    ]
  };
  const { EXAMPLE_MATRIX, LEVELS, LEVEL_NAMES, LEVEL_WORDS, ORDER, ABOVE, QUESTION, LEVEL_TEST, PLUGINS, NEUTRAL, CORE_WORDS, CT_FIRST, CT_NEXT, OVERRIDE_KINDS, SETTING_FACTORS } = D;

  // ------------------------------------------------------------ the decision matrix and the copilot
  function makeMatrix(id, center, branches) {
    if (branches.length !== 3) throw new Error("a decision matrix has three branches");
    return { schema: "rsos-matrix/1", id, center, branches: branches.map(b => ({ id: b.id, cue: b.cue, words: b.words.slice(), response: b.response, code: b.code || "" })) };
  }
  function copilotMatch(matrix, text) {
    let best = null, score = 0, found = [];
    matrix.branches.forEach(b => { const h = hits(text, b.words); if (h.length > score) { best = b.id; score = h.length; found = h; } });
    return { branch: best, score, words: found, unsafe: UNSAFE.test(text || "") };
  }
  function addUtterance(log, t, text, matrix) {
    const m = copilotMatch(matrix, text), u = { t, text, copilot: m.branch, words: m.words, unsafe: m.unsafe, therapist: null, therapist_t: null };
    log.push(u); return u;
  }
  function mark(log, i, branch, t) { log[i].therapist = branch; log[i].therapist_t = t; return log[i]; }
  function agreement(log) {
    const marked = log.filter(u => u.therapist !== null), k = kappa(marked.map(u => [u.copilot || "none", u.therapist]));
    const lat = marked.filter(u => u.therapist !== "none" && u.therapist_t !== null).map(u => u.therapist_t - u.t);
    const miss = marked.filter(u => u.copilot === null && u.therapist !== "none").length, extra = marked.filter(u => u.copilot !== null && u.therapist === "none").length;
    const unsafe = log.filter(u => u.unsafe).length;
    let say = !marked.length ? "Mark what you chose for each line to measure agreement."
      : "Copilot and therapist agreed on " + k.agree + "% of " + k.n + " lines (kappa " + k.kappa + ")." + (lat.length ? " The therapist answered in " + r1(median(lat)) + " s (median)." : "");
    if (unsafe) say += " " + unsafe + " line" + (unsafe !== 1 ? "s" : "") + " held for the therapist: unsafe wording.";
    return { lines: log.length, marked: marked.length, agree: k.agree, kappa: k.kappa, median_s: lat.length ? r1(median(lat)) : null, copilot_missed: miss, copilot_extra: extra, unsafe, say };
  }

  // ------------------------------------------------------------ levels and the five-step chain
  function levelOf(text) {
    for (const l of ORDER) { const h = hits(text, LEVEL_WORDS[l]); if (h.length) return { level: l, words: h }; }
    return { level: null, words: [] };
  }
  function chain(text) {
    if (UNSAFE.test(text || "")) return { steps: [{ step: "detect", say: "Unsafe wording: held for the therapist. Follow the escalation plan; nothing is generated." }], held: true, level: null };
    const d = levelOf(text), lv = d.level || "behaviour", up = ABOVE[lv];
    return { held: false, level: d.level, steps: [
      { step: "detect", say: "Speaking from " + LEVEL_NAMES[lv].toLowerCase() + (d.words.length ? " (" + d.words.join(", ") + ")" : " (no clear words; assumed)") + "." },
      { step: "analyse", say: "Work one level above: " + LEVEL_NAMES[up].toLowerCase() + "." },
      { step: "modify", say: QUESTION[lv] },
      { step: "output", say: "Ask it slowly, in the client's own words; the router and the safety layer check anything a model adds." },
      { step: "future", say: "Then: picture the next time this happens, and the answer already in place." }] };
  }
  function levelAccuracy() {
    const rows = LEVEL_TEST.map(([t, lv]) => [levelOf(t).level, lv]), by = {};
    LEVELS.forEach(l => { const xs = rows.filter(r => r[1] === l); by[l] = r1(xs.filter(r => r[0] === l).length / xs.length * 100); });
    return { n: rows.length, accuracy: r1(rows.filter(r => r[0] === r[1]).length / rows.length * 100), by_level: by, kappa: kappa(rows.map(r => [r[0] || "none", r[1]])).kappa };
  }

  // ------------------------------------------------------------ typologies from speech
  function count(text, lex) {
    const ws = words(text), joined = " " + ws.join(" ") + " ", singles = lex.filter(e => !e.includes(" "));
    let n = ws.filter(w => singles.some(e => (e.endsWith("*") ? w.startsWith(e.slice(0, -1)) : w === e))).length;
    lex.filter(e => e.includes(" ")).forEach(e => { n += joined.split(" " + e + " ").length - 1; });
    return n;
  }
  function profile(plugin, text, subject, consent) {
    subject = subject || "self";
    if (subject !== "self" && !consent) return { refused: true, say: "Profiling another person's speech needs their consent, recorded first." };
    const pl = PLUGINS[plugin], types = Object.keys(pl.types), counts = {};
    types.forEach(t => { counts[t] = count(text, pl.types[t]); });
    const total = sum(types.map(t => counts[t])), ranked = types.slice().sort((a, b) => (counts[b] - counts[a]) || (types.indexOf(a) - types.indexOf(b)));
    const shares = {}; types.forEach(t => { shares[t] = total ? r1(counts[t] / total * 100) : null; });
    const lead = counts[ranked[0]] - counts[ranked[1]], top = total >= 10 && lead >= Math.max(3, 2 * Math.sqrt(total)) ? ranked[0] : null;
    const say = total < 10 ? "Too few " + pl.title.toLowerCase() + " so far (" + total + "); ten or more give a profile."
      : top ? "Leans " + top + " (" + shares[top] + "% of " + total + " words)." : "No clear lean yet (" + total + " words).";
    return { refused: false, plugin, counts, total, shares, top, say };
  }

  // ------------------------------------------------------------ craving
  function contextTrigger(triggers, event) {
    for (const t of triggers) {
      if (t.kind !== event.kind) continue;
      const v = String(event.value === undefined ? "" : event.value).toLowerCase();
      if (t.kind === "time") { const [a, b] = t.match.split("-"); if (a <= v && v < b) return t; }
      else if (v.includes(t.match.toLowerCase())) return t;
    }
    return null;
  }
  function cueReactivity(log) {
    const rows = log.filter(r => r.craving !== null && r.craving !== undefined).sort((a, b) => a.ts - b.ts);
    if (rows.length < 6 || rows[rows.length - 1].ts - rows[0].ts < 14 * 86400) return { n: rows.length, per_month: null, lo: null, hi: null, verdict: "too_few",
      say: "Rate the craving at six or more cue exposures over two weeks or more to see a trend." };
    const [b, lo, hi] = slope(rows.map(r => (r.ts - rows[0].ts) / 86400 / 30), rows.map(r => r.craving));
    const v = hi < 0 ? "falling" : lo > 0 ? "rising" : "no_clear_change";
    const say = { falling: "Cue-reactivity is falling", rising: "Cue-reactivity is rising", no_clear_change: "No clear change in cue-reactivity yet" }[v];
    return { n: rows.length, per_month: r1(b), lo: r1(lo), hi: r1(hi), verdict: v, say: say + ": " + r1(b) + " points a month [" + r1(lo) + ", " + r1(hi) + "]." };
  }

  // ------------------------------------------------------------ Core Transformation
  const ctStart = state => ({ state, chain: [], done: false, question: CT_FIRST.replace("{state}", state || "this state") });
  function ctAnswer(ct, text) {
    if (ct.done) return ct;
    if (UNSAFE.test(text || "")) { ct.done = true; ct.held = true; ct.question = "Stop here: this needs the therapist. Follow the escalation plan."; return ct; }
    ct.chain.push(String(text).trim());
    if (hits(text, CORE_WORDS).length || ct.chain.length >= 7) { ct.done = true; ct.question = "Core state: " + ct.chain[ct.chain.length - 1] + ". Let it flow back through every step, in reverse."; }
    else ct.question = CT_NEXT;
    return ct;
  }
  const q = s => '"' + String(s).split('"').join("'").split("\n").join(" ") + '"';
  function ctRsx(ct, code) {
    code = code || "..--"; const core = ct.chain.length ? ct.chain[ct.chain.length - 1] : "the core state";
    let L = ['PROTOCOL core_transformation "Core Transformation"', "VERSION 1.0", "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4",
      "BREATH inhale=4s exhale=6s", "", "TIER 1 CORE {", "  V " + q("a light that is " + core), "  A " + q("I have " + core + " already"),
      "  K " + q("feel " + core + " through the whole body"), "  TACTON " + q(code), "}", "", "PHASE core breath=inhale {", "  ACTIVATE CORE", "}"];
    ct.chain.slice(0, -1).reverse().forEach((step, k) => { L = L.concat(["PHASE back" + (k + 1) + " breath=exhale {", "  FEEL " + q("having " + core + " already, " + step + " comes easily"), "}"]); });
    L = L.concat(["PHASE old breath=exhale {", "  FEEL " + q("let " + core + " flow into where " + (ct.state || "the old state") + " used to be"), "}", "PHASE seal breath=inhale {", "  ACTIVATE CORE", '  MARK "core"', "}"]);
    return L.join("\n") + "\n";
  }
  function rescriptRsx(event, symbol, behaviour, light) {
    light = light || "radiant gold";
    return ['PROTOCOL rescript "Re-living with the symbol"', "VERSION 1.0", "SAFETY max_per_hour=2 max_per_day=4 refractory=90s haptic_max=0.4",
      "BREATH inhale=4s exhale=6s", "", "TIER 1 SYMBOL {", "  GLYPH " + q(symbol), "  V " + q(light + " light from " + symbol), '  A "I am here now, and I am safe"', '  K "warmth spreading through the chest"', "}", "",
      "PHASE settle dur=20s {", '  FEEL "Feet on the floor, breathe out slowly"', "}",
      "PHASE distance dur=15s {", "  SEE " + q("the event, briefly, like a small picture far away: " + event), "}",
      "PHASE light breath=inhale {", "  ACTIVATE SYMBOL", "  SEE " + q(light + " light fills the whole scene"), "}",
      "PHASE rehearse dur=30s {", "  SEE " + q("you in the scene, doing what you would do now: " + behaviour), "  WAIT 10s", '  FEEL "notice the body as you act"', "}",
      "PHASE future dur=12s {", "  SEE " + q("the next similar moment, and you, " + behaviour), "}",
      "PHASE close breath=exhale {", '  SAY "Back in the room. Eyes open."', '  MARK "rescripted"', "}"].join("\n") + "\n";
  }

  // ------------------------------------------------------------ the life timeline
  function timelineReport(events) {
    const ev = events.slice().sort((a, b) => ((a.year || 0) - (b.year || 0)) || ((a.title || "") < (b.title || "") ? -1 : (a.title || "") > (b.title || "") ? 1 : 0));
    const spec = ev.filter(e => e.specific).length, dec = {};
    ev.forEach(e => { const d = String(Math.floor(Math.trunc(e.year || 0) / 10) * 10); dec[d] = (dec[d] || 0) + 1; });
    const by = {}; Object.keys(dec).sort().forEach(k => { by[k] = dec[k]; });
    return { nodes: ev.map(e => ({ year: e.year === undefined ? null : e.year, title: e.title === undefined ? null : e.title, glyph: e.glyph || "" })), n: ev.length,
      specific: ev.length ? r1(spec / ev.length * 100) : null, by_decade: by,
      say: !ev.length ? "Add events from any time of your life." : ev.length + " events; " + r1(spec / ev.length * 100) + "% recalled as a specific moment." };
  }

  // ------------------------------------------------------------ overrides, OXQ and DOL-9
  function overrideMetrics(log, days, wakingHours) {
    wakingHours = wakingHours === undefined ? 16 : wakingHours;
    const done = log.filter(e => e.overridden), lat = done.filter(e => e.latency_s !== null && e.latency_s !== undefined).map(e => e.latency_s).sort((a, b) => a - b);
    const wake = done.filter(e => e.latency_s !== null && e.latency_s !== undefined && e.after_wake).map(e => e.latency_s);
    const p90 = lat.length ? lat[Math.min(lat.length - 1, Math.ceil(0.9 * lat.length) - 1)] : null;
    const by = {}; OVERRIDE_KINDS.forEach(k => { by[k] = { events: log.filter(e => e.kind === k).length, turned: done.filter(e => e.kind === k).length }; });
    const oxq = days > 0 ? done.length / (days * wakingHours) * 100 : null;
    return { events: log.length, overrides: done.length, per_day: days > 0 ? r1(done.length / days) : null, turned: log.length ? r1(done.length / log.length * 100) : null,
      median_s: lat.length ? r1(median(lat)) : null, p90_s: r1(p90), after_wake_s: wake.length ? r1(median(wake)) : null, oxq: r1(oxq), by_kind: by,
      within_4s: lat.length ? r1(lat.filter(x => x <= 4).length / lat.length * 100) : null };
  }
  function monthly(log) {
    if (!log.length) return []; const t0 = Math.min(...log.map(e => e.ts)), out = {};
    log.forEach(e => { const m = Math.floor((e.ts - t0) / (30 * 86400)); const a = out[m] || (out[m] = [0, 0]); a[0]++; if (e.overridden) a[1]++; });
    return Object.keys(out).map(Number).sort((a, b) => a - b).map(m => ({ month: m + 1, events: out[m][0], turned: r1(out[m][1] / out[m][0] * 100) }));
  }
  function dol9Rsx(phrase, gesture, action) {
    phrase = phrase || "I move, I act"; gesture = gesture || "Fist closed, shoulders back"; action = action || "Do the next small task now";
    return ['PROTOCOL dol9 "DOL-9 daily override loop"', "VERSION 1.0", "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4",
      "BREATH inhale=4s hold=2s exhale=6s", "", "PHASE posture dur=6s {", '  GESTURE "Stand or sit tall, head up"', "}",
      "REPEAT 5 {", "  PHASE in breath=inhale {", '    FEEL "Breathe in"', "  }", "  PHASE hold breath=hold {", '    FEEL "Hold"', "  }",
      "  PHASE out breath=exhale {", '    FEEL "Breathe out"', "  }", "}",
      "PHASE phrase dur=6s {", "  SAY " + q(phrase), "}", "PHASE gesture dur=4s {", "  GESTURE " + q(gesture), "}",
      "PHASE action dur=14s {", "  FEEL " + q(action), '  MARK "override"', "}"].join("\n") + "\n";
  }
  function routeEvent(kind) {
    if (kind === "perceptual") return { route: "escalate", auto: false, say: "Unusual perceptual experiences go to your clinician, not to automatic cues. Note what happened and contact them; nothing fires by itself." };
    if (!OVERRIDE_KINDS.includes(kind)) throw new Error("kind must be one of " + OVERRIDE_KINDS.join(", "));
    return { route: "offer", auto: false, say: "Offer the override; the person starts it (the autonomy gate decides anything more)." };
  }

  // ------------------------------------------------------------ contexts, the four-day block, the burst, the setting
  function speechContext(text, contexts) { for (const c of contexts) { const h = hits(text, c.phrases); if (h.length) return { id: c.id, heard: h }; } return null; }
  function fourDayBlock(principle, startDay, perDay) {
    startDay = startDay || 0; perDay = perDay === undefined ? 3 : perDay;
    const names = ["Learn", "Rehearse", "Apply in real contexts", "Test without cues"];
    return [0, 1, 2, 3].map(d => ({ day: startDay + d, step: names[d], principle, sessions: d < 3 ? perDay : 1 }));
  }
  function burst(code, repeats, gapMs) {
    repeats = repeats === undefined ? 3 : repeats; gapMs = gapMs === undefined ? 400 : gapMs;
    let one = 0; for (const ch of code) one += ch === "." ? 100 : ch === "-" ? 300 : 0;
    one += 100 * Math.max(0, code.split(" ").join("").length - 1) + 400 * (code.split(" ").length - 1);
    return { code, repeats, ms: one * repeats + gapMs * (repeats - 1) };
  }
  function settingEffect(sessions, factor) {
    const has = s => s.setting && s.setting[factor];
    const on = sessions.filter(s => has(s)).map(s => s.change), off = sessions.filter(s => !has(s)).map(s => s.change);
    if (on.length < 3 || off.length < 3) return { factor, difference: null, lo: null, hi: null, verdict: "too_few", say: "Log three or more sessions with and without " + factor + "." };
    const [d, lo, hi] = ciDiff(on, off), v = lo > 0 ? "helps" : hi < 0 ? "hurts" : "unclear";
    return { factor, difference: r1(d), lo: r1(lo), hi: r1(hi), verdict: v,
      say: ({ helps: "Sessions with " + factor + " went better", hurts: "Sessions with " + factor + " went worse", unclear: "No clear effect of " + factor + " yet" })[v] + ": " + r1(d) + " points [" + r1(lo) + ", " + r1(hi) + "]." };
  }

  // ------------------------------------------------------------ simulation
  function simSession(seed, lines, therapistAcc, matrix) {
    lines = lines || 40; therapistAcc = therapistAcc === undefined ? 0.85 : therapistAcc; const m = matrix || EXAMPLE_MATRIX, rng = new P.Rng(seed), log = [];
    for (let i = 0; i < lines; i++) {
      let truth = null; const ws = []; for (let k = 0; k < 6; k++) ws.push(NEUTRAL[Math.floor(rng.u() * NEUTRAL.length)]);
      if (rng.u() < 0.5) { const b = m.branches[Math.floor(rng.u() * 3)]; truth = b.id; if (rng.u() < 0.8) ws.splice(3, 0, b.words[Math.floor(rng.u() * b.words.length)].replace("*", "")); }
      const u = addUtterance(log, i * 30, ws.join(" "), m); u._truth = truth;
      const choice = truth === null ? (rng.u() < 0.95 ? "none" : m.branches[Math.floor(rng.u() * 3)].id) : (rng.u() < therapistAcc ? truth : "none");
      mark(log, i, choice, i * 30 + 1 + 3 * rng.u());
    }
    return log;
  }

  const api = { UNSAFE, EXAMPLE_MATRIX, LEVELS, LEVEL_NAMES, LEVEL_WORDS, QUESTION, LEVEL_TEST, PLUGINS, CORE_WORDS, OVERRIDE_KINDS, SETTING_FACTORS, words, hits, kappa,
    makeMatrix, copilotMatch, addUtterance, mark, agreement, levelOf, chain, levelAccuracy, profile, contextTrigger, cueReactivity, ctStart, ctAnswer, ctRsx, rescriptRsx,
    timelineReport, overrideMetrics, monthly, dol9Rsx, routeEvent, speechContext, fourDayBlock, burst, settingEffect, simSession };
  if (node) module.exports = api; else root.RSOSCopilot = api;
})(typeof self !== "undefined" ? self : this);
