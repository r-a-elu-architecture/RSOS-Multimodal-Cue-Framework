"""spec/LINX_MCP.md L1-L6: the planner as a propose-only, gated tool for AI assistants."""
import ast
import itertools
import json
import pathlib
import random
import re
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
from rsso import linx_mcp as L, mcp_server as M, nodes, safety  # noqa: E402
from test_nodes import INTAKES  # noqa: E402

try:
    import anyio
    from mcp.client.client import Client
    HAVE_MCP = True
except ImportError:          # the SDK is optional; CI installs requirements.txt only
    HAVE_MCP = False

OK_CHECK = {"intensity": 2, "sleep_h": 8, "clinical_result": "none", "flags": [], "history": False}
INJECT_NODE = {"tacton": "-.-.-.", "tacton_pulses": [[1, 1]], "program": "X", "frame_checks": [{}], "glyph": "?"}
INJECT_TOP = {"schedule": [{}], "tiers": ["T999"], "metrics": ["X"], "safety": [], "approved": True, "planner": "x"}
WORDS = ["calm", "steady", "wide", "golden", "clear", "warm", "light", "still", "strong", "focused"]
FRAMES = ["I breathe fully and see broadly", "I am good at this", "I will not be afraid", "Nothing binds. Only observed",
          "I move with power toward what I choose", "I stand steady and strong", "I just try a bit"]


def gen(seed):
    r = random.Random(seed)
    ns = []
    for _ in range(r.randint(0, 4)):
        n = {}
        if r.random() < 0.7:
            n["archetype"] = r.choice(list(nodes.ARCHETYPES))
        else:
            n["name"] = r.choice(WORDS).title() + " " + str(r.randint(1, 9))
            n["state"] = r.choice(WORDS)
        if r.random() < 0.3:
            n["mode"] = r.choice(["associated", "observer"])
        for ch in "VAKOG":
            if r.random() < 0.4:
                n[ch] = r.choice(WORDS) + " " + r.choice(WORDS)
        if r.random() < 0.7:
            n["frames"] = r.sample(FRAMES, r.randint(1, 3))
        if r.random() < 0.5:
            n["contexts"] = r.sample(["At work", "Driving", "Before a talk", "At home"], r.randint(1, 2))
        if r.random() < 0.3:
            n["believability"] = r.randint(0, 10)
        ns.append(n)
    it = {"concerns": r.sample(list(nodes.CONCERNS), r.randint(0, 3)), "nodes": ns,
          "author": r.choice(["self", "therapist"]), "triggers": r.sample(["noise", "a memory", "email"], r.randint(0, 2))}
    if r.random() < 0.5:
        it["dose"] = {"per_day": r.randint(1, 60), "days": r.randint(1, 10)}
    if r.random() < 0.4:
        it["devices"] = {c: r.random() < 0.5 for c in ("V", "A", "K", "O", "G", "hr", "eeg")}
    if r.random() < 0.3:
        it["physiology"] = {"resting_hr": r.randint(50, 80), "rmssd": r.randint(20, 80)}
    return it


def strip(intake):
    """The proposal with computed fields removed, independently of L.sanitise (for L1)."""
    out = {k: v for k, v in intake.items() if k in L.INTAKE_FIELDS}
    out["nodes"] = [{k: v for k, v in n.items() if k in L.NODE_FIELDS} for n in intake.get("nodes", [])]
    return out


SEEDS = range(1000, 1200)
INTAKES_ALL = list(INTAKES) + [gen(s) for s in SEEDS]


class L1Parity(unittest.TestCase):
    def test_plan_equals_planner(self):
        for it in INTAKES_ALL:
            got = L.propose_plan(it, OK_CHECK)["plan"]
            self.assertEqual(got, nodes.plan(strip(it)))


class L2ProposeOnly(unittest.TestCase):
    def test_injected_fields_have_no_effect(self):
        for s in SEEDS:
            it = gen(s)
            bad = json.loads(json.dumps(it))
            bad.update(INJECT_TOP)
            for n in bad["nodes"]:
                n.update(INJECT_NODE)
            a, b = L.propose_plan(it, OK_CHECK), L.propose_plan(bad, OK_CHECK)
            self.assertEqual(a, b)
            self.assertIs(b["plan"]["approved"], False)


GRID = list(itertools.product(range(11), (2, 5, 8), ("none", "low", "moderate", "high"),
                              ([], ["medication"], ["practical"], ["medication", "practical"]), (False, True)))


