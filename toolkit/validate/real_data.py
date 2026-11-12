"""Real human data: MovieLens-1M (movies, families = primary genre) and goodbooks-10k (books, families = author).
Reframed as cue choice: each item is a 'program'; a user's rating is the outcome.
Per test user: 16 rated items = fixed decision set D; the other rated items = probe pool P; budget 24 probes.
Methods pick one item from D; regret = best rating in D - rating of the pick (stars).
Data is NOT redistributed; pass the dataset folder as argv[2]."""
from __future__ import annotations
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent
import sys, time, warnings, numpy as np, pandas as pd
sys.path[:0] = [str(_HERE.parent)]
from rsos_cue import ProgramSpace, ArchetypeBank, CueSession
warnings.filterwarnings('ignore')
DATASET, ROOT = sys.argv[1], _pl.Path(sys.argv[2])
N_TEST = int(sys.argv[3]) if len(sys.argv) > 3 else 300
BUDGET, ND = 24, 16

# ---------------- load ----------------
if DATASET == 'movielens':
    r = pd.read_csv(ROOT / 'ml/ratings.csv', sep='\t', index_col=0)[['user_id', 'movie_id', 'rating']]
    r.columns = ['user', 'item', 'rating']; NI = 100
    top = r.item.value_counts().index[:NI]
    mv = pd.read_csv(ROOT / 'ml/movies.csv', sep='\t', index_col=0, encoding='latin-1').set_index('movie_id')
    fam_label = [mv.loc[i, 'genres'].split('|')[0] for i in top]
else:
    r = pd.read_csv(ROOT / 'gb/ratings.csv'); r.columns = ['user', 'item', 'rating']; NI = 150
    top = r.item.value_counts().index[:NI]
    bk = pd.read_csv(ROOT / 'gb/books.csv').set_index('book_id')
    auth = [bk.loc[i, 'authors'].split(',')[0].strip() for i in top]
    cnt = pd.Series(auth).value_counts()
    fam_label = [a if cnt[a] >= 2 else f'solo:{i}' for i, a in zip(top, auth)]
r = r[r.item.isin(top)].drop_duplicates(['user', 'item'])
idx = {it: j for j, it in enumerate(top)}; r['j'] = r.item.map(idx)
labs = {l: k for k, l in enumerate(dict.fromkeys(fam_label))}; FAM = np.array([labs[l] for l in fam_label])
cnt = r.user.value_counts(); rng = np.random.default_rng(2026)
eligible = cnt[cnt >= ND + BUDGET + 16].index.to_numpy().copy(); rng.shuffle(eligible)
test_users = set(eligible[:N_TEST]); dev = r[~r.user.isin(test_users) & r.user.isin(cnt[cnt >= 24].index)]
print(DATASET, 'items', NI, 'families', FAM.max() + 1, 'dev users', dev.user.nunique(), 'test users', len(test_users), flush=True)

# ---------------- dev structures ----------------
mu_g = dev.rating.mean()
item_n = np.bincount(dev.j, minlength=NI); item_sum = np.bincount(dev.j, dev.rating, minlength=NI)
popularity = (item_sum + 5 * mu_g) / (item_n + 5)
du = {u: k for k, u in enumerate(dev.user.unique())}; U = len(du)
Rm = np.full((U, NI), np.nan); Rm[dev.user.map(du).to_numpy(), dev.j.to_numpy()] = dev.rating.to_numpy()

def als(R, k=10, lam=5.0, iters=12, seed=0):
    m = ~np.isnan(R); mu = np.nanmean(R); g = np.random.default_rng(seed)
    P = g.normal(0, .1, (R.shape[0], k)); Q = g.normal(0, .1, (R.shape[1], k)); bu = np.zeros(R.shape[0]); bi = np.zeros(R.shape[1])
    Y = np.nan_to_num(R - mu)
    for _ in range(iters):
        for side in (0, 1):
            A, B, bA, bB, M, YY = (P, Q, bu, bi, m, Y) if side == 0 else (Q, P, bi, bu, m.T, Y.T)
            Bx = np.c_[B, np.ones(len(B))]
            for a in range(len(A)):
                o = M[a]
                if not o.any(): continue
                X = Bx[o]; t = YY[a, o] - bB[o]
                sol = np.linalg.solve(X.T @ X + lam * np.eye(k + 1), X.T @ t); A[a], bA[a] = sol[:k], sol[k]
    return mu, P, Q, bu, bi

