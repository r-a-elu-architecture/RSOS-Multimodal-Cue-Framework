/* One English voice for every page. Default: American English (en-US), a natural voice where installed, a calm
 * male voice where there is a choice. A voice the person chose on the Player page (rsos.settings.voice, saved with
 * voice_v 2) is used everywhere. Without this, pages speak with the system's default voice, which on a non-English
 * system reads English with that language's voice. Browser: window.RSOSVoice.
 */
(function (root) {
  "use strict";
  const MALE = /\b(male|daniel|arthur|guy|davis|andrew|brian|christopher|eric|roger|ryan|thomas|alex|fred|aaron|george|oliver|james|william|liam|tony|mark|david)\b/i;
  function score(v) {
    let s = 0;
    if (/^en[-_]US/i.test(v.lang)) s += 4; else if (/^en[-_]GB/i.test(v.lang)) s += 2; else if (/^en/i.test(v.lang)) s += 1;
    if (/natural|neural|online|premium|enhanced/i.test(v.name)) s += 3;
    if (MALE.test(v.name)) s += 2;
    if (v.localService) s += 0.5;
    return s;
  }
  function english() {
    if (!("speechSynthesis" in root)) return [];
    return speechSynthesis.getVoices().filter(v => /^en/i.test(v.lang)).sort((a, b) => score(b) - score(a));
  }
  function chosen() {
    try { const s = JSON.parse(localStorage.getItem("rsos.settings") || "{}") || {}; return s.voice_v === 2 ? s.voice || null : null; } catch (e) { return null; }
  }
  function pick() { const vs = english(), c = chosen(); return (c && vs.find(v => v.name === c)) || vs[0] || null; }
  function speak(text, o) {
    try {
      if (!text || !("speechSynthesis" in root)) return;
      const u = new SpeechSynthesisUtterance(text), v = pick();
      if (v) { u.voice = v; u.lang = v.lang; } else u.lang = "en-US";
      u.rate = (o && o.rate) || 0.9; if (o && o.pitch) u.pitch = o.pitch;
      if (o && o.cancel) speechSynthesis.cancel();
      speechSynthesis.speak(u);
    } catch (e) { /* no voice */ }
  }
  if ("speechSynthesis" in root) { speechSynthesis.getVoices(); try { speechSynthesis.addEventListener("voiceschanged", () => {}); } catch (e) {} }
  root.RSOSVoice = { score, english, pick, speak };
})(window);
