# Mnemonic sets

A **mnemonic set** is a list of principles (laws, virtues, habits) that RSOS encodes as glyphs, so that each principle can be recalled as an image, a sound and a bodily response. In a session, a context (detected by the user, a device or an AI) can surface the glyph for a principle; the glyph cues the principle and its trained response.

## Bundled sets (public domain)

| File | Source | Status |
|---|---|---|
| `franklin_13_virtues.json` | Benjamin Franklin, *Autobiography* (written 1771–1790) | Public domain everywhere |
| `bushido_7_virtues.json` | The seven virtues of Bushidō (names only) | Public domain; also the RSIA Spine |

## User-loaded sets

Any other framework can be loaded by the user for personal use, for example Stephen Covey's *The 7 Habits of Highly Effective People* (the Raven archetype's reference set) or Dale Carnegie's *How to Win Friends and Influence People*. These works are protected by copyright (and in Covey's case also by trademark) in at least some countries, so **their text is not included in this repository**. Users supply their own items in the format below.

Note on Carnegie: the original 1936 text entered the public domain on 1 January 2026 in countries using a life-plus-70-years term (Carnegie died in 1955), but remains protected in the United States until 2032, and revised editions remain protected. It is therefore not bundled.

## Format

```json
{
  "id": "franklin_13_virtues",
  "title": "Benjamin Franklin's Thirteen Virtues",
  "source": "Benjamin Franklin, Autobiography",
  "licence": "public-domain",
  "default_archetype": "Lion",
  "items": [
    {
      "n": 1,
      "name": "Temperance",
      "text": "Eat not to dulness; drink not to elevation.",
      "glyph": null,
      "sound": null,
      "anchor": null,
      "target_response": null
    }
  ]
}
```

`glyph`, `sound`, `anchor` and `target_response` are filled in per person during calibration: the image, tone and bodily anchor that work for that individual, and the response the item should trigger.
