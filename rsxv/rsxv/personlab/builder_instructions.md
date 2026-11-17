# Person Lab profile builder: instructions for a reader (PERSONLAB step 3)

You read one support conversation and write the person's identity profile as JSON. Read only the text you are given. Do
not guess beyond it.

## The six levels (bottom to top)
- `environment`: where and when. The surroundings, place, time and conditions the person lives or works in.
- `behaviour`: what they do. Actions, habits, choices and reactions.
- `skills`: how they do it. Abilities, strategies, knowledge, or a lack of them that they name.
- `beliefs`: why. What they believe and value, what they think is allowed or not.
- `identity`: who they are. How they see themselves, and the roles they name ("I am a mother", "I'm not good enough").
- `mission`: for what or whom. Purpose, people or causes beyond themselves.

## What to write
```json
{
  "levels": {
    "<level>": {"statements": [
      {"id": "<short id>", "text": "<first-person statement, short>", "quote": "<exact words from the text>",
       "details": [{"kind": "where|when|detail", "text": "<short>", "quote": "<exact words>"}]}
    ]}
  },
  "current": {"<level>": [{"text": "<how it is now>", "node": "<statement id or null>", "quote": "<exact words>"}]},
  "desired": {"<level>": [{"text": "<how the person wants it to be>", "node": "<statement id or null>", "quote": "<exact words>"}]},
  "signals": [{"kind": "load|conflict|loss|change|other", "text": "<what is happening now>", "quote": "<exact words>"}]
}
```

## Rules
1. Every `quote` is copied **exactly** from the text: same words, same spelling and punctuation. It should be one short
   span (a phrase or a sentence), not a paragraph. Anything that cannot be quoted is left out.
2. Use only what the **person** says, or the SITUATION line. The SUPPORTER's words can help you understand, but they are
   never quoted as the person's profile.
3. A level with nothing in the text stays out. Leaving a level empty is correct; inventing is not.
4. `desired` holds only what the person says they want, hope for or would like. Do not write what you think would help.
5. Keep statements short and in the person's own terms. Use 1 to 4 statements per level at most.
6. Return only the JSON for each conversation, labelled with its id as given.
