/* The output gate (spec/FIXES_R3.md §1, FIXES_R4.md §1, FIXES_R5.md §1). Every channel that reaches the person goes
 * through here: sound to the speakers, unmuted media, speech, vibration and the wristband's START. The gate keeps a list
 * of sessions (a run, an offer, a code, a therapist session); open() and adopt() return a handle and close(handle)
 * removes that one. A refused open() changes no existing session. Output passes only when no session is held and a live
 * session allows it; the page's declared session (data-outlet-* on <body>) is used only when there is no session at all.
 * Every check uses the stricter of the session's saved domain and the live RSOSDomain. Live sessions are re-checked every
 * second and on any storage change in any tab; when one turns to hold, everything playing stops and "rsos-outlet-hold"
 * is dispatched. An expired session is removed; a held one stays until its page closes it. Stop calls always work.
 * Fails closed without the safety scripts. Browser: window.RSOSOutlet.
 */
(function (root) {
  "use strict";
  if (typeof window === "undefined") return;
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const sessions = [];                   // {id, action, extra, until, declared, held}
  let nextId = 1;
  const refused = new Set(), live = new Set(), media = new Set(), gates = new Map();
  const ready = () => !!(root.RSOSWatchdog && root.RSOSGuard && root.RSOSSafety && root.RSOSContain);
  const orig = {};
  const RANK = { self_guided: 0, structured: 1, clinician_led: 2 };
  const rank = l => (l in RANK ? RANK[l] : RANK.structured);

  // The stricter of the session's saved domain and the live one (FIXES_R5 O1).
  function ctxFor(extra) {
    const x = extra || {}, D = root.RSOSDomain || {};
    const levels = [x.max_level, D.max_level].filter(v => v !== undefined && v !== null);
    const max_level = levels.length ? levels.reduce((a, b) => (rank(b) < rank(a) ? b : a)) : null;
    const mwa = [x.memory_work_allowed, D.memory_work_allowed].filter(v => v !== undefined && v !== null);
    return { contain: get("rsos.contain", null), safety: get("rsos.safety", null), timeline: null, now: Date.now() / 1000,
      max_level: max_level && !(max_level in RANK) ? "structured" : max_level,
      clinician_present: !!x.clinician_present, screening_recorded: !!x.screening_recorded,
      consents: get("rsos.consents", []), plan_protocols: x.plan_protocols === undefined ? null : x.plan_protocols,
      memory_work_allowed: mwa.length ? mwa.every(Boolean) : null };
  }
  function add(action, extra, seconds, declared) {
    const s = { id: nextId++, action, extra: extra || {}, until: Date.now() + (seconds || 900) * 1000, declared: !!declared, held: false };
    sessions.push(s); refused.clear(); setAudio(sessions.every(t => !t.held)); return s.id;
  }
  function open(action, extra, opts) {
    const o = opts || {};
    if (!ready()) return { decision: "hold", reasons: [{ rule: "outlet", virtue: "jin", text: "The safety scripts are not loaded on this page.", resolve: "none" }], opened: false, handle: null };
    const c = ctxFor(extra);   // asked through RSOSGuard (logged), with the stricter domain (O1)
    const r = root.RSOSGuard.ask(action, Object.assign({}, extra || {}, { max_level: c.max_level, memory_work_allowed: c.memory_work_allowed }));
    const ok = r.decision === "allow" || (r.decision === "ask" && !!o.confirmed);
    const handle = ok ? add(action, extra, o.seconds, o.declared) : null;   // a refused open changes nothing (FIXES_R5 O2)
    return Object.assign({}, r, { opened: ok, handle });
  }
  function adopt(action, extra, opts) { return add(action, extra, (opts || {}).seconds, false); }
  function close(handle) {
    if (handle === undefined) sessions.length = 0;
    else { const i = sessions.findIndex(s => s.id === handle); if (i >= 0) sessions.splice(i, 1); }
    setAudio(sessions.length > 0 && sessions.every(s => !s.held));
  }
  function declared() {
    const b = document.body; if (!b || !b.dataset.outletKind) return null;
    return { kind: b.dataset.outletKind, protocol: b.dataset.outletProtocol || b.dataset.outletKind, trigger: b.dataset.outletTrigger || "self", source: "person" };
  }
  // Re-check every live session. Expired ones are removed (O3); one that turns to hold holds everything.
  function check() {
    const now = Date.now();
    for (let i = sessions.length - 1; i >= 0; i--) if (!sessions[i].held && sessions[i].until <= now) sessions.splice(i, 1);
    if (sessions.some(s => s.held)) return false;
    if (!sessions.length) return false;
    if (!ready()) { sessions.forEach(s => { s.held = true; }); return hold(); }
    let bad = false;
    for (const s of sessions) if (root.RSOSWatchdog.watch(s.action, ctxFor(s.extra)).decision === "hold") { s.held = true; bad = true; }
    return bad ? hold() : true;
  }
  function hold() {
    for (let i = sessions.length - 1; i >= 0; i--) if (sessions[i].declared) sessions.splice(i, 1);   // a declared session is simply dropped
    stopAll();
    try { root.dispatchEvent(new CustomEvent("rsos-outlet-hold")); } catch (e) {}
    return false;
  }
  function permit(channel) {
    if (sessions.length) { if (check()) return true; if (sessions.length) return refuse(channel); }
    if (sessions.some(s => s.held)) return refuse(channel);
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
  const liveOnes = () => sessions.some(s => !s.held);
  // Live sessions are re-checked every second and on storage changes in any tab (FIXES_R4 G2, G3).
  setInterval(() => { if (liveOnes()) check(); }, 1000);
  root.addEventListener("storage", () => { if (liveOnes()) check(); });
  const frozen = s => s ? Object.freeze(JSON.parse(JSON.stringify(s))) : null;   // copies (FIXES_R5 O5)

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
        if (!g) { g = ctx.createGain(); g.__rsosGate = true; g.gain.value = sessions.length && sessions.every(t => !t.held) ? 1 : 0; cn.call(g, dest); gates.set(ctx, g); }
        const args = Array.prototype.slice.call(arguments); args[0] = g;
        return cn.apply(this, args);
      }
      return cn.apply(this, arguments);
    };
  }
  root.RSOSOutlet = { open, adopt, close, ensure: () => permit("check"), permit, stopAll,
    active: () => liveOnes() && check(),
    session: () => frozen(sessions[sessions.length - 1]), sessions: () => sessions.map(frozen),
    gains: () => Array.from(gates.values()).map(g => g.gain.value) };   // copies, for tests
})(typeof window !== "undefined" ? window : globalThis);
