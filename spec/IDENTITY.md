# IDENTITY: identity profiles, level by level

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/identity.py` and `docs/js/identity.js` (identical, tested), page `docs/identity.html`. Simulation results: [`rsso/results/identity.md`](../rsso/results/identity.md). Protocol kit: [`kits/IDENTITY_PROTOCOL_KIT.md`](kits/IDENTITY_PROTOCOL_KIT.md). Roadmap items 5, 11, 23, 24, 25, 34, 35, 37, 39, 51 and 55 (54 is merged into them); claims C16, C17, C41, C61, C62, C82 and C89.

## 1. Why

Anchors (PEAK) work on single states. An identity is a whole stack: what a person is for, who they are, what matters, what they believe, what they can do, what they do, and where. RSOS treats that stack as one object that can be written, played, measured and changed. One symbol carries the whole stack, so a few seconds by day call it up; the whole chain plays at night. Every claim the design records make about identity work becomes a measure the page computes.

## 2. The profile

```
{schema: "rsos-identity/1", id, name, symbol, code, language,
 levels: {mission, identity, values, beliefs, skills, behaviour, environment: {text, image, code}},
 environment: {clothing, scent, music, space}, futures: [...],
 policy: {anchors, max_stage, night_chain}, tree: {center, parts: [{part, context, code}]},
 versions: [...], ratings: [...], contexts: [...], walks: [...], rehearsals: [...]}
```

- **Symbol and login code.** The symbol heads the tree; its vibration code calls the whole profile up.
- **Seven levels**, each with a statement, an image and an optional code of its own. The page checks that every code can be told apart from the others: no two the same, and none that starts like another (the body would not know which one it is until the end).
- **Environment layer** (item 39): clothing, scent, music and the practice space that prime the profile.
- **Language** (item 24): the profile can be practised in its own language. Whether that helps is the TRIAL design `identity_language` (claim C82).
- **Policy** (item 35): which anchors belong to the profile, the highest autonomy stage it allows, and whether the night chain may play.

## 3. Versions (item 37)

`save_version` stores the symbol, code, levels and environment with a date and a note; `diff` lists what changed between any two versions, field by field.

## 4. Measures

| Measure | What the person does | What is computed | Claims |
|---|---|---|---|
| Coherence | Rates each level 0-10: how true it feels now | Mean less the spread across levels; the weakest level | C41 |
| Trend | Rates on ordinary days over weeks | Change in coherence per month with a 95% interval: rising, falling or no clear change | C41 |
| Drift | Also rates right after time with other people | Coherence after mirroring minus baseline, Welch 95% interval: drifts, holds (within one point) or unclear | C89 |
| Generalisation | Logs moments they meant to act: where, trained there or not, did the behaviour start, how fast | Share started in new places against trained places; median seconds to start | C17 |
| Anchor tree walks | Recalls each context from its part of the central image, timed; also from one image | Accuracy and median time per walk; paired differences with intervals | C16 |
| Value-conflict rehearsal | Imagines a situation against a value, RMSSD before, during, after the symbol; also ordinary situations | Change while imagining (a drop of 10% or more is a reaction), recovery after the symbol, the value the body defends most, and how often ordinary situations are flagged | C62 |
| Switching | Logs in by code, by schedule, or interrupts to the base profile, then says when the switch has settled | Switches by kind; median time to settle | C61 |

## 5. Programs

All are RSX programs that compile and play in the player.

- **By day**: the symbol and one sentence, a few seconds.
- **At night**: the symbol, then each level from mission to environment, one per breath. Flagged "Plays while you sleep"; it needs consent to night cueing on the Safety page.
- **Four steps** (item 51): the identity peak, Core Transformation, three future situations, a movement with the code.
- **The prepared week** (item 55): one level a day for seven days with future-pacing, then on day 8 the symbol installed in a light trance with three future situations.
- **Dose** (item 51): 12 short practices a day for 30 days, evenly spread over the waking day, within CONTAIN's limit of 20 plays a day.

## 6. Library (item 34)

Six ready profiles to start from: steady under pressure, focused learner, creative maker, calm parent, athlete at rest, clear speaker. Each is complete and passes the code checks.

## 7. Simulation

`python -m rsso.identity --evaluate` checks every measure on 200 simulated people per row, each with a known answer ([identity.md](../rsso/results/identity.md)):

- coherence rising one point a month is found in 66% of people after 8 weekly ratings and 100% after 26; with no change it is called rising in 2.5 to 3%;
- drift of 1.5 points is found in 100%; stable people are called drifting in 2% and holding in 93.5%;
- a tree with two retrieval paths per context is found faster in 77.5% of people after 6 walks and 99.5% after 12, and recalled better in 79% after 12; with no difference, either is claimed in 3% or fewer;
- a value conflict lowering RMSSD by 18% is detected in 98.5% with a chest strap (0.5% of ordinary situations flagged) and 81% with the phone camera (10.5% flagged).

The simulation shows the measures behave as designed on known answers. It does not show that identity profiles change people; that is the protocol kit's question.

## 8. Limits

- Ratings are self-reports; coherence can rise from expectation alone. The protocol kit compares profiles against a control practice.
- The value-conflict measure uses heart rate variability, not EEG; EEG would be a further channel (item 30).
- Generalisation depends on the person logging moments when the behaviour did not start, as well as when it did.
- The ordered glyph route of item 5 (glyphs walked in ledger order) is not built yet; the anchor tree walk provides the timed recall it would use.
