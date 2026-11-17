# Stress rating: instructions for a reader (PERSONLAB step 5b)

You read one support conversation. The PERSON's turns are numbered S1, S2, … For **every** numbered PERSON turn, rate how
stressed the person sounds **in that turn**, from 1 to 5:

- 1: calm, settled, relieved or at ease.
- 2: mildly concerned, but steady.
- 3: clearly worried, upset or under pressure.
- 4: very stressed: strong worry, distress or overwhelm.
- 5: extremely stressed: overwhelmed, panicked or unable to cope.

Rules:
1. Rate what the person expresses in that turn. Use earlier turns only to understand it.
2. Short or neutral turns ("ok", "thanks", "yes") get the rating their tone shows. Thanks with relief is usually 1–2.
3. Rate every numbered turn. Do not skip any.
4. Write one JSON object per conversation, `{"S1": 3, "S2": 4, …}`, with whole numbers only.
