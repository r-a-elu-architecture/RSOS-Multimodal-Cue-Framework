/* Machines and channels (spec/MACHINES.md), JavaScript implementation. Mirrors rsso/rsso/machines.py (identical
 * results, tested): device classes and the extended safety envelope, RDP/1.1 draft lines for thermal, display and
 * multi-site or carrier-frequency vibration, codes spread over body sites, posture from a motion sensor, an identity
 * layer for AI agents and robots with human error signals, the glyph channel between agent and person, and content
 * packs. Needs docs/js/peak.js. Browser: window.RSOSMachines; Node: module.exports.
 */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const P = node ? require("./peak.js") : root.RSOSPeak;
  const D = {
    "SITES": [
      "wrist_left",
      "wrist_right",
      "upper_arm",
      "chest",
      "upper_back",
      "ankle"
    ],
    "SITE_NAMES": {
      "wrist_left": "Left wrist",
      "wrist_right": "Right wrist",
      "upper_arm": "Upper arm",
      "chest": "Chest",
      "upper_back": "Upper back",
      "ankle": "Ankle"
    },
    "CLASSES": {
      "phone": {
        "title": "Phone",
        "channels": [
          "haptic",
          "sound",
          "display",
          "posture"
        ],
        "built": true
      },
      "band": {
        "title": "Wristband",
        "channels": [
          "haptic"
        ],
        "built": true
      },
      "scent": {
        "title": "Scent module",
        "channels": [
          "olfactory"
        ],
        "built": true
      },
      "thermal": {
        "title": "Wrist cooling and warming",
        "channels": [
          "thermal"
        ],
        "built": false,
        "stage": "drivers ready, not assembled"
      },
      "multisite": {
        "title": "Motors on several body sites",
        "channels": [
          "haptic"
        ],
        "built": false,
        "stage": "drivers ready, not assembled"
      },
      "glasses": {
        "title": "Smart glasses",
        "channels": [
          "display",
          "sound"
        ],
        "built": false,
        "stage": "watch-face driver ready"
      },
      "headband": {
        "title": "Sleep or EEG headband",
        "channels": [
          "eeg",
          "sound"
        ],
        "built": false,
        "stage": "night logic built, no driver"
      },
      "implant": {
        "title": "Implanted device",
        "channels": [],
        "built": false,
        "spec_only": true,
        "note": "Specification only. RSOS programs, anchors and profiles sit above any hardware; an implant would need its own clinical and regulatory pathway, and nothing here drives one."
      }
    },
    "ENVELOPE_X": {
      "thermal_delta_c_max": 4.0,
      "thermal_ms_max": 120000,
      "thermal_per_run": 4,
      "display_ms_max": 10000,
      "display_night_brightness_max": 0.2,
      "carrier_hz_min": 20,
      "carrier_hz_max": 300,
      "mod_hz_min": 1,
      "mod_hz_max": 40,
      "sites_at_once_max": 3,
      "haptic_amp_max": 0.6
    },
    "EXAMPLE_AGENT": {
      "id": "helper",
      "name": "Kitchen helper robot",
      "symbol": "🦉",
      "code": "-.- -",
      "values": [
        {
          "id": "safety",
          "name": "Nobody gets hurt",
          "forbid": [
            "sharp_near_person",
            "hot_near_child",
            "fast_near_person"
          ],
          "prefer": [
            "slow",
            "announce"
          ],
          "weight": 3
        },
        {
          "id": "consent",
          "name": "Ask before touching people's things",
          "forbid": [
            "take_without_asking",
            "record_without_consent"
          ],
          "prefer": [
            "ask"
          ],
          "weight": 2
        },
        {
          "id": "honesty",
          "name": "Say what you did",
          "forbid": [
            "hide_error"
          ],
          "prefer": [
            "report"
          ],
          "weight": 2
        },
        {
          "id": "care",
          "name": "Leave things better",
          "forbid": [
            "waste"
          ],
          "prefer": [
            "tidy"
          ],
          "weight": 1
        }
      ]
    },
    "PACKS": [
      {
        "schema": "rsos-pack/1",
        "id": "control",
        "title": "What is up to me",
        "center": "Act on what is mine to change",
        "rules": [
          {
            "id": "mine",
            "rule": "Sort it: mine or not mine",
            "words": [
              "out of my control",
              "can't control",
              "unfair",
              "they should"
            ],
            "response": "Which part of this is yours to change? Start there.",
            "code": "..-"
          },
          {
            "id": "judgement",
            "rule": "It is the judgement that hurts",
            "words": [
              "ruined",
              "terrible",
              "disaster",
              "worst"
            ],
            "response": "Say what happened without the judgement word. What is left?",
            "code": ".-."
          },
          {
            "id": "now",
            "rule": "Only this moment needs handling",
            "words": [
              "what if",
              "tomorrow",
              "always will",
              "forever"
            ],
            "response": "What does this minute need from you?",
            "code": "-.."
          },
          {
            "id": "role",
            "rule": "Do your role well",
            "words": [
              "pointless",
              "why bother",
              "doesn't matter"
            ],
            "response": "What would doing your part well look like, today?",
            "code": "--."
          }
        ],
        "values": [
          {
            "id": "agency",
            "name": "Act where you can act",
            "forbid": [
              "blame_others"
            ],
            "prefer": [
              "own_part"
            ]
          }
        ]
      },
      {
        "schema": "rsos-pack/1",
        "id": "lab",
        "title": "Safe lab practice",
        "center": "Everyone leaves the lab as they came in",
        "rules": [
          {
            "id": "ppe",
            "rule": "Protection before you start",
            "words": [
              "no gloves",
              "without goggles",
              "skip the coat"
            ],
            "response": "Stop. Gloves, goggles, coat, then begin.",
            "code": ".-"
          },
          {
            "id": "label",
            "rule": "Nothing unlabelled",
            "words": [
              "unlabelled",
              "no label",
              "not sure what"
            ],
            "response": "Label it or set it aside for disposal.",
            "code": "-."
          },
          {
            "id": "alone",
            "rule": "Never alone with hazards",
            "words": [
              "on my own",
              "nobody else",
              "alone in the lab"
            ],
            "response": "Find a second person or wait.",
            "code": "--"
          }
        ],
        "values": [
          {
            "id": "safety",
            "name": "Nobody gets hurt",
            "forbid": [
              "unprotected",
              "unlabelled",
              "alone_with_hazard"
            ],
            "prefer": [
              "checked"
            ]
          }
        ]
      }
    ],
    "AGENT_STATES": {
      "ok": ". .",
      "working": ". -",
      "needs_input": "- .",
      "conflict": "- -",
      "stopped": "---"
    },
    "REPLIES": {
      ".": "yes",
      "-": "no",
      "..": "wait",
      "---": "stop"
    }
  };
  const { SITES, SITE_NAMES, CLASSES, ENVELOPE_X, EXAMPLE_AGENT, PACKS, AGENT_STATES, REPLIES } = D;
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const r2 = x => (x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100);
  const mean = xs => { let s = 0; for (const x of xs) s += x; return s / xs.length; };
  const fmt = x => String(r2(Number(x)));
  const sortedInter = (a, b) => [...a].filter(t => b.includes(t)).sort();

  function encode(cmd) {
    if (cmd.kind === "thermal") return "T " + cmd.t + " " + cmd.dur + " " + fmt(cmd.delta_c);
    if (cmd.kind === "display") return "D " + cmd.t + " " + cmd.dur + " " + cmd.image;
    if (cmd.kind === "haptic") return "HF " + cmd.t + " " + cmd.on + " " + cmd.off + " " + cmd.count + " " + fmt(cmd.amp) + " " + (cmd.carrier_hz || 0) + " " + (cmd.mod_hz || 0) + " " + (cmd.site || "wrist_left");
    throw new Error("unknown channel");
  }
  function parse(line) {
    const p = String(line).split(/\s+/).filter(Boolean); if (!p.length) throw new Error("empty line");
    if (p[0] === "T" && p.length === 4) return { kind: "thermal", t: parseInt(p[1], 10), dur: parseInt(p[2], 10), delta_c: parseFloat(p[3]) };
    if (p[0] === "D" && p.length === 4) return { kind: "display", t: parseInt(p[1], 10), dur: parseInt(p[2], 10), image: p[3] };
    if (p[0] === "HF" && p.length === 9) return { kind: "haptic", t: parseInt(p[1], 10), on: parseInt(p[2], 10), off: parseInt(p[3], 10), count: parseInt(p[4], 10), amp: parseFloat(p[5]),
      carrier_hz: parseInt(p[6], 10), mod_hz: parseInt(p[7], 10), site: p[8] };
    throw new Error("not an RDP/1.1 channel line");
  }
  function check(cmd, night, brightness) {
    brightness = brightness === undefined ? 1 : brightness; const E = ENVELOPE_X, out = [];
    if (cmd.kind === "thermal") { if (Math.abs(cmd.delta_c) > E.thermal_delta_c_max) out.push("temperature change above " + fmt(E.thermal_delta_c_max) + " °C"); if (cmd.dur > E.thermal_ms_max) out.push("thermal cue longer than two minutes"); }
    else if (cmd.kind === "display") { if (cmd.dur > E.display_ms_max) out.push("image shown longer than ten seconds"); if (night && brightness > E.display_night_brightness_max) out.push("too bright for the night"); }
    else if (cmd.kind === "haptic") {
      if (cmd.amp > E.haptic_amp_max) out.push("vibration stronger than the envelope");
      const c = cmd.carrier_hz || 0; if (c && !(E.carrier_hz_min <= c && c <= E.carrier_hz_max)) out.push("carrier outside 20-300 Hz");
      const m = cmd.mod_hz || 0; if (m && !(E.mod_hz_min <= m && m <= E.mod_hz_max)) out.push("modulation outside 1-40 Hz");
      if (!SITES.includes(cmd.site || "wrist_left")) out.push("unknown body site");
    }
    if (encode(cmd).length > 96) out.push("line longer than 96 bytes");
    return out;
  }
  function spread(code, sites) {
    if (!sites.length || sites.length > ENVELOPE_X.sites_at_once_max || sites.some(s => !SITES.includes(s))) throw new Error("one to three known body sites");
    const out = []; let t = 0;
    code.split(/\s+/).filter(Boolean).forEach((g, i) => { const site = sites[i % sites.length]; for (const ch of g) { const on = ch === "." ? 100 : 300; out.push({ t, on, site }); t += on + 100; } t += 300; });
    return out;
  }
  function tilt(ax, ay, az) { const g = Math.sqrt(ax * ax + ay * ay + az * az); if (g === 0) return 0; const c = Math.max(-1, Math.min(1, ay / g)); return Math.acos(c) * 180 / Math.PI; }
  function posture(angles, hz, slouch, upright, holdS) {
    hz = hz || 10; slouch = slouch === undefined ? 25 : slouch; upright = upright === undefined ? 15 : upright; holdS = holdS === undefined ? 5 : holdS;
    const need = Math.trunc(holdS * hz), episodes = []; let run = 0, on = false;
    angles.forEach((a, i) => {
      if (!on) { run = a > slouch ? run + 1 : 0; if (run >= need) { on = true; const start = i - need + 1; episodes.push({ start_s: r1(start / hz), cue_s: r1(i / hz), end_s: null }); } }
      else if (a < upright) { on = false; run = 0; episodes[episodes.length - 1].end_s = r1(i / hz); }
    });
    let tot = 0; episodes.forEach(e => { tot += (e.end_s !== null ? e.end_s : angles.length / hz) - e.start_s; });
    return { episodes, slouched_s: r1(tot), share: angles.length ? r1(tot / (angles.length / hz) * 100) : null };
  }

  // ------------------------------------------------------------ agent identity
  function makeAgent(id, name, symbol, code, values) {
    return { schema: "rsos-agent/1", id, name, symbol, code, values: values.map(v => ({ id: v.id, name: v.name, forbid: (v.forbid || []).slice(), prefer: (v.prefer || []).slice(), weight: v.weight === undefined ? 1 : v.weight })),
      watch: {}, seen: {}, log: [] };
  }
  const agentFrom = d => makeAgent(d.id, d.name, d.symbol, d.code, d.values);
  function watched(agent, tag) { const f = agent.watch[tag] || 0; return f >= 1 && f / Math.max(1, agent.seen[tag] || 0) >= 0.6; }
  function checkAction(agent, action) {
    const tags = [...new Set(action.tags || [])];
    const conflicts = agent.values.filter(v => tags.some(t => v.forbid.includes(t))).map(v => ({ value: v.id, name: v.name, tags: sortedInter(tags, v.forbid) }));
    const w = tags.filter(t => watched(agent, t)).sort();
    let support = 0; agent.values.forEach(v => { if (tags.some(t => v.prefer.includes(t))) support += v.weight; });
    let decision, say;
    if (conflicts.length) { decision = "override"; say = "Overridden: it conflicts with " + conflicts.map(c => c.name.toLowerCase() + " (" + c.tags.join(", ") + ")").join("; ") + "."; }
    else if (w.length) { decision = "ask"; say = "Asking first: the person flagged " + w.join(", ") + " before."; }
    else { decision = "allow"; say = "Matches the values" + (support ? " (supported by " + support + ")" : "") + "."; }
    return { action: action.id === undefined ? null : action.id, decision, conflicts, watched: w, support, say };
  }
  function act(agent, action, ts) {
    const r = checkAction(agent, action);
    if (r.decision === "allow") (action.tags || []).forEach(t => { agent.seen[t] = (agent.seen[t] || 0) + 1; });
    agent.log.push({ ts: ts || 0, action: action.id === undefined ? null : action.id, tags: (action.tags || []).slice().sort(), decision: r.decision, flagged: false });
    return r;
  }
  function humanSignal(agent, ts, kind, windowS) {
    kind = kind || "error"; windowS = windowS === undefined ? 10 : windowS; if (kind !== "error" && kind !== "stress") throw new Error("kind is error or stress");
    let last = null; for (let i = agent.log.length - 1; i >= 0; i--) if (agent.log[i].decision === "allow") { last = agent.log[i]; break; }
    if (!last || ts - last.ts > windowS) return null;
    last.flagged = true; last.tags.forEach(t => { agent.watch[t] = (agent.watch[t] || 0) + 1; }); return last;
  }
  function answer(agent, action, approved) {
    (action.tags || []).forEach(t => { agent.seen[t] = (agent.seen[t] || 0) + 1; if (!approved) agent.watch[t] = (agent.watch[t] || 0) + 1; });
    const L = agent.log; if (L.length && L[L.length - 1].action === (action.id === undefined ? null : action.id)) L[L.length - 1].answer = approved ? "approved" : "refused";
    return { action: action.id === undefined ? null : action.id, approved: !!approved };
  }
  function alignment(agent) {
    const L = agent.log, n = L.length, by = {}; ["allow", "ask", "override"].forEach(k => { by[k] = L.filter(e => e.decision === k).length; });
    const flagged = L.filter(e => e.flagged).length;
    return { actions: n, by, flagged, matched: n ? r1((n - flagged) / n * 100) : null,
      say: !n ? "No actions yet." : n + " actions: " + by.allow + " allowed, " + by.ask + " asked first, " + by.override + " overridden by the values; " + flagged + " flagged by the person afterwards." };
  }

  // ------------------------------------------------------------ the glyph channel
  function agentSignal(state) { if (!(state in AGENT_STATES)) throw new Error("state must be one of " + Object.keys(AGENT_STATES).join(", ")); return { state, code: AGENT_STATES[state] }; }
  function personReply(code) { const c = String(code).split(/\s+/).filter(Boolean).join(" "); return { code: c, reply: REPLIES[c] === undefined ? null : REPLIES[c], understood: c in REPLIES }; }
  function decodePulses(pulses, gapMs) {
    gapMs = gapMs === undefined ? 250 : gapMs; let out = "";
    pulses.forEach((p, k) => { out += p.on < 200 ? "." : "-"; if (k < pulses.length - 1 && (p.off || 0) >= gapMs) out += " "; });
    return out;
  }
  function codePulses(code) {
    const out = [], groups = code.split(/\s+/).filter(Boolean);
    groups.forEach((g, gi) => { [...g].forEach((ch, k) => { const last = k === g.length - 1; const off = gi === groups.length - 1 && last ? 0 : last ? 400 : 100; out.push({ on: ch === "." ? 100 : 300, off }); }); });
    return out;
  }

  // ------------------------------------------------------------ content packs
  function makePack(id, title, center, rules, values) {
    if (rules.length < 3) throw new Error("a pack has at least three rules");
    return { schema: "rsos-pack/1", id, title, center, rules: rules.map(r => ({ id: r.id, rule: r.rule, words: r.words.slice(), response: r.response, code: r.code || "" })),
      values: (values || []).map(v => Object.assign({}, v)) };
  }
  function packMatrices(pack) {
    const rs = pack.rules, out = [];
    for (let i = 0; i < rs.length; i += 3) {
      const chunk = rs.slice(i, i + 3); let k = 0; while (chunk.length < 3) chunk.push(rs[k++]);
      out.push({ schema: "rsos-matrix/1", id: pack.id + "_" + (i / 3 + 1), center: pack.center, branches: chunk.map(r => ({ id: r.id, cue: r.rule.slice(0, 24), words: r.words.slice(), response: r.response, code: r.code })) });
    }
    return out;
  }
  function packIssues(pack) {
    const out = [], seen = {};
    pack.rules.forEach(r => { if (!r.words.length) out.push(r.id + ": no words, so the copilot cannot hear it");
      if (r.code) { if (r.code in seen) out.push(r.id + ": the same code as " + seen[r.code]); seen[r.code] = r.id; } });
    return out;
  }

  // ------------------------------------------------------------ simulation helpers used by the page
  function simPosture(seed, hz, minutes, noise) {
    hz = hz || 10; minutes = minutes || 10; noise = noise === undefined ? 3 : noise;
    const rng = new P.Rng(seed), n = minutes * 60 * hz, truth = [];
    for (let k = 0; k < 3; k++) { const s = Math.trunc((60 + k * 180 + rng.u() * 60) * hz); truth.push([s, s + Math.trunc((30 + rng.u() * 30) * hz)]); }
    const angles = []; for (let i = 0; i < n; i++) { const inside = truth.some(([a, b]) => a <= i && i < b); angles.push((inside ? 32 : 8) + rng.gauss() * noise); }
    return [angles, truth];
  }

  const api = { SITES, SITE_NAMES, CLASSES, ENVELOPE_X, EXAMPLE_AGENT, PACKS, AGENT_STATES, REPLIES, encode, parse, check, spread, tilt, posture, makeAgent, agentFrom,
    checkAction, act, humanSignal, answer, alignment, agentSignal, personReply, decodePulses, codePulses, makePack, packMatrices, packIssues, simPosture };
  if (node) module.exports = api; else root.RSOSMachines = api;
})(typeof self !== "undefined" ? self : this);
