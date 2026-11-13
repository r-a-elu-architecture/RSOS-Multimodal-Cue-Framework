// Helper for test_night.py
const path = require("path");
const N = require(path.join(__dirname, "..", "..", "docs", "js", "night.js"));
const P = require(path.join(__dirname, "..", "..", "docs", "js", "peak.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const nights = i.seeds.map(([seed, kind, poor]) => {
    const sl = new N.Sleeper(seed, 8, 1, poor ? { W: 0.8, N1: 0.3, N2: 0.65, N3: 0.6, REM: 0.6 } : null, 1);
    const plan = N.makePlan(i.codes, ["vibration", "light"], seed % 2 ? "wake" : "safety");
    const run = sl.run(kind === "none" ? null : new N.Controller(plan, kind));
    return { run, nm: N.nightmareResponse(plan, sl) };
  });
  const rng = new P.Rng(77), moves = [];
  for (let k = 0; k < 12; k++) moves.push(N.detectMoves(N.simMove(rng, k % 2 === 0)));
  const st = N.rewardState("hoops", N.family("-.", 3)[0]); i.events.forEach(e => N.onEvent(st, e));
  process.stdout.write(JSON.stringify({ nights, plan: N.makePlan(i.codes), tmr: N.tmrAnalyze(i.tmr), diary: [N.diaryCompare(i.diary), N.diaryCompare(i.diary, "distress")],
    fam: [N.family("-.", 5), N.familiesOk(i.areas)], reward: [st.log, N.rewardReport(st)], moves, template: N.template(), notice: N.noticeReport(i.notice) }));
});