def mf_foldin(mf, items, ratings, lam):
    mu, P, Q, bu, bi = mf; k = Q.shape[1]; X = np.c_[Q[items], np.ones(len(items))]
    sol = np.linalg.solve(X.T @ X + lam * np.eye(k + 1), X.T @ (np.asarray(ratings) - mu - bi[items]))
    return mu + bi + Q @ sol[:k] + sol[k]

# choose MF regularization on a dev hold-out
hold = ~np.isnan(Rm) & (rng.random(Rm.shape) < .1); Rtr = np.where(hold, np.nan, Rm); best = None
for lam in (2.0, 5.0, 15.0):
    mf = als(Rtr, lam=lam, iters=8); mu, P, Q, bu, bi = mf; pred = mu + bu[:, None] + bi[None] + P @ Q.T
    e = np.sqrt(np.mean((pred[hold] - Rm[hold]) ** 2)); best = min(best or (9, 0), (e, lam))
MF_LAM = best[1]; MF = als(Rm, lam=MF_LAM); print('MF lambda', MF_LAM, 'dev RMSE', round(best[0], 3), flush=True)
Cd = Rm - np.nanmean(Rm, 1, keepdims=True); Cz = np.nan_to_num(Cd); Mz = ~np.isnan(Rm)

def knn(items, ratings, k=50):
    x = np.zeros(NI); m = np.zeros(NI, bool); xm = np.mean(ratings); x[items] = np.asarray(ratings) - xm; m[items] = True
    num = Cz[:, m] @ x[m]; den = np.sqrt((Cz[:, m] ** 2).sum(1) * (x[m] ** 2).sum()) + 1e-9
    ov = Mz[:, m].sum(1); sim = num / den * np.minimum(ov, 10) / 10
    out = np.full(NI, xm)
    for i in range(NI):
        cand = np.flatnonzero(Mz[:, i]); s = sim[cand]; top_ = cand[np.argsort(s)[-k:]]; s = sim[top_]; s = np.where(s > 0, s, 0)
        if s.sum() > 0: out[i] = xm + (s @ Cz[top_, i]) / s.sum()
    return out

def ridge_user(items, ratings, alpha=2.5):
    X = np.c_[np.eye(NI)[items], np.eye(FAM.max() + 1)[FAM[items]]]; Xa = np.c_[np.eye(NI), np.eye(FAM.max() + 1)[FAM]]
    y = np.asarray(ratings) - popularity[items]
    w = np.linalg.solve(X.T @ X + alpha * np.eye(X.shape[1]), X.T @ (y - y.mean()))
    return popularity + y.mean() + Xa @ w

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
FEAT = np.c_[np.eye(FAM.max() + 1)[FAM] * 1.0, np.eye(NI) * 0.7]
def gp_user(items, ratings):
    gp = GaussianProcessRegressor(ConstantKernel(1.0) * RBF(1.0) + WhiteKernel(.5), normalize_y=True, n_restarts_optimizer=0)
    y = np.asarray(ratings) - popularity[items]; gp.fit(FEAT[items], y); return popularity + gp.predict(FEAT)

# ---------------- rsos_cue banks (dev histories capped at 40 ratings) ----------------
def hists(space):
    out = []
    for u, d in dev.groupby('user'):
        d = d.sample(min(len(d), 40), random_state=int(u) % 1000)
        out.append(dict(programs=np.c_[d.j.to_numpy(), np.zeros((len(d), 2), int)], contexts=np.zeros(len(d), int), outcomes=d.rating.to_numpy(float)))
    return out
