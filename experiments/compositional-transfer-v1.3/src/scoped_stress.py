"""Stress tests scope, reuse, rebindings with an independent dictionary oracle."""
import argparse,csv,json,random
from pathlib import Path
from scoped_cue_registry import CueRegistry

def run(seed=9013,n=100000):
    r=random.Random(seed);registry=CueRegistry();oracle={};revoked=set()
    persons=[f'p{i:03d}' for i in range(100)]
    contexts=['neutral_learning','visual_color','practice','mnemonic','recovery']
    glyphs=['LION','DRAGON','BEAR','EAGLE','LIGHT','BLUE','MNEMONIC']
    # Same glyph reused across different individuals and contexts with independently declared meanings.
    for person in persons:
        for c in contexts:
            for g in glyphs:
                meaning=f'private-user-defined-{r.getrandbits(40):010x}'
                b=registry.bind(person,c,g,meaning)
                oracle[(person,c,g)]=[meaning,1]
    valid=0;denied=0;mismatch=0;wrong_global=0
    global_table={}
    for k,b in registry.current.items():global_table[k[2]]=b.meaning
    for i in range(n):
        person=r.choice(persons);context=r.choice(contexts);glyph=r.choice(glyphs)
        key=(person,context,glyph)
        if i%211==0:
            meaning=f'modified-{r.getrandbits(30):08x}'
            b=registry.bind(person,context,glyph,meaning)
            oracle[key]=[meaning,oracle[key][1]+1]
            revoked.discard((key,oracle[key][1]))
        if i%977==0:
            registry.revoke(*key)
            revoked.add((key,oracle[key][1]))
        queried_revision=oracle[key][1] if r.random()<.7 else oracle[key][1]-1
        consent=r.random()<.8;confidence=r.random()
        actual,why=registry.resolve(person,context,glyph,queried_revision,consent,confidence)
        expected=(consent and confidence>=.65 and queried_revision==oracle[key][1] and (key,oracle[key][1]) not in revoked)
        if bool(actual)!=bool(expected):mismatch+=1
        if actual is not None:
            valid+=1
            if actual.meaning!=oracle[key][0]:mismatch+=1
            if global_table.get(glyph)!=actual.meaning:wrong_global+=1
        else:denied+=1
    return {'seed':seed,'requests':n,'scoped_authorized':valid,'denied':denied,'unexpected_results':mismatch,'naive_global_symbol_collisions_among_authorized':wrong_global,'scope_bindings':len(oracle),'note':'Global table is intentionally missing person and context; collision comparison is an engineered scope counterexample, not a general SOTA benchmark.'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',default='results/scoped_stress.json');q=a.parse_args()
    result=run();p=Path(q.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
