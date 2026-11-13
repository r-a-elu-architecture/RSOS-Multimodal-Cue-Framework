# CHECKS: built-in cognitive tests

Status: built and tested; scoring identical in Python and the browser. Implementation: `rsso/rsso/checks.py` and `docs/js/checks.js`, page `docs/trials.html`. Roadmap item 48.

Research measures, not diagnostic tests. Scores vary with sleep, time of day and practice, so a person is compared with themselves over time, and practice effects are expected in the first sessions.

| Task | What it measures | How it runs | Scores |
|---|---|---|---|
| n-back (2-back) | Working memory | 24 letters, one every 2.5 s; tap when a letter matches the one two back (8 targets) | Hits, false alarms, accuracy, d′ (signal detection, log-linear correction), mean reaction time on hits |
| Digit span | Short-term memory | Digits shown one a second, then typed back; starts at 3, two tries per length, ends after two misses at one length | Longest correct length, correct trials |
| Reaction time | Alertness and speed | 15 trials with random waits of 1.5-4 s; tap when the circle lights. A pressure version adds a visible countdown and an error tone | Median and mean, standard deviation, lapses (over 500 ms), anticipations (under 150 ms), misses |
| Word recall | Episodic memory | 12 words shown for 30 s, a 30-second distraction, then type all you remember | Correct, intrusions, repeats, percent |
| Reading | Reading speed and comprehension | A short passage, then three questions | Words per minute, comprehension, effective words per minute |
| Attention to threat (dot-probe) | Whether attention is pulled toward threatening words | 32 trials: a threat word and a neutral word, then a dot where one of them was; tap the dot's side | Mean reaction time when the dot replaces the threat word and when it replaces the neutral word; bias (positive: attention drawn to threat) |

Sequences come from a seeded generator, so a session can be repeated exactly and compared across people. Each result is stored with its date. In trials, a task can be the outcome: for example the reading task as the "untrained activity" in the SSIT design.

The reading passages and word lists are original to RSOS. Threat words are mild (for example "failure", "reject", "danger").
