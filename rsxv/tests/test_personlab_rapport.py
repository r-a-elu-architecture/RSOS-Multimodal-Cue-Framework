"""spec/RAPPORT_ESCONV.md: features and verdict rules, on made-up data."""
import unittest

from rsxv.personlab import rapport as R


def conv(pairs):
    d = []
    for s, sup, fb in pairs:
        d.append({"speaker": "seeker", "content": s, "annotation": ({"feedback": fb} if fb else {})})
        d.append({"speaker": "supporter", "content": sup, "annotation": {"strategy": "Question"}})
    d.append({"speaker": "seeker", "content": "end", "annotation": {"feedback": "5"}})
    return {"dialog": d}


class Rapport(unittest.TestCase):
    def test_channel(self):
        self.assertEqual(R.channel("I feel stuck and heavy"), "K")
        self.assertEqual(R.channel("I can't see a clear picture"), "V")
        self.assertIsNone(R.channel("nothing here"))
        self.assertIsNone(R.channel("I see and I hear"))              # tie

    def test_echo(self):
        self.assertTrue(R.echo("my exams worry parents", "your exams and your parents"))
        self.assertFalse(R.echo("my exams worry parents", "that is hard"))
        self.assertTrue(R.phrase_echo("I lost my job today", "so you lost my job, I hear"))

    def test_events_outcome_is_next_rating(self):
        D = [conv([("I feel stuck", "how does that feel heavy", None), ("I see it", "picture it clearly", "4")]),
             conv([("other words here", "sure", "3")])]
        ev = R.events(D, exclude=set())
        self.assertEqual(len(ev), 3)
        first = [e for e in ev if e["conv"] == 0][0]
        self.assertEqual((first["y"], first["MATCH"], first["ch_seeker"]), (4.0, True, "K"))

    def test_verdicts(self):
        ev = []
        for c in range(200):
            for k in range(2):
                m = k == 0
                ev.append({"conv": c, "y": 5.0 if m else 4.0, "action": "EXPLORE", "stage": 0, "MATCH": m,
                           "MATCH_p": c % 2 == 0, "ECHO": False, "ECHO_p": False, "BOTH": False, "NEITHER": True,
                           "BOTH_p": False, "NEITHER_p": True})
        r = R.test(ev, "MATCH", B=200)
        self.assertEqual(r["verdict"], "HOLDS")
        self.assertEqual(R.test(ev, "ECHO", B=50)["verdict"], "NOT TESTABLE")


if __name__ == "__main__":
    unittest.main()
