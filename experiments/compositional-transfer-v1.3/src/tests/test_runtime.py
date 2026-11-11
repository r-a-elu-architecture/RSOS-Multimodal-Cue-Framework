import sys, pathlib, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from runtime import *

class TestRuntime(unittest.TestCase):
 def setUp(self):
  self.r=parse_recipe(dict(id='x',context='social',tier_start=1,tier_end=10,glyph_chain=['A','B'],ops=['interrupt','resource_recall','future_rehearsal'],channels=['visual','audio'],goal='mnemonic'))
  self.o=Observation(session_id='s',context='social',voluntary_event=True,active_consent=True,allowed_channels=frozenset(['visual','audio']),observation_confidence=.9,signal_quality=.9,user_requested=True,self_report_distress=.2,now_s=100)
 def test_variable_tier(self):
  self.assertEqual(self.r.tier_end,10)
  self.assertIsNone(parse_recipe(dict(id='x',context='z',glyph_chain=['a'],ops=['mnemonic'],channels=['visual'],goal='x')).tier_start)
 def test_levels_optional(self):
  raw=dict(id="x",context="z",glyph_chain=["a"],ops=["mnemonic"],channels=["visual"],goal="x",goal_map={"environment":"chosen setting","mission":"chosen aim"})
  self.assertEqual(len(parse_recipe(raw).goal_map),2)
  raw["goal_map"]={"brain_installed": "unverified"}
  self.assertRaises(ValueError,parse_recipe,raw)
 def test_valid(self):self.assertEqual(Session().decide(self.r,self.o).status,'SUGGEST')
 def test_no_consent(self):
  from dataclasses import replace
  self.assertEqual(Session().decide(self.r,replace(self.o,active_consent=False)).status,'ABSTAIN')
 def test_no_channel(self):
  from dataclasses import replace
  self.assertEqual(Session().decide(self.r,replace(self.o,allowed_channels=frozenset(['visual']))).status,'ABSTAIN')
 def test_context(self):
  from dataclasses import replace
  self.assertEqual(Session().decide(self.r,replace(self.o,context='gym')).status,'ABSTAIN')
 def test_confidence(self):
  from dataclasses import replace
  self.assertEqual(Session().decide(self.r,replace(self.o,observation_confidence=.1)).status,'ABSTAIN')
 def test_cooldown(self):
  from dataclasses import replace
  sess=Session();sess.decide(self.r,self.o);self.assertEqual(sess.decide(self.r,replace(self.o,now_s=110)).status,'ABSTAIN')
 def test_distress(self):
  from dataclasses import replace
  self.assertEqual(Session().decide(self.r,replace(self.o,self_report_distress=.95)).status,'MANUAL_GROUNDING_ONLY')
 def test_invalid_range(self):
  self.assertRaises(ValueError,parse_recipe,dict(id='x',context='z',tier_start=20,tier_end=10,glyph_chain=['a'],ops=['mnemonic'],channels=['visual'],goal='x'))
 def test_invalid_operator(self):
  self.assertRaises(ValueError,parse_recipe,dict(id='x',context='z',glyph_chain=['a'],ops=['mind_control'],channels=['visual'],goal='x'))
if __name__=='__main__':unittest.main()
