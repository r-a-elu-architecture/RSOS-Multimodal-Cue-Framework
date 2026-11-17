// Helper for test_profiles.py
const path = require("path");
const P = require(path.join(__dirname, "..", "..", "docs", "js", "profiles.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s), out = { profiles: P.PROFILES, terms: P.TERMS, exempt: P.EXEMPT_PAGES, text: {}, term: {}, vocab: {} };
  for (const p of P.IDS) for (const on of [false, true]) {
    const k = p + ":" + on;
    out.text[k] = i.corpus.map(c => P.text(c, p, on));
    out.term[k] = Object.keys(P.TERMS).map(t => P.term(t, p, on));
    out.vocab[k] = P.clinicalVocab(p, on);
  }
  out.flags = i.corpus.map(c => P.hasClinicalWords(c));
  process.stdout.write(JSON.stringify(out));
});
