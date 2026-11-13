# ATLAS: the trigger atlas and the transfer engine

Status: built and tested in simulation; effect unproven in people. Implementation: `rsso/rsso/atlas.py` and `docs/js/atlas.js` (identical, tested), page `docs/atlas.html`. Simulation results: [`rsso/results/atlas.md`](../rsso/results/atlas.md). Protocol kit: [`kits/ATLAS_PROTOCOL_KIT.md`](kits/ATLAS_PROTOCOL_KIT.md). Roadmap items 5 (the glyph route), 57, 58, 59, 60, 61, 63, 65 and 67; claims C92, C93, C94, C95, C99 and C100. Combination X4: map, intervene, remap.

## 1. Why

A state such as stress reaches a person along many paths at once: a sound, a smell, a place, a face, a thought. RSOS treats those paths as a network that can be measured, worked on and measured again. The atlas answers three questions with numbers and intervals: which paths really move this person, does working on one path change the others, and does working from a level above the problem do more than working on the problem itself.

## 2. The atlas

```
{schema: "rsos-atlas/1", id, state,
 nodes: [{id, label, sense}] and combinations [{id, label, sense: "combo", of: [ids]}],
 exposures: [{ts, nodes: [ids], before, after, phase: "map" | "map2" | "after"}],
 treatments: [{ts, node, method}], sweep: [{ts, higher, change}], routes: [{ts, start, length, results}]}
```

Senses: sight, sound, smell, taste, touch, place, thought, symbol, person. An exposure is one sampled moment (ecological momentary assessment): what was present and the state before and a few minutes after (0-10, higher is worse). A moment with nothing in particular present is a control moment.

## 3. Weights

One least-squares fit over the moments of a mapping: each moment's shift (after minus before) is the baseline (control moments) plus a weight for every node present plus an interaction for every combination present. Fitting all nodes together means a node that only appears beside a real trigger is not blamed for it. Each weight has a 95% interval and a verdict:

| Verdict | Rule |
|---|---|
| Trigger | interval above zero |
| Soothing | interval below zero |
| No effect | interval within one point of zero |
| Not clear | otherwise |
| Too few moments | fewer than three |

A weight is **stable** (item 61) when its interval is within one point either side; the page estimates how many moments each node still needs and names the nodes to sample next and any sense not sampled at all.

**Combinations** (item 59): the interaction says whether two nodes trigger only together, more together than apart, less, or simply add up.

**Prediction** (claim C93): each moment's shift is predicted by the map fitted without that moment (exact leave-one-out), and compared with predicting the average. The map "predicts" when its error is at least 10% lower and the correlation at least 0.3.

## 4. Rerouting (item 58, claim C92)

When a trigger with a weight of at least 2 points is present, the strongest anchor with a proven effect (PEAK) is offered or fired, exactly as the autonomy gate allows ([GATE.md](GATE.md)); otherwise nothing plays and the reasons are given.

## 5. The transfer engine (items 60 and 63, claims C94 and C95)

1. **Map** for a week or two (`map`).
2. **Map again** for the same time with no treatment (`map2`). The ratio of the trigger weights between the two mappings is the drift common to all triggers (habituation, season, mood).
3. **Choose the node**: the strongest trigger across the senses, or the best higher node from the sweep.
4. **Treat** it, for example with the network trance on the page, or a timeline session for comparison.
5. **Map a third time** (`after`).

Transfer is the change on the triggers that were never treated, beyond the drift: the mean change with a 95% interval from the fitted standard errors. Verdicts: spreads (interval below zero), stays (interval within half a point of zero), unclear, or no change (the treated node itself changed by less than a point). Without the repeat mapping the result is marked as possibly habituation.

The head-to-head comparison with Time Line Therapy is the TRIAL design `network_vs_timeline` (outcome: calm while picturing an untreated trigger).

## 6. Higher nodes and the level sweep (items 65 and 67, claims C99 and C100)

Ten higher nodes in two dimensions: by abstraction (the words for the feeling, the one who chooses, who you are, what matters, what your life is for) and by scope (the room, the city, the country, the world, all living things), each at levels 1 to 5. After each session the person rates the change in their untreated triggers. Per dimension the shape is: rises, falls, peaks (the best level is in the middle and better than both ends), or no clear shape; and abstraction against scope with an interval. The ten nodes are candidates, not an established hierarchy (C100).

## 7. The descent: a live 3D network trance

The page draws the person's own network in three dimensions (WebGL, no library, offline; drawn in two dimensions where WebGL is missing). Seven guided steps: the whole network, the paths and their strengths, the descent to the strongest node, light from the level above, the node changing, the change travelling along every thread, and the rise to see the whole again. Before and after, the person rates one trigger they will not work on; the session is recorded as a treatment. With reduced motion set, the camera moves in cuts. Stop works at every step.

## 8. The glyph route (item 5)

The original glyphs of the tier ledger in ledger order, as a memory route: the person studies a stretch, then for each glyph chooses the one that follows, timed. The report shows accuracy and time per walk.

## 9. Simulation

`python -m rsso.atlas --evaluate`, 100 simulated people per row with known triggers ([atlas.md](../rsso/results/atlas.md)):

- with ten moments a day, real triggers were found in 83.5% after a week and 98% after two, with 2.6% and 3% of null nodes called triggers; a pair that triggers only together was found in 68% and 86%; the map predicted unseen moments in 93% and 100%; with no real triggers, 1.9% of nodes were called triggers and the map was never said to predict;
- transfer (untreated triggers falling by 40%, every weight fading 15% per mapping): with two-week mappings and the repeat mapping, "spreads" in 67% where it spreads and 7% where it does not; without the repeat mapping, 14% false "spreads";
- the level sweep found the peak in 66% with eight sessions per level (2% false).

The simulation shows the measures behave as designed on known answers. It does not show that the network trance or higher nodes change people; that is the protocol kit's question.

## 10. Limits

- Ratings are self-reports, and noticing a trigger may change it.
- Showing that a change stayed put needs much more data than showing that it spread; with this design a negative result usually reads "unclear".
- The weights describe this person's moments, not nerve pathways (C96).
- Smell sensors that classify odours (item 59) belong to step 8; here smells are noted by the person.
