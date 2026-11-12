// Helper for test_nodes.py: {intakes, frames:[[text,mode,bel]], runs} -> JS results
const path = require("path");
const N = require(path.join(__dirname, "..", "..", "docs", "js", "nodes.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  process.stdout.write(JSON.stringify({ plans: i.intakes.map(N.plan), frames: i.frames.map(f => N.frameCheck(f[0], f[1], f[2])), opening: N.channelOpening(i.runs) }));
});
