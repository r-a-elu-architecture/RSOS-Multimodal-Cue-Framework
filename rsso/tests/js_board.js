// Helper for test_board.py: encode parity input on stdin, and the browser board check against the firmware core in real time
const path = require("path"), { spawn } = require("child_process");
const R = require(path.join(__dirname, "..", "..", "docs", "js", "rdp.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", async () => {
  const i = JSON.parse(s);
  const out = { encoded: i.timelines.map(t => R.encode(t)), codes: i.codes.map(([p, a]) => R.codeEvents(p, a)) };
  const sim = spawn(i.host_sim), lines = R.lineBuffer(), t0 = Date.now(); let rest = "";
  sim.stdout.on("data", d => { rest += d; let k; while ((k = rest.indexOf("\n")) >= 0) { const l = rest.slice(0, k).trim(); rest = rest.slice(k + 1); if (l && !l.startsWith("TOCK")) lines.push(l); } });
  const tick = () => sim.stdin.write("TICK " + (Date.now() - t0) + "\n");
  const timer = setInterval(tick, 2);
  const tx = { lines, send: line => { tick(); sim.stdin.write(line + "\n"); return Promise.resolve(); } };
  out.check = await R.quickCheck(tx);
  clearInterval(timer); sim.stdin.write("QUIT\n");
  process.stdout.write(JSON.stringify(out));
});
