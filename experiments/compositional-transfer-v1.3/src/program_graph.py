"""Graph compiler for voluntary cue/mnemonic program modules. Supports arbitrary small tier intervals, cycles prohibited.
A program is a suggestion-only directed graph, not an automatic psychological or neurofeedback intervention.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from runtime import ALLOWED_OPS,parse_recipe,Recipe

@dataclass(frozen=True)
class Compiled:
  recipe:Recipe
  entry:str
  nodes:dict
  order:tuple

def compile_program(raw:dict)->Compiled:
  rec=parse_recipe(raw)
  nodes=raw.get('nodes',[])
  if not nodes or len(nodes)>64:raise ValueError('nodes 1..64 required')
  by={}
  for node in nodes:
    id=node.get('node_id')
    if not isinstance(id,str) or not id or id in by:raise ValueError('duplicate/invalid node ID')
    if node.get('operator') not in ALLOWED_OPS:raise ValueError('unknown graph operator')
    if not isinstance(node.get('next',[]),list):raise ValueError('next requires list')
    if len(node.get('next',[]))>3:raise ValueError('too many branches')
    by[id]=node
  entry=raw.get('entry');
  if entry not in by:raise ValueError('missing entry')
  seen=set();active=set();order=[]
  def walk(k):
    if k in active:raise ValueError('cycle: unbounded intervention chain')
    if k in seen:return
    active.add(k)
    for dst in by[k].get('next',[]):
      if dst not in by:raise ValueError('dangling transition')
      walk(dst)
    active.remove(k);seen.add(k);order.append(k)
  walk(entry)
  if len(seen)!=len(by):raise ValueError('unreachable node')
  return Compiled(rec,entry,by,tuple(reversed(order)))

def suggestions(compiled:Compiled,allow_branch:bool=False):
  """Inspect a nonexecuted optional sequence; branching paths require explicit person choice."""
  current=compiled.entry;path=[]
  while True:
    n=compiled.nodes[current];path.append({'operator':n['operator'],'node_id':current})
    nxt=n.get('next',[])
    if not nxt:return path
    if len(nxt)>1 and not allow_branch:return path+ [{'operator':'PAUSE_FOR_USER_CHOICE','options':nxt}]
    current=nxt[0]

def route_compiled(compiled:Compiled, observation, session):
  """Context/consent gate precedes viewing the graph; no branch is auto-selected."""
  decision=session.decide(compiled.recipe,observation)
  if decision.status!='SUGGEST':return decision, []
  return decision, suggestions(compiled,allow_branch=False)
