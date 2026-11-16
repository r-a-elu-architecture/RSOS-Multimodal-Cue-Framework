/* RSOS player service worker: works offline, never serves a stale version when online.
 * Network first for everything; the cache is only a fallback when there is no connection. */
const CACHE = (/\/dev\//.test(self.location.pathname) ? "rsos-dev-" : "rsos-player-") + "v39";
const SHELL = ["js/devmode.js", "player.html", "agents.html", "js/machines.js", "js/pron.js", "data/parts.json", "js/rsx.js", "js/hrs.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png",
  "protocols/override.rsx", "protocols/interrupt_only.rsx", "protocols/swish.rsx", "protocols/legacy_vector.rsx",
  "protocols/paced_breathing.rsx", "protocols/tier013_lion_dragon.rsx", "protocols/ssit_higher.rsx", "protocols/ssit_local.rsx", "protocols/ssit_calm.rsx", "data/demo_rr.json", "js/memstack.js",
  "js/ugcl.js", "ugcl/library.json", "ugcl/originals.json", "glyphs.html",
  "js/metrics.js", "js/consent.js", "tiers.html", "metrics.html", "system.html", "data/tier_map.json", "nodes.html", "contribute.html", "js/contribution.js", "js/nodes.js", "js/linx.js", "js/contain.js", "js/safety.js", "js/outlet.js", "js/voice.js", "js/watchdog.js", "js/guard.js", "js/lineage.js", "js/foldtable.js", "js/profiles.js", "safety.html", "js/thera.js", "js/cm1.js", "js/rdp.js", "device.html", "data/cm1.json", "therapist.html", "roadmap.html", "world.html", "results.html", "data/world_runs.json", "data/results_register.json", "data/roadmap.json", "anchors.html", "js/peak.js", "js/ppg.js", "trials.html", "js/trial.js", "js/checks.js", "js/gate.js", "identity.html", "js/identity.js", "atlas.html", "js/atlas.js", "night.html", "js/night.js", "js/copilot.js", "data/thera.json", "safety.html", "protocols/node_lion.rsx", "protocols/node_observer.rsx",
  "protocols/tier003_command_stack.rsx", "protocols/tier012_breath_anchor.rsx", "protocols/tier014_seal.rsx",
  "protocols/tier016_stillness.rsx", "protocols/tier406_release.rsx", "protocols/tier579_glyph.rsx"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u => c.add(new Request(u, { cache: "reload" })).catch(() => null))))
    .then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k.startsWith(CACHE.replace(/v\d+$/, ""))).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith((async () => {
    try {
      // always ask the server whether the file changed (a cheap 304 when it did not), never a stale browser copy
      const res = await fetch(req, { cache: "no-cache" });
      // keep a copy for offline use (whole, same-origin responses only; never a redirect)
      if (res.ok && res.type === "basic" && !res.redirected) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req.url.split("?")[0], copy)).catch(() => null); }
      return res;
    } catch (err) {
      const hit = (await caches.match(req.url.split("?")[0])) || (await caches.match(req));
      if (hit) return hit;
      if (req.mode === "navigate") return new Response('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline — RSOS</title><body style="background:#151b2f;color:#e7e9f2;font:17px/1.6 system-ui;padding:40px"><h1 style="font-weight:500">This page is not available offline yet</h1><p>Connect to the internet and reload. Pages you have opened once work offline after that.</p><p><a style="color:#f7d995" href="./player.html">Open the player</a></p></body>', { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } });
      return new Response("", { status: 504 });
    }
  })());
});
