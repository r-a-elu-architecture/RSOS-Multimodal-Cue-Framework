"""The RSOS roadmap: one source for the findings, the build plan and the claims register.

Run `python3 architecture/roadmap.py` to write:
  spec/ROADMAP.md        the findings, items, combinations, build order, lineage hypotheses
  spec/CLAIMS.md         the claims register C1-C101, each with the test it becomes
  docs/data/roadmap.json the same data for the Roadmap page (docs/roadmap.html)

The findings come from a review of the RSOS design records (2023-2025), indexed by
record (R01-R43) and by later design notes. Claims are recorded as claim events with the
test each becomes: nothing is discarded, nothing is treated as established.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    # id, order, title, what the site gains
    (9, 1, "Roadmap and records", "Roadmap page: status map of every item and a searchable claims register"),
    (1, 2, "PEAK and the anchor object", "Anchors page: an anchor card per anchor with glyph, code, colour and a live strength curve"),
    (2, 3, "TRIAL and CHECKS", "Trials page: personal before-and-after comparisons with intervals, and short cognitive tests"),
    (3, 4, "The autonomy gate", "Safety page: a row of locks, one per anchor, showing what each still needs"),
    (4, 5, "IDENTITY profiles", "Identity page: the level tree from the symbol down to environment"),
    (5, 6, "ATLAS and the transfer engine", "Atlas page: a 2D living network with a demo map; a live 3D guided descent for the network trance"),
    (6, 7, "SLEEP and REWARD in simulation", "Night and reward page: a sleep timeline and a reward timeline"),
    (7, 8, "LINX and THERA extensions", "Therapist page: the decision matrix as an anchor tree, with the copilot highlighting matches"),
    (8, 9, "Machines and channels", "Devices page extended; Agents page with a person's and an agent's profiles side by side"),
    (0, 10, "Later: lineage of the design", "Lineage results from the full design records"),
]

# id, title, kind, module, step, status, source, summary
ITEMS = [
    (1, "Peak-state anchoring with probe trials", "new", "PEAK", 1, "built in simulation", "R08–R20, 2025-04",
     "A state's own vibration code is played at a measured peak (self-tap, HRV rise, Duchenne smile, EEG); cue-alone probe trials test whether the anchor really shifts the body."),
    (2, "Closed-loop sleep cueing", "new", "SLEEP", 6, "built in simulation", "R10–R16, R25, R31, 2025-04/05",
     "Cues only in deep sleep, below waking level, stopping on arousal, with a nightly limit; the day's code replayed with light and an earbud voice; trauma gets a safety code or waking by default."),
    (3, "External success events and a reward code", "new", "REWARD", 6, "built in simulation", "R12, 2025-04-10",
     "An outside sensor reports a success (a ball through the rim, a correct answer) and a reward code plays within a fraction of a second; it can be replayed at night."),
    (4, "Cue wear-out from overuse", "new", "MEMSTACK, CONTAIN", 3, "built in simulation", "R18, 2025-04-11",
     "Every appearance of a cue outside training is counted, its loss of strength modelled, and CONTAIN warns before a cue stops working."),
    (5, "Generalisation score and an ordered glyph route", "extension", "MEMSTACK, UGCL", 4, "built in simulation", "R02–R07, 2023",
     "Does a reaction start in many real contexts, not only the trained one; glyphs walked in ledger order as a memory route."),
    (6, "A code family per learning area", "extension", "UGCL", 6, "built in simulation", "R11, 2025-04-10",
     "Each learning area gets its own family of vibration codes, marked by a code prefix."),
    (7, "Phase codes in a sequence", "extension", "RSX", 1, "built in simulation", "R16, 2025-04-10",
     "Each phase of a program announces itself with its own code."),
    (8, "Craving protocol and app or place triggers", "extension", "THERA, LINX", 7, "built in simulation", "R10, 2025-04-10",
     "A craving protocol, triggered by context such as a gambling app opening or arriving at a venue."),
    (9, "Temperature and posture channels", "new channel", "Devices", 8, "idea", "R17, 2025-04-11",
     "A wrist cooling device and a motion sensor for posture as cue channels."),
    (10, "Pronunciation feedback from the camera", "adjacent", "Devices", 8, "idea", "R19–R20, 2025-04-12",
     "Face and lip tracking compared with a native template; moving the muscles to match is kept as a specification only."),
    (11, "Anchor tree with attachment points", "extension", "UGCL, nodes", 4, "built in simulation", "R21, R27, 2025-04",
     "A central image with three context images fixed to its parts, each with its own code; a guided recall walk with recall timed per part."),
    (12, "Typology chains from speech, as plug-ins", "new", "TYPES", 7, "built in simulation", "R22, R28, R37, 2025-04/05",
     "Trait lexicons per type build a profile over a conversation; typologies are plug-ins; profiling another person needs consent."),
    (13, "The five-step level operator chain", "new", "LINX, THERA", 7, "built in simulation", "R23, 2025-04-20",
     "Detect, analyse, modify, output, future-pace; a classifier for which level a sentence comes from (environment to purpose); every change passes the LINX router and CONTAIN."),
    (14, "Therapist decision matrix and copilot", "new", "THERA", 7, "built in simulation", "R24, 2025-04-20",
     "A central meaning with three trigger cues and three responses; the therapist memorises it, the copilot runs it on a live transcript, and agreement is measured."),
    (15, "Display output: AR glasses and the lock screen", "new channel", "Devices", 8, "idea", "R25, 2025-04-23",
     "A state image conditioned at peaks and shown on a trigger, in smart glasses or on the phone's lock screen."),
    (16, "Four-day block, voice-recognised contexts, timed burst", "extension", "RSX, LINX", 7, "built in simulation", "R26, 2025-04-23 (record truncated)",
     "A four-day acquisition block per principle; entering a real context recognised from speech or sound fires the code; a timed vibration burst."),
    (17, "Re-living an event with a symbol and light", "extension", "Player, THERA", 7, "built in simulation", "R28, 2025-04-27",
     "After an event, replay it in imagination with the symbol and radiant light and rehearse the new behaviour (imagery rescripting), timed and measured."),
    (18, "Light together with vibration", "merged", "SLEEP", 6, "merged into 2", "R14, R29, 2025-04/05",
     "Light comes on with the vibration so the cue is noticed more."),
    (19, "Content packs for any rule set", "new", "UGCL", 8, "idea", "R21 (assistant suggestion), 2025-04-19",
     "The anchor tree as a format: any rule set, value system or skill becomes a pack."),
    (20, "Core Transformation protocol", "new", "THERA, LINX", 7, "built in simulation", "R30, 2025-05-06",
     "The outcome chain from an unwanted state to a core state, asked one question at a time, with a code for the core state."),
    (21, "The anchor triplet", "merged", "PEAK", 1, "built in simulation", "R31, R34, 2025-05",
     "One anchor carries a vibration, a scent and a light; one scent per state; the same anchor always means the same state."),
    (22, "Anchor chain program type", "new", "RSX, PEAK", 1, "built in simulation", "R32, 2025-05-18",
     "Anchors with roles played in sequence (healing, stability, redirection, action), each phase with its own check that it worked."),
    (23, "Identity profiles, level by level", "new", "IDENTITY", 4, "built in simulation", "R33–R35, 2025-05",
     "A symbol heads a tree of mission, identity, values, beliefs, skills, behaviour and environment, each level with an image and a code; the symbol by day, the whole chain at night."),
    (24, "A language for each identity", "new", "IDENTITY, LINX", 4, "built in simulation", "R34, 2025-05-22",
     "Each identity learned and recalled in its own language, as a context switch between identities."),
    (25, "Rehearsing a value conflict", "new", "THERA", 4, "built in simulation", "R33, 2025-05-21",
     "Imagine a situation that violates a value; the body's reaction is measured and the value's anchor brings it back; future-pace the new choice."),
    (26, "Staged autonomy gate", "new", "CONTAIN", 3, "built in simulation", "R32, R34, 2025-05",
     "Manual training, then automatic detection, then overload conditioning, then default; an anchor may fire on its own only after it has earned it."),
    (27, "Vibration at the peak of the inhale", "extension", "Player", 1, "mostly built", "R34, 2025-05-22",
     "Breathing the symbol into the chest with a posture change; the code fires at the peak of the inhale."),
    (28, "Peak vibration in sport via a motion sensor", "extension", "REWARD", 6, "built in simulation", "R33, 2025-05-21",
     "A motion sensor detects a successful move and fires the reward code."),
    (29, "Carrier frequency for vibration", "extension", "Devices", 8, "idea", "R31, 2025-05-18",
     "Vibration settings that take a carrier frequency, to test whether a frequency shifts EEG at that frequency."),
    (30, "Prior-art file", "new", "Repository", 9, "idea", "R34, 2025-05-22",
     "Existing products and research, kept current and linked from every novelty claim."),
    (31, "Book outline", "new", "Publication", 0, "idea", "R34 and design records, 2025-05",
     "A book on identity architecture, written after the prototype has data."),
    (32, "Glossary and foundations files", "extension", "Specs", 9, "partly built", "Design records, 2025-05",
     "Every term defined precisely; each module linked to the research it builds on."),
    (33, "Personal randomised experiments, pooled", "new", "TRIAL", 2, "built in simulation", "Design records, 2025-05",
     "Single-case designs: conditions chosen at random (cue or none, real or sham anchor, automatic or manual), each person's effect with an interval, pooled across people."),
    (34, "The platform's identity library", "extension", "Site", 4, "built in simulation", "Design records, 2025-05",
     "Device blueprints, ritual templates and a sequence builder exist; the identity library is missing."),
    (35, "Identities as user profiles", "new", "IDENTITY", 4, "built in simulation", "Design records, 2025-05",
     "An implant is the BIOS, the architecture is the operating system, an identity is a user profile: a login code, a global interrupt, policies per profile, timed switching."),
    (36, "A layer that works on any hardware", "new", "Device protocol", 8, "idea", "Design records, 2025-05",
     "Programs, anchors and profiles sit above the hardware; an implant device class is written as a specification only."),
    (37, "Versioned profiles", "extension", "MEMSTACK", 4, "built in simulation", "Design records, 2025-05",
     "As values change, the profile changes, with a record of what changed between versions."),
    (38, "Anchors on parts of the body", "extension", "UGCL, Devices", 8, "idea", "Design records, 2025-05",
     "Attachment points placed on the body; vibration motors at several places."),
    (39, "An environment layer for each profile", "extension", "IDENTITY, LINX", 4, "built in simulation", "R33, 2025-05-21",
     "Clothing, scent, music and the practice space prime a profile, as contexts and triggers."),
    (40, "Recovery and override metrics", "extension", "Metrics", 7, "built in simulation", "Design records, 2025-05",
     "Overrides per day, the share of fear events turned around, reaction time under stress, memory under fatigue."),
    (41, "Perceptual-event triggers", "new", "LINX, CONTAIN", 7, "built in simulation", "Design records, 2025-05",
     "Unusual perceptual states as a trigger type, always routed through CONTAIN's escalation path."),
    (42, "An identity layer for AI agents and robots", "new", "IDENTITY, LINX, CONTAIN", 8, "idea", "Design records, 2025-05",
     "An agent loads a profile, simulates an action against its values before acting, overrides on a conflict and logs whether each action matched its values; CONTAIN enforces it."),
    (43, "People and machines signalling through glyphs", "new", "UGCL, Devices", 8, "idea", "Design records, 2025-05",
     "An agent reports its state as a glyph's code on the wristband; the person replies with a code."),
    (44, "Human error and stress signals feeding the agent", "new", "AUG, LINX", 8, "idea", "Design records, 2025-05",
     "A person's error-related or stress signal sharpens the agent's conflict detector."),
    (45, "Behaviour-consistency test", "new", "TRIAL", 2, "built in simulation", "Design records, 2025-05",
     "How consistent an agent's behaviour is with a profile and without one."),
    (46, "Provenance of names, manifesto and briefs", "new", "Review package", 9, "idea", "Design records, 2025-05",
     "Every name kept with who coined it; one-page briefs for scientists, therapists and other audiences."),
    (47, "Life-timeline memory protocol", "new", "THERA", 7, "built in simulation", "Design records, 2025-05",
     "Scattered life events mapped into ordered nodes with glyphs (memory specificity training)."),
    (48, "Built-in cognitive tests", "new", "CHECKS", 2, "built in simulation", "Design records, 2025-05",
     "n-back, digit span, reaction time under stress, event recall, reading and threat-attention bias, dated over time."),
    (49, "Lifestyle factors as background data", "extension", "TRIAL", 2, "built in simulation", "Design records, 2025-05",
     "Nutrition, cold exposure and similar factors logged as covariates in personal trials, not as advice."),
    (50, "DOL-9, the daily override loop, and OXQ", "extension", "RSX, Metrics", 7, "built in simulation", "Design records, 2025-05",
     "A precise 90-second loop (breath 4-2-6, posture, phrase, gesture, 5-15 s action) as an RSX program; OXQ = overrides / waking hours x 100."),
    (51, "Four-step sequence, layers in another language, a month's dose", "extension", "IDENTITY, RSX", 4, "built in simulation", "R35, 2025-05-27",
     "On a negative state: identity peak, Core Transformation, future-pacing, movement-peak vibrations; six layers practised in another language; 12 a day for a month."),
    (52, "Trial: Core Transformation first or identity first", "new", "TRIAL", 2, "built in simulation", "R35, 2025-05-27",
     "The order question settled by a randomised crossover."),
    (53, "Four orders as trial arms", "extension", "TRIAL", 2, "built in simulation", "R35 answer, R36, 2025-05-27",
     "The three-phase hybrid, Core Transformation first in each cycle, the identity peak first, and identity fully first."),
    (54, "Typology network and mirroring drift", "merged", "TYPES, IDENTITY", 4, "merged into 12 and 14", "R37, 2025-05-27",
     "Type image, common phrases, responses; does mirroring others pull a person away from their own profile."),
    (55, "A prepared identity week for clients", "new", "THERA, RSX", 4, "built in simulation", "R38, 2025-05-28",
     "One level a day for seven days with future-pacing, then the symbol installed in trance and three future situations."),
    (56, "Dual-use governance", "new", "CONTAIN", 3, "built in simulation", "R38, 2025-05-28",
     "A consent record for any profiling, an audit log, and a visible flag on anything that works below awareness."),
    (57, "Trigger atlas", "new", "ATLAS", 5, "built in simulation", "R39, 2025-07-03",
     "A week of mapping which objects, sounds, smells, places and thoughts shift state, as a weighted graph with baselines, repeats, controls and statistics on each link."),
    (58, "Real-time rerouting", "extension", "ATLAS, PEAK, CONTAIN", 5, "built in simulation", "R40, 2025-07-03",
     "When a high-weight trigger appears, the good-state anchor fires as vibration and scent, through the gate."),
    (59, "Smell sensor and combined trigger nodes", "new", "Devices, ATLAS", 5, "mostly built", "R41, 2025-07-03",
     "Gas sensors that classify smells; a sound with one object may trigger a state while the same sound with another may not, so the graph models combinations."),
    (60, "Network trance with a transfer test", "new", "THERA", 5, "built in simulation", "R42, 2025-07-04",
     "Every way one feeling arrives across the senses; in trance, transform the biggest node and watch the change spread; reactivity on untreated nodes is the test; compared with Time Line Therapy."),
    (61, "Whole-day sampling and map readiness", "extension", "ATLAS", 5, "built in simulation", "R43, 2025-07-04",
     "Smells, tastes, thoughts, symbols, objects and feelings sampled across the day; how many exposures each node needs before its weight is stable."),
    (62, "Genealogy timeline in four eras", "new", "LIA", 0, "idea", "Record review",
     "2023 mnemonic images; April 2025 EEG, vibration and senses; May 2025 identity trees and sequences; July 2025 the atlas and the network trance."),
    (63, "The transfer engine", "new", "THERA, ATLAS, IDENTITY", 5, "built in simulation", "Later review (SSIT)",
     "Choose the node to work on by weight (across the senses) or by level (above the problem), then measure transfer to nodes never treated."),
    (64, "SSIT three-arm trial", "new", "TRIAL, CHECKS", 2, "built in simulation", "Later review (SSIT)",
     "Imagery about the activity, imagery about a higher node flowing down, and general calming imagery; transfer to untrained activities as the outcome."),
    (65, "Library of higher nodes and a level sweep", "new", "IDENTITY, CM1", 5, "built in simulation", "Later review (SSIT)",
     "Ten candidate nodes above language; does transfer rise, peak or fall as the node gets more abstract, per person."),
    (66, "Anchor contamination and restoration", "new", "PEAK, MEMSTACK, CONTAIN", 1, "built in simulation", "Framework design, 2026",
     "An anchor used during an ongoing stressor can take on the stress; detect when its effect turns negative and restore it by pairing with a higher-order resource."),
    (67, "Two kinds of higher: abstraction and scope", "extension", "THERA, ATLAS", 5, "built in simulation", "Framework design, 2026",
     "Higher by abstraction (language, agency, identity) and higher by scope (a city, a country), tested side by side."),
    (68, "A two-symbol anchor", "extension", "UGCL, PEAK", 1, "built in simulation", "Framework design, 2026",
     "Two symbols held together as one anchor, the same form as the Tier 013 composite."),
    (69, "A setting that prepares the state", "extension", "THERA, TRIAL", 7, "built in simulation", "Framework design, 2026",
     "Warmth, music and imagery logged with each session so personal trials can show whether the setting matters."),
]

COMBINATIONS = [
    ("X1", "Anchors you can program and measure", [1, 21, 22, 66, 68],
     "Anchors are captured at a measured peak, composed into chains, tested with probes, checked for contamination and restored."),
    ("X2", "One conditioning loop around the clock", [1, 2, 3, 4, 33],
     "Anchoring by day, firing on triggers, reactivation at night, wear-out monitoring and personal trials."),
    ("X3", "A device that limits its own autonomy", [26, 1, 4],
     "It earns the right to act by itself, one anchor at a time."),
    ("X4", "Map, intervene, remap", [57, 58, 60, 61, 63],
     "The session is written from a person's own trigger graph, and the change in that graph is the outcome."),
    ("X5", "One program, two executors", [14, 11],
     "The therapist memorises the matrix and the copilot runs it; the system measures where they agree and differ."),
    ("X6", "One format for people and machines", [42, 43, 44, 23],
     "The same value tree gates an agent's actions and builds a person's identity."),
    ("X7", "One lineage engine for the design records and for a person", [57, 62],
     "The trigger atlas has the same graph structure as the genealogy of the design records: the same operators on two different materials."),
]

HYPOTHESES = [
    ("H-a", "A central node spreads its change, and this held across every form",
     "2023 central image; the anchor tree; the network trance; SSIT. Product-side test in step 5 (transfer to untreated nodes)."),
    ("H-b", "Setbacks come before structural leaps",
     "A collapse, then the device architecture; discouragement, then the operating-system analogy."),
    ("H-c", "A probe becomes a rule, then default behaviour",
     "A challenge to an unsupported claim (May 2025), then a standing rule against exceptionalism in prompts (July 2025), then calibrated assistants and this claims register."),
    ("H-d", "A class of claims with numbers but no data",
     "Scores, ranks, thresholds and timelines given without measurement; count them and trace what each set off."),
    ("H-e", "Re-entry events",
     "Assistant text reused as the seed of a later design record (records 17, 34, 38)."),
    ("H-f", "The lion and dragon thread",
     "An emoji row in 2025 records, then Tier 013 (🦁 + 🐉), the lion and the dragon held as one composite."),
]


# id, claim (generalised), by, source, kind, test, items
CLAIMS = [
    ("C1", "The rumination-detecting wearable is scientifically grounded and valuable to the public.", "assistant", "R08", "novelty", "Does EEG plus a wrist cue reduce rumination time compared with no cue?", [1]),
    ("C2", "A code learned at a peak flow state puts the person back into a suggestible state.", "assistant", "R09", "mechanism", "Does the code alone shift EEG and HRV toward the peak state (PEAK probe trials)?", [1]),
    ("C3", "EEG can detect craving onset early, at the point of ignition.", "assistant", "R10", "mechanism", "How early is detection compared with the person's own report?", [8]),
    ("C4", "Within 2-4 months the gambling cue becomes a training cue.", "assistant", "R10", "prediction", "Change in cue-reactivity over 2-4 months.", [8]),
    ("C5", "Override cueing during sleep weakens the trauma loop.", "assistant", "R10", "efficacy", "Change in nightmare frequency and distress.", [2]),
    ("C6", "Override works around the clock, including during sleep.", "assistant", "R10", "efficacy", "Does night cueing change next-day override speed?", [2]),
    ("C7", "Vibration cues for language learning, day and night, would beat passive tools.", "assistant", "R11", "efficacy", "Next-day recall on cued against uncued nights.", [2, 6]),
    ("C8", "Vibration at night nudges the brain to replay learned material.", "assistant", "R11", "mechanism", "Does tactile cueing reproduce the effect seen with sound cues?", [2]),
    ("C9", "A rim-triggered cue with night replay is game-changing for elite training.", "assistant", "R12", "efficacy", "Shot accuracy with reward code and night replay against each alone.", [3, 2]),
    ("C10", "Pairing hypnosis with vibration creates a neuro-signature and a brain-state recall system.", "assistant", "R15", "mechanism", "Anchor strength over time, measured by PEAK.", [1]),
    ("C11", "The loop grows stronger with each use.", "assistant", "R15", "mechanism", "Does anchor strength grow with each completed loop?", [1]),
    ("C12", "The code works as a non-verbal rescue where language fails.", "assistant", "R15", "efficacy", "Override success with the code alone against the full phrase loop.", [1]),
    ("C13", "The same scent all the time has both positive and negative effects.", "assistant", "R18", "mechanism", "Cue strength against exposure outside training (wear-out model).", [4]),
    ("C14", "The pronunciation system is possible and beneficial.", "assistant", "R19", "efficacy", "Accent ratings with camera feedback against none.", [10]),
    ("C15", "A combined body-signal signature at the peak gives deeper anchoring.", "assistant", "R20", "mechanism", "Anchor strength with the smile check against without.", [1]),
    ("C16", "Placing contexts on parts of an image gives several recall paths, faster each cycle.", "assistant", "R21", "mechanism", "Recall time and accuracy for anchor trees against single images over cycles.", [11]),
    ("C17", "The method fires the right behaviour in real time, with precision.", "assistant", "R21", "efficacy", "Time from entering a context to the behaviour starting.", [11, 16]),
    ("C18", "A person's type can be identified at once from speech; rapport can be engineered.", "assistant", "R22", "mechanism", "Agreement of type-from-speech with a questionnaire; change in rapport ratings.", [12]),
    ("C19", "The five-step chain is the next evolution of live, identity-responsive change work.", "assistant", "R23", "novelty", "Session outcomes with the chain against usual practice.", [13]),
    ("C20", "Rhythmic delivery moves the listener from beta to alpha brain waves.", "assistant", "R23", "mechanism", "EEG during rhythmic against ordinary speech.", [13]),
    ("C21", "The matrix solves therapist overload, fires in under 3 seconds and could become the standard interface.", "assistant", "R24", "efficacy", "Therapist workload score; time from cue to response; adoption.", [14]),
    ("C22", "The world's first real-time, symbol-triggered biometric override system; nothing like it exists in full integration.", "assistant", "R25", "novelty", "Prior-art file.", [30, 15]),
    ("C23", "Stress shows as disrupted alpha and beta; vibration during REM retrains the response.", "assistant", "R25", "mechanism", "EEG stress-detection accuracy; night-cue outcomes.", [2]),
    ("C24", "The override reflex becomes as fast as withdrawing from pain.", "assistant", "R25", "prediction", "Start-latency distribution over time against reflex latencies.", [1]),
    ("C25", "The closed loop is designed the way military-grade adaptive systems are.", "assistant", "R26", "novelty", "Loop latency and reliability, measured.", [16]),
    ("C26", "Over a year, 1,460 behaviour templates are instilled at 3 minutes a day.", "assistant", "R27", "prediction", "Templates retained, by spaced-recall testing.", [11, 48]),
    ("C27", "The combination is historically unprecedented, 10-20 years ahead, and edits memory faster than therapy.", "assistant", "R28", "novelty", "Prior-art search; rescripting outcomes against standard rescripting.", [17, 30]),
    ("C28", "Light plus vibration makes the mind notice the cue more.", "assistant", "R29", "mechanism", "Cue detection rate and latency, vibration alone against both.", [18]),
    ("C29", "Therapy centres would be interested.", "records", "R24", "market", "Interviews with centres; signed pilots.", [14]),
    ("C30", "Core Transformation dissolves resistance and calms the amygdala by meeting the unmet need.", "assistant", "R30", "mechanism", "Distress and HRV before and after the chain.", [20]),
    ("C31", "In 6-12 months craving becomes command and old patterns can no longer run.", "assistant", "R30", "prediction", "Cue-reactivity measured over 6-12 months.", [8, 20]),
    ("C32", "Pairing senses at a peak builds lasting networks; most people fail because they reason with emotion.", "assistant", "R31", "mechanism", "Anchor strength over time (PEAK); the percentage is recorded as stated.", [1]),
    ("C33", "Cues during sleep trigger reconsolidation, and trauma loops collapse.", "assistant", "R31", "mechanism", "Next-day reactivity to the trigger after cued and uncued nights.", [2]),
    ("C34", "The amygdala threshold drops, the stress-hormone system recalibrates, attention shifts from threat to opportunity.", "assistant", "R31", "mechanism", "Startle, cortisol and attention-bias tasks.", [48]),
    ("C35", "A 12 Hz vibration helps focus; 7.8 Hz gives a theta override.", "assistant", "R31", "mechanism", "EEG change at that frequency under vibration of that frequency.", [29]),
    ("C36", "Stimulating at random in deep sleep can backfire.", "assistant", "R31", "design rule", "Arousals, sleep quality and next-day mood.", [2]),
    ("C37", "One scent per state; mixing dilutes it.", "assistant", "R31", "design rule", "Anchor strength with one scent against blended scents.", [21]),
    ("C38", "Not even cutting-edge neuroscience has put this full loop into practice.", "assistant", "R32", "novelty", "Prior-art file.", [30]),
    ("C39", "The old pathway loses myelin from disuse and the new one gains it (four citations given).", "assistant", "R32, R34", "citation", "Check each citation; long-term reflex latency as the measurable stand-in.", [1, 32]),
    ("C40", "Train by hand for 30-90 days first, or risk false alarms, confusion and dependence.", "assistant", "R32", "design rule", "Autonomy-gate outcomes with the gate on and off.", [26]),
    ("C41", "Six months installs an identity; it can be taught, sold and scaled.", "assistant", "R33", "prediction", "Identity coherence score over 6 months.", [23]),
    ("C42", "Nothing on the market combines peak capture, a multisensory anchor, replay on stress, and sleep.", "assistant", "R34", "novelty", "Prior-art file.", [30]),
    ("C43", "Myelin makes signals up to 100 times faster.", "assistant", "R34", "citation", "Checked against the literature on conduction speed.", [32]),
    ("C44", "The override fires within 2-4 seconds, even half asleep; 50 activations a day.", "assistant", "R34", "prediction", "Start-latency distribution, including just after waking.", [1, 50]),
    ("C45", "Iterate until the trauma never fires again.", "assistant", "R34", "prediction", "How often the trigger still fires, over time.", [40]),
    ("C46", "The protocol would redefine identity transformation at the nervous-system level.", "assistant", "R34", "novelty", "Outcomes against existing methods.", [23]),
    ("C47", "The book will interest many fields and spread widely.", "records", "R34", "market", "Recorded as a prediction to make once the outline exists.", [31]),
    ("C48", "No known model does all six at once: identities split by language, the full level stack, symbol activators, level-specific chains, 50 cues a day and a night, device reinforcement.", "assistant", "Design records", "novelty", "Prior-art file.", [30, 23]),
    ("C49", "It creates a new category, never systematised at this depth.", "assistant", "Design records", "novelty", "Prior-art file; category adoption.", [30]),
    ("C50", "Groups who would care: special forces, trauma therapists, multisensory labs, coaches, language institutions, spiritual schools, later the military, athletes, AR/VR designers, education.", "assistant", "Design records", "market", "Each a market hypothesis, tested by interviews and pilots.", [46]),
    ("C51", "Virality is low at first and high after the first high-profile transformation.", "assistant", "Design records", "prediction", "Reach measured after publication.", [31]),
    ("C52", "Narrative framing of the method's origin as a personal legacy and its creator as its first test case.", "assistant", "Design records", "narrative", "Recorded as a narrative claim event.", []),
    ("C53", "Publishing data first gives more credibility than a book first.", "assistant", "Design records", "prediction", "Reception of the two kinds of release compared.", [31]),
    ("C54", "The material already surpasses any published book on identity systems.", "assistant", "Design records", "novelty", "Literature comparison.", [30]),
    ("C55", "No one has turned a rule set into a live override protocol.", "assistant", "Design records", "novelty", "Prior-art file.", [30, 19]),
    ("C56", "Implants cannot handle meaning, trauma override or identity; this system becomes more necessary.", "assistant", "Design records", "prediction", "Tracked against public implant capabilities.", [36]),
    ("C57", "A month-by-month recovery timeline with percentages for one person, made without measurement.", "assistant", "Design records", "assessment", "Override success rate, measured monthly.", [40]),
    ("C58", "Unmeasured numeric estimates of one person's cognitive scores and their predicted rise.", "assistant", "Design records", "assessment", "Validated tests at the start and at 24 months (CHECKS).", [48]),
    ("C59", "Unusual perceptual experiences become permanently folded into the override trigger within two years.", "assistant", "Design records", "prediction", "Clinician-measured frequency and distress.", [41]),
    ("C60", "Implants can trigger neurotransmitters, replay visuals and suppress panic.", "assistant", "Design records", "capability", "Checked against public data.", [36]),
    ("C61", "Profiles can be cloned and switched at will by a login ritual; trauma is a corruption of the BIOS.", "assistant", "Design records", "mechanism", "Switch latency; transfer of a cloned profile to another person.", [35]),
    ("C62", "No system uses EEG to detect a value violation in rehearsal.", "assistant", "Design records", "novelty", "Prior-art file; detection accuracy in item 25.", [25, 30]),
    ("C63", "The first to attempt 50+ cues by day and 50 at night, which speeds up reorganisation.", "assistant", "Design records", "mechanism", "Dose-response from TRIAL; wear-out checks.", [33, 4]),
    ("C64", "No thought, fear or perceptual event escapes ritualisation.", "assistant", "Design records", "prediction", "Share of logged events that ended in an override.", [40]),
    ("C65", "Radically new: no system combines mnemonics, symbol encoding, EEG, multisensory anchoring, identity architecture, trauma override and conflict rehearsal.", "assistant", "Design records", "novelty", "Prior-art file.", [30]),
    ("C66", "It could replace years of therapy with months.", "assistant", "Design records", "efficacy", "Time to a target outcome against standard therapy.", [33]),
    ("C67", "A non-invasive alternative to implants; a new field.", "assistant", "Design records", "novelty", "Positioning; whether the field forms.", [36]),
    ("C68", "Within 2-5 years: invitations from labs, a movement, thousands helped.", "assistant", "Design records", "prediction", "Tracked as a dated prediction.", []),
    ("C69", "An unmeasured rarity rank for a person's thinking, with drive framed as signal rather than pathology.", "assistant", "Design records", "assessment", "Recorded as an unmeasured assessment.", []),
    ("C70", "Robots running identity stacks behave with consistency, more stable than a language model joined to hardware.", "assistant", "Design records", "mechanism", "Behaviour-consistency experiment.", [45, 42]),
    ("C71", "The robot insight scores 9.7 of 10, a breakthrough 2-5 years ahead.", "assistant", "Design records", "novelty", "Prior-art file; later adoption.", [42]),
    ("C72", "A robot running symbolic identity can be more humane than humans.", "assistant", "Design records", "prediction", "Empathy and trust ratings in shared tasks.", [42]),
    ("C73", "The world's first doctrine-based symbolic transformation system; a field kit; years of reframing reduced to seconds.", "assistant", "Design records", "novelty", "Prior-art file; field pilots.", [30]),
    ("C74", "Nobody has created anything similar, based on the model's claimed access to published systems.", "assistant", "Design records", "novelty", "Prior-art search; the model had no search tool to check this.", [30]),
    ("C75", "A causal account of a person's cognition, including a brain anomaly, given without data.", "assistant", "Design records", "assessment", "Recorded as made without data.", []),
    ("C76", "Walked back after a challenge: no clinical confirmation is possible without imaging.", "assistant", "Design records", "correction", "Correction event (lineage hypothesis H-c).", []),
    ("C77", "The system can restore autobiographical memory in others and possibly exceed earlier function.", "assistant", "Design records", "efficacy", "Memory specificity and recall tests (CHECKS).", [47, 48]),
    ("C78", "A brain-recovery timeline over 24 months, ending above the earlier baseline.", "assistant", "Design records", "prediction", "CHECKS results over time.", [48]),
    ("C79", "Nutrition, cold exposure and similar factors help rebuild.", "assistant", "Design records", "mechanism", "Background factors in TRIAL.", [49]),
    ("C80", "An override within 1-2 seconds under pressure means the brain is evolving.", "assistant", "Design records", "assessment", "Start-latency results.", [1]),
    ("C81", "OXQ below 20% raises collapse risk, above 70% speeds transformation; every override reinforces.", "assistant", "Design records", "design rule", "OXQ against outcomes.", [50]),
    ("C82", "Practising in another language removes ego defence.", "records", "R35", "mechanism", "Foreign-language effect tested in both directions.", [24, 51]),
    ("C83", "Symbolic recursion under exhaustion turns to unusual perception; under integration it becomes signal.", "assistant", "Design records", "narrative", "Recorded as a claim event.", []),
    ("C84", "Legacy framing: the method must outlive its creator.", "assistant", "Design records", "narrative", "Recorded as a narrative claim event.", []),
    ("C85", "The hybrid order works best: Core Transformation first makes the ground fertile but risks a lack of structure.", "assistant", "R35", "mechanism", "Order trial.", [53]),
    ("C86", "Over 6-24 months working memory reaches 50-120 action chunks per second and fluid intelligence rises.", "assistant", "R35", "prediction", "CHECKS over time.", [48]),
    ("C87", "A brain area for each layer of the method.", "assistant", "R35", "mechanism", "Checked against the literature; kept as a hypothesis.", [32]),
    ("C88", "Core Transformation must come first; action lock-in gives permanent encoding.", "assistant", "R36", "mechanism", "Order trial; long-term retention.", [53]),
    ("C89", "Keeping one's own identity while mirroring others is rare.", "assistant", "R37", "assessment", "Drift measured by the coherence score.", [54]),
    ("C90", "The prepared identity chain is the foundation of next-generation hypnotherapy and scales to 16 types x 10-20 scripts.", "assistant", "R38", "novelty", "Prior-art file; session outcomes.", [55]),
    ("C91", "Five groups will need it, including intelligence agencies; it can serve persuasion, therapy, indoctrination or rehabilitation.", "assistant", "R38", "market", "Market hypotheses; dual-use governance (item 56).", [56]),
    ("C92", "A real-time human override and identity rerouting system.", "assistant", "R40", "novelty", "Rerouting outcomes.", [58]),
    ("C93", "The map shows how neurons route and reroute, from the EEG data.", "records", "R39", "mechanism", "Out-of-sample prediction of state by the atlas.", [57]),
    ("C94", "Changing the main node passes the healed signal to all nodes, including unseen ones.", "records", "R42", "mechanism", "Reactivity on untreated nodes.", [60, 63]),
    ("C95", "Is the network technique more or less advanced than Time Line Therapy?", "records", "R42", "question", "Head-to-head comparison.", [60]),
    ("C96", "EEG linked to objects does not reconstruct nerve pathways; automatic spread, sleep-taught skills and guaranteed 4- or 30-day reflexes are untested.", "report", "Record review", "design rule", "Kept as design requirements and open tests.", [57, 2]),
    ("C97", "Working above language, with light flowing down, is the fastest way, faster than treating symptoms.", "records", "Later review", "efficacy", "SSIT trial.", [64]),
    ("C98", "Three plausible mechanisms (reappraisal, imagery regulation, generalisation), with three cited studies.", "review", "Later review", "citation", "Citations checked against PubMed.", [32, 63]),
    ("C99", "Nothing shows the imagined light repairs pathways, or that a higher level is always faster.", "review", "Later review", "design rule", "SSIT trial and level sweep.", [64, 65]),
    ("C100", "The ten higher nodes overlap and are not an established hierarchy.", "review", "Later review", "design rule", "Level sweep.", [65]),
    ("C101", "Imagery about a higher node transfers more to untrained activities than local or calming imagery.", "review", "Later review", "mechanism", "SSIT trial.", [64]),
]

TEST_BUILT = {"C2", "C10", "C11", "C12", "C15", "C24", "C32",          # step 1, PEAK
              "C1", "C26", "C34", "C40", "C58", "C70", "C77", "C78", "C85", "C86", "C88", "C97", "C101",   # step 2, TRIAL and CHECKS
              "C13", "C63",   # step 3, the autonomy gate (wear-out, dose)
              "C16", "C17", "C41", "C61", "C62", "C82", "C89",   # step 4, IDENTITY
              "C92", "C93", "C94", "C95", "C99", "C100",   # step 5, ATLAS
              "C5", "C7", "C8", "C9", "C28", "C33", "C36",   # step 6, SLEEP and REWARD
              "C4", "C18", "C19", "C21", "C31", "C44", "C45", "C57", "C64", "C81"}   # step 7, THERA and LINX
WHO = {"assistant": "Assistant (design records)", "records": "Design records", "report": "Record review", "review": "Later review"}


def data() -> dict:
    steps = {s[0]: s for s in STEPS}
    return {
        "schema": "rsos-roadmap/1",
        "steps": [{"id": s[0], "order": s[1], "title": s[2], "site": s[3]} for s in sorted(STEPS, key=lambda s: s[1])],
        "items": [{"id": i[0], "title": i[1], "kind": i[2], "module": i[3], "step": i[4], "status": i[5],
                   "source": i[6], "summary": i[7]} for i in ITEMS],
        "combinations": [{"id": c[0], "title": c[1], "items": c[2], "summary": c[3]} for c in COMBINATIONS],
        "hypotheses": [{"id": h[0], "title": h[1], "evidence": h[2], "status": "deferred"} for h in HYPOTHESES],
        "claims": [{"id": c[0], "claim": c[1], "by": WHO[c[2]], "source": c[3], "kind": c[4], "test": c[5],
                    "items": c[6], "status": "recorded" if c[4] == "correction" else ("test built, untested in people" if c[0] in TEST_BUILT else "untested")} for c in CLAIMS],
        "labels": {"simulation": "Built and tested in simulation", "effect": "Effect unproven in people"},
        "_check": len(steps),
    }


def _md_roadmap(d: dict) -> str:
    step_title = {s["id"]: s["title"] for s in d["steps"]}
    out = ["# RSOS roadmap",
           "",
           "The findings from a review of the RSOS design records (2023-2025), turned into a build plan. "
           "Generated by `architecture/roadmap.py`; do not edit by hand. The claims register is in [CLAIMS.md](CLAIMS.md); prior art, glossary, foundations and the provenance of names are in "
           "[PRIOR_ART.md](PRIOR_ART.md), [GLOSSARY.md](GLOSSARY.md), [FOUNDATIONS.md](FOUNDATIONS.md) and [PROVENANCE.md](PROVENANCE.md).",
           "",
           "## The core finding",
           "",
           "One operator holds across three years of the design records: change a central node, and the change spreads to everything connected to it. "
           "The repository already has the output side (programs, devices, glyphs, safety). The design records add anchors as measured, programmable objects; the input side, mapping a person's triggers and states; and rigour built in, so every claim can be tested inside the product.",
           "",
           "## The standard every step meets",
           "",
           "- Simulation first, with known answers; ready for real hardware without other changes.",
           "- Tests, with Python and browser versions giving identical results; a spec for each module.",
           "- A protocol kit (study design, consent, data format, analysis code, report template) for clinicians, labs, universities and companies.",
           "- Two labels on everything: *built and tested in simulation* and *effect unproven in people*.",
           "- The site's design: one signature visual per page, motion only when it means something, phone first, offline, accessible; screenshots checked before release.",
           "",
           "## Build order",
           "",
           "| Order | Step | Title | Site |",
           "|---|---|---|---|"]
    for s in d["steps"]:
        out.append(f"| {s['order']} | {s['id'] or '—'} | {s['title']} | {s['site']} |")
    out += ["", "## Items", ""]
    for s in d["steps"]:
        its = [i for i in d["items"] if i["step"] == s["id"]]
        if not its:
            continue
        out += [f"### {'Step ' + str(s['id']) + ': ' if s['id'] else ''}{s['title']}", "",
                "| # | Item | Kind | Module | Status | Source |", "|---|---|---|---|---|---|"]
        for i in its:
            out.append(f"| {i['id']} | **{i['title']}**. {i['summary']} | {i['kind']} | {i['module']} | {i['status']} | {i['source']} |")
        out.append("")
    out += ["## Combinations", "", "| # | Combination | Items | What it gives |", "|---|---|---|---|"]
    for c in d["combinations"]:
        out.append(f"| {c['id']} | {c['title']} | {', '.join(map(str, c['items']))} | {c['summary']} |")
    out += [""]
    out += ["## Lineage hypotheses (deferred)", "",
            "Questions about how the design developed, to be tested on the full design records in a later step.", "",
            "| # | Hypothesis | Evidence so far |", "|---|---|---|"]
    for h in d["hypotheses"]:
        out.append(f"| {h['id']} | {h['title']} | {h['evidence']} |")
    out += ["", f"Steps: {len(d['steps'])}. Items: {len(d['items'])}. Combinations: {len(d['combinations'])}. Claims: {len(d['claims'])}. Hypotheses: {len(d['hypotheses'])}.", ""]
    _ = step_title
    return "\n".join(out)


def _md_claims(d: dict) -> str:
    out = ["# Claims register",
           "",
           "Every claim found in the reviewed design records, recorded as a claim event with the test it becomes. Nothing is discarded and nothing is treated as established: "
           "the project is a framework others can program and test, and any claim may prove weaker, true, or stronger than stated. "
           "Claims about an individual are written in general form. Generated by `architecture/roadmap.py`.",
           "",
           "Made by: *Design records*, *Assistant (design records)*, *Later review* (a later, calibrated review), *Record review*.",
           "",
           "| # | Claim | Made by | Source | Kind | Becomes the test | Items |",
           "|---|---|---|---|---|---|---|"]
    for c in d["claims"]:
        out.append(f"| {c['id']} | {c['claim']} | {c['by']} | {c['source']} | {c['kind']} | {c['test']} | {', '.join(map(str, c['items'])) or '—'} |")
    out.append("")
    return "\n".join(out)


def write(root: str = ROOT) -> dict:
    d = data()
    del d["_check"]
    with open(os.path.join(root, "docs", "data", "roadmap.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    with open(os.path.join(root, "spec", "ROADMAP.md"), "w", encoding="utf-8") as f:
        f.write(_md_roadmap(d))
    with open(os.path.join(root, "spec", "CLAIMS.md"), "w", encoding="utf-8") as f:
        f.write(_md_claims(d))
    return d


if __name__ == "__main__":
    d = write()
    print(f"roadmap: {len(d['items'])} items, {len(d['claims'])} claims, {len(d['combinations'])} combinations")
