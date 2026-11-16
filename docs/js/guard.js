/* Page glue for the Watchdog (spec/WATCHDOG.md §5). Pages call RSOSGuard.ask(action, extra) instead of CONTAIN
 * directly: it reads the saved CONTAIN state, session state and consents, asks RSOSWatchdog, writes the decision to
 * the hash-chained log (rsos.watchdog.log) and to the CONTAIN log the safety page already shows. RSOSGuard.link()
 * applies the CONTAIN-to-session-state link after a CONTAIN review. Browser only; needs contain.js, safety.js and
 * watchdog.js. The page passes the domain's highest guidance level (extra.max_level).
 */
(function (root) {
  "use strict";
  const W = root.RSOSWatchdog, K = root.RSOSContain, S = root.RSOSSafety;
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const set = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };

  function ask(action, extra) {
    const x = extra || {};
    const ctx = { contain: x.contain || get("rsos.contain", K.newState()), safety: get("rsos.safety", null), timeline: x.timeline || null,
      now: Date.now() / 1000, max_level: x.max_level || null, clinician_present: !!x.clinician_present, screening_recorded: !!x.screening_recorded,
      consents: get("rsos.consents", []), plan_protocols: x.plan_protocols === undefined ? null : x.plan_protocols,
      memory_work_allowed: x.memory_work_allowed === undefined ? null : x.memory_work_allowed };   // FIXES_R2 R2-2: every key the Watchdog reads
    const r = W.watch(action, ctx);
    const log = get("rsos.watchdog.log", []);
    W.record(log, action, r, Date.now());
    set("rsos.watchdog.log", W.trim(log));
    const clog = get("rsos.contain.log", []);
    clog.push({ at: Date.now(), action: (action.kind || "") + (action.protocol ? " " + action.protocol : ""), decision: r.decision, reasons: r.reasons.map(t => t.text) });
    set("rsos.contain.log", clog.slice(-200));
    return r;
  }
  function link() {
    const [st, changed] = W.link(get("rsos.contain", K.newState()), get("rsos.safety", null), Date.now() / 1000);
    if (changed) set("rsos.safety", st);
    return changed;
  }
  const VIRTUE = { makoto: "Makoto (honesty)", rei: "Rei (respect)", jin: "Jin (compassion)", gi: "Gi (righteousness)", yu: "Yū (courage)",
    meiyo: "Meiyo (honour)", chugi: "Chūgi (loyalty)", p3: "precept 3", p15: "precept 15" };
  const say = r => r.reasons.map(t => t.text.replace(/\.$/, "") + " [" + (VIRTUE[t.virtue] || t.virtue) + "]").join("; ") + ".";
  root.RSOSGuard = { ask, link, say, VIRTUE, ok: r => r.decision !== "hold" };
})(window);
