/* Consented programming, JavaScript implementation. Mirrors rsso/rsso/consent.py (identical results, tested).
 * A programmed cue runs only with a valid consent record naming its content; therapist-led tiers also need a
 * therapist present and the screening passed; the person can list and revoke every cue.
 * Browser: window.RSOSConsent; Node: module.exports.
 */
(function (root) {
  "use strict";
  const THERAPIST_LED_TIERS = ["414", "420", "439", "440"];
  const SCREENING_QUESTION = "Right now, are you in crisis, or having thoughts of harming yourself or not wanting to live?";
  const SCHEMA = "rsos-consent/1";
  const has = v => v !== null && v !== undefined;
  function therapistLed(c) { return THERAPIST_LED_TIERS.includes(String(c.tier || "")); }
  function check(c, now) {
    if (!c) return [false, "no consent record"];
    if (!String(c.content || "").trim() || !String(c.person || "").trim()) return [false, "consent must name the content and the person"];
    if (has(c.revoked_ms) && c.revoked_ms <= now) return [false, "revoked"];
    if (has(c.expires_ms) && now >= c.expires_ms) return [false, "expired"];
    if (therapistLed(c)) {
      if (!c.therapist_present) return [false, "therapist-led: needs a therapist present"];
      if (c.screened_ok !== true) return [false, "therapist-led: screening not passed"];
    }
    return [true, "ok"];
  }
  function programmedIds(tl) { return tl.events.filter(e => e.channel === "marker" && String(e.text || "").startsWith("programmed:")).map(e => e.text.split(":").slice(1).join(":")); }
  function gate(tl, items, now) {
    for (const id of programmedIds(tl)) { const [ok, why] = check(items ? items.find(c => c.id === id) : null, now); if (!ok) return [false, "cue " + id + ": " + why]; }
    return [true, "ok"];
  }
  const q = s => '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, " ") + '"';
  function cueProgram(c, inhale, exhale) {
    inhale = inhale || 4; exhale = exhale || 6;
    const L = ["# Programmed cue " + c.id + " (consent record), from tier " + (c.tier || "-") + "; author: " + (c.author || "self") + ".",
      "PROTOCOL cue_" + c.id + " " + q("Programmed cue"), "VERSION 1.0",
      "SAFETY max_per_hour=6 max_per_day=20 refractory=90s haptic_max=0.4",
      "BREATH inhale=" + inhale + "s exhale=" + exhale + "s",
      "PHASE settle dur=2s {", '  FEEL "Settle"', "}",
      "PHASE inhale breath=inhale {", '  FEEL "Breathe in"', "}",
      "PHASE cue breath=exhale {", "  SAY " + q(c.content)];
    if (c.sound_hz) L.push("  TONE " + Math.floor(c.sound_hz + 0.5) + "Hz 2s");
    L.push("  MARK " + q("programmed:" + c.id), "}", "PHASE rest breath=exhale {", '  FEEL "Let it settle"', '  MARK "installed"', "}");
    return L.join("\n") + "\n";
  }
  const api = { THERAPIST_LED_TIERS, SCREENING_QUESTION, SCHEMA, check, gate, cueProgram, programmedIds, therapistLed };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSConsent = api;
})(typeof self !== "undefined" ? self : this);
