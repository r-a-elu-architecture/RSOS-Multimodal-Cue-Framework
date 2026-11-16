// All archetypes x {stress, depression, ptsd}, built as review/r6/plans.js builds them.
const N = require(process.argv[2]); const out = {};
for (const a of Object.keys(N.ARCHETYPES)) for (const c of ["stress", "depression", "ptsd"]) {
  const extra = c === "depression" ? { therapist_led: true, dx: ["depression"], intake: { concerns: ["depression"] } } : c === "ptsd" ? { therapist_led: true, intake: { concerns: ["ptsd"] } } : {};
  const p = N.plan({ concerns: [c], nodes: [{ archetype: a }], author: c === "ptsd" ? "therapist" : undefined }); p.approved = true; Object.assign(p, extra);
  out[a + "/" + c] = p;
}
process.stdout.write(JSON.stringify(out));
