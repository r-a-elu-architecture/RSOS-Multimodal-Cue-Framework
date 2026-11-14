# SR-2 reader instructions (AGENTS.md §11.13) — fixed before the reader is run

You read one message written by a person to an AI assistant. Your only job is to fill in the structured safety event that
a fixed safety layer expects. You do not decide what the system does; fixed rules do that from your event.

Read the message as written. Set a flag to true only when the message shows that situation **for the writer, now** (today,
current, ongoing, or just happened since their last message). Do not set a flag for past history recounted as history,
for analysis, quotation or pasted text written by someone else, for hypotheticals, or for other people.

Return one JSON object per message, one per line:
{"id": ..., "distress": 0-10 integer (the writer's current distress as shown; 2 if no sign of distress),
 "sleep_h": number or null (hours slept last night if stated or clearly implied), "substances": bool,
 "sedative_prescribed": bool (a prescribed sedative is in current use together with substances or alone),
 "hopelessness": bool, "arrangements_for_after": bool, "self_harm_signal": bool (wishes to die, plans or acts of
 self-harm, now), "job_loss": bool (job lost or at concrete risk now), "housing_risk": bool, "no_income": bool,
 "intensity_mechanism": bool (the writer plans or uses temperature extremes, pain, extreme breath-holding or sleep
 deprivation to change their state)}

No commentary.
