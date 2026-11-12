import sys, pathlib, unittest, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rsos_cue import ProgramSpace, ArchetypeBank, CueSession, discover_families

def sim(space, rng, n=24):
    fam = rng.normal(0, .3, space.n_fam); prog = np.array([fam[space.fam[g]] for g, s, p in space.programs])
    rep = np.r_[fam[space.fam] + rng.normal(0, .1, space.n_glyph), rng.normal(0, .1, space.n_sound)]
    ids = rng.integers(0, space.n_program, n); ctx = rng.integers(0, space.n_context, n)
    y = prog[ids] + rng.normal(0, .2, n)
    return dict(programs=space.programs[ids], contexts=ctx, outcomes=y, reports=rep), prog

class T(unittest.TestCase):
    def setUp(self):
        self.sp = ProgramSpace(6, 2, 2, 2, families=[0, 0, 0, 1, 1, 1]); self.rng = np.random.default_rng(0)
    def test_bank_fit_save_load(self):
        H = [sim(self.sp, self.rng)[0] for _ in range(40)]
        b = ArchetypeBank(self.sp).fit(H, K=2, iters=3); b.save('/tmp/_b.json'); c = ArchetypeBank.load('/tmp/_b.json')
        self.assertTrue(np.allclose(b.H, c.H)); self.assertEqual(c.space.blocks, self.sp.blocks)
    def test_session_learns_family(self):
        b = ArchetypeBank(self.sp).fit([sim(self.sp, self.rng)[0] for _ in range(60)], K=1)
        hits = 0
        for i in range(30):
            h, prog = sim(self.sp, self.rng); s = CueSession(b, reports=h['reports'])
            for a, c, y in zip(h['programs'], h['contexts'], h['outcomes']): s.add(*a, c, y)
            best = s.recommend(0)[0]['program']; hits += prog[self.sp.program_id(*best)] >= prog.max() - 1e-9
        self.assertGreater(hits, 24)
    def test_next_probe_respects_allowed_context(self):
        b = ArchetypeBank(self.sp).fit([sim(self.sp, self.rng)[0] for _ in range(20)], K=1)
        s = CueSession(b, explore=0); q = s.next_probe(allowed_contexts=[1]); self.assertEqual(q['context'], 1)
    def test_explore_phase_random_then_projected(self):
        b = ArchetypeBank(self.sp).fit([sim(self.sp, self.rng)[0] for _ in range(20)], K=1)
        s = CueSession(b, explore=2, seed=3); qs = []
        for _ in range(3):
            q = s.next_probe(allowed_contexts=[0]); qs.append(q); s.add(q['glyph'], q['sound'], q['plan'], q['context'], 0.1)
        self.assertTrue(all(q['context'] == 0 for q in qs))
    def test_watchdog_weights_sum_to_one(self):
        b = ArchetypeBank(self.sp).fit([sim(self.sp, self.rng)[0] for _ in range(30)], K=2, iters=2)
        h, _ = sim(self.sp, self.rng); s = CueSession(b, reports=h['reports'])
        for a, c, y in zip(h['programs'], h['contexts'], h['outcomes']): s.add(*a, c, y)
        _, w = s.watchdog(); self.assertAlmostEqual(w.sum(), 1.0)
    def test_discover_families(self):
        fam = np.repeat([0, 1, 2], 4); X = np.random.default_rng(1).normal(0, 1, (400, 3))[:, fam] + np.random.default_rng(2).normal(0, .3, (400, 12))
        lab, info = discover_families(X); self.assertEqual(info['k'], 3)
    def test_links_learned_and_saved(self):
        H = [sim(self.sp, self.rng)[0] for _ in range(60)]
        b = ArchetypeBank(self.sp).fit(H, K=1, links=2); self.assertIn('linx', b.space.blocks)
        b.save('/tmp/_bl.json'); c = ArchetypeBank.load('/tmp/_bl.json'); self.assertTrue(np.allclose(b.space.E, c.space.E))
        s = CueSession(c, reports=H[0]['reports'])
        for a, cx, y in zip(H[0]['programs'], H[0]['contexts'], H[0]['outcomes']): s.add(*a, cx, y)
        self.assertEqual(s.predict().shape, (2, 24))
    def test_generic_space(self):
        sp = ProgramSpace(4, 2, 2, 3); self.assertNotIn('fam', sp.blocks); self.assertEqual(sp.Xcand.shape[0], 4 * 2 * 2 * 3)
if __name__ == '__main__': unittest.main()
