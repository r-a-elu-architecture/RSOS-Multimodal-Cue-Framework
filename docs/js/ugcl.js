/* UGCL — the native glyph layer, JavaScript implementation (spec/GLYPH_FORMAT.md).
 * Mirrors rsso/rsso/ugcl.py; rsso/tests/test_ugcl.py checks identical SVG, haptic signatures and tone motifs.
 * Also contains the Bradley-Terry calibration used by the player (mirrors rsso/rsso/calibration.py).
 * Browser: window.UGCL; Node: module.exports.
 */
(function (root) {
  "use strict";
  const FORMAT = "rsos-ugcl/1", STROKE_W = 0.09;
  const PENTATONIC = [261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33];
  const rint = x => Math.floor(x + 0.5);
  // vibration codes (spec/GLYPH_FORMAT.md §7): . 100 ms, - 300 ms, 100 ms apart; a space joins codes with a 400 ms pause
  const TACTON_SHORT = 100, TACTON_LONG = 300, TACTON_GAP = 100, TACTON_WORD = 400, TACTON_RE = /^[.\-]{1,6}( [.\-]{1,6}){0,2}$/;
  const EMOJI_FONTS = "'Noto Color Emoji','Apple Color Emoji','Segoe UI Emoji',sans-serif";
  const SYMBOL_FONTS = "'Noto Sans Symbols','Noto Sans Symbols 2','Noto Sans Math','Segoe UI Symbol','Apple Symbols',Symbola";
  const GLYPH_FONTS = SYMBOL_FONTS + "," + EMOJI_FONTS;   // as on the ledger pages: symbol fonts first, then colour emoji
  const JOINERS = ["\ufe0f", "\ufe0e", "\u200d"];
  function tactonPulses(code) {
    const out = [];
    for (const c of code || "") { if (c === " ") { if (out.length) out[out.length - 1][1] = TACTON_WORD; continue; } out.push([c === "." ? TACTON_SHORT : TACTON_LONG, TACTON_GAP]); }
    if (out.length) out[out.length - 1][1] = 0;
    return out;
  }
  function glyphFontSize(ch) { const n = [...ch].filter(c => !JOINERS.includes(c)).length; return n <= 1 ? 44 : n === 2 ? 32 : n === 3 ? 24 : rint(76 / n); }
  const xml = t => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  function fmt(x) {
    const v = rint(x * 1000) / 1000;
    if (v === 0) return "0";
    return v.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
  }
  const rad = d => d * Math.PI / 180;
  function rot(x, y, deg) { const a = rad(deg); return [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)]; }
  function transform(s, ang, mir) {
    const p = s.p.slice();
    if (s.k === "L") {
      let [x1, y1, x2, y2] = p; if (mir) { x1 = -x1; x2 = -x2; }
      const a = rot(x1, y1, ang), b = rot(x2, y2, ang); return { k: "L", p: [a[0], a[1], b[0], b[1]] };
    }
    if (s.k === "C" || s.k === "D") { let [cx, cy, r] = p; if (mir) cx = -cx; const c = rot(cx, cy, ang); return { k: s.k, p: [c[0], c[1], r] }; }
    if (s.k === "A") {
      let [cx, cy, r, a0, a1] = p; if (mir) { cx = -cx; const t = a0; a0 = 180 - a1; a1 = 180 - t; }
      const c = rot(cx, cy, ang); return { k: "A", p: [c[0], c[1], r, a0 + ang, a1 + ang] };
    }
    throw new Error("unknown stroke kind " + s.k);
  }
  function expand(g) {
    const out = [], sym = Math.trunc(g.sym || 1);
    for (let k = 0; k < sym; k++) {
      const ang = 360.0 * k / sym;
      for (const s of g.strokes) for (const mir of (g.mirror ? [false, true] : [false])) out.push(transform(s, ang, mir));
    }
    return out;
  }
  // Browser only: glyphs this device has no font for are drawn from their stored image instead (see prepare()).
  const FALLBACK = new Set();
  function svgImage(g, size, color, bg) {
    const body = g.colour ? '<image href="' + g.png + '" width="64" height="64"/>' :
      '<defs><mask id="m-' + g.id + '"><image href="' + g.png + '" width="64" height="64"/></mask></defs><rect width="64" height="64" fill="' + color + '" mask="url(#m-' + g.id + ')"/>';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size + '" viewBox="0 0 64 64" role="img" aria-label="' + xml(g.char) + '">' + bg + body + "</svg>";
  }
  function svgOriginal(g, size, color, background) {
    // the glyph as text, exactly as recorded and drawn as on the ledger pages; crisp at any size
    const bg = background ? '<rect width="64" height="64" fill="' + background + '"/>' : "";
    if (FALLBACK.has(g.id) && g.png) return svgImage(g, size, color, bg);
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size + '" viewBox="0 0 64 64" role="img" aria-label="' + xml(g.char) + '">' + bg +
      '<text x="32" y="33" text-anchor="middle" dominant-baseline="central" font-size="' + glyphFontSize(g.char) + '" font-family="' + GLYPH_FONTS + '" fill="' + color + '">' +
      xml(g.char).replace(/\+/g, '<tspan fill="' + color + '" font-family="sans-serif" dx="1">+</tspan>') + "</text></svg>";
  }
  function svg(g, size, color, background) {
    size = size || 120; color = color || "#e8b04a";
    if (g.kind === "original") return svgOriginal(g, size, color, background);
    const parts = [];
    for (const s of expand(g)) {
      const p = s.p;
      if (s.k === "L") parts.push(`<line x1="${fmt(p[0])}" y1="${fmt(-p[1])}" x2="${fmt(p[2])}" y2="${fmt(-p[3])}"/>`);
      else if (s.k === "C") parts.push(`<circle cx="${fmt(p[0])}" cy="${fmt(-p[1])}" r="${fmt(p[2])}"/>`);
      else if (s.k === "D") parts.push(`<circle cx="${fmt(p[0])}" cy="${fmt(-p[1])}" r="${fmt(p[2])}" fill="${color}" stroke="none"/>`);
      else {
        const [cx, cy, r, a0, a1] = p;
        const x0 = cx + r * Math.cos(rad(a0)), y0 = cy + r * Math.sin(rad(a0)), x1 = cx + r * Math.cos(rad(a1)), y1 = cy + r * Math.sin(rad(a1));
        const large = (((a1 - a0) % 360) + 360) % 360 > 180 ? 1 : 0;
        parts.push(`<path d="M${fmt(x0)} ${fmt(-y0)}A${fmt(r)} ${fmt(r)} 0 ${large} 0 ${fmt(x1)} ${fmt(-y1)}"/>`);
      }
    }
    const bg = background ? `<rect x="-1.2" y="-1.2" width="2.4" height="2.4" fill="${background}"/>` : "";
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.2 -1.2 2.4 2.4" width="${size}" height="${size}">${bg}` +
      `<g fill="none" stroke="${color}" stroke-width="${STROKE_W}" stroke-linecap="round" stroke-linejoin="round">` + parts.join("") + "</g></svg>";
  }
  function strokeLength(s) {
    const p = s.p;
    if (s.k === "L") return Math.hypot(p[2] - p[0], p[3] - p[1]);
    if (s.k === "C") return 2 * Math.PI * p[2];
    if (s.k === "A") return rad(Math.abs(p[4] - p[3])) * p[2];
    return 0;
  }
  function hapticSignature(g) {
    if (g.kind === "original") return g.tacton ? tactonPulses(g.tacton) : g.haptic.map(x => x.slice());
    const base = g.strokes.map(s => [s.k === "D" ? 50 : Math.min(220, Math.max(60, rint(60 + 60 * strokeLength(s)))), 80]);
    let seq = [];
    for (let r = 0; r < Math.min(Math.trunc(g.sym || 1), 3); r++) { seq = seq.concat(base.map(x => x.slice())); seq[seq.length - 1][1] = 160; }
    if (g.mirror) seq.push([40, 80]);
    const out = []; let total = 0;
    for (const [on, off] of seq) { if (total + on > 2000) break; out.push([on, off]); total += on + off; }
    out[out.length - 1][1] = 0;
    return out;
  }
  function toneMotif(g) {
    if (g.kind === "original") return g.tone.map(x => x.slice());
    const notes = [];
    for (const s of g.strokes) {
      const p = s.p;
      const [mx, my] = s.k === "L" ? [(p[0] + p[2]) / 2, (p[1] + p[3]) / 2] : [p[0], p[1]];
      const ang = (mx || my) ? ((Math.atan2(my, mx) * 180 / Math.PI) + 360) % 360 : 0;
      notes.push([PENTATONIC[Math.floor(ang / (360 / 7)) % 7], 180]);
    }
    if (Math.trunc(g.sym || 1) > 1) notes.push([Math.round(notes[0][0] * 2 * 100) / 100, 260]);
    return notes;
  }

  function encode(g) {
    return String(Math.trunc(g.sym || 1)) + (g.mirror ? "m" : "") + ":" + g.strokes.map(s => s.k + s.p.map(fmt).join(",")).join(";");
  }
  function decode(code, id) {
    const i = code.indexOf(":"), head = code.slice(0, i);
    return { id: id || "glyph", sym: parseInt(head, 10), mirror: head.endsWith("m"),
      strokes: code.slice(i + 1).split(";").map(part => ({ k: part[0], p: part.slice(1).split(",").map(Number) })) };
  }

  /* Bradley-Terry ranking from pairwise choices (minorization-maximization), with adaptive pair choice. */
  function btFit(n, comparisons, iters) {
    iters = iters || 200;
    const w = new Array(n).fill(1);
    const wins = new Array(n).fill(0), pairs = {};
    for (const [a, b] of comparisons) { wins[a] += 1; const k = a < b ? a + "," + b : b + "," + a; pairs[k] = (pairs[k] || 0) + 1; }
    for (let t = 0; t < iters; t++) {
      for (let i = 0; i < n; i++) {
        let den = 0;
        for (const k in pairs) { const [a, b] = k.split(",").map(Number); if (a === i || b === i) { const j = a === i ? b : a; den += pairs[k] / (w[i] + w[j]); } }
        w[i] = den > 0 ? (wins[i] + 0.5) / (den + 0.5 / (w[i] + 1) * 2) : w[i];
      }
      const g = Math.exp(w.reduce((s, x) => s + Math.log(x), 0) / n);
      for (let i = 0; i < n; i++) w[i] /= g;
    }
    return w.map(x => Math.log(x));
  }
  function nextPair(n, comparisons, scores) {
    const count = new Array(n).fill(0), seen = {};
    for (const [a, b] of comparisons) { count[a]++; count[b]++; seen[a < b ? a + "," + b : b + "," + a] = true; }
    let best = null;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      const cost = (seen[i + "," + j] ? 10 : 0) + Math.abs(scores[i] - scores[j]) + 0.5 * (count[i] + count[j]);
      if (best === null || cost < best[0] - 1e-12) best = [cost, i, j];
    }
    return [best[1], best[2]];
  }

  /* ---- browser helpers: fonts, the vibration code as a cue you can see, feel and hear ---- */
  function prepare(glyphs) {
    // load the symbol fonts for these glyphs, then find any glyph this device still cannot draw (it would show as an
    // empty box) and draw that one from its stored image
    if (typeof document === "undefined" || !document.fonts) return Promise.resolve();
    const mono = glyphs.filter(g => g.kind === "original");
    const text = mono.map(g => g.char).join("");
    const fams = ["Noto Sans Symbols", "Noto Sans Symbols 2", "Noto Sans Math", "Noto Color Emoji"];
    return Promise.all(fams.map(f => document.fonts.load("32px '" + f + "'", text).catch(() => null))).then(() => {
      const c = document.createElement("canvas"); c.width = c.height = 48; const x = c.getContext("2d");
      const draw = t => { x.clearRect(0, 0, 48, 48); x.font = "32px " + GLYPH_FONTS; x.fillText(t, 4, 36); return x.getImageData(0, 0, 48, 48).data.join(","); };
      const box = draw("\u{10FFFD}");
      for (const g of mono) { const ch = g.char.replace(/[\ufe0e\ufe0f\u200d]/g, ""); if ([...ch].some(k => draw(k) === box)) FALLBACK.add(g.id); }
    });
  }
  function codeSVG(code, color, h) {
    // the vibration code drawn as dots and dashes; each mark has class "tm" so a page can light it while it plays
    h = h || 10; color = color || "#e8b04a";
    const marks = []; let x = 0;
    for (const c of code || "") {
      if (c === " ") { x += h * 1.2; continue; }
      if (c === ".") marks.push('<circle class="tm" cx="' + fmt(x + h / 2) + '" cy="' + fmt(h / 2) + '" r="' + fmt(h / 2) + '"/>');
      else marks.push('<rect class="tm" x="' + fmt(x) + '" y="0" width="' + fmt(h * 2.6) + '" height="' + fmt(h) + '" rx="' + fmt(h / 2) + '"/>');
      x += (c === "." ? h : h * 2.6) + h * 0.7;
    }
    const w = Math.max(h, x - h * 0.7);
    return '<svg class="tcode" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + fmt(w) + " " + fmt(h) + '" width="' + fmt(w) + '" height="' + fmt(h) + '" fill="' + color + '" role="img" aria-label="Vibration code ' + code + '">' + marks.join("") + "</svg>";
  }
  let AC = null;
  function audioCtx() { try { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === "suspended") AC.resume(); } catch (e) { AC = null; } return AC; }
  function feel(code, opts) {
    // plays a vibration code: the wrist vibrates where the device can, the speaker gives the same pattern as the low
    // buzz of a vibration motor, and the code's marks (opts.marks: an element containing codeSVG) light up in time
    opts = opts || {};
    const pulses = tactonPulses(code); let total = 0;
    if (opts.vibrate !== false && typeof navigator !== "undefined" && navigator.vibrate) navigator.vibrate(pulses.flat());
    const ac = opts.sound === false ? null : audioCtx();
    const marks = opts.marks ? [...opts.marks.querySelectorAll(".tm")] : [];
    let t0 = ac ? ac.currentTime + 0.04 : 0, t = 0;
    pulses.forEach(([on, off], i) => {
      if (ac) {
        const a = t0 + t / 1000, b = a + on / 1000, g = ac.createGain(), f = ac.createBiquadFilter();
        f.type = "lowpass"; f.frequency.value = 700; f.Q.value = 3;
        for (const [type, hz, lv] of [["sawtooth", 150, 0.22], ["square", 75, 0.1]]) {
          const o = ac.createOscillator(), v = ac.createGain(); o.type = type; o.frequency.value = hz; v.gain.value = lv;
          o.connect(v).connect(f); o.start(a); o.stop(b + 0.03);
        }
        g.gain.setValueAtTime(0, a); g.gain.linearRampToValueAtTime(opts.volume || 0.9, a + 0.008); g.gain.setValueAtTime(opts.volume || 0.9, b - 0.012); g.gain.linearRampToValueAtTime(0, b);
        f.connect(g).connect(ac.destination);
      }
      if (marks[i]) { setTimeout(() => marks[i].classList.add("on"), t + 40); setTimeout(() => marks[i].classList.remove("on"), t + 40 + on); }
      t += on + off;
    });
    total = t;
    return total;
  }
  const api = { FORMAT, prepare, codeSVG, feel, audioCtx, TACTON_RE, tactonPulses, glyphFontSize, encode, decode, expand, svg, hapticSignature, toneMotif, strokeLength, fmt, btFit, nextPair };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.UGCL = api;
})(typeof self !== "undefined" ? self : this);
