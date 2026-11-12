# RSOS data contribution — specification

Format `rsos-contribution/1`. Status: built and tested. `rsso/rsso/contribution.py` and `docs/js/contribution.js` build
identical files (same content and SHA-256), and the contribution page is `docs/contribute.html`.

## 1. Purpose

RSOS can already measure a great deal on a single phone. A contribution turns what one person, one clinician or one
lab has measured into evidence that can be pooled:

- which programs, tiers, glyphs, vibration codes and nodes change a state;
- how fast a start becomes a reflex, and for whom;
- what the body and the brain do around each cue.

One file goes from each contributor. The project pools the files and runs the same analysis kit that already runs on
synthetic studies.

## 2. Principles

| Principle | How it is built |
|---|---|
| Consent first, per part | Twelve scopes (§4). Practice runs are required; every other scope is chosen. The file cannot be created without the contributor's agreement. A clinician file also needs the client's consent, and a lab file needs an ethics approval reference. |
| De-identified by construction | No names or e-mail addresses. Ids are random (`p-…` per device, `c-…` per file). Dates become day numbers counted from the first run; only the hour of day and the weekday remain. Age, region and experience are recorded only in broad bands. Protocols the person wrote themselves are reported as `custom`. |
| Own words only when shared | Frames, cue texts, contexts, trigger notes, clinician notes and adverse-event descriptions appear only with the `texts` scope. |
| Health data only when shared | Concerns, conditions and diagnosis codes appear only with the `health` scope. |
| Nothing is uploaded | The page builds the file in the browser. Lab files are fingerprinted (SHA-256), not read or sent. The contributor sends the file to the study team or clinician. |
| Tamper-evident | A SHA-256 checksum over the canonical JSON. `python -m rsso.contribution check` verifies it. |
| Withdrawable | The contribution code (`c-…`) identifies the file, so a contributor can quote it to withdraw. The participant code links one device's contributions over time. |
| One format for all | A person, a clinician and a lab produce the same format, with role-specific sections. Every file pools into one run table. |

## 3. Roles

| Role | Adds | Requires |
|---|---|---|
| `person` | Their own practice, questionnaires, safety events, profile, code check | Their consent |
| `clinician` | Sessions (minutes, nodes used, fidelity, engagement, CGI-S, CGI-I, therapist-led), profession, approaches combined, setting, ICD-11 diagnosis categories (health scope) | The client's informed consent. Runs can be added from the client's memory file. |
| `lab` | Site code, ethics and protocol references, device (kind, channels, sampling rate, montage, reference, impedance, connection), recordings (file SHA-256, BIDS path, program, duration, clock offset, artifact %) | An ethics approval reference |

## 4. Scopes and what each makes possible

| Scope | Contents | What it makes possible |
|---|---|---|
| `runs` (required) | Per run: day, hour, weekday; protocol; program kind and fingerprint; trigger and trigger sense; distress and agency before and after (and their change); start latency; completed or stopped phase; tier; voice; outputs; breath lengths; glyph; vibration code; node mode; planned and actual duration. Also the weekly automaticity checks (SRBAI) and the 20 computed personal metrics. | H1 (one run versus paced breathing), H2 (latency and automaticity over weeks), H5 (device-triggered versus self-started runs), the MEMSTACK reflex curve, time-of-day effects, and comparisons between programs, tiers and glyphs |
| `physiology` | Heart rate and RMSSD before and after each run, with their source (strap or simulated); the node plan's resting baseline | Body change versus felt change; training the stress detector on real people (AUG) |
| `plan` | Node structure: archetype, mode, which senses have cues, number of frames, contexts and rules, frame-check scores and flags, believability, vibration code, glyph; ledger tiers, dose, devices; programmed cues (tier, therapist-led, author, revoked, sound) | H3 (multichannel versus single-channel); which nodes and frames work, so the planner and LINX learn |
| `texts` | The person's own words in every section | Language-level learning about which frames and cues work. This is the most personal scope. |
| `calibration` | Glyph pairwise comparisons, Bradley–Terry scores, chosen glyph and colour | Population glyph preferences across cultures, so glyphs are designed from evidence (UGCL) |
| `recognition` | Vibration-code check: code, options, choice, correct, reaction time, modality | How learnable the vibration alphabet is, and how many codes a wrist can carry (UGCL §7) |
| `outcomes` | Totals with day and rater: PHQ-9, GAD-7, PCL-5, PSS-10, WEMWBS, PGIC, SUDS. Out-of-range totals are dropped. | Clinical change over weeks, alongside practice dose |
| `safety` | Adverse events (day, severity, relatedness, resolved), stopped runs, run count | Setting the safety limits (CONTAIN) from real events |
| `profile` | Age band, gender, handedness, world region, prior practice (meditation, breathwork, hypnosis, NLP, psychotherapy, neurofeedback, martial arts, music: none, some or regular) | Whether results hold across groups; moderators |
| `health` | Concerns of the node plan, self-reported conditions, in therapy, medication change, ICD-11 diagnosis categories | For whom RSOS helps most; confounds such as therapy and medication |
| `clinical` | §3 | How RSOS works inside therapy (THERA) |
| `lab` | §3 | Brain and body signals aligned with every cue: pre-attentive detection (Tiers 589–590) and a body signature for each node |

