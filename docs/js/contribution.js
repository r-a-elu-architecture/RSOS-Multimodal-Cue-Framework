/* Research data contribution, JavaScript implementation. Mirrors rsso/rsso/contribution.py (identical files, tested).
 * One de-identified, checksummed file per person, clinician or lab (spec/DATA_CONTRIBUTION.md): only the scopes
 * the contributor chose, dates as day numbers from the first run, random ids, no free text unless shared.
 * Browser: window.RSOSContribution (needs RSOSMetrics and RSOSMemstack); Node: module.exports.
 */
(function (root) {
  "use strict";
  const M = typeof module !== "undefined" && module.exports ? require("./metrics.js") : root.RSOSMetrics;
  const MS = typeof module !== "undefined" && module.exports ? require("./memstack.js") : root.RSOSMemstack;
  const SCHEMA = "rsos-contribution/1", CONSENT_VERSION = "rsos-data-consent/1";
  const ROLES = ["person", "clinician", "lab"];
  const SCOPES = {
    runs: "Practice runs: program, tier, glyph, code, trigger, ratings before and after, start time, completion; weekly automaticity checks; computed metrics",
    physiology: "Heart rate and heart-rate variability before and after each run",
    plan: "The structure of node plans and programmed cues: archetypes, modes, which senses have cues, frame scores, dose",
    texts: "Your own words: frames, cue texts, contexts, trigger notes, clinician and lab notes",
    calibration: "Glyph and colour choices",
    recognition: "Results of the vibration-code recognition check",
    outcomes: "Standard questionnaire totals over time (PHQ-9, GAD-7, PCL-5, PSS-10, WEMWBS, global change)",
    safety: "Adverse events and stopped runs",
    profile: "Age band, gender, handedness, world region, prior practice",
    health: "Health information: what the plan is for, self-reported conditions, diagnosis categories",
    clinical: "Clinician sessions and ratings",
    lab: "Lab, device and recording descriptions (EEG, BCI, heart rate)"
  };
  const REQUIRED = ["runs"];
  const KNOWN_PROTOCOLS = ["override", "interrupt_only", "swish", "legacy_tier8", "paced_breathing", "tier003_command_stack",
    "tier012_breath_anchor", "tier014_seal", "tier016_stillness", "tier406_release", "tier579_glyph", "node_lion", "node_observer"];
  const RUN_CORE = ["program_kind", "program_hash", "trigger", "trigger_channel", "sud_before", "sud_after", "agency_before",
    "agency_after", "latency_s", "completed", "stopped_at_phase", "tier", "voice", "outputs", "inhale_s", "exhale_s", "glyph", "tacton",
    "node_mode", "duration_s", "planned_s"];
  const RUN_NUM = new Set(["sud_before", "sud_after", "agency_before", "agency_after", "latency_s", "completed", "inhale_s",
    "exhale_s", "duration_s", "planned_s", "hr_before", "hr_after", "rmssd_before", "rmssd_after"]);
  const RUN_PHYS = ["hr_before", "hr_after", "rmssd_before", "rmssd_after", "hr_source"];
  const SCALES = { PHQ9: [0, 27], GAD7: [0, 21], PCL5: [0, 80], PSS10: [0, 40], WEMWBS: [14, 70], PGIC: [1, 7], SUDS: [0, 10] };
  const SEVERITY = ["mild", "moderate", "serious"], RELATED = ["unrelated", "unlikely", "possible", "likely"];
  const AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"];
  const GENDERS = ["woman", "man", "non-binary", "another", "prefer not to say"], HANDS = ["right", "left", "both"];
  const REGIONS = ["Africa", "Asia", "Europe", "Latin America and Caribbean", "Middle East", "North America", "Oceania"];
  const PRACTICES = ["meditation", "breathwork", "hypnosis", "nlp", "psychotherapy", "neurofeedback", "martial arts", "music"];
  const LEVELS = ["none", "some", "regular"];
  const CONDITIONS = ["ptsd", "depression", "anxiety", "chronic_stress", "adhd", "insomnia", "chronic_pain", "addiction", "other"];
  const DAY = 86400;
  const has = v => v !== null && v !== undefined;

  function num(v) {
    if (typeof v === "boolean") return v ? 1 : 0;
    if (v === null || v === undefined || v === "") return null;
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }
  function pick(d, keys, allowed) {
    const out = {};
    for (const k of keys) { const v = d[k]; if (!has(v) || v === "" || (allowed && allowed[k] && !allowed[k].includes(v))) continue; out[k] = v; }
    return out;
  }
  function fnv1a(text) {
    let h = 0x811c9dc5;
    for (const b of new TextEncoder().encode(text)) { h ^= b; h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(16).padStart(8, "0");
  }
  function day(ts, t0) { const t = num(ts); return t === null || t0 === null || t0 === undefined ? null : Math.floor((t - t0) / DAY); }
  const tsOf = r => num(r.timestamp) || 0;

  function runs(raw, scopes, t0) {
    return raw.slice().sort((a, b) => tsOf(a) - tsOf(b)).map(r => {
      const x = { day: day(r.timestamp, t0) };
      if (num(r.local_hour) !== null) x.hour = num(r.local_hour);
      if (num(r.weekday) !== null) x.weekday = num(r.weekday);
      const proto = String(r.protocol || "");
      x.protocol = KNOWN_PROTOCOLS.includes(proto) || scopes.has("texts") ? proto : "custom";
      for (const k of RUN_CORE.concat(scopes.has("physiology") ? RUN_PHYS : [])) {
        let v = r[k];
        v = RUN_NUM.has(k) ? num(v) : (!has(v) || v === "" ? null : String(v));
        if (v !== null) x[k] = v;
      }
      if (scopes.has("texts") && r.trigger_note) x.trigger_note = String(r.trigger_note);
      if ("sud_before" in x && "sud_after" in x) x.sud_change = x.sud_after - x.sud_before;
      if ("agency_before" in x && "agency_after" in x) x.agency_change = x.agency_after - x.agency_before;
      return x;
    });
  }
  function plan(p, scopes) {
    if (!p || !p.nodes || !p.nodes.length) return null;
    const texts = scopes.has("texts"), intake = p.intake || {}, rawNodes = intake.nodes || [];
    const nodes = p.nodes.map((n, i) => {
      const ch = n.channels || {}, raw = rawNodes[i] || {};
      const x = { archetype: n.archetype || "own", mode: n.mode, tacton: n.tacton, glyph: n.glyph || null,
        senses: Object.fromEntries([..."VAKOG"].map(k => [k, !!raw[k]])), frames: (n.frames || []).length,
        contexts: (n.contexts || []).length, rules: (n.rules || []).length,
        frame_checks: (n.frame_checks || []).map(f => ({ score: f.score, scope: f.scope, kind: f.kind, flags: (f.flags || []).slice() })) };
      if (num(raw.believability) !== null) x.believability = num(raw.believability);
      if (texts) Object.assign(x, { name: n.name, state: n.meaning, cues: Object.fromEntries(Object.entries(ch).filter(([, v]) => v)),
        frame_texts: (n.frames || []).slice(), context_texts: (n.contexts || []).slice(), rule_texts: (n.rules || []).slice() });
      for (const k of Object.keys(x)) if (!has(x[k])) delete x[k];
      return x;
    });
    const first = (p.schedule || [])[0] || {};
    const out = { planner: p.planner, author: p.author, nodes, tiers: (p.tiers || []).slice(), dose: { per_day: num(first.per_day), days: num(first.days) },
      approved: !!p.approved, therapist_led: !!p.therapist_led, devices: Object.entries(intake.devices || {}).filter(([, v]) => v).map(([k]) => k).sort() };
    if (scopes.has("health")) {
      out.concerns = (intake.concerns || []).slice();
      const phys = intake.physiology || {};
      if (scopes.has("physiology") && Object.keys(phys).length) out.baseline = Object.fromEntries(Object.entries(phys).filter(([, v]) => num(v) !== null).map(([k, v]) => [k, num(v)]));
    }
    if (texts) Object.assign(out, { symptoms: intake.symptoms || "", triggers: (intake.triggers || []).slice() });
    for (const k of Object.keys(out)) if (!has(out[k])) delete out[k];
    return out;
  }
  function cues(list, scopes, t0) {
    return (list || []).map(c => {
      const x = { tier: String(c.tier || ""), therapist_led: ["414", "420", "439", "440"].includes(String(c.tier || "")), author: c.author || "self",
        revoked: has(c.revoked_ms), sound: !!c.sound_hz };
      if (t0 !== null && num(c.created_ms) !== null) x.day = day(num(c.created_ms) / 1000, t0);
      if (scopes.has("texts")) x.content = c.content || "";
      return x;
    });
  }
  function calibration(u) {
    if (!u) return null;
    const tiers = {};
    for (const [k, v] of Object.entries(u.tiers || {})) tiers[k] = { glyph: v.glyph, candidates: (v.candidates || []).slice(), comparisons: v.comparisons || [], scores: (v.scores || []).slice() };
    return { tiers, colour: u.colour || null };
  }
  const dayOf = (o, t0) => t0 !== null && has(o.ts) ? day(o.ts, t0) : num(o.day);
  function outcomes(items, t0) {
    const out = [];
    for (const o of items || []) {
      const s = String(o.scale || "").toUpperCase(), total = num(o.total);
      if (!(s in SCALES) || total === null || total < SCALES[s][0] || total > SCALES[s][1]) continue;
      out.push({ scale: s, total, rater: ["self", "clinician"].includes(o.rater) ? o.rater : "self", day: dayOf(o, t0) });
    }
    const key = x => x.day === null ? -1e9 : x.day;
    return out.sort((a, b) => key(a) - key(b) || (a.scale < b.scale ? -1 : a.scale > b.scale ? 1 : 0));
  }
  function adverse(items, t0, texts) {
    return (items || []).map(a => {
      const x = pick(a, ["severity", "related"], { severity: SEVERITY, related: RELATED });
      x.resolved = !!a.resolved; x.day = dayOf(a, t0);
      if (texts && a.text) x.text = String(a.text);
      return x;
    });
  }
  function profile(p, scopes) {
    p = p || {}; const out = {};
    if (scopes.has("profile")) {
      Object.assign(out, pick(p, ["age_band", "gender", "handedness", "region"], { age_band: AGE_BANDS, gender: GENDERS, handedness: HANDS, region: REGIONS }));
      const exp = Object.fromEntries(Object.entries(p.experience || {}).filter(([k, v]) => PRACTICES.includes(k) && LEVELS.includes(v)));
      if (Object.keys(exp).length) out.experience = exp;
    }
    if (scopes.has("health")) {
      const cond = (p.conditions || []).filter(c => CONDITIONS.includes(c)).sort();
      if (cond.length) out.conditions = cond;
      for (const k of ["in_therapy", "medication_change"]) if (typeof p[k] === "boolean") out[k] = p[k];
    }
    return Object.keys(out).length ? out : null;
  }
  function clinical(c, scopes, t0) {
    if (!c) return null;
    const out = pick(c, ["profession", "years_band", "setting"]);
    out.modalities = (c.modalities || []).map(String).sort();
    out.client_consent = !!c.client_consent;
    out.sessions = (c.sessions || []).map(s => {
      const x = { day: dayOf(s, t0) };
      for (const k of ["minutes", "nodes_used", "fidelity", "engagement", "cgi_s", "cgi_i"]) if (num(s[k]) !== null) x[k] = num(s[k]);
      x.therapist_led = !!s.therapist_led;
      if (scopes.has("texts") && s.notes) x.notes = String(s.notes);
      return x;
    });
    if (scopes.has("health") && c.diagnoses && c.diagnoses.length) out.diagnoses = c.diagnoses.map(d => String(d).trim().toUpperCase()).filter(Boolean).sort();
    return out;
  }
  function lab(l, scopes) {
    if (!l) return null;
    const out = pick(l, ["site_code", "ethics_ref", "protocol_ref"]);
    const dev = l.device || {}, d = pick(dev, ["name", "kind", "reference", "montage", "ground", "transport"]);
    for (const k of ["channels", "fs_hz", "impedance_kohm_max"]) if (num(dev[k]) !== null) d[k] = num(dev[k]);
    out.device = d;
    out.recordings = (l.recordings || []).map(r => {
      const x = pick(r, ["file_sha256", "bids_path", "program", "task"]);
      for (const k of ["day", "duration_s", "clock_offset_ms", "artifact_pct", "run_index"]) if (num(r[k]) !== null) x[k] = num(r[k]);
      return x;
    });
    if (scopes.has("texts") && l.notes) out.notes = String(l.notes);
    return out;
  }
  function build(inp) {
    const role = inp.role;
    if (!ROLES.includes(role)) throw new Error("role must be person, clinician or lab");
    const consent = inp.consent || {};
    if (consent.agreed !== true) throw new Error("a contribution needs the contributor's consent");
    const scopes = new Set((consent.scopes || []).filter(s => s in SCOPES).concat(REQUIRED));
    if (role === "clinician") { scopes.add("clinical"); if (!(inp.clinical || {}).client_consent) throw new Error("a clinician contribution needs the client's consent"); }
    if (role === "lab") { scopes.add("lab"); if (!String((inp.lab || {}).ethics_ref || "").trim()) throw new Error("a lab contribution needs its ethics approval reference"); }
    const ids = inp.ids || {}, raw = inp.runs || [];
    const stamps = raw.map(r => num(r.timestamp)).filter(x => x !== null);
    const t0 = stamps.length ? Math.min(...stamps) : num(inp.t0);
    const texts = scopes.has("texts");
    const rs = runs(raw, scopes, t0);
    const srbai = (inp.srbai || []).map(s => ({ week: num(s.week), srbai: num(s.srbai) })).sort((a, b) => (a.week || 0) - (b.week || 0));
    const app = Object.fromEntries(Object.entries(inp.app || {}).filter(([k]) => ["player", "planner", "ugcl", "platform", "vibration", "schema_runs"].includes(k)));
    const body = { schema: SCHEMA, contribution_id: ids.contribution_id, participant: ids.participant, role,
      consent: { version: CONSENT_VERSION, scopes: [...scopes].sort(), sharing: ["open", "research"].includes(consent.sharing) ? consent.sharing : "research", contact: !!consent.contact, agreed: true },
      app, runs: rs, weekly: srbai, metrics: raw.length ? M.compute(raw, inp.srbai || [], inp.settings || {}, num(inp.now)) : {} };
    if (scopes.has("plan")) { body.plan = plan(inp.plan, scopes); body.cues = cues(inp.cues, scopes, t0); }
    if (scopes.has("calibration")) body.calibration = calibration(inp.ugcl);
    if (scopes.has("recognition")) body.recognition = (inp.recognition || []).map(x => Object.assign(pick(x, ["code", "chosen", "modality"]),
      { correct: !!x.correct, rt_ms: num(x.rt_ms), options: (x.options || []).slice() }));
    if (scopes.has("outcomes")) body.outcomes = outcomes(inp.outcomes, t0);
    if (scopes.has("safety")) body.safety = { adverse: adverse(inp.adverse, t0, texts), stopped_runs: rs.filter(r => r.completed === 0).length, runs: rs.length };
    const prof = profile(inp.profile, scopes); if (prof) body.profile = prof;
    if (role === "clinician") body.clinical = clinical(inp.clinical, scopes, t0);
    if (role === "lab") body.lab = lab(inp.lab, scopes);
    const days = [...new Set(rs.map(r => r.day).filter(d => d !== null))].sort((a, b) => a - b);
    const rated = rs.filter(r => "sud_change" in r).length;
    body.quality = { runs: rs.length, days_active: days.length, span_days: days.length ? days[days.length - 1] - days[0] + 1 : 0,
      rated_share: rs.length ? Math.floor(rated / rs.length * 1000 + 0.5) / 1000 : 0,
      with_physiology: rs.filter(r => "hr_before" in r).length, weekly_checks: srbai.length };
    for (const k of Object.keys(body)) if (!has(body[k])) delete body[k];
    return body;
  }
  async function sha256Hex(text) {
    if (typeof crypto !== "undefined" && crypto.subtle) {
      const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    }
    return require("crypto").createHash("sha256").update(text, "utf8").digest("hex");
  }
  async function seal(body) { return Object.assign({}, body, { sha256: await sha256Hex(MS.canonical(body)) }); }
  async function check(c) {
    const errs = [];
    if (c.schema !== SCHEMA) errs.push("schema is " + JSON.stringify(c.schema) + ", expected " + SCHEMA);
    const body = Object.assign({}, c); delete body.sha256;
    if (await sha256Hex(MS.canonical(body)) !== c.sha256) errs.push("checksum does not match: the file was changed or damaged");
    if (!ROLES.includes(c.role)) errs.push("unknown role");
    if (!(c.consent || {}).agreed) errs.push("no consent");
    return errs;
  }
  function bidsEvents(tl) {
    const L = ["onset\tduration\ttrial_type\tphase\tvalue"];
    for (const e of tl.events) {
      let val = e.tier ? e.tier : e.channel === "haptic" ? "on=" + (e.on || 0) + " off=" + (e.off || 0) + " x=" + (has(e.count) ? e.count : 1) : e.channel === "marker" ? String(e.text || "") : "";
      val = val.replace(/\t/g, " ").replace(/\n/g, " ") || "n/a";
      L.push((e.t / 1000).toFixed(3) + "\t" + ((e.dur || 0) / 1000).toFixed(3) + "\t" + e.channel + "/" + e.kind + "\t" + (e.phase || "") + "\t" + val);
    }
    return L.join("\n") + "\n";
  }
  function randomId(prefix, n) {
    const b = new Uint8Array(n || 8);
    (typeof crypto !== "undefined" && crypto.getRandomValues ? crypto : require("crypto").webcrypto).getRandomValues(b);
    return prefix + Array.from(b).map(x => x.toString(16).padStart(2, "0")).join("");
  }
  const api = { SCHEMA, CONSENT_VERSION, ROLES, SCOPES, SCALES, AGE_BANDS, GENDERS, HANDS, REGIONS, PRACTICES, LEVELS, CONDITIONS, SEVERITY, RELATED,
    KNOWN_PROTOCOLS, num, fnv1a, build, seal, check, bidsEvents, randomId };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSContribution = api;
})(typeof self !== "undefined" ? self : this);
