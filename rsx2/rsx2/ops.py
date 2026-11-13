"""RSX/2 operator table: 30 operators from the record plus 4 proposed ones.

Each operator is typed by the cognitive layer it acts on (C1-C11, see the
private registry) or by a system role (contain, audit, device, export).
`effect` is the simulator's assumption about what one second of the operator
does; it is a model to test, not a finding.
"""

LAYERS = {
    "C1": "Node activation", "C2": "Associative expansion", "C3": "Symbolic compression",
    "C4": "Multi-layer simulation", "C5": "Recursive mapping", "C6": "Affective overlay",
    "C7": "Network updating", "C8": "Somatic integration", "C9": "Meta-eye",
    "C10": "Meta-self", "C11": "Meta-aggregator",
}
DEEP = {"C3", "C4", "C5", "C7", "C10", "C11"}   # layers whose work the model gates on low arousal

# name: (family, target, origin, effect per second {var: delta}, device line template or None)
#   effect vars: arousal, distress, agency, drift, layer (activation of the target layer)
OPS = {
    # safety, audit, export
    "NullSafe":            ("safety",   "contain", "vector-0", {}, None),
    "EthicsContain":       ("safety",   "contain", "canon17",  {}, None),
    "DriftLock":           ("safety",   "contain", "ext13",    {"drift": -0.004}, None),
    "StateReset":          ("safety",   "contain", "ext13",    {"arousal": -0.004}, None),
    "SymbolicDriftCheck":  ("safety",   "audit",   "canon17",  {}, None),
    "SymbolicCommandExport": ("export", "export",  "canon17",  {}, None),
    # body
    "BreathOverride":      ("body",     "C8", "canon17", {"arousal": -0.010, "distress": -0.020, "layer": 0.012}, "breath"),
    "BreathSync":          ("body",     "C8", "ext13",   {"arousal": -0.008, "distress": -0.012, "layer": 0.010}, "breath"),
    "BreathLock":          ("body",     "C8", "ext13",   {"arousal": -0.006, "layer": 0.008}, "breath"),
    "PostureShift":        ("body",     "C8", "canon17", {"arousal": -0.002, "agency": 0.006, "layer": 0.010}, "posture"),
    # affect
    "EmotionalLock":       ("affect",   "C6", "canon17", {"distress": -0.015, "arousal": -0.004, "layer": 0.010}, "warm"),
    # memory and identity
    "MemoryRecall":        ("memory",   "C1", "canon17", {"layer": 0.020, "arousal": 0.002}, None),
    "MemoryUpdate":        ("memory",   "C7", "canon17", {"layer": 0.006, "agency": 0.004}, None),
    "MemoryPurge":         ("memory",   "C7", "ext13",   {"distress": -0.006, "layer": 0.004}, None),
    "IdentityRebuild":     ("identity", "C7", "canon17", {"agency": 0.020, "layer": 0.015, "arousal": 0.003}, None),
    "IdentityShift":       ("identity", "C7", "ext13",   {"agency": 0.012, "layer": 0.010, "arousal": 0.003}, None),
    # symbol
    "CompressionRun":      ("symbol",   "C3", "canon17", {"layer": 0.018, "agency": 0.004}, None),
    "ArchetypeMerge":      ("symbol",   "C3", "canon17", {"layer": 0.016, "agency": 0.008, "arousal": 0.003}, "image"),
    # future
    "FutureProjection":    ("future",   "C4", "canon17", {"layer": 0.016, "agency": 0.010}, "image"),
    "FutureSelfLink":      ("future",   "C4", "ext13",   {"layer": 0.012, "agency": 0.008}, None),
    "FutureAnchor":        ("future",   "C4", "ext13",   {"layer": 0.010, "agency": 0.006}, None),
    # recursion
    "SymbolicEcho":        ("recursion", "C5", "canon17", {"layer": 0.012, "drift": 0.003}, None),
    "EchoLock":            ("recursion", "C5", "ext13",   {"layer": 0.006, "drift": -0.003}, None),
    "EchoSeal":            ("recursion", "C5", "ext13",   {"drift": -0.004}, None),
    "EchoPropagationStop": ("recursion", "C5", "canon17", {"drift": -0.006}, None),
    "RecursiveLawApply":   ("recursion", "C5", "canon17", {"layer": 0.012, "agency": 0.004}, None),
    "SymbolicLawApply":    ("recursion", "C5", "ext13",   {"layer": 0.010}, None),
    # device
    "DeviceOutput":        ("device",   "device", "canon17", {"layer_C1": 0.010}, "device"),
    "DeviceTrigger":       ("device",   "device", "ext13",   {"layer_C8": 0.008}, "device"),
    "ARSymbolOutput":      ("device",   "device", "ext13",   {"layer_C1": 0.010}, "image"),
    # proposed: close the four uncovered layers
    "AssociativeExpand":   ("symbol",   "C2",  "proposed", {"layer": 0.018, "arousal": 0.002}, None),
    "MetaObserve":         ("meta",     "C9",  "proposed", {"layer": 0.015, "distress": -0.004}, None),
    "SelfRevise":          ("meta",     "C10", "proposed", {"layer": 0.012, "agency": 0.010}, None),
    "IntegrateAll":        ("meta",     "C11", "proposed", {"layer": 0.012, "agency": 0.006, "drift": -0.002}, None),
}

# pairs that pull against each other when run at the same time (model assumption)
CONFLICTS = {
    frozenset({"IdentityRebuild", "ArchetypeMerge"}): "identity rebuilt while two archetypes are still merging",
    frozenset({"EmotionalLock", "MemoryRecall"}): "calm locked while an archetype memory is activated",
    frozenset({"SymbolicEcho", "EchoPropagationStop"}): "echo started and stopped together",
    frozenset({"IdentityRebuild", "IdentityShift"}): "two identity operations at once",
}
PRIORITY = {"safety": 0, "body": 1, "affect": 2, "memory": 3, "symbol": 4, "identity": 5, "future": 6,
            "recursion": 7, "meta": 8, "device": 9, "export": 10}
MAX_CONCURRENT = 17


def info(name):
    if name not in OPS:
        raise KeyError(name)
    fam, tgt, origin, eff, dev = OPS[name]
    return {"name": name, "family": fam, "target": tgt, "origin": origin, "effect": eff, "device": dev}