t0 = time.time()
sp_r = ProgramSpace(NI, 1, 1, 1, families=list(FAM)); sp_g = ProgramSpace(NI, 1, 1, 1, families=None)
dev_sample = dev[dev.user.isin(pd.Series(dev.user.unique()).sample(min(1500, U), random_state=1))]
dev_bak = dev; dev = dev_sample
B8 = ArchetypeBank(sp_r).fit(hists(sp_r), K=8, seed=1); B1 = ArchetypeBank(sp_r, contain_mass=0, self_archetype=False).fit(hists(sp_r), K=1)
G8 = ArchetypeBank(sp_g).fit(hists(sp_g), K=8, seed=1)
L8 = ArchetypeBank(sp_r).fit(hists(sp_r), K=8, seed=1, links=8); dev = dev_bak
print('banks fitted', round(time.time() - t0), 's; spine ridge', B8.meta.get('mean_ridge'), flush=True)

def cue(bank, items, ratings, explore=8):
    s = CueSession(bank, explore=explore, seed=0)
    for i, y in zip(items, ratings): s.add(int(i), 0, 0, 0, float(y))
    return s

# ---------------- evaluation ----------------
rows = []
for n, (u, d) in enumerate(r[r.user.isin(test_users)].groupby('user')):
    g = np.random.default_rng(int(u)); d = d.sample(frac=1, random_state=int(u))
    items = d.j.to_numpy(); rat = dict(zip(d.j, d.rating))
    D = items[:ND]; Pool = items[ND:]; rand = Pool[:BUDGET]
    yR = [rat[i] for i in rand]
    def score(name, s, probe='random'):
        pick = D[np.argmax(np.asarray(s)[D])]; best = max(rat[i] for i in D)
        rows.append((DATASET, int(u), name, probe, best - rat[pick], float(rat[pick] == best)))
    score('popularity', popularity); score('user_knn', knn(rand, yR)); score('matrix_factorization', mf_foldin(MF, rand, yR, MF_LAM))
    score('per_user_ridge', ridge_user(rand, yR)); score('per_user_gp', gp_user(rand, yR))
    score('hier_bayes_K1', cue(B1, rand, yR).predict()[0]); score('rsos_cue_generic', cue(G8, rand, yR).predict()[0])
    score('rsos_cue', cue(B8, rand, yR).predict()[0]); score('rsos_cue_links', cue(L8, rand, yR).predict()[0])
    # active: probes restricted to the pool, decision on D
    for name, rule in (('rsos_cue', 'project'), ('rsos_cue', 'thompson'), ('rsos_cue', 'ucb'), ('hier_bayes_K1', 'thompson'), ('rsos_cue_links', 'project'), ('rsos_cue_links', 'thompson')):
        bank = {'rsos_cue': B8, 'hier_bayes_K1': B1, 'rsos_cue_links': L8}[name]
        s = cue(bank, [], [], explore=8 if rule == 'project' else 0); used = []
        for t in range(BUDGET):
            left = [i for i in Pool if i not in used]
            if rule == 'project':
                q = s.next_probe(allowed_programs=left); i = q['glyph']
            else:
                m, v = s.posterior(); m, v = m[left], v[left]
                i = left[int(np.argmax(g.normal(m, np.sqrt(v)) if rule == 'thompson' else m + np.sqrt(v)))]
            used.append(i); s.add(int(i), 0, 0, 0, float(rat[i]))
        score(name, s.predict()[0], probe=rule)
        if rule == 'project':  # standard CF fed the same actively chosen ratings
            score('matrix_factorization', mf_foldin(MF, np.array(used), [rat[i] for i in used], MF_LAM), probe=name + '_probes')
    if n % 50 == 0: print(n, round(time.time() - t0), 's', flush=True)

out = pd.DataFrame(rows, columns=['dataset', 'user', 'method', 'probes', 'regret', 'hit'])
out.to_csv(_HERE / f'results_real_{DATASET}.csv', index=False)
print(out.groupby(['probes', 'method'])[['regret', 'hit']].mean().round(4).sort_values('regret').to_string())
