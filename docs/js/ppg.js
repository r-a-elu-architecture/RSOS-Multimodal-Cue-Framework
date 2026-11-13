/* Heart rate and HRV from a fingertip over the phone camera, JavaScript implementation (spec/PEAK.md section 4).
 * analyze() mirrors rsso/rsso/ppg.py (identical results, tested). measure() runs the camera with the flash on,
 * samples the mean red value of each frame and analyses it. Works in Chrome on Android; on iPhone the browser
 * cannot turn on the flash, so a bright light behind the finger is needed.
 * Browser: window.RSOSPpg; Node: module.exports (analyze only).
 */
(function (root) {
  "use strict";
  const MIN_RR = 333, MAX_RR = 1500, DETREND_MS = 750, SMOOTH = 2;
  const r1 = x => (x === null || x === undefined ? null : Math.floor(x * 10 + 0.5) / 10);

  function analyze(samples) {
    const s = samples.map(p => [Number(p[0]), Number(p[1])]);
    const out = { ok: false, rmssd_ok: false, hr: null, rmssd: null, beats: 0, quality: 0, seconds: 0, say: "" };
    if (s.length < 2) { out.say = "No signal. Cover the camera fully with a fingertip, flash on."; return out; }
    const secs = (s[s.length - 1][0] - s[0][0]) / 1000;
    out.seconds = r1(secs);
    if (secs < 10 || s.length < 150) { out.say = "Too short. Hold still for at least 20 seconds."; return out; }
    const n = s.length, det = [];
    for (let i = 0; i < n; i++) {
      const t = s[i][0]; let tot = 0, k = 0, j = i;
      while (j >= 0 && t - s[j][0] <= DETREND_MS) { tot += s[j][1]; k++; j--; }
      j = i + 1;
      while (j < n && s[j][0] - t <= DETREND_MS) { tot += s[j][1]; k++; j++; }
      det.push(s[i][1] - tot / k);
    }
    const y = [];
    for (let i = 0; i < n; i++) {
      let tot = 0, k = 0;
      for (let j = Math.max(0, i - SMOOTH); j < Math.min(n, i + SMOOTH + 1); j++) { tot += det[j]; k++; }
      y.push(-(tot / k));
    }
    let m = 0; for (const v of y) m += v; m /= n;
    let ss = 0; for (const v of y) ss += (v - m) * (v - m);
    const sd = Math.sqrt(ss / n);
    if (sd <= 0) { out.say = "The signal is flat. Cover the camera fully and turn the flash on."; return out; }
    const thr = m + 0.3 * sd, peaks = [];
    for (let i = 1; i < n - 1; i++) {
      if (y[i] > y[i - 1] && y[i] >= y[i + 1] && y[i] > thr) {
        if (peaks.length && s[i][0] - s[peaks[peaks.length - 1]][0] < MIN_RR) { if (y[i] > y[peaks[peaks.length - 1]]) peaks[peaks.length - 1] = i; }
        else peaks.push(i);
      }
    }
    const pt = peaks.map(i => {
      const den = y[i - 1] - 2 * y[i] + y[i + 1];
      let off = den !== 0 ? 0.5 * (y[i - 1] - y[i + 1]) / den : 0;
      off = Math.max(-0.5, Math.min(0.5, off));
      return s[i][0] + off * ((s[i + 1][0] - s[i - 1][0]) / 2);
    });
    let rr = []; for (let k = 1; k < pt.length; k++) rr.push(pt[k] - pt[k - 1]);
    rr = rr.filter(x => x >= MIN_RR && x <= MAX_RR);
    out.beats = peaks.length;
    if (rr.length < 5) { out.say = "Too few clear beats. Press lightly, keep still, and try again."; return out; }
    const srt = rr.slice().sort((a, b) => a - b), h = Math.floor(srt.length / 2);
    const med = srt.length % 2 ? srt[h] : (srt[h - 1] + srt[h]) / 2;
    const keep = rr.map(x => Math.abs(x - med) <= 0.25 * med), good = rr.filter((x, k) => keep[k]);
    const q = good.length / rr.length;
    out.quality = r1(q * 100);
    const diffs = []; for (let k = 1; k < rr.length; k++) if (keep[k] && keep[k - 1] && Math.abs(rr[k] - rr[k - 1]) <= 0.2 * med) diffs.push(rr[k] - rr[k - 1]);
    let g = 0; for (const x of good) g += x;
    out.hr = r1(60000 / (g / good.length));
    let d2 = 0; for (const d of diffs) d2 += d * d;
    out.rmssd = diffs.length ? r1(Math.sqrt(d2 / diffs.length)) : null;
    out.ok = q >= 0.7 && good.length >= 8;
    out.rmssd_ok = out.ok && q >= 0.95 && diffs.length >= 8;
    out.say = out.ok ? "Good reading." : "Noisy reading: keep the finger still and press lightly, then try again.";
    return out;
  }

  // Camera capture (browser only). opts: { seconds = 30, onProgress(fraction, covered) }
  async function measure(opts) {
    opts = opts || {};
    const seconds = (opts.seconds || 30) + 3;
    if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) throw new Error("This browser cannot use the camera.");
    const stream = await navigator.mediaDevices.getUserMedia({ audio: false,
      video: { facingMode: { ideal: "environment" }, width: { ideal: 160 }, height: { ideal: 120 }, frameRate: { ideal: 30 } } });
    const track = stream.getVideoTracks()[0];
    let torch = false;
    try { await track.applyConstraints({ advanced: [{ torch: true }] }); torch = true; } catch (e) { torch = false; }
    const video = document.createElement("video");
    video.muted = true; video.playsInline = true; video.setAttribute("playsinline", ""); video.srcObject = stream;
    await video.play();
    const cv = document.createElement("canvas"); cv.width = 40; cv.height = 30;
    const ctx = cv.getContext("2d", { willReadFrequently: true });
    const samples = [], greens = []; const t0 = performance.now(); let frames = 0, coveredFrames = 0, sumR = 0, sumG = 0, sumB = 0;
    await new Promise(resolve => {
      const step = () => {
        const now = performance.now();
        try {
          ctx.drawImage(video, 0, 0, cv.width, cv.height);
          const d = ctx.getImageData(0, 0, cv.width, cv.height).data; let rs = 0, gs = 0, bs = 0;
          for (let i = 0; i < d.length; i += 4) { rs += d[i]; gs += d[i + 1]; bs += d[i + 2]; }
          const px = d.length / 4, red = rs / px, green = gs / px, blue = bs / px;
          // a fingertip lit from behind glows red: red clearly above green and blue. A screen, a room or a face does not.
          const covered = red > 60 && red >= 1.15 * green && red >= 1.3 * blue;
          frames++; if (covered) coveredFrames++; sumR += red; sumG += green; sumB += blue;
          const tt = Math.round((now - t0) * 10) / 10;
          samples.push([tt, Math.round(red * 1000) / 1000]); greens.push([tt, Math.round(green * 1000) / 1000]);
          if (opts.onProgress) opts.onProgress(Math.min(1, (now - t0) / (seconds * 1000)), covered);
        } catch (e) { /* frame not ready */ }
        if (now - t0 >= seconds * 1000) return resolve();
        if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(step); else requestAnimationFrame(step);
      };
      step();
    });
    track.stop(); stream.getTracks().forEach(t => t.stop());
    // skip the first 3 s (exposure settling, finger moving into place); analyse red and green, keep the cleaner one
    // (red often saturates with the flash right behind the fingertip, flattening the pulse)
    const settle = x => x.filter(p => p[0] >= 3000);
    const rr = analyze(settle(samples)), rg = analyze(settle(greens));
    const score = r => (r.ok ? 1000 : 0) + (r.quality || 0);
    const res = score(rg) > score(rr) ? rg : rr; res.channel = res === rg ? "green" : "red"; res.torch = torch;
    res.covered = frames ? Math.round(coveredFrames / frames * 1000) / 10 : 0;
    res.colour = frames ? [Math.round(sumR / frames), Math.round(sumG / frames), Math.round(sumB / frames)] : [0, 0, 0];
    if (res.covered < 60) {   // no fingertip: whatever rhythm was found is not a pulse
      Object.assign(res, { ok: false, rmssd_ok: false, hr: null, rmssd: null,
        say: "No fingertip detected (the camera saw red " + res.colour[0] + ", green " + res.colour[1] + ", blue " + res.colour[2] +
          " on average, a fingertip in " + res.covered + "% of frames). Cover the camera fully with a fingertip, flash on, and try again." });
    }
    return { result: res, samples };
  }

  const api = { analyze, measure };
  if (typeof module !== "undefined" && module.exports) module.exports = { analyze }; else root.RSOSPpg = api;
})(typeof self !== "undefined" ? self : this);
