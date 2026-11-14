"""Phase 9 extractor (AGENTS.md §11.11): WildChat shards -> workspace pickle of included conversations. The user pair
(hashed_ip, user-agent) is kept only as its SHA-256; the pickle never leaves the workspace.

    python3 -m rsxv.p9_extract SHARD.parquet ... OUT.pkl
"""
import sys, pickle, hashlib, collections, time
from rsxv import parquet_min as pq
SH = sys.argv[1:-1]  # shard paths, then output path
convs = []; stats = collections.Counter(); seen = set(); dup = 0
t0 = time.time()
for path in SH:
    F = pq.File(path)
    for rg in range(len(F.rgs)):
        H = F.rows_flat(rg, ('conversation_hash',)); M = F.rows_flat(rg, ('model',)); LG = F.rows_flat(rg, ('language',))
        TS = F.rows_flat(rg, ('timestamp',)); IP = F.rows_flat(rg, ('hashed_ip',)); UA = F.rows_flat(rg, ('header', 'user-agent'))
        C = F.rows_list(rg, ('conversation', 'list', 'element', 'content'))
        R = F.rows_list(rg, ('conversation', 'list', 'element', 'role'))
        for h, m, lg, ts, ip, ua, c, r in zip(H, M, LG, TS, IP, UA, C, R):
            stats['conv_all'] += 1; stats['turns_all'] += len(c)
            if h in seen: dup += 1; continue
            seen.add(h)
            turns = [((ro or b'').decode(), (co or b'').decode('utf-8', 'replace')) for ro, co in zip(r, c)]
            nu = sum(1 for ro, _ in turns if ro == 'user')
            if (lg or b'').decode() != 'English': continue
            stats['conv_english'] += 1
            if nu < 3: continue
            stats['conv_english_3u'] += 1
            if any(ro == 'user' and not co.strip() for ro, co in turns): continue
            key = hashlib.sha256((ip or b'') + b'\x00' + (ua or b'')).hexdigest()
            convs.append({'cid': len(convs), 'model': m.decode(), 'ts': ts, 'user': key, 'turns': turns})
    print(path, time.time() - t0, len(convs), flush=True)
stats['duplicates_dropped'] = dup
stats['conv_included'] = len(convs); stats['turns_included'] = sum(len(c['turns']) for c in convs)
stats['user_turns_included'] = sum(sum(1 for r, _ in c['turns'] if r == 'user') for c in convs)
pickle.dump({'stats': dict(stats), 'convs': convs}, open(sys.argv[-1], 'wb'))
print(dict(stats)); print(collections.Counter(c['model'] for c in convs))
