// Helper for test_memstack.py: {runs, srbai, pysnap} on stdin -> {summary, jssnap, pysnap_ok}
const path = require("path");
const M = require(path.join(__dirname, "..", "..", "docs", "js", "memstack.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", async () => {
  const inp = JSON.parse(s);
  const summary = M.summarize(inp.runs, inp.srbai);
  const jssnap = await M.snapshot(inp.runs, inp.srbai);
  let pysnap_ok = true; try { await M.restore(inp.pysnap); } catch (e) { pysnap_ok = String(e.message); }
  let tampered = "accepted"; try { const t = JSON.parse(JSON.stringify(inp.pysnap)); t.runs[0].sud_after = 0; await M.restore(t); } catch (e) { tampered = "rejected"; }
  process.stdout.write(JSON.stringify({ summary, jssnap, pysnap_ok, tampered }));
});
