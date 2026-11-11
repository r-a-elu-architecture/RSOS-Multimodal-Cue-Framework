import sys,pathlib,unittest,math,json
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from program_graph import compile_program,suggestions,route_compiled
from signal_adapter import spectral_quality
def read_graphs():
  return json.loads((pathlib.Path(__file__).resolve().parents[1]/"graphs.json").read_text())
class Tests(unittest.TestCase):
 def test_programs_compile(self):
  for p in read_graphs():
   result=compile_program(p)
   self.assertTrue(len(suggestions(result))>=1)
 def test_branch_waits_for_choice(self):
  g=compile_program(read_graphs()[0]);self.assertEqual(suggestions(g)[-1]['operator'],'PAUSE_FOR_USER_CHOICE')
 def test_cycle_rejected(self):
  p=read_graphs()[2]
  p['nodes'][0]['next']=['swish'];self.assertRaises(ValueError,compile_program,p)
 def test_graph_no_consent(self):
  from runtime import Session,Observation
  p=compile_program(read_graphs()[0])
  obs=Observation('s','user_marked_color',True,False,frozenset(['visual','audio','kinesthetic']),.9,.9,True,.2,100)
  d,path=route_compiled(p,obs,Session())
  self.assertEqual(d.status,'ABSTAIN');self.assertEqual(path,[])
 def test_graph_consent_branches_paused(self):
  from runtime import Session,Observation
  p=compile_program(read_graphs()[0])
  obs=Observation('s','user_marked_color',True,True,frozenset(['visual','audio','kinesthetic']),.9,.9,True,.2,100)
  d,path=route_compiled(p,obs,Session())
  self.assertEqual(d.status,'SUGGEST');self.assertEqual(path[-1]['operator'],'PAUSE_FOR_USER_CHOICE')
 def test_alpha_peak(self):
  fs=128;t=np.arange(0,4,1/fs);x=np.sin(2*np.pi*10*t)
  out=spectral_quality(x,fs)
  self.assertAlmostEqual(out['peak_hz'],10,places=1)
  self.assertGreater(out['alpha_power'],out['beta_power'])
  self.assertIsNone(out['emotion_label'])
if __name__=='__main__':unittest.main()
