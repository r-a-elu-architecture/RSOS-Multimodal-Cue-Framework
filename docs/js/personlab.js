/* PERSONLAB §7d C: the Person Lab session engine in the browser.
 * A line-for-line port of rsxv/rsxv/personlab/person.py (ProfilePerson, unchanged model) and lab.py (mulberry32,
 * policies, targets), checked identical to Python by rsso/tests/test_personlab_parity.py. Architecture, not evidence. */
(function (root) {
  "use strict";
  const LEVEL_IDS = ["environment", "behaviour", "skills", "beliefs", "identity", "mission"];
  const ARCH = { STABILISE: "BEAR", EXPLORE: "RAVEN", SUGGEST: "TIGER", SHARE: "LION", NONE: null };
  const POLICIES = ["agents", "always_bear", "no_support"];

  function mulberry32(seed) {
    let a = seed >>> 0;
    const random = () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1) >>> 0;
      t = (t ^ ((t + (Math.imul(t ^ (t >>> 7), t | 61) >>> 0)) >>> 0)) >>> 0;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const gauss = (mu, sigma) => {
      const u1 = 1.0 - random(), u2 = random();
      return mu + sigma * Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    };
    return { random, gauss };
  }

  const clip = (x, lo, hi) => (x < lo ? lo : x > hi ? hi : x);
  function roundHalfEven(x) {   // Python's round()
    const f = Math.floor(x), d = x - f;
    if (d > 0.5) return f + 1;
    if (d < 0.5) return f;
    return f % 2 === 0 ? f : f + 1;
  }

  function targets(p) {   // person.targets
    const des = p.desired || {};
    const agreed = LEVEL_IDS.filter(lv => (des[lv] || []).some(it => it.agreed));
    if (agreed.length) return [agreed, "desired_agreed"];
    const anyd = LEVEL_IDS.filter(lv => (des[lv] || []).length);
    if (anyd.length) return [anyd, "desired_any"];
    const cur = LEVEL_IDS.filter(lv => ((p.current || {})[lv] || []).length);
    if (cur.length) return [cur, "current"];
    return [["behaviour"], "default"];
  }

  function targetNodes(p) {   // lab.target_nodes
    const out = [], has = (lv, n) => out.some(x => x[0] === lv && x[1] === n);
    for (const lv of targets(p)[0]) {
      for (const part of ["desired", "current"])
        for (const it of ((p[part] || {})[lv] || []))
          if (it.node && !has(lv, it.node)) out.push([lv, it.node]);
      if (!out.some(x => x[0] === lv)) {
        const sts = (((p.levels || {})[lv] || {}).statements) || [];
        out.push([lv, sts.length ? sts[0].id : "all"]);
      }
    }
    return out;
  }

  function Person(profile, params, rng) {   // person.ProfilePerson with the rng substituted
    const P = params;
    const nSig = Math.min(4, (profile.signals || []).length);
    const s = {
      P, rng, rho: P.rho * (1 + 0.25 * nSig),
      skill: ((((profile.levels || {}).skills || {}).statements) || []).length ? 1.25 : 1.0,
      I: clip(Number(profile.initial_intensity), 1.0, 5.0), k: 0.0, g: 0.0, t: 0, cues: 0
    };
    s.u = (s.I - 1) / 4;
    s.step = action => {
      const a = P.act[action], I0 = s.I, g0 = s.g;
      const cue = s.rng.random() < s.rho;
      if (cue) { s.cues += 1; s.I = clip(s.I + P.delta, 1, 5); s.u = clip(s.u + P.delta / 4, 0, 1); }
      const Iac = s.I;
      s.I = clip(s.I - a.r, 1, 5);
      s.u = clip(s.u - a.m, 0, 1);
      s.k = clip(s.k + a.e, 0, 1);
      if (s.u < P.tau) s.g = clip(s.g + a.p * (0.5 + s.k) * s.skill, 0, 1);
      else s.u = clip(s.u + a.c, 0, 1);
      s.I = clip(s.I - P.lam * (s.I - 1), 1, 5);
      const relief = Iac - s.I, progress = s.g - g0;
      const fb = roundHalfEven(clip(3 + P.f1 * relief + P.f2 * progress + s.rng.gauss(0, P.noise), 1, 5));
      const spike = (s.I - I0) > 1;
      const out = { t: s.t, action, cue, I: s.I, u: s.u, k: s.k, g: s.g, relief, progress, feedback: fb,
                    score: relief + progress - (spike ? 1.0 : 0.0) };
      s.t += 1;
      return out;
    };
    return s;
  }

  function session(lab, p, number, policy, effects, ticks) {
    ticks = ticks || lab.ticks;
    const params = Object.assign({}, lab.defaults, { act: lab.effects[effects] });
    const person = Person(p, params, mulberry32(lab.seed0 + number));
    const tg = targetNodes(p);
    let ti = 0, calm = 0;
    const rows = [];
    for (let i = 0; i < ticks; i++) {
      let action;
      if (policy === "no_support") action = "NONE";
      else if (policy === "always_bear") action = "STABILISE";
      else if (person.u >= params.tau) action = "STABILISE";
      else { calm += 1; action = calm % 6 === 0 ? "SHARE" : (person.k < 0.5 ? "EXPLORE" : "SUGGEST"); }
      const [lv, node] = policy === "agents" ? tg[ti % tg.length] : tg[0];
      const Ib = person.I;
      const o = person.step(action);
      rows.push({ t: o.t, action, archetype: ARCH[action], target: action === "NONE" ? null : lv + ":" + node, cue: o.cue,
                  I: o.I, u: o.u, k: o.k, g: o.g, feedback: o.feedback, score: o.score, spike: (o.I - Ib) > 1 });
      if (policy === "agents" && action === "SUGGEST") ti += 1;
    }
    const last = rows[rows.length - 1];
    return { id: p.id, policy, effects, ticks: rows, final_I: last.I, final_g: last.g,
             spikes: rows.filter(r => r.spike).length, mean_score: rows.reduce((s, r) => s + r.score, 0) / rows.length };
  }

  function program(lab, action, target) { return action === "NONE" ? "" : lab.programs[action].replace("{target}", target); }

  function population(lab, persons) {
    const out = {};
    for (const eff of Object.keys(lab.effects)) {
      const runs = {};
      for (const pol of POLICIES) runs[pol] = persons.map((p, n) => session(lab, p, n + 1, pol, eff));
      const summ = {};
      for (const pol of POLICIES) {
        const rs = runs[pol], n = rs.length, m = f => rs.reduce((s, r) => s + f(r), 0) / n;
        summ[pol] = { mean_final_I: m(r => r.final_I), mean_final_g: m(r => r.final_g), mean_spikes: m(r => r.spikes), mean_score: m(r => r.mean_score) };
      }
      const a = runs.agents, b = runs.always_bear;
      summ.agents_vs_bear = {
        more_progress: a.filter((x, i) => x.final_g > b[i].final_g + 1e-9).length,
        same: a.filter((x, i) => Math.abs(x.final_g - b[i].final_g) <= 1e-9).length,
        less_progress: a.filter((x, i) => x.final_g < b[i].final_g - 1e-9).length
      };
      out[eff] = summ;
    }
    return out;
  }

  const API = { mulberry32, targets, targetNodes, session, program, population, POLICIES, ARCH, LEVEL_IDS };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  else root.PersonLab = API;
})(typeof window !== "undefined" ? window : this);
