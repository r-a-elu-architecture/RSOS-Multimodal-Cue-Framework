"""Minimal pure-Python Parquet reader used for Phase 9 (no pyarrow in the workspace): Thrift compact footer, SNAPPY or
uncompressed pages (v1/v2), PLAIN and RLE_DICTIONARY encodings, one level of list nesting. Read-only; no dependencies."""
import struct

class R:
    def __init__(self, b, pos=0):
        self.b, self.p = b, pos
    def byte(self):
        v = self.b[self.p]; self.p += 1; return v
    def varint(self):
        s = 0; r = 0
        while True:
            x = self.byte(); r |= (x & 0x7f) << s; s += 7
            if not x & 0x80: return r
    def zz(self):
        v = self.varint(); return (v >> 1) ^ -(v & 1)
    def binary(self):
        n = self.varint(); v = self.b[self.p:self.p + n]; self.p += n; return bytes(v)
    def value(self, t):
        if t == 1: return True
        if t == 2: return False
        if t == 3: return struct.unpack('b', bytes([self.byte()]))[0]
        if t in (4, 5, 6): return self.zz()
        if t == 7:
            v = struct.unpack('<d', self.b[self.p:self.p + 8])[0]; self.p += 8; return v
        if t == 8: return self.binary()
        if t in (9, 10): return self.list()
        if t == 11: return self.map()
        if t == 12: return self.struct()
        raise ValueError(f"type {t}")
    def list(self):
        h = self.byte(); n = h >> 4; et = h & 0x0f
        if n == 15: n = self.varint()
        out = []
        for _ in range(n):
            if et in (1, 2):
                out.append(self.byte() == 1)
            else:
                out.append(self.value(et))
        return out
    def map(self):
        n = self.varint()
        if n == 0: return {}
        kv = self.byte(); kt, vt = kv >> 4, kv & 0x0f
        return {self.value(kt): self.value(vt) for _ in range(n)}
    def struct(self):
        d = {}; last = 0
        while True:
            h = self.byte()
            if h == 0: return d
            t = h & 0x0f; delta = h >> 4
            fid = last + delta if delta else self.zz()
            last = fid
            if t == 1: d[fid] = True
            elif t == 2: d[fid] = False
            else: d[fid] = self.value(t)


def snappy(src):
    p = 0; n = 0; s = 0
    while True:
        b = src[p]; p += 1; n |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    out = bytearray()
    L = len(src)
    while p < L:
        tag = src[p]; p += 1; t = tag & 3
        if t == 0:
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59; ln = int.from_bytes(src[p:p+nb], 'little'); p += nb
            ln += 1
            out += src[p:p+ln]; p += ln
            continue
        if t == 1:
            ln = ((tag >> 2) & 7) + 4; off = ((tag >> 5) << 8) | src[p]; p += 1
        elif t == 2:
            ln = (tag >> 2) + 1; off = src[p] | (src[p+1] << 8); p += 2
        else:
            ln = (tag >> 2) + 1; off = int.from_bytes(src[p:p+4], 'little'); p += 4
        st = len(out) - off
        if off >= ln:
            out += out[st:st+ln]
        else:
            while ln > 0:
                k = min(ln, off); out += out[st:st+k]; st += k; ln -= k
    assert len(out) == n, (len(out), n)
    return bytes(out)

def rle_hybrid(buf, pos, end, bw, count):
    out = []
    bpw = (bw + 7) // 8
    mask = (1 << bw) - 1
    while len(out) < count and pos < end:
        h = 0; s = 0
        while True:
            b = buf[pos]; pos += 1; h |= (b & 0x7f) << s; s += 7
            if not b & 0x80: break
        if h & 1:
            groups = h >> 1; nbytes = groups * bw
            v = int.from_bytes(buf[pos:pos+nbytes], 'little'); pos += nbytes
            for i in range(groups * 8):
                out.append((v >> (i * bw)) & mask)
        else:
            run = h >> 1
            v = int.from_bytes(buf[pos:pos+bpw], 'little') if bpw else 0; pos += bpw
            out.extend([v] * run)
    return out[:count]

