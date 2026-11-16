# FIXES_R3 — structural fixes after the third independent review

Status: registered 2026-11-16, before code. Review: branch `review/r3`, commit 15256fa (reviewed dev at 14d096c).
Three rounds of review found the same pattern: each page had to remember to ask the Watchdog, a program's level came
from labels pages attach, and a local PIN was presented as more than it can be. This pass changes the structure.

## 1. One gate at the output (`docs/js/outlet.js`)

Loaded first on every page (after devmode). It wraps every channel that reaches the person:

| Channel | Wrapped | Always allowed |
|---|---|---|
| Sound (tones, recordings, synthesis) | `AudioNode.connect` to a context's destination: without an allowed session the node is routed to a silent gain | — |
| Recorded audio | `HTMLMediaElement.play` (unmuted elements) | muted elements (camera for heart-rate) |
| Speech | `speechSynthesis.speak` | `speechSynthesis.cancel` |
| Vibration | `navigator.vibrate` | `vibrate(0)` and `vibrate([])` (stop) |
| Wristband | the RDP send (`docs/js/rdp.js`) for play commands | stop, status and handshake commands |

An output goes through only inside an **allowed session**:

- `RSOSOutlet.open(action, extra, {confirmed, seconds})` asks the Watchdog (through the guard, logged). Hold: no
  session. Ask: a session only when `confirmed` (the person pressed the button). Sessions expire (default 15 minutes)
  and close on stop.
- A page may declare its default action (`<body data-outlet-kind=... data-outlet-protocol=...>`). On the first output
  without an open session, the outlet opens that page session on demand (self-triggered actions count as confirmed:
  outputs follow the person's click; device- or agent-triggered declarations do not).
- At **every output** the outlet re-runs the Watchdog for the session's action against the current saved state
  (without logging). If the decision is now hold, the output is refused and the session closes. A change of session
  state or domain therefore stops output on every page, including open trial and player views.
- A refused output is logged once per session in the guard's log as `hold outlet`.
- Pages no longer compute the domain context: `profiles.js` publishes `window.RSOSDomain` = `{max_level,
  memory_work_allowed, clinical_vocab}`; the guard reads it. (The PROFILES P4 rule stands: no engine module reads
  profiles.)

## 2. Level from content

`level_of_program(source, {cues, edited})` (Watchdog, Python and JavaScript) returns `{therapist_led, memory_work}`:

- clinician-led when the source names a clinician tier (414, 420, 439, 440) in its PROTOCOL id or a `Tier NNN`
  comment; when a programmed cue in it (`MARK "programmed:<id>"`) has a clinician tier in its consent record; or when
  it carries `# rsos-level: clinician_led` (written by the therapist page for therapist-led THERA programs);
- memory work when it carries `# rsos-memory: yes`;
- for **edited** text (differs from its built-in or generated source): any observer mode (`MODE "observer"`) makes it
  clinician-led memory work (conservative: copying an observer node into another program cannot lower its level).

The player unites this with the plan flags. A plan with the difficult-memories concern marks **every** node as memory
work (not only observer nodes). Program text (SAY, SEE, FEEL, GESTURE, WORD, FRAME strings) is passed to the Watchdog,
so Spine wording flags apply to programs and cues.

## 3. Clinician control: honest

- A PIN can be set only outside the clinician-led protocol; "Record result" never sets one. With no PIN, there is no
  way out of the clinician-led protocol on the device; the page says to contact the responsible clinician.
- The specs and the Safety page say plainly: on a person's own device, clinician-led control is **advisory** (a record,
  a prompt and a default block); clearing browser data resets it; whoever sets the PIN first holds it. Enforced
  clinician control needs a clinician-held device or a server (a later step).
- The `pin_set_older_state` path and value are removed.

## 4. Smaller fixes

| ID | Finding | Fix |
|---|---|---|
| R3-a | Lion and Dragon codes overlap | The two codes play in separate phases with a 1 s pause; test: compiled haptic events of the two codes do not overlap and are at least 600 ms apart. |
| R3-b | A therapist session resumes without a re-check | Resuming an open session asks the Watchdog again; a hold ends the session view with the reason. |
| R3-c | Python/JS differ on malformed saved state in `observe` and `link` | A state without a known mode counts as a new state, both languages. |
| R3-d | Night page shows memory items in Workplace | The per-code "painful memory" column is memory work (hidden in Workplace). |
| R3-e | The safety log styles hold like any decision | Hold rows are marked. |
| R3-f | CONTAIN §9 not marked where §10 replaces it | A note in §9 (in this registration commit). |
| R3-g | Records | The results commit 14d096c edited a registered row (FIXES_R1 W-6); `pages.yml` exists only on `dev` and reaches `main` at a merge; trial sessions are held in Stabilisation even when nothing plays (by design: a trial is practice); sham blinding is nominal (the person can feel the difference over time); the header link "Therapist" stays (navigation label) and is excluded from wording checks. |

## 5. Acceptance

- G1 Every review-3 scenario reproduced in a browser test (`scripts/check_outlet.py`) fails on 14d096c and passes
  after the fix: leaving the protocol via Record result; a tier-414 cue run in Personal and Workplace; Device page code
  sends in the clinician-led protocol; Anchors capture, probe and chain in the clinician-led protocol; an observer node
  pasted into another program in Workplace; dangerous wording in an edited program; a therapist session resumed after a
  domain change; a player or trial view left open while the state changes.
- G2 Structural: in a browser, with no session, every wrapped channel is silent on every page (vibrate returns false,
  speech does not start, audio reaches only a silent gain, the RDP play command is not sent), and stop calls still
  work. Every page that produces output either declares its action or opens sessions; a test lists output call sites
  per page and checks each page is covered.
- G3 `level_of_program` identical in Python and JavaScript; built-in programs have no Spine flags and keep their levels.
- G4 All suites and browser checks pass; no threshold changes.
