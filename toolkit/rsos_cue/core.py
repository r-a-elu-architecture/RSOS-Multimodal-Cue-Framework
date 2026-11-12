"""rsos_cue — few-shot personalization of multimodal cue programs.

A *program* is (glyph, sound, plan) shown in a *context*; each trial yields a numeric *outcome*
(higher is better: recall accuracy, -latency, self-rated usefulness, ...). Optional *reports* are a
person's prior ratings of each glyph and sound.

Mechanisms (names from the RSOS/RSIA/RSX/RSSO archive):
  ProgramSpace    RSOS glyph families + RSX typed (glyph, sound, plan) command  -> latent effect blocks
  ArchetypeBank   RSIA archetypes compressed from other people's histories (RSSO MEMSTACK / CM1, EM)
  CueSession      RSIA Watchdog: posterior over archetypes for one person (soft switching)
                  RSX FutureProjection: next_probe() picks the most decision-relevant trial
                  RSSO CONTAIN: distrust twins; Meta-Architect: person's own fitted archetype

Exact linear-Gaussian inference; numpy + scipy only. Research software: no clinical claim.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import minimize

STRUCTURED_BLOCKS = ('fam', 'glyph', 'sound', 'plan', 'ctxfam', 'famplan', 'program')
GENERIC_BLOCKS = ('glyph', 'sound', 'plan', 'ctx', 'ctxglyph', 'glyphplan', 'ctxsound', 'program')


@dataclass
class ProgramSpace:
    n_glyph: int
    n_sound: int
    n_plan: int
    n_context: int
    families: list | None = None          # glyph -> family id; None = generic (no family structure)
    blocks: tuple = None
    embedding: list | None = None         # RSSO LINX: (n_context*n_program, k) learned item links; adds block 'linx'

    def __post_init__(self):
        if self.families is None:
            self.families = [0] * self.n_glyph
            self.blocks = tuple(self.blocks or GENERIC_BLOCKS)
        else:
            self.blocks = tuple(self.blocks or STRUCTURED_BLOCKS)
        self.fam = np.asarray(self.families, int)
        assert len(self.fam) == self.n_glyph
        self.n_fam = int(self.fam.max()) + 1
        self.n_program = self.n_glyph * self.n_sound * self.n_plan
        self.E = None if self.embedding is None else np.asarray(self.embedding, float)
        if self.E is not None and 'linx' not in self.blocks: self.blocks = tuple(self.blocks) + ('linx',)
        G, S, P, C, F = self.n_glyph, self.n_sound, self.n_plan, self.n_context, self.n_fam
        size = dict(icpt=1, fam=F, glyph=G, sound=S, plan=P, ctx=C, ctxfam=C * F, famplan=F * P,
                    program=self.n_program, ctxglyph=C * G, glyphplan=G * P, ctxsound=C * S,
                    linx=0 if self.E is None else self.E.shape[1])
        self.off, o = {}, 0
        for b in ('icpt',) + self.blocks:
            self.off[b] = (o, o + size[b]); o += size[b]
        self.dim = o
        self.programs = np.array([(g, s, p) for g in range(G) for s in range(S) for p in range(P)], int)
        self.cand_prog = np.tile(np.arange(self.n_program), C)
        self.cand_ctx = np.repeat(np.arange(C), self.n_program)
        self.Xcand = self.design(self.programs[self.cand_prog], self.cand_ctx)
        self.R = self._report_design()

    def program_id(self, glyph, sound, plan):
        return (np.asarray(glyph) * self.n_sound + np.asarray(sound)) * self.n_plan + np.asarray(plan)

    def design(self, programs, contexts):
        a = np.asarray(programs, int).reshape(-1, 3); c = np.asarray(contexts, int).reshape(-1)
        g, s, p = a.T; f = self.fam[g]; n = len(a); r = np.arange(n)
        X = np.zeros((n, self.dim)); X[r, 0] = 1
        G, S, P, F = self.n_glyph, self.n_sound, self.n_plan, self.n_fam
        col = dict(fam=f, glyph=g, sound=s, plan=p, ctx=c, ctxfam=c * F + f, famplan=f * P + p,
                   program=(g * S + s) * P + p, ctxglyph=c * G + g, glyphplan=g * P + p, ctxsound=c * S + s)
        for b in self.blocks:
            if b == 'linx': X[:, slice(*self.off['linx'])] = self.E[c * self.n_program + col['program']]
            else: X[r, self.off[b][0] + col[b]] = 1
        return X

    def _report_design(self):
        R = np.zeros((self.n_glyph + self.n_sound, self.dim))
        for g in range(self.n_glyph):
            if 'fam' in self.blocks: R[g, self.off['fam'][0] + self.fam[g]] = 1
            if 'glyph' in self.blocks: R[g, self.off['glyph'][0] + g] = 1
        for s in range(self.n_sound):
            if 'sound' in self.blocks: R[self.n_glyph + s, self.off['sound'][0] + s] = 1
        return R

    def n_hyp(self):
        return len(self.blocks) + 2  # log sd per block, log outcome-noise sd, log report-noise sd

    def to_dict(self):
        return dict(n_glyph=self.n_glyph, n_sound=self.n_sound, n_plan=self.n_plan, n_context=self.n_context,
                    families=list(map(int, self.fam)) if 'fam' in self.blocks else None, blocks=list(self.blocks),
                    embedding=None if self.E is None else self.E.tolist())


class _Obs:
    """Sufficient statistics for one person's data under a ProgramSpace."""
    def __init__(self, space: ProgramSpace, programs, contexts, outcomes, reports=None):
        self.space = space
        X = space.design(programs, contexts) if len(outcomes) else np.zeros((0, space.dim))
        self.n = len(outcomes)
        self.has_rep = reports is not None
        M = np.vstack([X, space.R]) if self.has_rep else X
        self.obs = np.r_[np.asarray(outcomes, float), np.asarray(reports, float)] if self.has_rep else np.asarray(outcomes, float)
        bl = ('icpt',) + space.blocks
        self.G = np.stack([M[:, slice(*space.off[b])] @ M[:, slice(*space.off[b])].T for b in bl])
        self.C = np.stack([space.Xcand[:, slice(*space.off[b])] @ M[:, slice(*space.off[b])].T for b in bl])
        self.M = M
        m = len(self.obs)
        self.d_sig = np.r_[np.ones(self.n), np.zeros(m - self.n)]
        self.d_rep = np.r_[np.zeros(self.n), np.ones(space.n_glyph), np.full(space.n_sound, .64)][:m] if self.has_rep else np.zeros(m)

    def _scale(self, lam):
        # report loading: report = lam * effect + noise (lam=1 trusted, 0 ignored, <0 inverted)
        return np.where(self.d_rep > 0, lam, 1.0) if self.has_rep else np.ones(len(self.obs))

    def cov(self, h, lam=1.0):
        nb = len(self.space.blocks)
        v = np.r_[1.0, np.exp(2 * h[:nb])]; D = self._scale(lam)
        S = D[:, None] * np.tensordot(v, self.G, 1) * D[None, :] + np.diag(np.exp(2 * h[-2]) * self.d_sig + np.exp(2 * h[-1]) * self.d_rep)
        return S, v

    def logml(self, h, lam=1.0):
        S, _ = self.cov(h, lam)
        L = np.linalg.cholesky(S); a = np.linalg.solve(L, self.obs)
        return float(-0.5 * a @ a - np.log(np.diag(L)).sum() - 0.5 * len(a) * np.log(2 * np.pi))

    def predict(self, h, lam=1.0, return_var=False):
        S, v = self.cov(h, lam)
        Kc = np.tensordot(v, self.C, 1) * self._scale(lam)[None, :]
        alpha = np.linalg.solve(S, self.obs); mean = Kc @ alpha
        if not return_var: return mean
        prior = self.space.Xcand ** 2 @ self._prior_vec(v)
        return mean, prior - np.einsum('ij,ji->i', Kc, np.linalg.solve(S, Kc.T))

    def _prior_vec(self, v):
        pv = np.zeros(self.space.dim)
        for i, b in enumerate(('icpt',) + self.space.blocks): pv[slice(*self.space.off[b])] = v[i]
        return pv


