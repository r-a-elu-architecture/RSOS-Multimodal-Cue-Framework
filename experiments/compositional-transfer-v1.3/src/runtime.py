"""Research-only, consent-first programmable cue routing. No autonomous health inference or stimulus delivery."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json, hashlib

ALLOWED_OPS={"interrupt","resource_recall","breath","swish_visual","future_rehearsal","mnemonic","posture","grounding","dual_attention_prompt","reflect"}
ALLOWED_CHANNELS={"visual","audio","kinesthetic","olfactory","gustatory"}

@dataclass(frozen=True)
class Recipe:
    id:str
    context:str
    tier_start:Optional[int]
    tier_end:Optional[int]
    glyph_chain:tuple[str,...]
    ops:tuple[str,...]
    channels:frozenset[str]
    goal:str
    duration_s:int=45
    goal_map:tuple[tuple[str,str],...]=()

@dataclass(frozen=True)
class Observation:
    session_id:str
    context:str
    voluntary_event:bool
    active_consent:bool
    allowed_channels:frozenset[str]
    observation_confidence:float
    signal_quality:float
    user_requested:bool
    self_report_distress:Optional[float]
    now_s:int

@dataclass(frozen=True)
class Decision:
    status:str
    recipe_id:str
    reason:str
    steps:tuple[str,...]=()

class Session:
    def __init__(self, cooldown_s=60):
        self.cooldown_s=cooldown_s; self.last_active={}; self.history=[]
        self.last_hash='0'*64

    def decide(self, recipe:Recipe, o:Observation)->Decision:
        # Do not infer emotion, belief, goals or trauma from EEG.
        if not o.active_consent or not o.user_requested or not o.voluntary_event:
            d=Decision('ABSTAIN',recipe.id,'user did not actively request a consented suggestion')
        elif o.context != recipe.context:
            d=Decision('ABSTAIN',recipe.id,'context mismatch')
        elif o.observation_confidence < .65:
            d=Decision('ABSTAIN',recipe.id,'context classification uncertain')
        elif o.signal_quality < .5:
            d=Decision('ABSTAIN',recipe.id,'sensor quality insufficient; use manual non-sensor mode')
        elif not recipe.channels.issubset(o.allowed_channels):
            d=Decision('ABSTAIN',recipe.id,'channel opt-in missing')
        elif (o.session_id in self.last_active and o.now_s-self.last_active[o.session_id]<self.cooldown_s):
            d=Decision('ABSTAIN',recipe.id,'cooldown')
        elif o.self_report_distress is not None and o.self_report_distress>=.8:
            d=Decision('MANUAL_GROUNDING_ONLY',recipe.id,'user-reported strong distress: no memory/conditioning sequence',('optional grounding; user may stop',))
        else:
            # suggestions only; olfactory/gustatory channel names never command a delivery device
            steps=tuple('optional '+op.replace('_',' ') for op in recipe.ops)
            d=Decision('SUGGEST',recipe.id,'user-directed, non-clinical sequence; no automatic actuation',steps)
            self.last_active[o.session_id]=o.now_s
        raw=json.dumps({'session':o.session_id,'time':o.now_s,'recipe':recipe.id,'status':d.status,'reason':d.reason,'prev':self.last_hash},sort_keys=True).encode()
        self.last_hash=hashlib.sha256(raw).hexdigest()
        self.history.append({'event_hash':self.last_hash,'status':d.status,'recipe':recipe.id})
        return d

def parse_recipe(data:dict)->Recipe:
    mandatory=('id','context','glyph_chain','ops','channels','goal')
    for k in mandatory:
        if k not in data: raise ValueError(f'missing {k}')
    if not isinstance(data['id'],str) or not (1<=len(data['id'])<=80): raise ValueError('invalid recipe ID')
    glyphs=tuple(data['glyph_chain']); ops=tuple(data['ops']); ch=frozenset(data['channels'])
    if not 1<=len(glyphs)<=8 or len(set(glyphs)) != len(glyphs):raise ValueError('glyph chain 1..8 unique user-registered glyphs')
    if any(not isinstance(g,str) or not 1<=len(g)<=64 for g in glyphs):raise ValueError('invalid glyph name')
    if not 1<=len(ops)<=12 or any(x not in ALLOWED_OPS for x in ops):raise ValueError('unknown or excessive operator')
    if not ch or not ch.issubset(ALLOWED_CHANNELS):raise ValueError('unsupported channel')
    t1=data.get('tier_start');t2=data.get('tier_end')
    if (t1 is None)!=(t2 is None):raise ValueError('both tier bounds or neither')
    if t1 is not None and (not isinstance(t1,int) or not isinstance(t2,int) or t1<0 or t1>t2 or t2>100000):raise ValueError('invalid optional tier range')
    n=data.get('duration_s',45)
    if not isinstance(n,int) or not 1<=n<=600:raise ValueError('invalid duration')
    if not isinstance(data['context'],str) or not data['context']:raise ValueError('context required')
    valid_levels={'environment','behavior','skills','capabilities','beliefs','values','identity','mission'}
    mp=data.get('goal_map',{})
    if not isinstance(mp,dict) or not set(mp).issubset(valid_levels) or any(not isinstance(v,str) or len(v)>256 for v in mp.values()):
        raise ValueError('goal_map has unsupported levels or values')
    return Recipe(data['id'],data['context'],t1,t2,glyphs,ops,ch,data['goal'],n,tuple(sorted(mp.items())))

def load_recipes(path:str)->list[Recipe]:
    with open(path,encoding='utf-8') as f:raw=json.load(f)
    recipes=[parse_recipe(x) for x in raw]
    if len(set(x.id for x in recipes))!=len(recipes): raise ValueError('duplicate recipes')
    return recipes