## 5. File layout

```
schema, contribution_id, participant, role
consent    {version, scopes[], sharing: research|open, contact, agreed}
app        {player, planner, ugcl, platform, vibration}
runs[]     {day, hour, weekday, protocol, program_kind, program_hash, trigger, trigger_channel,
            sud_before, sud_after, sud_change, agency_before, agency_after, agency_change, latency_s,
            completed, stopped_at_phase, tier, voice, outputs, inhale_s, exhale_s, glyph, tacton,
            node_mode, planned_s, duration_s, [hr_before, hr_after, rmssd_before, rmssd_after, hr_source]}
weekly[]   {week, srbai}
metrics    {code: value}              # the personal metrics (spec/TIER_LEDGER.md, metrics.json)
plan, cues, calibration, recognition, outcomes, safety, profile, clinical, lab   # by scope and role
quality    {runs, days_active, span_days, rated_share, with_physiology, weekly_checks}
sha256
```

The player records the run context from version 1.11.0. Older runs keep the 15 original columns, and the
extra fields are simply absent. The player's CSV export carries the new columns too.

## 6. Labs: aligning recordings with cues

`bids_events(timeline)` (Python and JavaScript, identical) writes a BIDS `events.tsv` for any RSX program. It has one
row per timeline event: `onset`, `duration`, `trial_type` (`channel/kind`), `phase` and `value` (tier, vibration
pulse or marker). The page offers it for every built-in program. A recording's `clock_offset_ms` (the RSX timeline's
start minus the recording's start) aligns every cue with the signal. The format follows EEG-BIDS. The recording files
stay with the lab and are matched by their SHA-256.

## 7. Pooling and analysis

```
python -m rsso.contribution check contributions/*.json    # schema and checksum of every file
python -m rsso.contribution pool  contributions/*.json > runs.csv   # one row per run, all contributors
```

`to_runlog(contribution)` turns a file back into run-log rows. MEMSTACK and the metrics run on them unchanged (tested
with a synthetic contributor). The pooled table is the input for the pre-specified analyses (`rsso/rsso/analysis.py`:
H1, H2 and H5).

## 8. What the project needs to decide before collecting

This specification covers the format and the tools. Collecting real data also needs the following, which are the
project owner's decisions:

- who holds the data (the data controller) and where contributions are sent;
- ethics approval for studies that recruit;
- the licence of the open dataset (for example CC0 for the de-identified data);
- a withdrawal procedure that deletes a contribution by its code.

Until then, contributions go only to studies and clinicians who run under their own approvals.

## 9. Next data to add (specified)

- Node body signature: heart rate, HRV and EEG band powers during each node's tier. This lets a node be recognised from the body.
- Cue-level ratings: which sense opened the state, as the player's trigger-sense question already asks per run.
- Real-encounter diaries for H4 and H6: the futures rehearsed against what happened later.
- Device telemetry from the wristband (RDP/1): delivered pulse timing and stop latency on real hardware.
