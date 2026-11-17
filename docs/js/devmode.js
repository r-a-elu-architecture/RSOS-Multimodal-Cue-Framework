/* Development site mode. The Pages workflow publishes the dev branch under /dev/ next to the live site. On /dev/
 * pages this script (loaded first, in <head>) keeps the development site's saved data apart from the live site's
 * (both share one browser origin): every localStorage key gets the prefix "dev.". It also shows a banner.
 * On the live site (any path without /dev/) it does nothing.
 */
(function () {
  "use strict";
  if (typeof location === "undefined" || !/\/dev\//.test(location.pathname)) return;
  window.RSOS_DEV = true;
  const P = "dev.", S = Storage.prototype, get = S.getItem, set = S.setItem, rem = S.removeItem;
  S.getItem = function (k) { return get.call(this, P + k); };
  S.setItem = function (k, v) { return set.call(this, P + k, v); };
  S.removeItem = function (k) { return rem.call(this, P + k); };
  function banner() {
    if (document.getElementById("rsosDevBanner")) return;
    const b = document.createElement("div");
    b.id = "rsosDevBanner";
    b.setAttribute("role", "note");
    b.style.cssText = "position:sticky;top:0;z-index:9999;background:#7a1f1f;color:#fff;font:600 14px/1.4 system-ui,sans-serif;padding:6px 12px;text-align:center";
    const live = location.pathname.replace(/\/dev\/.*$/, "/");
    b.innerHTML = 'DEVELOPMENT VERSION, not yet released. Its data is kept apart from the live site. <a style="color:#fff;text-decoration:underline" href="' + live + '">Go to the live site</a>';
    document.body.prepend(b);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", banner); else banner();
})();