def _batch_logml(objs, h, grad=False):
    G = np.stack([o.G for o in objs]); Y = np.stack([o.obs for o in objs])
    ds = objs[0].d_sig; dr = objs[0].d_rep; nb = G.shape[1] - 1
    v = np.r_[1.0, np.exp(2 * h[:nb])]; sig2, rep2 = np.exp(2 * h[-2]), np.exp(2 * h[-1])
    S = np.einsum('b,pbij->pij', v, G) + np.diag(sig2 * ds + rep2 * dr)
    L = np.linalg.cholesky(S); Si = np.linalg.inv(S); al = np.einsum('pij,pj->pi', Si, Y)
    ll = -0.5 * np.einsum('pi,pi->p', Y, al) - np.log(np.diagonal(L, axis1=1, axis2=2)).sum(1) - 0.5 * Y.shape[1] * np.log(2 * np.pi)
    if not grad: return ll
    W = np.einsum('pi,pj->pij', al, al) - Si
    gb = 0.5 * np.einsum('pij,pbji->pb', W, G)[:, 1:] * 2 * v[1:]
    gs = 0.5 * np.einsum('pii,i->p', W, ds) * 2 * sig2
    gr = 0.5 * np.einsum('pii,i->p', W, dr) * 2 * rep2
    return ll, np.column_stack([gb, gs, gr])


