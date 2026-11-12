// Helper for the conformance test: compile RSX from stdin with docs/js/rsx.js and print JSON.
const path = require("path");
const RSX = require(path.join(__dirname, "..", "..", "docs", "js", "rsx.js"));
let src = "";
process.stdin.on("data", d => (src += d));
process.stdin.on("end", () => {
  try { process.stdout.write(JSON.stringify({ ok: RSX.compile(src) })); }
  catch (e) { if (e instanceof RSX.RSXError) process.stdout.write(JSON.stringify({ error: e.message })); else throw e; }
});
