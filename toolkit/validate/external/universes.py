"""Random-universe benchmark: each universe is a population generator drawn from a broad family that was
NOT designed around rsos_cue (random structure, shared effects, 1-8 hidden person types, report reliability
from inverted to trustworthy, non-Gaussian noise, nonlinear links, binary outcomes, wrong declared families).
Every method sees identical data. Clusters for inference = universes."""
from __future__ import annotations
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent
import sys, time, warnings, numpy as np, pandas as pd
sys.path[:0] = [str(_HERE.parents[1])]
from rsos_cue import ProgramSpace, ArchetypeBank, CueSession
from multiprocessing import Pool
warnings.filterwarnings('ignore')
COMP = ['fam', 'glyph', 'sound', 'plan', 'ctx', 'ctxglyph', 'glyphsound', 'glyphsoundctx', 'program']
N_DEV, N_TEST, CAL, N_EVAL = 240, 48, 24, 8
lu = lambda r, a, b: float(np.exp(r.uniform(np.log(a), np.log(b))))

class Universe:
    def __init__(self, u):
        r = np.random.default_rng([9001, u]); self.r = r; self.u = u
        self.G, self.S, self.P, self.C = int(r.integers(6, 13)), int(r.integers(2, 5)), int(r.integers(2, 4)), int(r.integers(2, 5))
        F = int(r.integers(2, min(6, self.G // 2) + 1))
        while True:
            fam = r.integers(0, F, self.G)
            if len(set(fam)) == F: break
        self.fam = fam; self.F = F
        dec = fam.copy(); self.wrong = 0.0
        if r.random() < .5:
            self.wrong = r.uniform(.2, .6); idx = r.choice(self.G, int(round(self.wrong * self.G)), replace=False); dec[idx] = r.integers(0, F, len(idx))
        self.declared = dec
        self.shape = dict(fam=F, glyph=self.G, sound=self.S, plan=self.P, ctx=self.C, ctxglyph=(self.C, self.G),
                          glyphsound=(self.G, self.S), glyphsoundctx=(self.G, self.S, self.C), program=(self.G, self.S, self.P))
        self.mean = {c: r.normal(0, lu(r, .01, .25), self.shape[c]) * (r.random() < .6) for c in COMP}
        self.T = int(r.integers(1, 9)); self.tw = r.dirichlet(np.ones(self.T))
        self.types = [dict(sd={c: lu(r, .005, .35) * (r.random() < .7) for c in COMP}, lam=r.uniform(-.5, 1.2),
                           rep=lu(r, .05, .5), noise=lu(r, .05, .4)) for _ in range(self.T)]
        self.noise_kind = r.choice(['gauss', 't3', 'skew']); self.link = r.choice(['identity', 'tanh', 'threshold'])
        self.binary = r.random() < .3
        self.desc = dict(universe=u, G=self.G, S=self.S, P=self.P, C=self.C, F=F, wrong_families=round(self.wrong, 2), types=self.T,
                         noise=self.noise_kind, link=self.link, binary=bool(self.binary))

    def person(self, seed):
        r = np.random.default_rng([9002, self.u, seed]); t = self.types[r.choice(self.T, p=self.tw)]
        th = {c: self.mean[c] + r.normal(0, t['sd'][c], self.shape[c]) for c in COMP}
        G, S, P, C = self.G, self.S, self.P, self.C
        g, s, p, c = np.meshgrid(np.arange(G), np.arange(S), np.arange(P), np.arange(C), indexing='ij')
        lin = (th['fam'][self.fam[g]] + th['glyph'][g] + th['sound'][s] + th['plan'][p] + th['ctx'][c] + th['ctxglyph'][c, g]
               + th['glyphsound'][g, s] + th['glyphsoundctx'][g, s, c] + th['program'][g, s, p])
        z = lin / (lin.std() + 1e-9) * .3 if lin.std() > 0 else lin
        f = {'identity': lin, 'tanh': .3 * np.tanh(z / .3 * 1.5), 'threshold': .3 * (z > np.quantile(z, .7)) + .1 * z}[self.link]
        util = 1 / (1 + np.exp(-4 * f)) if self.binary else .5 + f          # expected outcome; argmax target
        util = np.moveaxis(util, 3, 0).reshape(C, G * S * P)                # (context, program id)
        rep = np.r_[t['lam'] * (th['fam'][self.fam] + th['glyph']) + r.normal(0, t['rep'], G), t['lam'] * th['sound'] + r.normal(0, t['rep'], S)]
        return util, rep, t['noise'], r

    def draw(self, util, nsd, r, prog, ctx):
        m = util[ctx, prog]
        if self.binary: return (r.random(len(m)) < m).astype(float)
        e = {'gauss': r.normal(0, 1, len(m)), 't3': r.standard_t(3, len(m)) / np.sqrt(3), 'skew': (r.exponential(1, len(m)) - 1)}[self.noise_kind]
        return m + nsd * e

def ridge_pp(sp, prog, ctx, y, alpha=2.5):
    X = sp.design(sp.programs[prog], ctx); Xc = sp.Xcand
    w = np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ (y - y.mean())); return (y.mean() + Xc @ w).reshape(sp.n_context, -1)

def gp_pp(sp, prog, ctx, y):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
    oh = lambda a, c: np.c_[np.eye(sp.n_glyph)[a[:, 0]], np.eye(sp.n_sound)[a[:, 1]], np.eye(sp.n_plan)[a[:, 2]], np.eye(sp.n_context)[c]]
    gp = GaussianProcessRegressor(ConstantKernel() * RBF(1.0) + WhiteKernel(.1), normalize_y=True).fit(oh(sp.programs[prog], ctx), y)
    return gp.predict(oh(sp.programs[sp.cand_prog], sp.cand_ctx)).reshape(sp.n_context, -1)

def run_universe(u):
    t0 = time.time(); U = Universe(u); rows = []
    sp_d = ProgramSpace(U.G, U.S, U.P, U.C, families=list(U.declared)); sp_g = ProgramSpace(U.G, U.S, U.P, U.C, families=None)
    NP = sp_d.n_program
    def hist(seed):
        util, rep, nsd, r = U.person(seed); prog = r.integers(0, NP, CAL); ctx = r.integers(0, U.C, CAL)
        return dict(programs=sp_d.programs[prog], contexts=ctx, outcomes=U.draw(util, nsd, r, prog, ctx), reports=rep), (util, rep, nsd, r, prog, ctx)
    devh = [hist(i)[0] for i in range(N_DEV)]
    B8 = ArchetypeBank(sp_d).fit(devh, K=8, seed=1); G8 = ArchetypeBank(sp_g).fit(devh, K=8, seed=1)
    B1 = ArchetypeBank(sp_d, contain_mass=0, self_archetype=False).fit(devh, K=1)
    probe = lambda b: ArchetypeBank(b.space, b.H, b.pi, b.contain_mass, False, b.self_penalty, b.meta, b.mu, b.rep_mean)
    for i in range(N_TEST):
        h, (util, rep, nsd, r, prog, ctx) = hist(10_000 + i); y = h['outcomes']
        ev = np.random.default_rng([9003, u, i]).integers(0, U.C, N_EVAL)
        def score(name, pred, probes='random'):
            for c in ev:
                k = int(np.argmax(pred[c])); rows.append((u, i, name, probes, float(util[c].max() - util[c, k])))
        def sess(bank, prg=prog, cx=ctx, yy=y, explore=8):
            s = CueSession(bank, reports=rep, explore=explore, seed=i)
            for pp, cc, v in zip(prg, cx, yy): s.add(*map(int, sp_d.programs[pp]), int(cc), float(v))
            return s
        score('population_only', B1.offset().reshape(U.C, NP)); score('per_person_ridge', ridge_pp(sp_d, prog, ctx, y))
        score('per_person_gp', gp_pp(sp_d, prog, ctx, y)); score('hier_bayes_K1', sess(B1).predict())
        score('rsos_cue_generic', sess(G8).predict()); score('rsos_cue', sess(B8).predict())
        for name, rule, bank in (('rsos_cue', 'project', B8), ('rsos_cue', 'thompson', B8), ('rsos_cue', 'ucb', B8), ('hier_bayes_K1', 'thompson', B1)):
            rr = np.random.default_rng([9004, u, i]); s = sess(probe(bank) if bank is B8 else bank, [], [], [], explore=8 if rule == 'project' else 0)
            P_, C_, Y_ = [], [], []
            for t in range(CAL):
                if rule == 'project':
                    q = s.next_probe(); pp = int(sp_d.program_id(q['glyph'], q['sound'], q['plan'])); cc = q['context']
                else:
                    m, v = s.posterior(); sc = rr.normal(m, np.sqrt(v)) if rule == 'thompson' else m + np.sqrt(v)
                    j = int(np.argmax(sc)); pp, cc = int(sp_d.cand_prog[j]), int(sp_d.cand_ctx[j])
                v_ = float(U.draw(util, nsd, rr, np.array([pp]), np.array([cc]))[0])
                s.add(*map(int, sp_d.programs[pp]), cc, v_); P_.append(pp); C_.append(cc); Y_.append(v_)
            final = sess(bank, np.array(P_), np.array(C_), np.array(Y_))
            score(name, final.predict(), probes=rule)
    print('universe', u, U.desc, round(time.time() - t0), 's', flush=True)
    return rows, U.desc

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 24; procs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    with Pool(procs) as pool: res = pool.map(run_universe, range(n))
    d = pd.DataFrame([x for r_, _ in res for x in r_], columns=['universe', 'person', 'method', 'probes', 'regret'])
    d.to_csv(_HERE / 'results_universes.csv', index=False); pd.DataFrame([dsc for _, dsc in res]).to_csv(_HERE / 'universes.csv', index=False)
    print(d.groupby(['probes', 'method']).regret.mean().round(4).sort_values().to_string())
