// Helper for test_atlas.py
const path = require("path");
const A = require(path.join(__dirname, "..", "..", "docs", "js", "atlas.js"));
let s = ""; process.stdin.on("data", d => (s += d)); process.stdin.on("end", () => {
  const i = JSON.parse(s);
  const out = i.atlases.map(a => ({ weights: A.weights(a), w2: A.weights(a, "map2"), combos: A.combos(a), edges: A.edges(a), readiness: A.readiness(a),
    predict: A.predict(a), choose: A.chooseNode(a), transfer: A.transfer(a, A.chooseNode(a) || "n0"), sweep: A.sweepReport(a), route: A.routeReport(a),
    reroute: A.reroute(a, i.present, i.anchors, i.offers, i.now, {}, i.history, i.consents) }));
  process.stdout.write(JSON.stringify({ atlases: out, demo: A.simDemo(11, 5), route: A.glyphRoute(i.glyphs, 3, 5) }));
});
