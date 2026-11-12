/* RSOS player service worker: works offline, never serves a stale version when online.
 * Network first for everything; the cache is only a fallback when there is no connection. */
const CACHE = "rsos-player-v11";
const SHELL = ["player.html", "js/rsx.js", "js/hrs.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png",
  "protocols/override.rsx", "protocols/interrupt_only.rsx", "protocols/swish.rsx", "protocols/legacy_vector.rsx",
  "protocols/paced_breathing.rsx", "data/demo_rr.json", "js/memstack.js",
  "js/ugcl.js", "ugcl/library.json", "ugcl/originals.json", "glyphs.html",
  "js/metrics.js", "js/consent.js", "tiers.html", "metrics.html", "system.html", "data/tier_map.json", "nodes.html", "contribute.html", "js/contribution.js", "js/nodes.js", "js/linx.js", "js/contain.js", "safety.html", "protocols/node_lion.rsx", "protocols/node_observer.rsx",
  "protocols/tier003_command_stack.rsx", "protocols/tier012_breath_anchor.rsx", "protocols/tier014_seal.rsx",
  "protocols/tier016_stillness.rsx", "protocols/tier406_release.rsx", "protocols/tier579_glyph.rsx"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u => c.add(new Request(u, { cache: "reload" })).catch(() => null))))
    .then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(fetch(req).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req.url.split("?")[0], copy)); }
    return res;
  }).catch(() => caches.match(req.url.split("?")[0]).then(r => r || caches.match(req))));
});
