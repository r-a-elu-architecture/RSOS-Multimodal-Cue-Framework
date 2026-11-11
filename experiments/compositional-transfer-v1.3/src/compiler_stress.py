"""Bounded randomized structural test of arbitrary tier intervals and glyph-chain program DAGs."""
import random,json,time
from pathlib import Path
from program_graph import compile_program
OPS=['interrupt','resource_recall','breath','swish_visual','future_rehearsal','mnemonic','posture','grounding','dual_attention_prompt','reflect']

def gen(r,i,bad=False):
 count=r.randrange(1,9);ids=[f'n{j}' for j in range(count)]
 nodes=[{'node_id':k,'operator':r.choice(OPS),'next':ids[j+1:j+2]} for j,k in enumerate(ids)]
 tiers=r.choice([None,(1,10),(1,20),(20,23),(605,605),(300,605)])
 p={'id':f'v{i}','context':r.choice(['social','user_marked_color','personal_practice']),
 'tier_start':tiers[0] if tiers else None,'tier_end':tiers[1] if tiers else None,
 'glyph_chain':[f'g{j}' for j in range(r.randint(1,4))],
 'ops':[r.choice(OPS)], 'channels':r.sample(['visual','audio','kinesthetic'],k=r.randrange(1,4)),
 'goal':'user-defined', 'entry':'n0','nodes':nodes}
 if bad:
  typ=r.choice(['cycle','dangling','range','operator'])
  if typ=='cycle':p['nodes'][-1]['next']=['n0']
  elif typ=='dangling':p['nodes'][0]['next']=['not_here']
  elif typ=='range':p['tier_start']=50;p['tier_end']=20
  elif typ=='operator':p['nodes'][0]['operator']='undefined_operator'
 return p

def run(n=50000,seed=121212):
 r=random.Random(seed);okay=0;rejected=0;mistakes=0
 t=time.perf_counter()
 for i in range(n):
  invalid=(i%4==0)
  p=gen(r,i,invalid)
  try: c=compile_program(p);approved=True
  except ValueError: approved=False
  mistakes+=int(approved==invalid)
  okay+=int(approved);rejected+=int(not approved)
 sec=time.perf_counter()-t
 return {'compiled_valid':okay,'rejected_corrupt':rejected,'structural_mismatches':mistakes,'randomized_programs':n,'seconds':sec,'programs_per_second':n/sec}
if __name__=='__main__':
 res=run();(Path(__file__).resolve().parent/'compiler_stress_results.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
