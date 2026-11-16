/* The output gate (spec/FIXES_R3.md §1). Every channel that reaches the person goes through here: sound starts,
 * unmuted media, speech, vibration and the wristband's START command. An output goes through only inside an allowed
 * session, and the Watchdog is asked again at every output against the current saved state, so a change of session
 * state or domain stops output on every page. Stop calls always work. A page declares its default action on <body>
 * (data-outlet-kind, data-outlet-protocol, data-outlet-trigger); pages with richer context open sessions themselves.
 * Fails closed: without the safety scripts nothing plays. Browser: window.RSOSOutlet.
 */
(function (root) {
  "use strict";
  if (typeof window === "undefined") return;
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  let session = null;
  const refused = new Set();
  const ready = () => !!(root.RSOSWatchdog && root.RSOSGuard && root.RSOSSafety && root.RSOSContain);

  function ctxFor(extra) {
    const x = extra || {}, D = root.RSOSDomain || {};
    return { contain: get("rsos.contain", null), safety: get("rsos.safety", null), timeline: null, now: Date.now() / 1000,
      max_level: x.max_level || D.max_level || null, clinician_present: !!x.clinician_present, screening_recorded: !!x.screening_recorded,
      consents: get("rsos.consents", []), plan_protocols: x.plan_protocols === undefined ? null : x.plan_protocols,
      memory_work_allowed: x.memory_work_allowed !== undefined ? x.memory_work_allowed : (D.memory_work_allowed === undefined ? null : D.memory_work_allowed) };
  }
  // Open a session: asks the Watchdog through the guard (logged). Hold: none. Ask: only when the person confirmed.
  function open(action, extra, opts) {
    const o = opts || {};
    if (!ready()) return { decision: "hold", reasons: [{ rule: "outlet", virtue: "jin", text: "The safety scripts are not loaded on this page.", resolve: "none" }], opened: false };
    const r = root.RSOSGuard.ask(action, extra || {});
    const ok = r.decision === "allow" || (r.decision === "ask" && !!o.confirmed);
    session = ok ? { action, extra: extra || {}, until: Date.now() + (o.seconds || 900) * 1000 } : null;
    refused.clear();
    return Object.assign({}, r, { opened: ok });
  }
  // Adopt a decision the page has just made through the guard (no second log entry). Output is still re-checked.
  function adopt(action, extra, opts) { session = { action, extra: extra || {}, until: Date.now() + ((opts || {}).seconds || 900) * 1000 }; refused.clear(); }
  function close() { session = null; }
  function declared() {
    const b = document.body; if (!b || !b.dataset.outletKind) return null;
    return { kind: b.dataset.outletKind, protocol: b.dataset.outletProtocol || b.dataset.outletKind, trigger: b.dataset.outletTrigger || "self", source: "person" };
  }
  // A page's own session, opened on demand (self-triggered declarations count as confirmed).
  function ensure() {
    if (session && session.until > Date.now() && check()) return true;
    const a = declared(); if (!a) return false;
    return open(a, {}, { confirmed: a.trigger === "self" }).opened;
  }
  function check() {
    if (!session || session.until <= Date.now() || !ready()) { session = null; return false; }
    const r = root.RSOSWatchdog.watch(session.action, ctxFor(session.extra));
    if (r.decision === "hold") { session = null; return false; }
    return true;
  }
  function permit(channel) {
    if ((session && check()) || ensure()) return true;
    if (!refused.has(channel) && ready()) {
      refused.add(channel);
      try {
        const log = get("rsos.watchdog.log", []);
        root.RSOSWatchdog.record(log, { kind: "outlet", protocol: channel, trigger: null, source: null },
          { decision: "hold", level: "self_guided", reasons: [{ rule: "outlet", virtue: "jin", text: "no allowed session", resolve: "none" }] }, Date.now());
        localStorage.setItem("rsos.watchdog.log", JSON.stringify(root.RSOSWatchdog.trim(log)));
      } catch (e) {}
    }
    return false;
  }

  /* ---- wrap the channels ---- */
  const stopPattern = p => p === 0 || (Array.isArray(p) && (p.length === 0 || p.every(x => !x)));
  if (root.Navigator && Navigator.prototype.vibrate) {
    const v = Navigator.prototype.vibrate;
    Navigator.prototype.vibrate = function (p) { return stopPattern(p) || permit("vibration") ? v.call(this, p) : false; };
  }
  if (root.SpeechSynthesis && SpeechSynthesis.prototype.speak) {
    const sp = SpeechSynthesis.prototype.speak;
    SpeechSynthesis.prototype.speak = function (u) { if (permit("speech")) return sp.call(this, u); };
  }
  if (root.HTMLMediaElement) {
    const pl = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () { return this.muted || permit("audio") ? pl.call(this) : Promise.resolve(); };
  }
  if (root.AudioScheduledSourceNode) {
    const st = AudioScheduledSourceNode.prototype.start;
    AudioScheduledSourceNode.prototype.start = function () { if (permit("sound")) return st.apply(this, arguments); };
    // A refused sound was never started; the page's later stop() must not throw (stop always works).
    const sp2 = AudioScheduledSourceNode.prototype.stop;
    AudioScheduledSourceNode.prototype.stop = function () { try { return sp2.apply(this, arguments); } catch (e) { if (!e || e.name !== "InvalidStateError") throw e; } };
  }
  root.RSOSOutlet = { open, adopt, close, ensure, permit, active: () => !!(session && check()), session: () => session };
})(typeof window !== "undefined" ? window : globalThis);