def _fit(objs, wts, h0, prior_sd=3.0, maxiter=200):
    # Batched objective needs equal-shaped persons; group by shape.
    groups = {}
    for o, w in zip(objs, wts):
        groups.setdefault(len(o.obs), ([], []))
        groups[len(o.obs)][0].append(o); groups[len(o.obs)][1].append(w)
    c = np.log(0.1)
    def f(h):
        tot, g = 0.0, np.zeros_like(h)
        for os_, ws in groups.values():
            ll, gr = _batch_logml(os_, h, True); ws = np.asarray(ws); tot += ws @ ll; g += ws @ gr
        pen = 0.5 * np.sum((h - c) ** 2) / prior_sd ** 2
        return -tot + pen, -g + (h - c) / prior_sd ** 2
    return minimize(f, h0, jac=True, method='L-BFGS-B', bounds=[(-7, 1)] * len(h0), options={'maxiter': maxiter}).x


@dataclass
class ArchetypeBank:
    """Population archetypes. H[k] = log-sd vector (blocks..., outcome noise, report noise)."""
    space: ProgramSpace
    H: np.ndarray = None
    pi: np.ndarray = None
    contain_mass: float = 0.1     # prior mass for CONTAIN distrust twins (0 disables)
    self_archetype: bool = True   # Meta-Architect: add the person's own fitted archetype
    self_penalty: float = 2.0     # nats per log(n) charged to the person's own archetype (tuned on dev seeds)
    meta: dict = field(default_factory=dict)
    mu: np.ndarray = None         # RSIA Spine: population-mean effects shared by everyone (None = zero)
    rep_mean: np.ndarray = None   # population-mean self-ratings

    def residualize(self, programs, contexts, outcomes, reports):
        y = np.asarray(outcomes, float)
        if self.mu is not None and len(y): y = y - self.space.design(programs, contexts) @ self.mu
        r = None if reports is None else (np.asarray(reports, float) - (self.rep_mean if self.rep_mean is not None else 0))
        return y, r

    def offset(self):
        return np.zeros(len(self.space.Xcand)) if self.mu is None else self.space.Xcand @ self.mu

    @staticmethod
    def _objs(space, histories):
        return [_Obs(space, h['programs'], h['contexts'], h['outcomes'], h.get('reports')) for h in histories]

    def fit(self, histories, K=8, iters=12, seed=0, population_mean=True, mean_ridge='cv', links=0, link_ridge=10.0):
        """histories: list of dicts {programs:(n,3), contexts:(n,), outcomes:(n,), reports:(G+S,) optional}.
        population_mean: first estimate the Spine (effects shared by the population) by pooled ridge,
        then fit archetypes to each person's deviations from it."""
        if population_mean:
            D = self.space.dim
            perm = np.random.default_rng(seed).permutation(len(histories)); folds = np.array_split(perm, 2)
            fold_of = np.empty(len(histories), int)
            for f, idx in enumerate(folds): fold_of[idx] = f
            SA, Sb = np.zeros((2, D, D)), np.zeros((2, D))   # per-fold sums only (memory O(D^2), not O(N D^2))
            for i, h in enumerate(histories):
                X = self.space.design(h['programs'], h['contexts']); SA[fold_of[i]] += X.T @ X; Sb[fold_of[i]] += X.T @ np.asarray(h['outcomes'], float)
            def solve(fs, lam):
                A = SA[fs].sum(0) + lam * np.eye(D); A[0, 0] -= lam - 1e-6; return np.linalg.solve(A, Sb[fs].sum(0))
            if mean_ridge == 'cv':  # pick shrinkage by 2-fold cross-validation over people (huge = intercept only)
                best = None
                for lam in (1, 10, 100, 1e3, 1e4, 1e7):
                    err = 0.0
                    for f in range(2):
                        m = solve([1 - f], lam)
                        for i in folds[f]:
                            h = histories[i]; r = np.asarray(h['outcomes'], float) - self.space.design(h['programs'], h['contexts']) @ m
                            err += np.sum((r - r.mean()) ** 2)  # person's own level is free; judge only the shape
                    if best is None or err < best[0] - 1e-9: best = (err, lam)
                mean_ridge = best[1]
            self.mu = solve([0, 1], mean_ridge); self.meta['mean_ridge'] = float(mean_ridge)
            reps = [h['reports'] for h in histories if h.get('reports') is not None]
            self.rep_mean = np.mean(reps, 0) if reps else None
            histories = [dict(h, **dict(zip(('outcomes', 'reports'), self.residualize(h['programs'], h['contexts'], h['outcomes'], h.get('reports')))))
                         for h in histories]
            if all(h.get('reports') is None for h in histories): histories = [{k: v for k, v in h.items() if k != 'reports'} for h in histories]
        if links:
            self._learn_links(histories, links, link_ridge, seed)
        objs = self._objs(self.space, histories); N = len(objs); nh = self.space.n_hyp()
        base = _fit(objs, np.ones(N) / N, np.full(nh, np.log(.1)))
        if K == 1:
            self.H, self.pi = base[None], np.ones(1); return self
        rng = np.random.default_rng(seed); H = base[None] + rng.normal(0, .8, (K, nh)); pi = np.ones(K) / K
        for _ in range(iters):
            LL = np.stack([np.r_[[o.logml(H[k]) for o in objs]] for k in range(K)], 1) + np.log(pi)
            Rr = np.exp(LL - LL.max(1, keepdims=True)); Rr /= Rr.sum(1, keepdims=True)
            pi = Rr.mean(0) + 1e-6; pi /= pi.sum()
            newH = []
            for k in range(K):
                keep = Rr[:, k] > 1e-3
                newH.append(_fit([o for o, z in zip(objs, keep) if z], Rr[keep, k] / max(Rr[:, k].sum(), 1e-9), H[k], maxiter=25)
                            if keep.sum() > 5 else H[k])
            H = np.stack(newH)
        self.H, self.pi = H, pi
        self.meta.update(n_people=N, K=K)
        return self

    def _learn_links(self, histories, k, lam, seed):
        """RSSO LINX: low-rank links between (context, program) candidates, learned by ALS on other people's
        deviations from the Spine. Scaled so person loadings have unit variance; the archetypes then learn how
        much each person follows these links (the 'linx' block variance)."""
        sp = self.space; NC = sp.n_context * sp.n_program; g = np.random.default_rng(seed)
        rows = [(np.asarray(h['contexts'], int) * sp.n_program + sp.program_id(*np.asarray(h['programs'], int).T),
                 np.asarray(h['outcomes'], float)) for h in histories]
        rows = [(ci, y - y.mean()) for ci, y in rows]
        Q = g.normal(0, .1, (NC, k)); Pm = np.zeros((len(rows), k))
        for _ in range(15):
            for i, (ci, y) in enumerate(rows):
                X = Q[ci]; Pm[i] = np.linalg.solve(X.T @ X + lam * np.eye(k), X.T @ y)
            A = np.repeat(lam * np.eye(k)[None], NC, 0); b = np.zeros((NC, k))
            for i, (ci, y) in enumerate(rows):
                np.add.at(A, ci, Pm[i][:, None] * Pm[i][None, :]); np.add.at(b, ci, y[:, None] * Pm[i][None, :])
            Q = np.linalg.solve(A, b[..., None])[..., 0]
        Q = Q * Pm.std(0, keepdims=True).clip(1e-6)
        d = self.space.to_dict(); d['embedding'] = Q.tolist()
        d['blocks'] = [b for b in d['blocks'] if b != 'linx']
        self.space = ProgramSpace(**d); self.meta['links'] = k
        if self.mu is not None: self.mu = np.r_[self.mu, np.zeros(k)]  # 'linx' is the last block: zero population mean

    def expanded(self):
        """Learned archetypes (reports trusted) + CONTAIN twins (reports ignored, 10x program-level variance)."""
        H, pi, lam = self.H, self.pi, np.ones(len(self.H))
        if self.contain_mass > 0:
            A = H.copy(); bl = self.space.blocks
            if 'program' in bl: A[:, bl.index('program')] += 0.5 * np.log(10)
            # reports ignored: their spread must then be explained as noise (marginal report sd)
            marg = sum(np.exp(2 * H[:, bl.index(x)]) for x in ('fam', 'glyph') if x in bl)
            A[:, -1] = 0.5 * np.log(marg + np.exp(2 * H[:, -1]))
            H = np.vstack([H, A]); pi = np.r_[pi * (1 - self.contain_mass), pi * self.contain_mass]
            lam = np.r_[lam, np.zeros(len(A))]
        return H, pi, lam

    def save(self, path):
        with open(path, 'w') as fh:
            json.dump(dict(space=self.space.to_dict(), H=self.H.tolist(), pi=self.pi.tolist(), contain_mass=self.contain_mass,
                           self_archetype=self.self_archetype, self_penalty=self.self_penalty, meta=self.meta,
                           mu=None if self.mu is None else self.mu.tolist(),
                           rep_mean=None if self.rep_mean is None else self.rep_mean.tolist()), fh, indent=1)

    @classmethod
    def load(cls, path):
        with open(path) as fh: d = json.load(fh)
        arr = lambda k: None if d.get(k) is None else np.array(d[k])
        d['space'].setdefault('embedding', None); sp = ProgramSpace(**d['space'])
        return cls(sp, np.array(d['H']), np.array(d['pi']), d['contain_mass'], d['self_archetype'], d.get('self_penalty', 2.0), d['meta'],
                   arr('mu'), arr('rep_mean'))


