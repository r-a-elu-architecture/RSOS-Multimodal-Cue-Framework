import sys, pathlib, unittest
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from transfer_benchmark import ARMS,CAN_A,CAN_C,generate_world,actual,matrix,WORLDS,run
from scoped_cue_registry import CueRegistry
from scoped_stress import run as stress

class TestTransfer(unittest.TestCase):
 def test_program_space(self):
  self.assertEqual(ARMS.shape,(180,3));self.assertEqual(CAN_A.shape,(720,3))
 def test_null_scenario(self):
  w=generate_world(2,'null_effect',4)
  v=actual(CAN_A,CAN_C,w)
  self.assertTrue(np.allclose(v,v[0]))
 def test_no_hidden_outcome_in_relation_features(self):
  w=generate_world(2,'family_transfer',4)
  a=matrix(CAN_A,CAN_C,w[-1]);b=matrix(CAN_A,CAN_C,w[-1]);self.assertTrue(np.array_equal(a,b))
 def test_same_relation_is_same_policy(self):
  z=run(2,2,12,3)
  a=z[z.model=='rsos_relational'].regret.to_numpy()
  b=z[z.model=='generic_same_relations'].regret.to_numpy()
  self.assertTrue(np.array_equal(a,b))
 def test_no_cross_profile_meaning(self):
  x=CueRegistry()
  a=x.bind('one','social','LION','calm');b=x.bind('two','social','LION','study')
  self.assertEqual(x.resolve('one','social','LION',1,True,.9)[0].meaning,'calm')
  self.assertEqual(x.resolve('two','social','LION',1,True,.9)[0].meaning,'study')
 def test_rebinding_and_revoke(self):
  x=CueRegistry();x.bind('p','c','LION','old');b=x.bind('p','c','LION','new')
  self.assertEqual(x.resolve('p','c','LION',1,True,.9)[1],'STALE_REVISION')
  self.assertEqual(x.resolve('p','c','LION',b.revision,True,.9)[1],'OK')
  x.revoke('p','c','LION');self.assertEqual(x.resolve('p','c','LION',b.revision,True,.9)[1],'REVOKED')
 def test_stress_oracle(self):
  x=stress(9,5000);self.assertEqual(x['unexpected_results'],0)
if __name__=='__main__':unittest.main()
