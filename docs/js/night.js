/* SLEEP and REWARD (spec/NIGHT.md), JavaScript implementation. Mirrors rsso/rsso/night.py (identical results,
 * tested): the closed-loop sleep-cue controller with its simulated sleeper and night report, next-day recall for cued
 * against uncued items, the night diary, nightmare responses, reward codes for outside success events, code families
 * per learning area, recognising a good move from an accelerometer, and the notice test. Needs docs/js/peak.js and
 * docs/js/trial.js. Browser: window.RSOSNight; Node: module.exports.
 */
(function (root) {
  "use strict";
  const node = typeof module !== "undefined" && module.exports;
  const P = node ? require("./peak.js") : root.RSOSPeak;
  const T = node ? require("./trial.js") : root.RSOSTrial;
  const EPOCH = 30, STAGES = ["W", "N1", "N2", "N3", "REM"];
  const STAGE_NAMES = { W: "Awake", N1: "Light (N1)", N2: "Light (N2)", N3: "Deep (N3)", REM: "REM" };
  const POLICY = { stable_epochs: 3, pause_epochs: 10, start: 0.3, max: 0.6, step_down: 0.7, step_up: 0.02, up_every: 20, limit: 300, detect_arousal: 0.9 };
  const ACC = { W: 0.85, N1: 0.4, N2: 0.8, N3: 0.8, REM: 0.75 };
  const NEIGHBOUR = { W: ["N1", "N1"], N1: ["W", "N2"], N2: ["N1", "N3"], N3: ["N2", "N2"], REM: ["N1", "N2"] };
  const AROUSE = { W: 0, N1: 0.25, N2: 0.08, N3: 0.03, REM: 0.1 };
  const TRAUMA_MODES = ["safety", "wake"], REWARD = { budget_ms: 300, refractory_ms: 1500, per_minute: 20, device_ms: 40 };
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);
  const r2 = x => (x === null || x === undefined ? null : Math.floor(x * 100 + 0.5) / 100);
  const sum = xs => { let s = 0; for (const x of xs) s += x; return s; };
  const mean = xs => sum(xs) / xs.length;
  const vr = xs => { if (xs.length < 2) return 0; const m = mean(xs); let s = 0; for (const x of xs) s += (x - m) * (x - m); return s / (xs.length - 1); };
  const median = xs => { const s = xs.slice().sort((a, b) => a - b), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
  function ci(xs) { const m = mean(xs); if (xs.length < 2) return [m, null, null]; const h = T.tcrit(xs.length - 1) * Math.sqrt(vr(xs) / xs.length); return [m, m - h, m + h]; }
  function ciDiff(a, b) {
    const d = mean(a) - mean(b); if (a.length < 2 || b.length < 2) return [d, null, null];
    const va = vr(a) / a.length, vb = vr(b) / b.length, se = Math.sqrt(va + vb); if (se === 0) return [d, d, d];
    const den = va * va / (a.length - 1) + vb * vb / (b.length - 1);
    const df = den > 0 ? Math.max(1, Math.floor((va + vb) * (va + vb) / den)) : a.length + b.length - 2;
    const h = T.tcrit(df) * se; return [d, d - h, d + h];
  }
  const s_ = n => (n !== 1 ? "s" : "");

  // ------------------------------------------------------------ the night plan
  function makePlan(codes, channels, trauma, safetyCode, limit, maxIntensity) {
    trauma = trauma || "safety"; if (!TRAUMA_MODES.includes(trauma)) throw new Error("trauma must be one of " + TRAUMA_MODES.join(", "));
    channels = channels || ["vibration"]; safetyCode = safetyCode === undefined ? ". ." : safetyCode;
    limit = limit === undefined ? POLICY.limit : limit; maxIntensity = maxIntensity === undefined ? POLICY.max : maxIntensity;
    const play = codes.filter(c => !c.trauma), held = codes.filter(c => c.trauma);
    return { schema: "rsos-night/1", codes: play, held, channels: channels.slice(), trauma, safety_code: safetyCode, limit: Math.trunc(limit),
      max_intensity: Math.min(maxIntensity, 0.9),
      say: play.length + " code" + s_(play.length) + " to replay in deep sleep" + (held.length ? "; " + held.length + " trauma-related code" + s_(held.length) + " held back, never played during sleep" : "") +
        "; a nightmare gets " + (trauma === "safety" ? "the safety code" : "a gentle waking") + "." };
  }
  function Controller(plan, kind) { this.plan = plan; this.kind = kind || "closed"; this.stable = 0; this.pause = 0; this.n = 0; this.intensity = POLICY.start; this.quiet = 0; this.k = 0; }
  Controller.prototype.step = function (i, est, aroused, rng) {
    if (this.kind === "none" || !this.plan.codes.length) return null;
    if (this.kind === "random") { if (rng.u() < 0.25 && this.n < this.plan.limit) return this.cue(i, this.plan.max_intensity); return null; }
    if (aroused || est === "W") { if (aroused) this.intensity = Math.max(0.1, this.intensity * POLICY.step_down); this.pause = i + POLICY.pause_epochs; this.stable = 0; return null; }
    this.stable = est === "N3" ? this.stable + 1 : 0;
    if (i < this.pause || this.stable < POLICY.stable_epochs || this.n >= this.plan.limit) return null;
    this.quiet++;
    if (this.quiet >= POLICY.up_every) { this.quiet = 0; this.intensity = Math.min(this.plan.max_intensity, this.intensity + POLICY.step_up); }
    return this.cue(i, this.intensity);
  };
  Controller.prototype.cue = function (i, x) { const c = this.plan.codes[this.k % this.plan.codes.length]; this.k++; this.n++; return { epoch: i, code: c.code, intensity: r2(x) }; };

  // ------------------------------------------------------------ a simulated sleeper
  function Sleeper(seed, hours, arousability, acc, nightmares) {
    this.rng = new P.Rng(seed === undefined ? 1 : seed); hours = hours || 8; this.arousability = arousability === undefined ? 1 : arousability; this.acc = acc || ACC;
    const n = Math.trunc(hours * 3600 / EPOCH), rng = this.rng, h = [];
    const add = (stage, minutes) => { const k = Math.max(0, Math.floor(minutes * 2 + 0.5)); for (let j = 0; j < k; j++) h.push(stage); };
    add("W", 6 + rng.u() * 10); add("N1", 3 + rng.u() * 4);
    const n3 = [35, 25, 12, 5, 0, 0, 0], rem = [8, 15, 22, 28, 32, 35, 35]; let c = 0;
    while (h.length < n) {
      add("N2", 10 + rng.u() * 15); add("N3", n3[Math.min(c, 6)] * (0.7 + 0.6 * rng.u())); add("N2", 5 + rng.u() * 5);
      add("REM", rem[Math.min(c, 6)] * (0.7 + 0.6 * rng.u())); if (rng.u() < 0.5) add("W", 0.5 + rng.u()); c++;
    }
    this.plan = h.slice(0, n); this.nightmare_epochs = new Set();
    if (nightmares > 0) {
      const rems = []; this.plan.forEach((s, i) => { if (s === "REM") rems.push(i); });
      const k = Math.floor(nightmares + rng.u());
      for (let q = 0; q < k; q++) if (rems.length) { const start = rems[Math.floor(rng.u() * rems.length)];
        for (let j = start; j < Math.min(start + 6, this.plan.length); j++) if (this.plan[j] === "REM") this.nightmare_epochs.add(j); }
    }
  }
  Sleeper.prototype.estimate = function (stage) { if (this.rng.u() < this.acc[stage]) return stage; const [a, b] = NEIGHBOUR[stage]; return this.rng.u() < 0.5 ? a : b; };
  Sleeper.prototype.run = function (controller) {
    const tru = this.plan.slice(), est = [], cues = [], arousals = []; let wakeUntil = -1, flag = false;
    for (let i = 0; i < tru.length; i++) {
      if (i <= wakeUntil) tru[i] = i < wakeUntil ? "W" : "N1";
      const e = this.estimate(tru[i]); est.push(e);
      const seen = flag && this.rng.u() < POLICY.detect_arousal; flag = false;
      const cue = controller ? controller.step(i, e, seen, this.rng) : null;
      if (cue) {
        cue.stage = tru[i];
        const p = tru[i] !== "W" ? Math.min(0.9, AROUSE[tru[i]] * (0.2 + 1.6 * cue.intensity * cue.intensity) * this.arousability) : 0;
        if (this.rng.u() < p) { cue.aroused = true; arousals.push(i); flag = true; wakeUntil = i + 1 + Math.floor(this.rng.u() * 2); } else cue.aroused = false;
        cues.push(cue);
      }
    }
    return { true: tru, est, cues, arousals, report: nightReport(tru, cues, arousals) };
  };
  function nightReport(tru, cues, arousals) {
    let onset = tru.findIndex(s => s !== "W"); if (onset < 0) onset = tru.length;
    const rest = tru.slice(onset), sleep = rest.filter(s => s !== "W"), waso = rest.filter(s => s === "W").length;
    const by = {}; STAGES.forEach(s => { by[s] = cues.filter(c => c.stage === s).length; });
    const good = cues.filter(c => (c.stage === "N3" || c.stage === "N2") && !c.aroused).length;
    return { epochs: tru.length, sleep_min: r1(sleep.length * EPOCH / 60), n3_min: r1(tru.filter(s => s === "N3").length * EPOCH / 60),
      rem_min: r1(tru.filter(s => s === "REM").length * EPOCH / 60), waso_min: r1(waso * EPOCH / 60), efficiency: tru.length ? r1(sleep.length / tru.length * 100) : null,
      cues: cues.length, by_stage: by, in_n3: cues.length ? r1(by.N3 / cues.length * 100) : null, arousals: arousals.length, good };
  }

  // ------------------------------------------------------------ next-day recall, diary, nightmares
  function tmrAnalyze(nights) {
    const d = []; nights.forEach(n => { if (n.cued_before && n.uncued_before) d.push(n.cued_after / n.cued_before * 100 - n.uncued_after / n.uncued_before * 100); });
    if (d.length < 3) return { nights: d.length, advantage: null, lo: null, hi: null, verdict: "too_few",
      say: "Three or more cued nights are needed: learn in the evening, test, sleep with half the items cued, test again in the morning." };
    const [m, lo, hi] = ci(d), verdict = lo > 0 ? "helps" : hi < 0 ? "hurts" : "unclear";
    const say = { helps: "Cued items were kept better", hurts: "Cued items were kept worse", unclear: "No clear difference yet between cued and uncued items" }[verdict];
    return { nights: d.length, advantage: r1(m), lo: r1(lo), hi: r1(hi), verdict, say: say + ": " + r1(m) + " points of retention [" + r1(lo) + ", " + r1(hi) + "] over " + d.length + " nights." };
  }
  function diaryCompare(entries, metric) {
    metric = metric || "nightmares";
    const ok = e => e[metric] !== null && e[metric] !== undefined;
    const on = entries.filter(e => e.cueing && ok(e)).map(e => e[metric]), off = entries.filter(e => !e.cueing && ok(e)).map(e => e[metric]);
    if (on.length < 3 || off.length < 3) return { on: on.length, off: off.length, difference: null, lo: null, hi: null, verdict: "too_few", say: "Three or more nights with and without cueing are needed." };
    const [d, lo, hi] = ciDiff(on, off), verdict = hi < 0 ? "lower" : lo > 0 ? "higher" : "unclear";
    const name = ({ nightmares: "nightmares", distress: "distress" })[metric] || metric;
    const say = { lower: "Fewer " + name + " on cueing nights", higher: "More " + name + " on cueing nights", unclear: "No clear difference in " + name + " yet" }[verdict];
    return { on: on.length, off: off.length, difference: r2(d), lo: r2(lo), hi: r2(hi), verdict, say: say + ": " + r2(d) + " [" + r2(lo) + ", " + r2(hi) + "]." };
  }
  function nightmareResponse(plan, sleeper, sensitivity) {
    sensitivity = sensitivity === undefined ? 0.8 : sensitivity;
    const set = sleeper.nightmare_epochs, eps = [...set].sort((a, b) => a - b);
    let minutes = 0, wakings = 0, codes = 0, activeEnd = -1;
    for (const i of eps) {
      if (i <= activeEnd) continue; let j = i;
      while (set.has(j)) {
        if (sleeper.rng.u() < sensitivity) { if (plan.trauma === "wake") { wakings++; break; } codes++; if (sleeper.rng.u() < 0.6) break; }
        minutes++; j++;
      }
      while (set.has(j)) j++;
      activeEnd = j;
    }
    return { nightmares: eps.filter(i => !set.has(i - 1)).length, minutes: r1(minutes * EPOCH / 60), wakings, safety_codes: codes };
  }

  // ------------------------------------------------------------ REWARD
  const SUFFIXES = [".", "-", "..", ".-", "-.", "--", "...", "..-", ".-.", ".--", "-..", "-.-", "--.", "---"];
  function family(prefix, n) {
    if (!prefix || [...prefix].some(ch => ch !== "." && ch !== "-")) throw new Error("the prefix is dots and dashes");
    if (n > SUFFIXES.length) throw new Error("at most " + SUFFIXES.length + " codes in a family");
    return SUFFIXES.slice(0, n).map(s => prefix + " " + s);
  }
  function familiesOk(areas) {
    const out = [], names = Object.keys(areas).sort();
    for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
      const a = names[i], b = names[j], x = areas[a], y = areas[b];
      if (x === y) out.push(a + " and " + b + " share a prefix"); else if (x.startsWith(y) || y.startsWith(x)) out.push(a + " and " + b + ": one prefix starts the other");
    }
    return out;
  }
  const rewardState = (area, code) => ({ area, code, log: [] });
  function onEvent(state, ev) {
    const log = state.log, src = ev.source || "manual";
    if (!ev.success) { const d = { t_ms: ev.t_ms, source: src, play: false, why: "not a success", latency_ms: null }; log.push(d); return d; }
    const played = log.filter(e => e.play); let why = null;
    if (played.length && ev.t_ms - played[played.length - 1].t_ms < REWARD.refractory_ms) why = "too soon after the last reward";
    else if (played.filter(e => ev.t_ms - e.t_ms < 60000).length >= REWARD.per_minute) why = "the per-minute limit";
    const lat = (ev.detect_ms || 0) + REWARD.device_ms;
    const d = { t_ms: ev.t_ms, source: src, play: why === null, why, latency_ms: why === null ? lat : null, code: why === null ? state.code : null };
    log.push(d); return d;
  }
  function rewardReport(state) {
    const log = state.log, succ = log.filter(e => e.why !== "not a success"), played = log.filter(e => e.play), lat = played.map(e => e.latency_ms);
    const within = lat.filter(x => x <= REWARD.budget_ms).length;
    return { successes: succ.length, rewarded: played.length, blocked: succ.length - played.length, median_ms: lat.length ? r1(median(lat)) : null,
      within: lat.length ? r1(within / lat.length * 100) : null,
      say: !succ.length ? "No successes yet." : played.length + " of " + succ.length + " successes rewarded; median " + (lat.length ? r1(median(lat)) : "—") +
        " ms from the success to the code, " + (lat.length ? r1(within / lat.length * 100) : 0) + "% within " + REWARD.budget_ms + " ms." };
  }

  // ------------------------------------------------------------ recognising a good move
  const TEMPLATE_N = 32;
  function moveShape(t, good) {
    const g = z => Math.exp(-z * z);
    if (good === undefined || good) return 0.6 * g((t - 150) / 48) + 2.2 * g((t - 300) / 30) + 0.8 * g((t - 420) / 42);
    return 0.15 * g((t - 150) / 48) + 1.8 * g((t - 300) / 50) + 1.2 * g((t - 390) / 30);
  }
  function template(n) { n = n || TEMPLATE_N; const out = []; for (let k = 0; k < n; k++) out.push(moveShape(-150 + 600 * k / (n - 1))); return out; }
  function resample(xs, n) {
    if (xs.length === n) return xs.slice(); const out = [];
    for (let k = 0; k < n; k++) { const p = k * (xs.length - 1) / (n - 1), i = Math.floor(p), f = p - i; out.push(i + 1 >= xs.length ? xs[i] : xs[i] * (1 - f) + xs[i + 1] * f); }
    return out;
  }
  function corr(a, b) {
    const ma = mean(a), mb = mean(b); let sab = 0, saa = 0, sbb = 0;
    for (let i = 0; i < a.length; i++) sab += (a[i] - ma) * (b[i] - mb);
    for (const x of a) saa += (x - ma) * (x - ma); for (const y of b) sbb += (y - mb) * (y - mb);
    return saa > 0 && sbb > 0 ? sab / Math.sqrt(saa * sbb) : 0;
  }
  function detectMoves(samples, tmpl, hz, peakG, match) {
    tmpl = tmpl || template(); hz = hz || 100; peakG = peakG === undefined ? 1.5 : peakG; match = match === undefined ? 0.85 : match;
    const pre = Math.trunc(0.45 * hz), post = Math.trunc(0.15 * hz), back = Math.trunc(0.3 * hz), out = [], n = samples.length; let i = pre;
    while (i < n - post) {
      let mx = -Infinity; for (let j = i - back; j < Math.min(n, i + post + 1); j++) if (samples[j] > mx) mx = samples[j];
      if (samples[i] >= peakG && samples[i] === mx) {
        const w = resample(samples.slice(i - pre, i + post), TEMPLATE_N), r = corr(w, tmpl);
        out.push({ t_ms: r1(i * 1000 / hz), peak: r2(samples[i]), r: r2(r), success: r >= match, detect_ms: r1(post * 1000 / hz) });
        i += post + back;
      } else i++;
    }
    return out;
  }
  function simMove(rng, good, hz, noise) {
    good = good === undefined ? true : good; hz = hz || 100; noise = noise === undefined ? 0.15 : noise;
    const scale = 0.85 + 0.3 * rng.u(), n = Math.trunc(0.6 * hz), sig = [];
    for (let k = 0; k < hz; k++) sig.push(Math.abs(rng.gauss() * noise * 0.3));
    for (let k = 0; k < n; k++) sig.push(moveShape(k * 1000 / hz, good) * scale + rng.gauss() * noise);
    for (let k = 0; k < hz; k++) sig.push(Math.abs(rng.gauss() * noise * 0.3));
    return sig.map(x => Math.max(0, x));
  }

  // ------------------------------------------------------------ the notice test
  function noticeReport(trials) {
    const out = {}, lats = {};
    ["vibration", "both"].forEach(ch => {
      const xs = trials.filter(t => t.channel === ch), lat = xs.filter(t => t.noticed && t.latency_ms !== null && t.latency_ms !== undefined).map(t => t.latency_ms);
      out[ch] = { n: xs.length, noticed: xs.length ? r1(xs.filter(t => t.noticed).length / xs.length * 100) : null, median_ms: lat.length ? r1(median(lat)) : null }; lats[ch] = lat;
    });
    const a = lats.both, b = lats.vibration;
    if (a.length >= 3 && b.length >= 3) {
      const [d, lo, hi] = ciDiff(a, b); out.faster = { difference_ms: r1(d), lo: r1(lo), hi: r1(hi) };
      out.say = (hi < 0 ? "With light, cues were noticed sooner" : lo > 0 ? "With light, cues were noticed later" : "No clear difference in how fast cues were noticed") + ": " + r1(d) + " ms [" + r1(lo) + ", " + r1(hi) + "].";
    } else { out.faster = null; out.say = "Run at least three trials of each kind."; }
    return out;
  }

  const api = { EPOCH, STAGES, STAGE_NAMES, POLICY, ACC, AROUSE, TRAUMA_MODES, REWARD, SUFFIXES, makePlan, Controller, Sleeper, nightReport, tmrAnalyze,
    diaryCompare, nightmareResponse, family, familiesOk, rewardState, onEvent, rewardReport, moveShape, template, detectMoves, simMove, noticeReport };
  if (node) module.exports = api; else root.RSOSNight = api;
})(typeof self !== "undefined" ? self : this);