def plain(buf, pos, ptype, n):
    out = []
    if ptype == 6:
        for _ in range(n):
            ln = struct.unpack_from('<i', buf, pos)[0]; pos += 4
            out.append(buf[pos:pos+ln]); pos += ln
    elif ptype == 1:
        out = list(struct.unpack_from('<%di' % n, buf, pos))
    elif ptype == 2:
        out = list(struct.unpack_from('<%dq' % n, buf, pos))
    elif ptype == 5:
        out = list(struct.unpack_from('<%dd' % n, buf, pos))
    elif ptype == 0:
        out = [(buf[pos + i // 8] >> (i % 8)) & 1 for i in range(n)]
    else:
        raise ValueError(ptype)
    return out

def bitw(m):
    return m.bit_length()

class File:
    def __init__(self, path):
        self.f = open(path, 'rb')
        self.f.seek(-8, 2); n = struct.unpack('<i', self.f.read(4))[0]
        self.f.seek(-8 - n, 2)
        self.md = R(self.f.read(n)).struct()
        self.schema = self.md[2]
        self.nrows = self.md[3]
        self.rgs = self.md[4]
        # compute max levels per leaf path
        self.leaf = {}
        def walk(i, path, d, r):
            el = self.schema[i]; nch = el.get(5, 0); rt = el.get(3, 0)
            if i > 0:
                if rt == 1: d += 1
                elif rt == 2: d += 1; r += 1
                path = path + [el[4].decode()]
            j = i + 1
            if nch:
                for _ in range(nch):
                    j = walk(j, path, d, r)
                return j
            self.leaf[tuple(path)] = (el.get(1), d, r)
            return j
        walk(0, [], 0, 0)

    def column(self, rg, path):
        """returns (values, defs, reps) for a leaf path in a row group"""
        ptype, maxd, maxr = self.leaf[path]
        for cc in self.rgs[rg][1]:
            cm = cc[3]
            if tuple(x.decode() for x in cm[3]) == path: break
        else:
            raise KeyError(path)
        codec = cm[4]
        start = cm.get(11, cm[9])
        if cm.get(11) is not None and cm[11] < cm[9]: start = cm[11]
        total = cm[7]
        self.f.seek(start); raw = self.f.read(total)
        pos = 0; dic = None; vals = []; defs = []; reps = []
        nvals = cm[5]; got = 0
        while got < nvals:
            r = R(raw, pos); ph = r.struct(); pos = r.p
            csz = ph[3]; body = raw[pos:pos+csz]; pos += csz
            pt = ph[1]
            if pt == 2:
                data = snappy(body) if codec == 1 else body
                dic = plain(data, 0, ptype, ph[7][1])
                continue
            if pt == 0:
                dh = ph[5]; n = dh[1]; enc = dh[2]
                data = snappy(body) if codec == 1 else body
                p = 0
                if maxr:
                    ln = struct.unpack_from('<i', data, p)[0]; p += 4
                    rl = rle_hybrid(data, p, p + ln, bitw(maxr), n); p += ln
                else: rl = [0] * n
                if maxd:
                    ln = struct.unpack_from('<i', data, p)[0]; p += 4
                    dl = rle_hybrid(data, p, p + ln, bitw(maxd), n); p += ln
                else: dl = [0] * n
            elif pt == 3:
                dh = ph[8]; n = dh[1]; enc = dh[4]; dlb = dh[5]; rlb = dh[6]
                comp = dh.get(7, True)
                rl = rle_hybrid(body, 0, rlb, bitw(maxr), n) if maxr else [0] * n
                dl = rle_hybrid(body, rlb, rlb + dlb, bitw(maxd), n) if maxd else [0] * n
                rest = body[rlb + dlb:]
                data = snappy(rest) if (codec == 1 and comp) else rest
                p = 0
            else:
                continue
            nn = sum(1 for d in dl if d == maxd)
            if enc in (8, 2):
                bw = data[p]; p += 1
                idx = rle_hybrid(data, p, len(data), bw, nn)
                v = [dic[i] for i in idx]
            elif enc == 0:
                v = plain(data, p, ptype, nn)
            elif enc == 3 and ptype == 0:
                ln = struct.unpack_from('<i', data, p)[0]; p += 4
                v = rle_hybrid(data, p, p + ln, 1, nn)
            else:
                raise ValueError(f"enc {enc}")
            vals += v; defs += dl; reps += rl; got += n
        return vals, defs, reps, maxd

    def rows_flat(self, rg, path):
        vals, defs, reps, maxd = self.column(rg, path)
        it = iter(vals); return [next(it) if d == maxd else None for d in defs]

    def rows_list(self, rg, path):
        vals, defs, reps, maxd = self.column(rg, path)
        it = iter(vals); out = []
        for d, r in zip(defs, reps):
            if r == 0: out.append([])
            if d == maxd: out[-1].append(next(it))
            elif d >= 2: out[-1].append(None)   # element present but null
        return out
