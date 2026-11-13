# COPILOT protocol kit: the decision matrix, the copilot and the session tools

A ready protocol for testing the copilot and the tools of [COPILOT.md](../COPILOT.md) with therapists and clients.

## 1. Questions

1. Does a learned decision matrix with a live copilot shorten the therapist's response time and lower their workload, and how well do therapist and copilot agree (C21)?
2. Do sessions using the five-step level chain go better than usual practice (C19)?
3. Does a typology from speech agree with a questionnaire, and does matching it change rapport (C18)?
4. Does cue-reactivity to craving contexts fall over two to six months (C4, C31)?
5. How do override latency, the share of events turned around and OXQ change over months, and does OXQ predict outcomes (C44, C45, C57, C64, C81)?

## 2. Design

- **Copilot (1)**: therapists alternate sessions with and without the copilot visible (randomised order); the transcript is captured live (with consent) or typed by an assistant. Measures per session: response time, a workload scale (for example NASA-TLX), kappa between therapist and copilot.
- **Level chain (2)**: randomised sessions with and without the chain, outcome distress and agency (THERA measures), therapist fidelity rated from recordings.
- **Typology (3)**: 500 or more words of speech per participant (with consent), a validated questionnaire of the same construct, and rapport ratings in sessions with and without matching.
- **Craving (4)**: participants with a craving problem, context triggers set up with them, craving rated at each exposure, 2 to 6 months, alongside usual care.
- **Overrides (5)**: participants log events and overrides daily for three months; outcomes at baseline and the end.

## 3. Measures

| Measure | When |
|---|---|
| Copilot log: lines, copilot branch, therapist branch, times | Each session |
| Workload scale | After each session |
| THERA session measures (distress, agency, CGI) | Each session |
| Speech profile and questionnaire | Once |
| Craving at exposure | Each exposure |
| Override log | Daily |
| Adverse events | Any time (the Safety page) |

## 4. Consent wording (adapt to your ethics board)

> Your therapist may use a computer program that listens to what is said in the session, as text, and suggests which part of a prepared plan fits. It suggests; your therapist decides. If you agree, the words you use may also be counted to describe your style of speaking; this is optional and you can withdraw it. Between sessions you may log moments of fear or craving and how you handled them. The methods are experimental and are not a treatment.

## 5. Data format

The matrix (`rsos-matrix/1`), the copilot log, the override log and the craving log, as the page exports them. Transcripts stay with the clinic; only labels, times and counts are shared. The research contribution format (spec/DATA_CONTRIBUTION.md) can carry these files.

## 6. Analysis

- Question 1: response time and workload, with against without the copilot (mixed model, therapist as a random effect); kappa per therapist.
- Question 2: session outcomes by arm.
- Question 3: kappa between profile and questionnaire; rapport difference with an interval.
- Question 4: `cue_reactivity` per participant, pooled.
- Question 5: monthly series per participant; OXQ against outcome change.

## 7. Report template

1. Therapists, clients, sessions.
2. Copilot agreement, misses and additions; response times and workload.
3. Level-chain sessions against usual practice.
4. Typology agreement and rapport.
5. Cue-reactivity over months.
6. Overrides, latency and OXQ over months.
7. Adverse events and escalations, including perceptual events.
8. What this means for claims C4, C18, C19, C21, C31, C44, C45, C57, C64 and C81.
