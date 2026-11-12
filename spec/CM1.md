# CM1 — the compression layer

Status: built and tested. `rsso/rsso/cm1.py` and `docs/js/cm1.js` give identical signatures, assignments,
suggestions and device bundles (tested). The profiles and patterns are in `docs/data/cm1.json`, written by
`python -m rsso.cm1`. Results on synthetic data are in `rsso/results/cm1.md`.

## 1. Role, as recovered from the archive

The archive (`CM1_Historical_Reconstruction.txt`) describes CM1 as follows:

- **Purpose:** "higher-level symbolic compression", later "pattern distillation and cross-domain transfer" (Universal Compression).
- **Operator:** CompressionRun(CM1).
- **Flow:** post-run compression that feeds MEMSTACK.
- **Interoperability:** works with UGCL for glyph encoding.
- **Gap:** the exact codec is absent.

CM1 compresses in three directions here.

| Archive | Built as |
|---|---|
| Post-run compression feeding MEMSTACK | `signature(runs)`: one person's practice in 13 numbers |
| Pattern distillation | `fit(signatures, K)`, `describe(profile)`: a few response profiles that summarise many people; `patterns(rows)`: what repeats across everyone |
| Cross-domain transfer | `assign`, `suggest`: what is learned from others tells a new person where to start |
| Codec, with UGCL | `pack`, `unpack`: a person's nodes, vibration codes, glyphs, dose and safety state for a device |

## 2. The signature

`signature(runs)` returns `{v: 13 numbers, n: the runs behind each}`:

- **help** for each kind of program (associated node, observer node, Override Protocol, paced breathing, other): the
  mean drop in distress (before − after), shrunk toward 0 by 3 runs. One run with a drop of 6 counts as 1.5.
- **speed** for each starting sense (V, A, K, O, G, thought, memory): the share of runs that started within 3 s,
  shrunk the same way.
- **completion:** the share of runs completed, shrunk toward 0.9.

## 3. Profiles, assignment and where to start

- `fit` runs k-means on the signatures, in units of each number's spread across people (k-means++ seeding with
  a deterministic generator, the best of 10 restarts).
- `describe` puts each profile in plain words, for example "helped most by the observer (nothing binds); a memory
  starts the state fastest", or "often stops runs early: worth a session with a therapist".
- `assign` finds the closest profile. Its confidence is the margin over the second-closest profile, times
  runs ÷ (runs + 10), so it grows with practice.
- `suggest` blends the person's own numbers with their profile's, weighted by their support (n ÷ (n + 5)). It
  recommends:
  - which kind of node or program to start with;
  - which of the five senses should carry the strongest cue;
  - a review with a therapist when runs are often stopped.

The metrics page shows the person's profile and recommendations. The node studio adds them to the plan summary
once 3 rated runs exist.

## 4. Patterns across everyone

`patterns(rows)` groups all rated runs by program kind, starting sense, glyph, vibration code, outputs and time
of day. For each group with at least 20 runs it gives the mean drop in distress with a 95% interval, ranked by
how far the group stands from the overall mean. The metrics page draws them as dots with intervals against the
overall mean.

## 5. The device bundle

`pack(plan, glyph_chars, contain_state)` produces base64 with this layout:

- the header `C1`, the version and the number of nodes;
- for each node: its mode, its original-glyph index (2 bytes), its vibration code (2 bits a symbol: `.` `-` and
  the joining space) and its name (up to 16 bytes);
- the dose;
- the safety envelope: vibration strength, refractory period, and hourly and daily limits;
- a bit mask of nodes paused by CONTAIN, and an escalation flag;
- a Fletcher-16 checksum.

A two-node plan takes 39 bytes. `unpack` rejects a damaged bundle.

## 6. Checked against known answers

A synthetic population has 160 people from 4 true profiles: sound-led, scent-led, observer-helped and struggling.
Each has 30 runs. CM1 is fitted on half of them, and the other half are assigned from only their first 10 runs.
The hard setting puts the profiles twice as close together, makes the fastest sense less consistent and makes
the ratings noisier.

| | Clear | Hard |
|---|---|---|
| Right profile from the first 10 runs | 100% | 96% |
| Right profile from all 30 runs | 100% | 100% |
| Suggests the kind of program that truly helps most (people whose profile has one) | 100% | 97% |

These results show that the method recovers known structure. They do not show that real people fall into these
profiles. When real contributions arrive (spec/DATA_CONTRIBUTION.md), `python -m rsso.contribution pool` gives
the run table, and the same fit, its descriptions and the patterns run on it unchanged.

## 7. Next

- Refit on pooled contributions; choose the number of profiles from the data (held-out likelihood).
- Add body signals (heart rate and HRV change during runs) and frame features (scope, process, believability) to the signature.
- Send the device bundle to the wristband over RDP/1 (MICRO).