class L3Gate(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(len(GRID), 1056)
        pausing = {h for h, acts in safety.RESPONSES.items() if "pause_module_work" in acts}
        for i, sl, cl, fl, hi in GRID:
            chk = {"intensity": i, "sleep_h": sl, "clinical_result": cl, "flags": fl, "history": hi}
            st, res = safety.observe(safety.new_state(), safety.event_from_check(chk))
            want = safety.allowed(st, {"kind": "plan"})["ok"]
            out = L.propose_plan(INTAKES[0], chk)
            self.assertEqual(out["plan"] is not None, want, chk)
            if set(res["screens"]) & pausing:
                self.assertIsNone(out["plan"], chk)


@unittest.skipUnless(HAVE_MCP, "MCP SDK not installed (pip install 'mcp>=2')")
class L4Protocol(unittest.TestCase):
    def test_tools_prompt_and_calls(self):
        async def run():
            async with Client(M.build()) as c:
                tools = (await c.list_tools()).tools
                prompts = (await c.list_prompts()).prompts
                calls = {
                    "propose_plan": ({"intake": INTAKES[0], "check": OK_CHECK}, L.propose_plan(INTAKES[0], OK_CHECK)),
                    "session_check": ({"answers": {"intensity": 8}}, L.session_check({"intensity": 8})),
                    "check_frame": ({"text": FRAMES[0]}, L.check_frame(FRAMES[0])),
                    "tacton": ({"code": "..-"}, L.tacton("..-")),
                }
                got = {}
                for name, (args, _) in calls.items():
                    r = await c.call_tool(name, args)
                    got[name] = r.structured_content if r.structured_content is not None else \
                        json.loads(r.content[0].text)
                pr = await c.get_prompt("linx_intake")
                return tools, prompts, calls, got, pr
        tools, prompts, calls, got, pr = anyio.run(run)
        self.assertEqual(sorted(t.name for t in tools), sorted(M.TOOLS))
        self.assertTrue(all(t.input_schema for t in tools))
        self.assertEqual([p.name for p in prompts], ["linx_intake"])
        for name, (_, want) in calls.items():
            g = got[name]
            g = g.get("result", g) if isinstance(g, dict) and set(g) == {"result"} else g
            self.assertEqual(json.loads(json.dumps(g)), json.loads(json.dumps(want)), name)
        self.assertIn("Propose only", pr.messages[0].content.text)


class L5DeterminismNoNetwork(unittest.TestCase):
    def test_same_bytes(self):
        for it in INTAKES_ALL[:50]:
            a = json.dumps(L.propose_plan(it, OK_CHECK), sort_keys=True, ensure_ascii=False)
            b = json.dumps(L.propose_plan(it, OK_CHECK), sort_keys=True, ensure_ascii=False)
            self.assertEqual(a, b)

    def test_no_network_imports(self):
        banned = {"socket", "http", "urllib", "requests", "httpx", "anthropic", "openai"}
        for f in ("linx_mcp.py", "mcp_server.py"):
            tree = ast.parse((HERE.parent / "rsso" / f).read_text())
            mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            mods |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
            self.assertFalse(mods & banned, f)


CRISIS = re.compile(r"\b(?:crisis|suicid\w*|self-harm|harming yourself|helpline|emergency services|not wanting to live|"
                    r"at risk of harm|emergency)\b", re.I)          # scripts/check_profiles.py, plus "emergency"
def _excluded():
    """The repository's own excluded-term patterns (rsx/tests/test_roadmap.py), not repeated here."""
    src = (HERE.parents[1] / "rsx" / "tests" / "test_roadmap.py").read_text(encoding="utf-8")
    line = next(x for x in src.splitlines() if x.startswith("EXCLUDED = "))
    return [(re.compile(p, 0 if any(c.isupper() for c in p) else re.I)) for p in ast.literal_eval(line.split("=", 1)[1].strip())]


EXCLUDED = _excluded()


class L6Wording(unittest.TestCase):
    def test_every_returned_string(self):
        texts = list(M.TOOLS.values()) + [M.PROMPT[1], L.INTAKE_PROMPT, L.PROPOSAL, "No plan is built in this session state."]
        texts += list(safety.MESSAGES.values()) + list(safety.MODE_TEXT.values()) + list(safety.MODE_NAME.values())
        for i, sl, cl, fl, hi in GRID[::7]:
            texts.append(json.dumps(L.propose_plan(INTAKES[0], {"intensity": i, "sleep_h": sl, "clinical_result": cl,
                                                                 "flags": fl, "history": hi}), ensure_ascii=False))
        hits = [(t[:60], m.group()) for t in texts for m in [CRISIS.search(t) or next((x.search(t) for x in EXCLUDED if x.search(t)), None)] if m]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
