"""Paired bootstrap contrasts for the real-data and random-universe benchmarks."""
import pathlib as _pl, sys, numpy as np, pandas as pd
H = _pl.Path(__file__).resolve().parent
pd.set_option('display.width', 250)

def paired(d, key, ref, others, cluster, B=4000, seed=7):
    p = d.pivot_table(index=cluster, columns=key, values='regret', aggfunc='mean')
    g = np.random.default_rng(seed); out = []
    top = p.index.get_level_values(0).unique() if isinstance(p.index, pd.MultiIndex) else p.index
    for o in others:
        if o not in p or ref not in p: continue
        diff = (p[o] - p[ref])
        if isinstance(p.index, pd.MultiIndex):
            groups = [diff.loc[t].to_numpy() for t in top]
            reps = [np.mean([np.mean(groups[i][g.integers(0, len(groups[i]), len(groups[i]))]) for i in g.integers(0, len(groups), len(groups))]) for _ in range(B)]
            wins = int(sum(np.mean(x) > 0 for x in groups)); n = len(groups)
        else:
            x = diff.to_numpy(); reps = [np.mean(x[g.integers(0, len(x), len(x))]) for _ in range(B)]; wins, n = None, len(x)
        out.append(dict(comparison=f'{o}  vs  {ref}', regret_other=round(p[o].mean(), 4), regret_ref=round(p[ref].mean(), 4),
                        ref_better_by_pct=round(100 * (p[o].mean() - p[ref].mean()) / p[o].mean(), 1),
                        ci_low=round(np.percentile(reps, 2.5), 4), ci_high=round(np.percentile(reps, 97.5), 4), clusters_ref_wins=wins, n=n))
    return pd.DataFrame(out)

if __name__ == '__main__':
    for ds in ('movielens', 'goodbooks'):
        f = H / f'results_real_{ds}.csv'
        if not f.exists(): continue
        d = pd.read_csv(f); d['key'] = d.method + '|' + d.probes
        print(f'\n===== {ds}: {d.user.nunique()} test users ====='); print(d.groupby('key')[['regret', 'hit']].mean().round(4).sort_values('regret').to_string())
        others = [k for k in d.key.unique()]
        for ref in ('rsos_cue_links|project', 'rsos_cue_links|random', 'rsos_cue|random', 'matrix_factorization|rsos_cue_links_probes'):
            if ref in others: print(paired(d, 'key', ref, [k for k in others if k != ref], 'user').sort_values('regret_other').to_string(index=False))

    f = H / 'results_universes.csv'
    if f.exists():
        d = pd.read_csv(f); d['key'] = d.method + '|' + d.probes
        print(f'\n===== random universes: {d.universe.nunique()} universes ====='); print(d.groupby('key').regret.mean().round(4).sort_values().to_string())
        for ref in ('rsos_cue|project', 'rsos_cue|random'):
            print(paired(d, 'key', ref, [k for k in d.key.unique() if k != ref], ['universe', 'person']).sort_values('regret_other').to_string(index=False))
        u = pd.read_csv(H / 'universes.csv'); w = d[d.probes == 'random'].pivot_table(index='universe', columns='method', values='regret')
        w['rsos_minus_best_other'] = w['rsos_cue'] - w.drop(columns='rsos_cue').min(1)
        print(u.merge(w[['rsos_cue', 'per_person_ridge', 'hier_bayes_K1', 'rsos_minus_best_other']].round(4), left_on='universe', right_index=True).to_string(index=False))
