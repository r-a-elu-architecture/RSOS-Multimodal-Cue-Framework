/* THERA — therapist mode and session protocols, JavaScript implementation (spec/THERA.md).
 * Mirrors rsso/rsso/thera.py (identical results, tested). The protocols are data (docs/data/thera.json); pass them in.
 * Browser: window.RSOSThera; Node: module.exports.
 */
(function (root) {
  "use strict";
  const FORMAT = "rsos-thera/1";
  const clone = o => JSON.parse(JSON.stringify(o));
  const r1 = x => Math.floor(x * 10 + 0.5) / 10;
  const nt = x => String(Number(x));
  const blank = v => v === null || v === undefined || v === "";
  function nodeIndex(plan, ref) {
    const nodes = (plan || {}).nodes || [];
    if (ref === "node:observer") { const i = nodes.findIndex(n => n.mode === "observer"); return i; }
    if (ref.startsWith("node:")) {
      const i = +ref.split(":")[1], assoc = nodes.map((n, k) => [n, k]).filter(([n]) => n.mode !== "observer").map(([, k]) => k);
      return i < assoc.length ? assoc[i] : (i < nodes.length ? i : -1);
    }
    return -1;
  }
  function fill(text, plan, node) {
    const it = (plan || {}).intake || {}, trig = (it.triggers && it.triggers.length ? it.triggers : null) || (plan || {}).triggers || [];
    const sched = ((plan || {}).schedule && plan.schedule.length ? plan.schedule : [{}])[0];
    const has = Object.keys(sched).length > 0;
    const vals = { node: node ? String(node.name || "node").toLowerCase() : "node",
      frame: ((node || {}).frames && node.frames.length ? node.frames : ["I breathe fully and completely"])[0],
      code: node && node.tacton !== undefined ? node.tacton : "..-",
      contexts: ((node || {}).contexts || []).join(", ") || "the situations ahead",
      trigger: trig.length ? trig[0].toLowerCase() : "the moment the old state begins",
      dose: has ? (sched.per_day === undefined ? 10 : sched.per_day) + " times a day for " + (sched.days === undefined ? 7 : sched.days) + " days" : "every day" };
    for (const [k, v] of Object.entries(vals)) text = text.split("{" + k + "}").join(v);
    return text;
  }
  function sessionPlan(protocols, id, plan) {
    const pr = protocols[id], steps = [], problems = [];
    for (const st of pr.steps) {
      const s = Object.assign({}, st); let node = null; const run = st.run || "";
      if (run.startsWith("node:")) {
        const i = nodeIndex(plan, run);
        if (i < 0) problems.push(st.title + ": the plan has no " + (run === "node:observer" ? "observer node" : "node") + "; add one in the node studio");
        else { node = plan.nodes[i]; s.program = "plan:" + i; s.node = node.name; }
      } else if (run.startsWith("program:")) s.program = run.split(":")[1];
      if (node === null && plan && (plan.nodes || []).length) { const j = nodeIndex(plan, "node:0"); node = j >= 0 ? plan.nodes[j] : null; }
      s.say = fill(st.say, plan || {}, node); s.do = fill(st.do, plan || {}, node);
      delete s.run; steps.push(s);
    }
    return { format: FORMAT, protocol: id, title: pr.title, aim: pr.aim, therapist_led: pr.therapist_led, stop_sud: pr.stop_sud, steps, problems, events: [] };
  }
  function record(session, stepId, values, at) { const s = clone(session); s.events.push(Object.assign({ step: stepId, at }, values)); return s; }
  const sudSeries = s => s.events.filter(e => !blank(e.sud)).map(e => [e.step, Number(e.sud)]);
  function check(session) {
    const out = [];
    if (session.events.some(e => e.screen === "yes")) out.push({ level: "stop", text: "The screening answer was yes: stop the session work, follow your crisis procedure, and do not start device practice." });
    const series = sudSeries(session);
    if (series.length && series[series.length - 1][1] >= session.stop_sud)
      out.push({ level: "return", text: "Distress is " + nt(series[series.length - 1][1]) + ", at or above this session's ceiling of " + session.stop_sud + ": stop the current step, return to paced breathing and grounding, and continue only when it is below " + (session.stop_sud - 2) + "." });
    if (session.events.some(e => e.adverse === "moderate" || e.adverse === "serious")) out.push({ level: "stop", text: "An adverse event was recorded: CONTAIN pauses the linked program until you restore it." });
    return out.length ? out : [{ level: "ok", text: "No stop rule applies." }];
  }
  function summary(session, runs, started, ended) {
    const ev = session.events, done = new Set(ev.filter(e => e.done).map(e => e.step));
    const required = session.steps.filter(s => s.required).map(s => s.id);
    const fidelity = required.length ? r1(10 * required.filter(r => done.has(r)).length / required.length) : 0;
    const suds = sudSeries(session).map(x => x[1]), ags = ev.filter(e => !blank(e.agency)).map(e => Number(e.agency));
    const t0 = started !== undefined && started !== null ? started : (ev.length ? ev[0].at : 0);
    const t1 = ended !== undefined && ended !== null ? ended : (ev.length ? ev[ev.length - 1].at : t0);
    const inSession = (runs || []).filter(r => t0 <= Number(r.timestamp || 0) && Number(r.timestamp || 0) <= t1 + 60);
    const last = {};
    for (const e of ev) for (const k of ["cgi_s", "cgi_i", "engagement", "adverse"]) if (!blank(e[k])) last[k] = e[k];
    const out = { protocol: session.protocol, minutes: ev.length ? Math.max(1, Math.floor((t1 - t0) / 60 + 0.5)) : 0, steps_done: done.size, steps: session.steps.length,
      fidelity, sud_start: suds.length ? suds[0] : null, sud_end: suds.length ? suds[suds.length - 1] : null, sud_peak: suds.length ? Math.max(...suds) : null,
      sud_change: suds.length >= 2 ? r1(suds[suds.length - 1] - suds[0]) : null, agency_change: ags.length >= 2 ? r1(ags[ags.length - 1] - ags[0]) : null,
      runs: inSession.length, nodes_used: new Set(inSession.map(r => r.protocol).filter(p => String(p || "").startsWith("node_"))).size,
      adverse: last.adverse || "none", stops: check(session).filter(c => c.level !== "ok").map(c => c.text) };
    out.record = { ts: Math.trunc(t0 * 1000), minutes: out.minutes, nodes_used: out.nodes_used, fidelity, engagement: last.engagement === undefined ? null : last.engagement,
      cgi_s: last.cgi_s === undefined ? null : last.cgi_s, cgi_i: last.cgi_i === undefined ? null : last.cgi_i, therapist_led: !!session.therapist_led };
    return out;
  }
  function homework(plan, session) {
    plan = plan || {};
    const nodes = plan.nodes || [], sched = (plan.schedule && plan.schedule.length ? plan.schedule : [{}])[0], trig = (plan.intake || {}).triggers || [], out = [];
    for (const n of nodes) {
      if (n.mode === "observer") out.push("Use the " + String(n.name === undefined ? "observer" : n.name).toLowerCase() + " node only as agreed in sessions" + ((session || {}).therapist_led ? " (therapist-led work stays in sessions)." : "."));
      else out.push("Practise the " + String(n.name === undefined ? "node" : n.name).toLowerCase() + " node " + (sched.per_day === undefined ? 10 : sched.per_day) + " times a day for " + (sched.days === undefined ? 7 : sched.days) + " days, spread over the day; its vibration code is " + (n.tacton === undefined ? "" : n.tacton) + ".");
    }
    if (trig.length) out.push("Start the node when this happens: " + trig[0].toLowerCase() + ". Rate distress before and after in the player.");
    out.push("Fill in the weekly automaticity check in the player once a week.");
    out.push("If anything feels wrong, press “Something felt wrong” in the player; practice pauses until you have talked it through.");
    return out;
  }
  const api = { FORMAT, sessionPlan, record, check, summary, homework };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSThera = api;
})(typeof self !== "undefined" ? self : this);