class CueSession:
    """One person. Add trials, ask for recommendations or the next most informative probe."""
    def __init__(self, bank: ArchetypeBank, reports=None, explore=8, seed=None):
        """explore: number of initial random probes before next_probe() starts projecting (guards against
        misleading self-ratings steering every probe; 8 chosen on development seeds)."""
        self.bank, self.space, self.reports = bank, bank.space, None if reports is None else np.asarray(reports, float)
        self.explore, self.rng = explore, np.random.default_rng(seed)
        self.programs, self.contexts, self.outcomes = [], [], []

    def add(self, glyph, sound, plan, context, outcome):
        self.programs.append((glyph, sound, plan)); self.contexts.append(context); self.outcomes.append(float(outcome))

    def _obj(self):
        a = np.array(self.programs, int).reshape(-1, 3); c = np.array(self.contexts, int)
        y, r = self.bank.residualize(a, c, self.outcomes, self.reports)
        return _Obs(self.space, a, c, y, r)

    def watchdog(self):
        """Posterior over archetypes (RSIA Watchdog). Returns (H, weights)."""
        o = self._obj(); H, pi, lam = self.bank.expanded()
        if self.bank.self_archetype and len(self.outcomes) >= 8:
            # Meta-Architect: the person's own archetype incl. report loading, shrunk toward the
            # best bank archetype (prior sd 1 on log-sds, N(1,1) on loading), BIC-style penalty.
            k0 = int(np.argmax([o.logml(h, l) for h, l in zip(H, lam)])); h0 = H[k0]
            def f(x):
                try: return -o.logml(x[:-1], x[-1]) + 0.5 * np.sum((x[:-1] - h0) ** 2) + 0.5 * (x[-1] - 1) ** 2
                except np.linalg.LinAlgError: return 1e9
            x = minimize(f, np.r_[h0, 1.0], method='L-BFGS-B', bounds=[(-7, 1)] * len(h0) + [(-3, 3)], options={'maxiter': 80}).x
            H = np.vstack([H, x[:-1]]); lam = np.r_[lam, x[-1]]; pi = np.r_[pi * 0.9, 0.1]
            pen = np.r_[np.zeros(len(H) - 1), self.bank.self_penalty * np.log(max(len(o.obs), 2))]
        else:
            pen = np.zeros(len(H))
        ll = np.array([o.logml(h, l) for h, l in zip(H, lam)]) - pen + np.log(pi)
        w = np.exp(ll - ll.max()); w /= w.sum()
        self._cache = (o, H, w, lam)
        return H, w

    def report_trust(self):
        """Posterior-weighted report loading (1 = ratings trusted, 0 = ignored, <0 = inverted)."""
        H, w = self.watchdog(); return float(w @ self._cache[3])

    def predict(self):
        H, w = self.watchdog(); o, lam = self._cache[0], self._cache[3]
        mean = sum(wk * o.predict(h, l) for wk, h, l in zip(w, H, lam) if wk > 1e-4) + self.bank.offset()
        return mean.reshape(self.space.n_context, self.space.n_program)

    def posterior(self):
        """Watchdog-averaged mean and (MAP-archetype) variance for every (context, program) candidate."""
        H, w = self.watchdog(); o, lam = self._cache[0], self._cache[3]; k = int(np.argmax(w))
        mean = sum(wk * o.predict(h, l) for wk, h, l in zip(w, H, lam) if wk > 1e-4) + self.bank.offset()
        var = np.maximum(o.predict(H[k], lam[k], return_var=True)[1], 1e-12)
        return mean, var

    def recommend(self, context, k=1):
        m = self.predict()[context]; top = np.argsort(m)[::-1][:k]
        return [dict(program=tuple(map(int, self.space.programs[i])), predicted=float(m[i])) for i in top]

    def next_probe(self, allowed_contexts=None, allowed_programs=None, top=5):
        """RSX FutureProjection: the trial that most reduces uncertainty about current contenders.
        allowed_programs: program ids that can actually be presented (default: all); also the decision set."""
        sp = self.space
        ok = np.ones(len(sp.cand_ctx), bool)
        if allowed_contexts is not None: ok &= np.isin(sp.cand_ctx, list(allowed_contexts))
        if allowed_programs is not None: ok &= np.isin(sp.cand_prog, list(allowed_programs))
        if len(self.outcomes) < self.explore:
            j = int(self.rng.choice(np.flatnonzero(ok))); g, s_, p = sp.programs[sp.cand_prog[j]]
            return dict(glyph=int(g), sound=int(s_), plan=int(p), context=int(sp.cand_ctx[j]))
        H, w = self.watchdog(); o, lam = self._cache[0], self._cache[3]; k = int(np.argmax(w)); h = H[k]; sp = self.space
        pv = o._prior_vec(np.r_[1.0, np.exp(2 * h[:len(sp.blocks)])])
        nvar = np.exp(2 * h[-2]) * o.d_sig + np.exp(2 * h[-1]) * o.d_rep
        Ms = o.M * o._scale(lam[k])[:, None]
        Sth = np.linalg.inv(np.diag(1 / pv) + Ms.T @ (Ms / nvar[:, None]))
        mean = sum(wk * o.predict(hh, l) for wk, hh, l in zip(w, H, lam) if wk > 1e-4) + self.bank.offset()
        P = sp.n_program; m2 = np.where(ok, mean, -np.inf)
        cont = np.concatenate([c * P + np.argsort(m2[c * P:(c + 1) * P])[-top:] for c in range(sp.n_context)])
        cont = cont[ok[cont]]
        XS = sp.Xcand @ Sth; var = np.einsum('ij,ij->i', XS, sp.Xcand)
        score = ((XS @ sp.Xcand[cont].T) ** 2).sum(1) / (var + np.exp(2 * h[-2]))
        score[~ok] = -np.inf
        j = int(np.argmax(score))
        g, s, p = sp.programs[sp.cand_prog[j]]
        return dict(glyph=int(g), sound=int(s), plan=int(p), context=int(sp.cand_ctx[j]))
