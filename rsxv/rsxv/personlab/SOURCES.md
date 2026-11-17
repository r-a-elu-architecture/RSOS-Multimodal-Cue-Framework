# Person Lab: candidate data sources (PERSONLAB step 2, 17 November 2026)

Searched under spec/PERSONLAB.md §3. Nothing has been downloaded yet. Licences are as stated on each dataset's card or
release page on 17 November 2026, and must be re-checked at download time.

| Source | Owner | Licence | Access | Size | Content | Later part for validation? | Decision |
|---|---|---|---|---|---|---|---|
| **ESConv** | Tsinghua CoAI | CC BY-NC 4.0 (Hugging Face card `thu-coai/esconv`) | Hugging Face; GitHub `thu-coai/Emotional-Support-Conversation` | About 1,300 conversations | A seeker writes a short situation, then talks with a trained supporter over many turns. A pre-chat survey labels problem, emotion and intensity (1–5) | **Yes**: the seeker's later turns, and a post-chat intensity for most conversations | **Usable: primary.** It is the only source with a measured before and after |
| **Hippocorpus** | Microsoft Research | Open Use of Data Agreement v1.0 | Microsoft download page; Hugging Face `hippocorpus` | 6,854 stories | First-person, diary-like stories of life events, plus imagined versions by other writers | **Yes**: the same writer retold the story 3–6 months later | **Usable: secondary.** Rich identity and environment content. The retelling tests whether a profile holds over time |
| **EmpatheticDialogues** | Meta AI | CC BY-NC 4.0 | Hugging Face `facebook/empathetic_dialogues` | About 25,000 conversations | A person describes a situation tied to a feeling, then has a short conversation | Partly: a few later turns | **Usable: tertiary.** Short; good for testing the builder at scale |
| counsel-chat | N. Bertagnolli | Unclear: derived copies state MIT or OpenRAIL, the original repository was not confirmed | GitHub `nbertagnolli/counsel-chat` | About 3,000 questions | One question, with answers from counsellors | **No**: a single message per person | **Not usable** (no later part; licence unclear) |
| MentalChat16K | ShenLab | MIT | Hugging Face | About 16,000 pairs | Partly synthetic question–answer pairs, plus interview material | No reliable later part; partly synthetic | **Not usable** (synthetic content cannot ground a real-story profile) |

## Notes
- **Non-commercial licences.** ESConv and EmpatheticDialogues are CC BY-NC 4.0: research use is fine, and anything derived
  from them is shared only for non-commercial research, with attribution.
- **Sensitive topics.** ESConv covers personal difficulties. Its profiles stay private, as spec §4 requires. The public
  repo gets the schema, code, aggregates and invented illustrative profiles only.
- **Crowdworkers, not patients.** All three usable sources were written by paid crowdworkers about real or recalled events.
  That is stated wherever the lab's results are shown.
- **Proposed plan for steps 3–5.** Build the first 100 profiles from ESConv, holding out each conversation's second half
  and post-chat intensity for validation. Add Hippocorpus profiles to test whether a profile built from a story predicts
  the same writer's retelling.
