# Security and safety

RSOS is open software and an open specification, not a regulated medical product. Report security, privacy or safety problems privately to the maintainer (open a GitHub security advisory) rather than in a public issue.

## Safety-relevant behaviour to protect

- **Stopping.** A person must always be able to stop a run at once (Stop button, Esc key, device button). Any change that delays or hides stopping is a safety bug.
- **No silent triggering.** Device-triggered runs require the person's prior opt-in and respect the refractory period and hourly and daily limits (`rsx/rsx/runtime.py`).
- **Intensity limits.** Haptic intensity above a program's `SAFETY haptic_max` must fail to compile, in both the Python and the JavaScript compiler.
- **Scent and taste.** Programs with olfactory or gustatory cues must ask the person to confirm they have no allergy or aversion before use.
- **Shared programs.** RSX programs from other people are code that controls breath, imagery and devices. Read them before running them, and never run one that removes safety limits.

## Privacy

- The protocol player keeps run logs and voice recordings only in the browser on the device; it sends nothing to a server.
- Never commit run logs, voice recordings, physiological recordings or other personal data to this repository.
- Studies that collect data from people need informed consent and appropriate ethical oversight.

## Not for crisis use

The protocol is not a crisis intervention. Anyone at risk of harm should contact local emergency services or a crisis line.
