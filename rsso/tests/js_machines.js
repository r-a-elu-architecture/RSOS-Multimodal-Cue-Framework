// Helper for test_machines.py
const path = require("path");
const M = require(path.join(__dirname, "..", "..", "docs", "js", "machines.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const agent = M.agentFrom(M.EXAMPLE_AGENT), out = [];
  i.actions.forEach((a, k) => { const r = M.act(agent, a, k * 30); out.push(r); if (r.decision === "ask") M.answer(agent, a, k % 2 === 0); if (k % 3 === 1) M.humanSignal(agent, k * 30 + 3); });
  const [angles] = M.simPosture(5);
  process.stdout.write(JSON.stringify({ lines: i.cmds.map(c => [M.encode(c), M.check(c, true, 0.5), M.parse(M.encode(c))]), spread: M.spread("..- ---", ["wrist_left", "chest"]),
    tilts: i.vecs.map(v => Math.floor(M.tilt(...v) * 10 + 0.5) / 10), posture: M.posture(angles), agent: [out, agent, M.alignment(agent)],
    signals: Object.keys(M.AGENT_STATES).map(M.agentSignal), replies: [".", "-", " ---", "..-"].map(M.personReply),
    decode: Object.values(M.AGENT_STATES).map(c => M.decodePulses(M.codePulses(c))), packs: M.PACKS.map(p => [M.packMatrices(p), M.packIssues(p)]),
    made: M.makePack("x", "X", "c", i.rules) }));
});
