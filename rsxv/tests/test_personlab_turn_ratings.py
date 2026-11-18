"""TURN_RATINGS (spec/TURN_RATINGS.md): unit, split, verdict rule and model fit on invented fixtures only."""
import random

import numpy as np

from rsxv.personlab import turn_ratings as T


def conv(turns, start="4"):
    d = []
    for sp, x in turns:
        if sp == "seeker":
            d.append({"speaker": "seeker", "content": "s", "annotation": ({"feedback": x} if x else {})})
        else:
            d.append({"speaker": "supporter", "content": "t", "annotation": {"strategy": x}})
    return {"dialog": d, "survey_score": {"seeker": {"initial_emotion_intensity": start}}}


def test_events_previous_rating_stage_and_actions():
    c = conv([("seeker", None), ("supporter", "Question"), ("seeker", "3"),
              ("supporter", "Affirmation and Reassurance"), ("supporter", "Providing Suggestions"), ("seeker", "5"),
              ("supporter", "Others"), ("seeker", None)])
    ev = T.events([c])
    assert [e["y"] for e in ev] == [3.0, 5.0]
    assert ev[0]["p"] is None and ev[1]["p"] == 3.0
    assert ev[0]["act"]["EXPLORE"] and not ev[0]["act"]["STABILISE"]
    assert ev[1]["act"]["STABILISE"] and ev[1]["act"]["SUGGEST"] and not ev[1]["act"]["EXPLORE"]
    assert [e["stage"] for e in ev] == [0, 0]          # RAPPORT's rule: min(2, 3a // 4) for a = 0, 1
    assert [T.min_stage(a, 9) for a in (0, 2, 3, 5, 6, 8)] == [0, 0, 1, 1, 2, 2]
    assert ev[0]["start"] == 4.0
    assert len(T.usable(ev)) == 1


def test_bad_values_are_missing():
    c = conv([("seeker", None), ("supporter", "Question"), ("seeker", "x")], start="")
    assert T.events([c]) == []
    c2 = conv([("seeker", "4"), ("supporter", "Question"), ("seeker", "2")], start="")
    ev = T.events([c2])
    assert ev[0]["p"] == 4.0 and ev[0]["start"] is None and T.usable(ev) == []


def test_split_is_seeded_disjoint_and_complete():
    a, b = T.split(101)
    assert a.isdisjoint(b) and a | b == set(range(101)) and len(a) == 50
    assert T.split(101) == (a, b)


def test_verdict_rule():
    assert T.verdict(-0.05, -0.001) == "SIGNAL"
    assert T.verdict(-0.005, 0.008) == "NULL"
    assert T.verdict(0.02, 0.05) == "WORSE"
    assert T.verdict(-0.03, 0.004) == "INCONCLUSIVE"
    assert T.verdict(-0.004, 0.02) == "INCONCLUSIVE"


def test_fit_recovers_a_planted_action_effect_and_signal():
    rng = random.Random(7)
    D = []
    for _ in range(400):
        turns = [("seeker", "3")]
        for _ in range(8):
            s = rng.choice(["Question", "Affirmation and Reassurance", "Providing Suggestions"])
            turns.append(("supporter", s))
            base = 3.0 + (1.0 if s == "Affirmation and Reassurance" else 0.0)
            turns.append(("seeker", str(int(max(1, min(5, round(base + rng.gauss(0, 0.5))))))))
        D.append(conv(turns))
    r = T.main_stage(D, B=200)
    assert r["M1_action_coefficients"]["STABILISE"]["coef"] > 0.6
    assert r["Q1_M1_minus_B1"]["verdict"] == "SIGNAL"
    assert r["mse"]["M1"] < r["mse"]["B1"]


def test_no_effect_is_not_signal():
    rng = random.Random(8)
    D = []
    for _ in range(400):
        turns = [("seeker", "4")]
        for _ in range(8):
            turns.append(("supporter", rng.choice(["Question", "Affirmation and Reassurance", "Self-disclosure"])))
            turns.append(("seeker", str(rng.choice([3, 4, 5]))))
        D.append(conv(turns))
    r = T.main_stage(D, B=200)
    assert r["Q1_M1_minus_B1"]["verdict"] != "SIGNAL"


def test_pilot_pairs_no_action_with_a_rating():
    c = conv([("seeker", "4"), ("supporter", "Question"), ("seeker", "3"), ("supporter", "Others"), ("seeker", "5")])
    p = T.pilot([c, c])
    allowed = {"conversations", "rated_seeker_turns", "events", "events_without_previous_rating", "events_without_start",
               "usable_events", "usable_dev", "usable_test", "events_per_conversation", "action_true_all",
               "action_true_test", "indicators_per_block", "rating_distribution", "share_at_5", "amendment_needed"}
    assert set(p) == allowed
    assert all(isinstance(v, int) for v in p["action_true_all"].values())
    assert np.isclose(sum(p["rating_distribution"].values()), p["usable_events"])
