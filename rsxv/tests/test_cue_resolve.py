"""CUE_RESOLVE (spec/CUE_RESOLVE.md §5): person model v3 and the Part A measures."""
import json
import os

from rsxv import cue_resolve as C
from rsxv.person2 import PersonEnvV2
from rsxv.world import person_world

HERE = os.path.dirname(__file__)


def trace(env, ticks=60):
    w = person_world(env, seed=7, score="mission")
    for _ in range(ticks):
        w.tick()
    return w.rewards, [(e["t"], e["interrupted"], e["resolved"]) for e in env.events]


def test_T1_none_is_v2_exactly():
    assert trace(PersonEnvV2(7)) == trace(PersonEnvV2(7, self_resolve=None))


def test_T2_uninterrupted_cue_closes_after_R_and_a_new_one_can_start():
    env = PersonEnvV2(7, trig_rate=0.0, self_resolve=4)
    env._trigger()
    t0 = env.events[0]["t"]
    for _ in range(4):
        assert env.open is not None
        env.step("BEAR")                      # untrained module: Bear cannot interrupt
    assert env.open is None
    assert env.events[0]["resolved"] == t0 + 4 and env.events[0].get("self_resolved")
    env.trig_rate = 1.0
    env.step("LION")
    assert len(env.events) == 2


def test_T3_part_a_measures_on_v2_reproduce_the_recorded_runs():
    """On v2, the replicated Bear runs show what world_runs.json recorded: one cue, open at the end."""
    data = json.load(open(os.path.join(HERE, "..", "..", "docs", "data", "world_runs.json")))
    rec = {(r["seed"], r["event"], r["t0"]): r["summary"]["cues"] for r in data["runs"]}
    for (s, ev, t0), cues in list(rec.items())[:5]:
        b = C.run_recorded(s, ev, t0, "BEAR", None)
        w = C.run_recorded(s, ev, t0, "WATCHDOG", None)
        assert b["cues"] == cues["bear"] and b["open_at_end"] == cues["bear_open_at_end"]
        assert w["cues"] == cues["watchdog"] and w["open_at_end"] == cues["watchdog_open_at_end"]
        assert b["stuck_at_end"] and b["blocked_ticks"] > 100


def test_verdict_rule():
    assert C.verdict([-0.02, -0.001]) == "BEAR STILL WINS"
    assert C.verdict([0.001, 0.02]) == "WATCHDOG WINS"
    assert C.verdict([-0.01, 0.01]) == "TIE"


def test_follow_up_B_rule():
    assert C.adopt_pass({"ratio": 0.95, "ci": [0.85, 1.05]})
    assert not C.adopt_pass({"ratio": 0.84, "ci": [0.82, 0.9]})
    assert not C.adopt_pass({"ratio": 0.95, "ci": [0.78, 1.1]})
    r = C.ratio_ci([2, 2, 2, 2], [1, 1, 1, 1], B=50)
    assert r["ratio"] == 2.0 and r["ci"] == [2.0, 2.0]
