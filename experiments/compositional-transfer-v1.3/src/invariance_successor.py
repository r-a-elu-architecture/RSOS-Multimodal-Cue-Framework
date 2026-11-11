"""Context-stability v1.4 successor to the archived RSOS v1.3 synthetic benchmark.

Policies have the same 24 calibration observations and action space; synthetic
outcome generator never enters selection logic. Generic identical controls tie.
No human or physiological outcomes. Run from the v1.3 src/ directory.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import transfer_benchmark as b

STYLES = ("relation", "flat", "all_pairs")

def flat(ids, y, q):
    n = np.bincount(ids, minlength=b.NA)
    sums = np.bincount(ids, weights=y, minlength=b.NA)
    return ((sums + .5*y.mean()) / (n + .5))[q]

def predictions(ids, ctx, actions, y, report, seed, wi, pid):
    """Three-fold calibration-only predictions, folds from original v1.3."""
    n=len(y)
    folds=np.random.default_rng(seed+21378*wi+1033*pid).permutation(n)
    out={key:np.full(n,np.nan) for key in STYLES}
    for val in np.array_split(folds,3):
        train=np.setdiff1d(np.arange(n),val)
        out["flat"][val]=flat(ids[train],y[train],ids[val])
        for kind,alpha in (("relation",2.5),("all_pairs",3.5)):
            xt=b.matrix(actions[train],ctx[train],report,style=kind)
            xv=b.matrix(actions[val],ctx[val],report,style=kind)
            out[kind][val]=b.predict_dual(xt,y[train],xv,alpha)
    assert all(np.isfinite(v).all() for v in out.values())
    return out

def scores(y,ctx,cv,weight):
    """CV MSE plus context-wise signed bias variance (observable calibration)."""
    out={}
    for kind,pred in cv.items():
        residual=y-pred
        bias=[float(residual[ctx==c].mean()) for c in range(b.N_C) if (ctx==c).any()]
        mse=float(np.mean(residual**2))
        out[kind]=mse+weight*(float(np.var(bias)) if len(bias)>1 else 0.)
    return out

def synthetic_person(seed,wi,pid,calibration,tests,ood):
    world_name=b.WORLDS[wi]
    rng=np.random.default_rng(seed+700009*wi+2003*pid)
    world=b.generate_world(seed,world_name,pid)
    report=world[-1]
    ids,ctx=b.calibrate(rng,calibration,False)
    if ood and world_name=="novel_context_drift":
        ctx=np.where(ctx==3,np.random.default_rng(seed+31393*wi+1337*pid).integers(0,3,len(ctx)),ctx)
    actions=b.ARMS[ids]
    y=b.actual(actions,ctx,world)+np.random.default_rng(seed+82371*wi+17779*pid).normal(0,.20,calibration)
    target=np.random.default_rng(seed+88091*wi+29027*pid).integers(0,b.N_C,tests)
    if world_name=="novel_context_drift":target[::2]=3
    return world,report,ids,ctx,actions,y,target

def run(seed,people=48,tests=16,calibration=24,weight=.5,threshold=.23,hard_ood=False,temperature=.025):
    if people<1 or tests<1 or calibration<6 or weight<0 or temperature<=0:
        raise ValueError("invalid settings")
    rows=[]
    for wi,world_name in enumerate(b.WORLDS):
        for pid in range(people):
            world,report,ids,ctx,actions,y,target=synthetic_person(seed,wi,pid,calibration,tests,hard_ood)
            cv=predictions(ids,ctx,actions,y,report,seed,wi,pid)
            guard=scores(y,ctx,cv,weight)
            plain=scores(y,ctx,cv,0.)
            kind_guard=min(STYLES,key=lambda k:guard[k])
            kind_plain=min(STYLES,key=lambda k:plain[k])
            kind_cv="relation" if plain["relation"]<=plain["flat"] else "flat"
            family=b.FAMILY[actions[:,0]]
            ssb=sum((family==f).sum()*(y[family==f].mean()-y.mean())**2
                    for f in range(b.N_F) if (family==f).any())
            eta=float(ssb)/(float(np.sum((y-y.mean())**2))+1e-12)
            kind_gate="relation" if eta>=threshold else "flat"
            fitted={}
            fitted["flat"]=np.tile(flat(ids,y,np.arange(b.NA)),(b.N_C,1))
            for k,alpha in (("relation",2.5),("all_pairs",3.5)):
                x=b.matrix(actions,ctx,report,style=k)
                z=b.matrix(b.CAN_A,b.CAN_C,report,style=k)
                fitted[k]=b.predict_dual(x,y,z,alpha).reshape(b.N_C,b.NA)
            def blend(risks):
                r=np.array([risks[k] for k in STYLES])
                u=np.exp(-(r-r.min())/temperature)
                u=u/u.sum()
                return sum(float(u[i])*fitted[k] for i,k in enumerate(STYLES))
            fitted["blend_guard"]=blend(guard)
            fitted["blend_plain"]=blend(plain)
            choices={"invariance_guard":kind_guard,
                     "generic_same_invariance":kind_guard,
                     "invariance_blend":"blend_guard",
                     "generic_same_blend":"blend_guard",
                     "generic_threeway_blend":"blend_plain",
                     "generic_threeway_cv":kind_plain,
                     "generic_cv_selector":kind_cv,
                     "rsia_evidence_gate":kind_gate,
                     "generic_same_gate":kind_gate,
                     "flat_arm":"flat",
                     "generic_all_pairs":"all_pairs",
                     "rsos_relational":"relation"}
            # Test oracle is not used until model decisions have been computed.
            actual=b.actual(b.CAN_A,b.CAN_C,world).reshape(b.N_C,b.NA)
            for j,c in enumerate(target):
                optimal=float(actual[c].max())
                for model,kind in choices.items():
                    picked=int(np.argmax(fitted[kind][c]))
                    rows.append((seed,world_name,pid,j,model,picked,optimal-float(actual[c,picked]),kind))
                rows.append((seed,world_name,pid,j,"oracle",int(actual[c].argmax()),0.,"oracle"))
    return pd.DataFrame(rows,columns=["seed","world","person","trial","model","selected_program","regret","selected_model"])

def exact_tie(df,first,second):
    order=["seed","world","person","trial"]
    a=df[df.model==first].sort_values(order)
    z=df[df.model==second].sort_values(order)
    return bool(np.array_equal(a.selected_program,z.selected_program) and np.array_equal(a.regret,z.regret))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",nargs="+",type=int,required=True)
    p.add_argument("--people",type=int,default=48)
    p.add_argument("--tests",type=int,default=16)
    p.add_argument("--weight",type=float,default=.5)
    p.add_argument("--temperature",type=float,default=.025)
    p.add_argument("--threshold",type=float,default=.23)
    p.add_argument("--hard-ood",action="store_true")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=pd.concat([run(seed,people=a.people,tests=a.tests,weight=a.weight,
                     threshold=a.threshold,hard_ood=a.hard_ood,
                     temperature=a.temperature) for seed in a.seed],ignore_index=True)
    a.output.mkdir(parents=True,exist_ok=True)
    result.to_csv(a.output/"trials.csv",index=False)
    result.groupby(["model"],as_index=False).regret.agg(["mean","count"]).to_csv(a.output/"means.csv")
    result.groupby(["world","model"],as_index=False).regret.mean().to_csv(a.output/"world_means.csv",index=False)
    result.groupby(["seed","world","person","model"],as_index=False).regret.mean().to_csv(a.output/"person_blocks.csv",index=False)
    assert exact_tie(result,"invariance_guard","generic_same_invariance")
    assert exact_tie(result,"invariance_blend","generic_same_blend")
    print("rows",len(result))
    print(result.groupby("model").regret.mean().sort_values().to_string())
if __name__=="__main__":main()
