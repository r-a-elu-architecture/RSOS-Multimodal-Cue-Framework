// Helper for test_copilot.py
const path = require("path");
const C = require(path.join(__dirname, "..", "..", "docs", "js", "copilot.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const sessions = i.seeds.map(x => { const log = C.simSession(x[0], 30, x[1]); return { log, agree: C.agreement(log) }; });
  const ct = C.ctStart("the urge to check the phone"); i.ct.forEach(a => C.ctAnswer(ct, a));
  process.stdout.write(JSON.stringify({ sessions, chains: i.sentences.map(C.chain), levels: C.levelAccuracy(),
    profiles: i.speech.map(([p, t, subj, cons]) => C.profile(p, t, subj, cons)), trig: i.events.map(e => C.contextTrigger(i.triggers, e)),
    cue: C.cueReactivity(i.cue), ct: [ct, C.ctRsx(ct, "..--")], rescript: C.rescriptRsx("the argument at the door", "🦁", "I breathe out and speak slowly"),
    timeline: C.timelineReport(i.timeline), over: [C.overrideMetrics(i.over, 14), C.monthly(i.over)], dol9: C.dol9Rsx(), route: ["fear", "perceptual"].map(C.routeEvent),
    ctx: i.sentences.map(t => C.speechContext(t, i.contexts)), block: C.fourDayBlock("Speak slowly", 3), burst: ["..-", "-. .-", "---"].map(c => C.burst(c)),
    setting: C.SETTING_FACTORS.map(f => C.settingEffect(i.setting, f)), data: { m: C.EXAMPLE_MATRIX, p: C.PLUGINS, t: C.LEVEL_TEST } }));
});
