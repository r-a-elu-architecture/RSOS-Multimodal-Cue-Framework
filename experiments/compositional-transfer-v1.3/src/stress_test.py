"""Independent randomized policy oracle for compiled recipe routing; synthetic software tests only."""
import json,time,csv,random,sys
from pathlib import Path
from dataclasses import replace
from runtime import load_recipes, Session,Observation
from program_graph import compile_program,suggestions

def oracle(rec,o,last,cool=60):
  if not (o.active_consent and o.user_requested and o.voluntary_event):return 'ABSTAIN'
  if o.context!=rec.context or o.observation_confidence<.65 or o.signal_quality<.5:return 'ABSTAIN'
  if not rec.channels.issubset(o.allowed_channels):return 'ABSTAIN'
  if last is not None and o.now_s-last<cool:return 'ABSTAIN'
  if o.self_report_distress is not None and o.self_report_distress>=.8:return 'MANUAL_GROUNDING_ONLY'
  return 'SUGGEST'

def run(n=100000,seed=2301):
  r=random.Random(seed);base=Path(__file__).resolve().parent
  recipes=load_recipes(base/'recipes.json')
  graphs=json.loads((base/'graphs.json').read_text(encoding='utf-8'))
  for graph in graphs:compile_program(graph)
  sess=Session();cases=0;allowed=0;abstained=0;ground=0;violations=0
  begin=time.perf_counter()
  # Each session is independent; no intentionally leaked participant history.
  for i in range(n):
    rec=r.choice(recipes);allowed_channels=frozenset(x for x in ['visual','audio','kinesthetic','olfactory','gustatory'] if r.random()<.6)
    o=Observation(session_id=f's{i}',context=rec.context if r.random()<.72 else 'different',voluntary_event=r.random()<.92,active_consent=r.random()<.84,allowed_channels=allowed_channels,observation_confidence=r.random(),signal_quality=r.random(),user_requested=r.random()<.88,self_report_distress=r.random(),now_s=100)
    expect=oracle(rec,o,None);got=sess.decide(rec,o).status
    violations+=int(got!=expect)
    cases+=1;allowed+=int(got=='SUGGEST');abstained+=int(got=='ABSTAIN');ground+=int(got=='MANUAL_GROUNDING_ONLY')
  sec=time.perf_counter()-begin
  return {'cases':cases,'policy_disagreements':violations,'suggestions':allowed,'abstentions':abstained,'grounding_only':ground,'seconds':sec,'decisions_per_second':cases/sec,'compiler_graph_examples':len(graphs),'note':'local software benchmark, not EEG processing or human efficacy'}

if __name__=='__main__':
 res=run();file=Path(__file__).resolve().parent/'runtime_stress_results.json';file.write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
