"""Per-person, per-context, versioned mnemonic bindings.
This is a conventional safety-oriented namespace mechanism, not novel cryptography or therapy.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json

@dataclass(frozen=True)
class Binding:
    profile:str
    context:str
    glyph:str
    meaning:str
    revision:int
    digest:str

class CueRegistry:
    def __init__(self):
        self.current={}
        self.revoked=set()
    def bind(self,profile,context,glyph,meaning):
        if not all(isinstance(v,str) and 0<len(v)<=128 for v in (profile,context,glyph,meaning)):
            raise ValueError('all scope fields must be nonempty bounded strings')
        key=(profile,context,glyph)
        revision=(self.current[key].revision+1) if key in self.current else 1
        raw=json.dumps([profile,context,glyph,meaning,revision],ensure_ascii=False).encode()
        b=Binding(profile,context,glyph,meaning,revision,hashlib.sha256(raw).hexdigest())
        self.current[key]=b
        return b
    def revoke(self,profile,context,glyph):
        key=(profile,context,glyph)
        if key in self.current:self.revoked.add((key,self.current[key].revision))
    def resolve(self,profile,context,glyph,revision,consent,confidence):
        key=(profile,context,glyph)
        if not consent:return None,'NO_CONSENT'
        if confidence<.65:return None,'UNCERTAIN_CONTEXT'
        b=self.current.get(key)
        if not b:return None,'UNKNOWN_SCOPE'
        if b.revision!=revision:return None,'STALE_REVISION'
        if (key,b.revision) in self.revoked:return None,'REVOKED'
        return b,'OK'
