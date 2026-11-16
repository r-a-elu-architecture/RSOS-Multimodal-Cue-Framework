/* The output gate (spec/FIXES_R3.md §1, spec/FIXES_R4.md §1). Every channel that reaches the person goes through
 * here: sound to the speakers, unmuted media, speech, vibration and the wristband's START. Output goes through only
 * inside an allowed session. An explicit session (a run, an offer, a code, a therapist session) that turns to hold or
 * expires stays held: no fallback. The page's declared session (data-outlet-kind / -protocol / -trigger on <body>) is
 * used only when there is no explicit session. While a session is live the gate re-checks every second and on any
 * storage change in any tab; when the decision turns to hold it stops everything that is playing and dispatches
 * "rsos-outlet-hold". Stop calls always work. Fails closed without the safety scripts. Browser: window.RSOSOutlet.
 */
(function (root) {
  "use strict";
  if (typeof window === "undefined") return;
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  let session = null;                    // {action, extra, until, declared, held}
  const refused = new Set(), live = new Set(), media = new Set(), gates = new Map();
  const ready = () => !!(root.RSOSWatchdog && root.RSOSGuard && root.RSOSSafety && root.RSOSContain);
  const orig = {};

  function ctxFor(extra) {
    const x = extra || {}, D = root.RSOSDomain || {};
    return { contain: get("rsos.contain", null), safety: get("rsos.safety", null), timeline: null, now: Date.now() / 1000,
      max_level: x.max_level || D.max_level || null, clinician_present: !!x.clinician_present, screening_recorded: !!x.screening_recorded,
      consents: get("rsos.consents", []), plan_protocols: x.plan_protocols === undefined ? null : x.plan_protocols,
      memory_work_allowed: x.memory_work_allowed !== undefined ? x.memory_work_allowed : (D.memory_work_allowed === undefined ? null : D.memory_work_allowed) };
  }
  function open(action, extra, opts) {
    const o = opts || {};
    if (!ready()) return { decision: "hold", reasons: [{ rule: "outlet", virtue: "jin", text: "The safety scripts are not loaded on this page.", resolve: "none" }], opened: false };
    const r = root.RSOSGuard.ask(action, extra || {});
    const ok = r.decision === "allow" || (r.decision === "ask" && !!o.confirmed);
    session = ok ? { action, extra: extra || {}, until: Date.now() + (o.seconds || 900) * 1000, declared: !!o.declared, held: false } : null;
    refused.clear(); setAudio(ok);
    return Object.assign({}, r, { opened: ok });
  }
  function adopt(action, extra, opts) {
    session = { action, extra: extra || {}, until: Date.now() + ((opts || {}).seconds || 900) * 1000, declared: false, held: false };
    refused.clear(); setAudio(true);
  }
  function close() { session = null; setAudio(false); }
  function declared() {
    const b = document.body; if (!b || !b.dataset.outletKind) return null;
    return { kind: b.dataset.outletKind, protocol: b.dataset.outletProtocol || b.dataset.outletKind, trigger: b.dataset.outletTrigger || "self", source: "person" };
  }
  // Is the current session allowed now? An explicit session that fails stays held (FIXES_R4 G1).
  function check() {
    if (!session || session.held) return false;
    if (!ready() || session.until <= Date.now()) return hold();
    const r = root.RSOSWatchdog.watch(session.action, ctxFor(session.extra));
    return r.decision === "hold" ? hold() : true;
  }
  function hold() {
    if (session && !session.declared) session.held = true; else session = null;
    stopAll();
    try { root.dispatchEvent(new CustomEvent("rsos-outlet-hold")); } catch (e) {}
    return false;
  }
  function permit(channel) {
    if (session) return check() ? true : refuse(channel);  // explicit or declared: no fallback while one exists
    const a = declared();                                  // only when there is no session at all
    if (a && open(a, {}, { confirmed: a.trigger === "self", declared: true }).opened && check()) return true;
    return refuse(channel);
  }
  function refuse(channel) {
    setAudio(false);
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
  // Stop everything that is playing (FIXES_R4 G3). Stop always works.
  function stopAll() {
    try { if (orig.vibrate) orig.vibrate.call(navigator, 0); } catch (e) {}
    try { if (root.speechSynthesis) speechSynthesis.cancel(); } catch (e) {}
    for (const n of Array.from(live)) { try { orig.stop.call(n); } catch (e) {} live.delete(n); }
    for (const m of Array.from(media)) { try { m.pause(); } catch (e) {} media.delete(m); }
    setAudio(false);
  }
  function setAudio(on) { for (const g of gates.values()) { try { g.gain.value = on ? 1 : 0; } catch (e) {} } }
  // A live session is re-checked every second and on storage changes in any tab (FIXES_R4 G2, G3).
  setInterval(() => { if (session && !session.held) check(); }, 1000);
  root.addEventListener("storage", () => { if (session && !session.held) check(); });

  /* ---- wrap the channels ---- */
  const stopPattern = p => p === 0 || (Array.isArray(p) && (p.length === 0 || p.every(x => !x)));
  if (root.Navigator && Navigator.prototype.vibrate) {
    orig.vibrate = Navigator.prototype.vibrate;
    Navigator.prototype.vibrate = function (p) { return stopPattern(p) || permit("vibration") ? orig.vibrate.call(this, p) : false; };
  }
  if (root.SpeechSynthesis && SpeechSynthesis.prototype.speak) {
    const sp = SpeechSynthesis.prototype.speak;
    SpeechSynthesis.prototype.speak = function (u) { if (permit("speech")) return sp.call(this, u); };
  }
  if (root.HTMLMediaElement) {
    const pl = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () { if (this.muted || permit("audio")) { if (!this.muted) media.add(this); return pl.call(this); } return Promise.resolve(); };
    // Autoplay and unmuting after play() are caught too (FIXES_R4 G4).
    const watchMedia = e => { const m = e.target; if (!(m instanceof HTMLMediaElement) || m.muted || m.paused) return; if (permit("audio")) media.add(m); else { try { m.pause(); } catch (x) {} } };
    document.addEventListener("play", watchMedia, true);
    document.addEventListener("volumechange", watchMedia, true);
    document.addEventListener("ended", e => media.delete(e.target), true);
  }
  if (root.AudioScheduledSourceNode) {
    const st = AudioScheduledSourceNode.prototype.start;
    orig.stop = AudioScheduledSourceNode.prototype.stop;
    AudioScheduledSourceNode.prototype.start = function () {
      if (!permit("sound")) return;
      live.add(this); try { this.addEventListener("ended", () => live.delete(this)); } catch (e) {}
      return st.apply(this, arguments);
    };
    // A refused sound was never started; the page's later stop() must not throw.
    AudioScheduledSourceNode.prototype.stop = function () { live.delete(this); try { return orig.stop.apply(this, arguments); } catch (e) { if (!e || e.name !== "InvalidStateError") throw e; } };
  }
  // Every connection to the speakers goes through a per-context gate gain (FIXES_R3 §1, FIXES_R4 G4).
  if (root.AudioNode && root.AudioDestinationNode) {
    const cn = AudioNode.prototype.connect;
    AudioNode.prototype.connect = function (dest) {
      if (dest instanceof AudioDestinationNode && !this.__rsosGate) {
        const ctx = dest.context;
        let g = gates.get(ctx);
        if (!g) { g = ctx.createGain(); g.__rsosGate = true; g.gain.value = session && !session.held ? 1 : 0; cn.call(g, dest); gates.set(ctx, g); }
        const args = Array.prototype.slice.call(arguments); args[0] = g;
        return cn.apply(this, args);
      }
      return cn.apply(this, arguments);
    };
  }
  root.RSOSOutlet = { open, adopt, close, ensure: () => permit("check"), permit, stopAll,
    active: () => !!(session && !session.held && check()), session: () => session,
    gains: () => Array.from(gates.values()).map(g => g.gain.value) };   // read-only, for tests
})(typeof window !== "undefined" ? window : globalThis);
