"""Research-only compositional cue-program selection benchmark.
All preferences and outcomes are SIMULATED and NOT physiological or therapeutic effects.
Same candidate actions and calibration observations are available to every controller.
Source-inspired relational encoding is checked against a generic exact-match relation model.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

N_G=12; N_S=5; N_P=3; N_C=4; N_F=4
ARMS=np.array([(g,s,p) for g in range(N_G) for s in range(N_S) for p in range(N_P)],dtype=int)
NA=len(ARMS)
CAN_A=np.tile(ARMS,(N_C,1))
CAN_C=np.repeat(np.arange(N_C),NA)
FAMILY=np.repeat(np.arange(N_F),3)
WORLDS=['family_transfer','family_program_synergy','context_reversal','idiosyncratic_glyphs','unstructured_actions','sensor_report_noise','novel_context_drift','null_effect']
MODELS=('fixed_global','flat_arm','generic_additive','generic_all_pairs','rsos_relational','generic_same_relations','shuffled_relations','rsia_evidence_gate','generic_same_gate','generic_cv_selector','oracle')

def onehot(vals,n):return np.eye(n,dtype=np.float32)[vals]

def matrix(actions,contexts,report, family=FAMILY,style='relation'):
    actions=np.asarray(actions);contexts=np.asarray(contexts);r=np.asarray(report)
    g,s,p=actions.T;f=family[g]
    eg=onehot(g,N_G);es=onehot(s,N_S);ep=onehot(p,N_P);ec=onehot(contexts,N_C);ef=onehot(f,N_F)
    main=np.column_stack([eg,es,ep,ec, r[g],r[N_G+s]])
    if style=='additive': return np.asarray(main,dtype=np.float32)
    gp=(eg[:,:,None]*ep[:,None,:]).reshape(len(g),-1)
    gs=(eg[:,:,None]*es[:,None,:]).reshape(len(g),-1)
    sc=(es[:,:,None]*ec[:,None,:]).reshape(len(g),-1)
    if style=='all_pairs':return np.asarray(np.column_stack([main,gp,gs,sc]),dtype=np.float32)
    fc=(ef[:,:,None]*ec[:,None,:]).reshape(len(g),-1)
    fp=(ef[:,:,None]*ep[:,None,:]).reshape(len(g),-1)
    return np.asarray(np.column_stack([main,ef,fc,fp]),dtype=np.float32)

def predict_dual(x,y,xt,penalty):
    # Bayesian ridge in dual space; center features and outcomes, shrink toward sampled mean.
    mu=np.mean(x,axis=0);xm=x-mu;xq=xt-mu;y0=np.mean(y)
    gram=xm@xm.T + penalty*np.eye(len(y))
    weights=np.linalg.solve(gram,y-y0)
    return y0 + xq@(xm.T@weights)

def generate_world(seed,world,person):
    r=np.random.default_rng(seed + WORLDS.index(world)*1000003 + person*30427)
    fam=r.normal(0,.17,N_F); glyph=r.normal(0,.065,N_G);sound=r.normal(0,.11,N_S);program=r.normal(0,.075,N_P)
    ctxfam=r.normal(0,.08,(N_C,N_F));famp=r.normal(0,.075,(N_F,N_P))
    rawarm=r.normal(0,.025,NA);w_noise=.14
    if world=='family_transfer':fam*=1.45; glyph*=.55;ctxfam*=1.5
    elif world=='family_program_synergy':fam*=1.25;famp*=2.5;glyph*=.7
    elif world=='context_reversal':ctxfam[1]=-ctxfam[0]*1.8;ctxfam[2]=-ctxfam[3]*1.3
    elif world=='idiosyncratic_glyphs':fam*=0;glyph*=4.5;famp*=0;ctxfam*=0
    elif world=='unstructured_actions':fam*=0;glyph*=0;sound*=0;program*=0;famp*=0;ctxfam*=0;rawarm=r.normal(0,.27,NA)
    elif world=='sensor_report_noise':w_noise=.55
    elif world=='novel_context_drift':ctxfam[3]=r.normal(0,.32,N_F);glyph*=1.7
    elif world=='null_effect':fam*=0;glyph*=0;sound*=0;program*=0;famp*=0;ctxfam*=0;rawarm*=0
    report=np.r_[fam[FAMILY]+glyph+r.normal(0,w_noise,N_G),sound+r.normal(0,w_noise*.8,N_S)]
    return (fam,glyph,sound,program,ctxfam,famp,rawarm,report)

def actual(a,c,world):
    fam,gl,so,pr,cf,fp,arm,_=world
    g,s,p=np.asarray(a).T;c=np.asarray(c)
    idx=g*(N_S*N_P)+s*N_P+p
    return .40+fam[FAMILY[g]]+gl[g]+so[s]+pr[p]+cf[c,FAMILY[g]]+fp[FAMILY[g],p]+arm[idx]

def calibrate(rng,n,balanced=False):
    if not balanced:
        i=rng.integers(0,NA,n);c=rng.integers(0,N_C,n)
        return i,c
    # Prespecified coverage-based (not reward-optimized) design, equal samples and no oracle access.
    # Greedy balanced sampling over glyph families, sounds, operators and contexts.
    candidates=np.arange(NA*N_C)
    counts={'f':np.zeros(N_F),'s':np.zeros(N_S),'p':np.zeros(N_P),'c':np.zeros(N_C)}
    chosen=[]
    for k in range(n):
        proposal=rng.choice(candidates,size=128,replace=False)
        ids=proposal%NA;ctx=proposal//NA; aa=ARMS[ids];f=FAMILY[aa[:,0]]
        score=1/(1+counts['f'][f])+1/(1+counts['s'][aa[:,1]])+1/(1+counts['p'][aa[:,2]])+1/(1+counts['c'][ctx])
        score+=rng.normal(0,1e-6,len(score))
        j=int(np.argmax(score));pick=int(proposal[j]);chosen.append(pick)
        index=pick%NA;ct=pick//NA;g,s,p=ARMS[index]
        counts['f'][FAMILY[g]]+=1;counts['s'][s]+=1;counts['p'][p]+=1;counts['c'][ct]+=1
    arr=np.array(chosen);return arr%NA,arr//NA

def run(seed=6001,people=45,calibration=24,tests=12,design='random',threshold=.23,hard_ood=False):
    records=[]; decisions=[]
    for wi,wname in enumerate(WORLDS):
      for pid in range(people):
        rr=np.random.default_rng(seed + 700009*wi + 2003*pid)
        world=generate_world(seed,wname,pid)
        report=world[-1]
        ids,ctx=calibrate(rr,calibration,design=='balanced')
        if hard_ood and wname=='novel_context_drift':
            ctx=np.where(ctx==3,np.random.default_rng(seed+31393*wi+1337*pid).integers(0,3,len(ctx)),ctx)
        actions=ARMS[ids]
        y=actual(actions,ctx,world)+np.random.default_rng(seed + 82371*wi + 17779*pid).normal(0,.20,calibration)
        # Out of calibration arm-context combinations are evaluated; same person, no hidden access.
        tctx=np.random.default_rng(seed + 88091*wi + 29027*pid).integers(0,N_C,tests)
        if wname=='novel_context_drift':tctx[::2]=3
        shuffled=FAMILY.copy();shuffler=np.random.default_rng(seed+41003*wi+pid);shuffler.shuffle(shuffled)
        matrices={}
        for style in ('additive','all_pairs','relation'):
            matrices[style]=(matrix(actions,ctx,report,style=style),matrix(CAN_A,CAN_C,report,style=style))
        matrices['shuffle']=(matrix(actions,ctx,report,shuffled),matrix(CAN_A,CAN_C,report,shuffled))
        preds={}
        for style,pol,alpha in [('additive','generic_additive',2.5),('all_pairs','generic_all_pairs',3.5),('relation','rsos_relational',2.5),('shuffle','shuffled_relations',2.5)]:
            x,xt=matrices[style]
            preds[pol]=predict_dual(x,y,xt,alpha).reshape(N_C,NA)
        preds['generic_same_relations']=preds['rsos_relational'].copy()
        # Evidence watchdog is a testable standard statistical ANOVA gate, not a neuroscience algorithm.
        family_id=FAMILY[actions[:,0]]
        sst=float(np.sum((y-y.mean())**2))+1e-12
        ssb=float(sum(np.sum(family_id==i)*(y[family_id==i].mean()-y.mean())**2 for i in range(N_F) if np.any(family_id==i)))
        eta=ssb/sst
        # Strong generic fallback can compute identical test; exact tie is a required negative control.
        use_relation=eta>=threshold
        # 3-fold CV selector: generic model selection from the SAME observations, no oracle.
        folds=np.random.default_rng(seed+21378*wi+1033*pid).permutation(calibration)
        score_rel=0.;score_flat=0.;vcount=0
        for fold in np.array_split(folds,3):
            keep=np.setdiff1d(np.arange(calibration),fold)
            if len(keep)<4 or len(fold)==0:continue
            x_train=matrices['relation'][0][keep]
            x_val=matrices['relation'][0][fold]
            pv=predict_dual(x_train,y[keep],x_val,2.5)
            # If no arm observed in a fold, this estimator backs off to the personal mean.
            flatv=np.array([(.5*np.mean(y[keep])+np.sum(y[keep][ids[keep]==ids[k]]))/(.5+np.sum(ids[keep]==ids[k])) for k in fold])
            score_rel+=float(np.sum((pv-y[fold])**2));score_flat+=float(np.sum((flatv-y[fold])**2));vcount+=len(fold)
        prefer_relation=(score_rel <= score_flat)
        
        # Flat: per arm sample estimate, shrink to mean, with no extrapolation over unseen combinations.
        flat=np.array([(y[ids==i].sum()+.5*y.mean())/(np.sum(ids==i)+.5) for i in range(NA)])
        preds['flat_arm']=np.tile(flat,(N_C,1))
        preds['rsia_evidence_gate']=preds['rsos_relational'] if use_relation else preds['flat_arm']
        preds['generic_same_gate']=preds['rsia_evidence_gate'].copy()
        preds['generic_cv_selector']=preds['rsos_relational'] if prefer_relation else preds['flat_arm']
        # Fixed: one global program, no within-person contextual choice.
        fix=0;preds['fixed_global']=np.tile(np.eye(NA)[fix],(N_C,1))
        all_true=actual(CAN_A,CAN_C,world).reshape(N_C,NA)
        for j,c in enumerate(tctx):
            ideal=float(np.max(all_true[c]));opt=int(np.argmax(all_true[c]))
            for pol in MODELS:
                if pol=='oracle':pick=opt
                elif pol=='fixed_global':pick=fix
                else:pick=int(np.argmax(preds[pol][c]))
                records.append((seed,wname,pid,j,pol,float(all_true[c,pick]),ideal-float(all_true[c,pick]),int(pick),int(c),design,float(eta),bool(use_relation) if pol in ('rsia_evidence_gate','generic_same_gate') else (bool(prefer_relation) if pol=='generic_cv_selector' else None),bool(hard_ood)))
      
    return pd.DataFrame(records,columns=['seed','world','person','trial','model','utility','regret','selected_program','context','design','eta','uses_relation','hard_ood'])

def summarize(df):
    out=df.groupby(['seed','model']).agg(utility=('utility','mean'),regret=('regret','mean'),n=('regret','size')).reset_index()
    worlds=df.groupby(['world','model']).agg(utility=('utility','mean'),regret=('regret','mean')).reset_index()
    return out,worlds

def contrast(df, ref='rsos_relational', bootstrap=3000, seed=99):
    # Cluster by independent world then person, not by within-person trials.
    p=df.groupby(['seed','world','person','model'])['regret'].mean().unstack('model').reset_index()
    rng=np.random.default_rng(seed);v=[]
    for other in ['fixed_global','flat_arm','generic_additive','generic_all_pairs','generic_same_relations','shuffled_relations','rsia_evidence_gate','generic_same_gate','generic_cv_selector']:
        d=(p[other]-p[ref]).to_numpy()
        # two-stage bootstrap: scenarios are primary clusters, people are nested.
        groups=[]
        for _,x in p.groupby(['seed','world']):groups.append((x[other]-x[ref]).to_numpy())
        reps=[]
        for _ in range(bootstrap):
            ix=rng.integers(0,len(groups),len(groups))
            reps.append(float(np.mean([np.mean(groups[i][rng.integers(0,len(groups[i]),len(groups[i]))]) for i in ix])))
        v.append({'comparison':f'{ref} vs {other}', 'mean_regret_improvement':float(np.mean(d)),'ci_low':float(np.percentile(reps,2.5)),'ci_high':float(np.percentile(reps,97.5)),'world_seed_clusters':len(groups)})
    return pd.DataFrame(v)

def main():
    a=argparse.ArgumentParser();a.add_argument('--seed',nargs='+',type=int,default=[61001,61002,61003]);a.add_argument('--people',type=int,default=45);a.add_argument('--calibration',type=int,default=24);a.add_argument('--tests',type=int,default=12);a.add_argument('--output',default='results');a.add_argument('--design',choices=['random','balanced'],default='random');a.add_argument('--threshold',type=float,default=.23);a.add_argument('--hard-ood',action='store_true');q=a.parse_args()
    out=Path(q.output);out.mkdir(parents=True,exist_ok=True)
    all_runs=[]
    for seed in q.seed:
        all_runs.append(run(seed,q.people,q.calibration,q.tests,q.design,q.threshold,q.hard_ood))
        print('Completed seed',seed,flush=True)
    df=pd.concat(all_runs,ignore_index=True)
    summary,worlds=summarize(df)
    df.to_csv(out/'heldout_trials.csv',index=False)
    summary.to_csv(out/'results_by_seed.csv',index=False)
    worlds.to_csv(out/'results_by_world.csv',index=False)
    c=contrast(df);c.to_csv(out/'paired_cluster_bootstrap.csv',index=False)
    contrast(df,ref='rsia_evidence_gate').to_csv(out/'watchdog_vs_baselines.csv',index=False)
    print(summary.to_string(index=False));print('\nPAIRED CLUSTER CONTRASTS\n',c.to_string(index=False))
if __name__=='__main__':main()
