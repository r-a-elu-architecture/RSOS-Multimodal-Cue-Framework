/* RSOS Device Protocol (RDP/1, spec/DEVICE_PROTOCOL.md) in the browser: encode a compiled RSX timeline for a device,
 * turn a vibration code into device events, connect over USB (Web Serial) or Bluetooth LE (Nordic UART Service),
 * and run the board check B1–B7 (identical to rsso/rsso/board.py quick_check, tested against the firmware core).
 * Browser: window.RSOSRdp; Node: module.exports.
 */
(function (root) {
  "use strict";
  const NUS = "6e400001-b5a3-f393-e0a9-e50e24dcca9e", NUS_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e", NUS_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e";
  function a2(x) { const k = Math.floor(Number(x) * 100 + 0.5); return Math.floor(k / 100) + "." + String(k % 100).padStart(2, "0"); }
  function encode(tl, caps) {
    caps = caps || ["haptic", "olfactory", "gustatory"]; const ev = [];
    for (const e of tl.events) {
      if (e.channel === "haptic" && caps.includes("haptic")) ev.push("H " + e.t + " " + e.on + " " + e.off + " " + e.count + " " + a2(e.amp));
      else if ((e.channel === "olfactory" || e.channel === "gustatory") && caps.includes(e.channel)) ev.push("S " + e.t + " " + e.dur + " " + (e.channel === "olfactory" ? "O" : "G"));
    }
    if (ev.length > 64) throw new Error("RDP/1 devices hold at least 64 events; this program needs more");
    return ["LOAD " + ev.length + " " + a2(tl.safety.haptic_max)].concat(ev);
  }
  function codeEvents(pulses, amp) {
    // pulses: [[on, off], ...] from UGCL.tactonPulses; one H event per pulse, as the compiler emits them
    const L = []; let t = 0;
    for (const [on, off] of pulses) { L.push("H " + t + " " + on + " " + (off || 100) + " 1 " + a2(amp)); t += on + off; }
    return ["LOAD " + L.length + " " + a2(amp)].concat(L);
  }

  /* A line transport: send(line), and lines arriving in a buffer that readFor() drains. */
  function lineBuffer() {
    const buf = [], waiters = [];
    return { buf, push(line) { if (line) { buf.push(line); while (waiters.length) waiters.shift()(); } },
      wait(ms) { return new Promise(r => { const t = setTimeout(r, ms); waiters.push(() => { clearTimeout(t); r(); }); }); } };
  }
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  async function readFor(tx, ms) { await sleep(ms); return tx.lines.buf.splice(0); }
  async function connectSerial(onLine) {
    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: 115200 });
    const lines = lineBuffer(), enc = new TextEncoder(), writer = port.writable.getWriter();
    const reader = port.readable.pipeThrough(new TextDecoderStream()).getReader();
    let rest = "", open = true;
    (async () => { try { while (open) { const { value, done } = await reader.read(); if (done) break; rest += value; let i; while ((i = rest.indexOf("\n")) >= 0) { const l = rest.slice(0, i).trim(); rest = rest.slice(i + 1); lines.push(l); if (l && onLine) onLine(l); } } } catch (e) {} })();
    await sleep(1500);   // many ESP32 boards reset when the port opens
    lines.buf.splice(0);
    return { kind: "USB", lines, send: line => writer.write(enc.encode(line + "\n")), close: async () => { open = false; try { reader.cancel(); writer.releaseLock(); await port.close(); } catch (e) {} } };
  }
  async function connectBle(onLine) {
    const dev = await navigator.bluetooth.requestDevice({ filters: [{ services: [NUS] }, { namePrefix: "RSOS" }], optionalServices: [NUS] });
    const gatt = await dev.gatt.connect(), svc = await gatt.getPrimaryService(NUS);
    const rx = await svc.getCharacteristic(NUS_RX), txc = await svc.getCharacteristic(NUS_TX);
    const lines = lineBuffer(), enc = new TextEncoder(), dec = new TextDecoder(); let rest = "";
    await txc.startNotifications();
    txc.addEventListener("characteristicvaluechanged", e => { rest += dec.decode(e.target.value); let i; while ((i = rest.indexOf("\n")) >= 0) { const l = rest.slice(0, i).trim(); rest = rest.slice(i + 1); lines.push(l); if (l && onLine) onLine(l); } });
    let q = Promise.resolve();
    const send = line => { const b = enc.encode(line + "\n"); q = q.then(async () => { for (let i = 0; i < b.length; i += 20) await rx.writeValueWithoutResponse(b.slice(i, i + 20)); }); return q; };
    return { kind: "Bluetooth", name: dev.name, lines, send, close: async () => { try { gatt.disconnect(); } catch (e) {} } };
  }
  const motor = lines => lines.map(x => x.split(" ")).filter(f => f[0] === "MOTOR").map(f => [Number(f[1]), Number(f[2])]);
  function pulses(m) { const out = []; let on = null; for (const [t, a] of m) { if (a > 0 && on === null) on = t; else if (a === 0 && on !== null) { out.push([on, t - on]); on = null; } } return out; }
  async function quickCheck(tx) {
    const res = [], send = async ls => { for (const l of ls) await tx.send(l); };
    await send(["HELLO"]); const hello = (await readFor(tx, 300)).find(x => x.startsWith("HELLO")) || "";
    res.push(["B1", "the device answers HELLO with RDP/1 and its capabilities", hello.startsWith("HELLO RDP/1"), hello || "no answer"]);
    await send(["STOP"]); await readFor(tx, 100);
    await send(["LOAD 1 0.40", "H 0 300 300 3 0.40", "START"]);
    let p = pulses(motor(await readFor(tx, 2200)));
    let ok = p.length === 3 && p.every(([, l]) => Math.abs(l - 300) <= 15) && p.slice(1).every((x, i) => Math.abs(x[0] - p[i][0] - 600) <= 15);
    res.push(["B2", "a 3-pulse pattern plays on the device's own clock: 300 ms pulses, 300 ms apart (±15 ms)", ok, p.map(([s, l]) => s + "+" + l).join(", ") || "no pulses"]);
    await send(["LOAD 1 0.40", "H 0 200 100 1 0.90", "START"]);
    let out = await readFor(tx, 600); const clamped = out.some(x => x.startsWith("CLAMPED")), amps = motor(out).map(x => x[1]);
    res.push(["B3", "a pulse asked at 0.9 under a limit of 0.4 is clamped to 0.4 and reported", clamped && amps.length > 0 && Math.max(...amps) <= 0.4 + 1e-9,
      "CLAMPED " + (clamped ? "reported" : "missing") + "; highest motor " + (amps.length ? Math.max(...amps) : 0).toFixed(2)]);
    await send(["LOAD 1 0.40", "H 0 2000 0 1 0.40", "START"]); await readFor(tx, 300);
    const sent = performance.now(); await tx.send("STOP");
    let got = null, off = false; const end = sent + 1000;
    while (performance.now() < end && got === null) {
      await tx.lines.wait(20);
      for (const l of tx.lines.buf.splice(0)) { if (l.startsWith("MOTOR") && l.endsWith(" 0.00")) off = true; if (l.startsWith("STOPPED") && got === null) got = performance.now() - sent; }
    }
    res.push(["B4", "after STOP the motor is off and STOPPED arrives within 100 ms (host round trip)", got !== null && off && got <= 100, got !== null ? Math.round(got) + " ms" : "no STOPPED"]);
    await send(["CONSENT 0", "LOAD 1 0.40", "S 0 500 O", "START"]);
    out = await readFor(tx, 700); const refused = out.some(x => x.startsWith("REFUSED")), opened = out.some(x => x.startsWith("SCENT") && x.endsWith(" 1"));
    res.push(["B5", "without consent a scent release is refused", refused && !opened, refused ? "refused" : opened ? "released" : "no report"]);
    await send(["CONSENT 1", "LOAD 1 0.40", "S 0 5000 O", "START"]);
    out = await readFor(tx, 3600);
    const closes = out.map(x => x.split(" ")).filter(f => f[0] === "SCENT" && f[2] === "O" && f[3] === "0").map(f => Number(f[1]));
    res.push(["B6", "a 5 s scent release closes by 3 s", closes.length > 0 && closes[0] <= 3000, closes.length ? "closed at " + closes[0] + " ms" : "did not close"]);
    await send(["STOP"]); await readFor(tx, 100); await send(["CONSENT 0"]); await readFor(tx, 100);
    await send(["LOAD 3 0.40", "H 0 100 100 1 0.40", "H 200 100 100 1 0.40", "H 400 300 100 1 0.40", "START"]);
    const lengths = pulses(motor(await readFor(tx, 1100))).map(x => x[1]);
    ok = lengths.length === 3 && lengths.every((a, i) => Math.abs(a - [100, 100, 300][i]) <= 15);
    res.push(["B7", "the Lion's vibration code ..- plays as 100, 100 and 300 ms pulses", ok, lengths.join(", ") || "no pulses"]);
    return res;
  }
  const api = { NUS, a2, encode, codeEvents, lineBuffer, connectSerial, connectBle, quickCheck, readFor };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RSOSRdp = api;
})(typeof self !== "undefined" ? self : this);
