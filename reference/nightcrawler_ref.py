"""NIGHTCRAWLER reference model (Appendix D).

Executable restatement of the definitions in Sections 4 to 8:
evidence partial order, D_verify, D_act, U(q), live subgraph, P_H,
min-cut special case, hitting-set general case, and the canonical
state-assignment predicate (conditions C0 to C9, with C4a-C4c separate).

The property test checks internal consistency only: whenever the state
rule emits COMPLETE on a generated world, the hidden ground truth of that
world contains no q-descended prohibited path inside S that fires within
the validity window. Ablations confirm the test is not vacuous. Results
say nothing about real providers.
"""
from __future__ import annotations
import itertools, random, sys
from dataclasses import dataclass, field
import networkx as nx

# ---------------------------------------------------------------- evidence order
# Hasse diagram: A > B > {C1, C2} > D > E ; C1 and C2 incomparable.
_COVERS = {"A": ["B"], "B": ["C1", "C2"], "C1": ["D"], "C2": ["D"], "D": ["E"], "E": []}

def _below(g):
    out, stack = set(), list(_COVERS[g])
    while stack:
        x = stack.pop()
        if x not in out:
            out.add(x); stack.extend(_COVERS[x])
    return out

BELOW = {g: _below(g) for g in _COVERS}
def strictly_below(x, y): return x in BELOW[y]          # x < y
def geq(x, y): return x == y or y in BELOW[x]            # x >= y

# ---------------------------------------------------------------- REG
@dataclass
class REG:
    g: nx.DiGraph                      # node attrs: kind, system, creator, t_created, present, refuted, confirmed
    q: str = "q"                       # edge attrs: rel, grade
    effects: set = field(default_factory=set)

def auth_closure(r: REG):
    """Identities reachable from q through delegation edges that are not refuted."""
    seen, stack = set(), [r.q]
    while stack:
        x = stack.pop()
        for _, y, d in r.g.out_edges(x, data=True):
            if d["rel"] == "delegates" and r.g.nodes[y]["kind"] == "identity" and y not in seen:
                seen.add(y); stack.append(y)
    seen.add("cred_q")
    return seen

def descendants(r: REG, keep):
    seen, stack = set(), [r.q]
    while stack:
        x = stack.pop()
        for _, y, d in r.g.out_edges(x, data=True):
            if keep(d["grade"]) and y not in seen:
                seen.add(y); stack.append(y)
    return seen

def d_verify(r, e_v): return descendants(r, lambda gr: not strictly_below(gr, e_v))
def d_act(r, e_a):    return descendants(r, lambda gr: geq(gr, e_a))

def u_set(r, auth, scope, t_lo, t_s):
    return {v for v, a in r.g.nodes(data=True)
            if v != r.q and a.get("system") in scope and a.get("creator") in auth
            and t_lo <= a.get("t_created", -1) <= t_s}

def live_subgraph(r, scope):
    keep = [v for v, a in r.g.nodes(data=True)
            if v != r.q and a.get("system") in scope and a.get("present") is not False and not a.get("refuted", False)]
    return r.g.subgraph(keep)

def p_h_nonempty(r, sources, scope, confirmed_only=False):
    h = live_subgraph(r, scope)
    if confirmed_only:
        h = h.subgraph([v for v, a in h.nodes(data=True) if a.get("present") is True and a.get("confirmed", False)])
    for s in sources:
        if s not in h: continue
        reach = nx.descendants(h, s) | {s}
        if reach & r.effects: return True
    return False

# ---------------------------------------------------------------- planners
def min_cut_plan(r, sources, scope, cost):
    """Special case: one intervention per node, additive cost (node splitting)."""
    h = live_subgraph(r, scope); f = nx.DiGraph()
    for v in h.nodes:
        f.add_edge(("in", v), ("out", v), capacity=cost.get(v, float("inf")))
    for u, v in h.edges:
        f.add_edge(("out", u), ("in", v), capacity=float("inf"))
    for s in sources:
        if s in h: f.add_edge("SRC", ("in", s), capacity=float("inf"))
    for e in r.effects:
        if e in h: f.add_edge(("out", e), "SNK", capacity=float("inf"))
    if "SRC" not in f or "SNK" not in f: return set(), 0.0
    try:
        val, (a, b) = nx.minimum_cut(f, "SRC", "SNK")
    except nx.NetworkXUnbounded:
        return None, float("inf")
    if val == float("inf"): return None, val
    return {u[1] for u in a for w in f[u] if w in b and u[0] == "in"}, val

def hitting_set_plan(paths, interventions, invariant):
    """General case: exact search for small instances. interventions: {m: (cost, kappa_minus)}."""
    best, best_cost = None, float("inf")
    names = sorted(interventions)
    for k in range(len(names) + 1):
        for X in itertools.combinations(names, k):
            if not invariant(set(X)): continue
            cut = set().union(*(interventions[m][1] for m in X)) if X else set()
            if all(cut & set(p) for p in paths):
                c = sum(interventions[m][0] for m in X)
                if c < best_cost: best, best_cost = set(X), c
    return best, best_cost        # best is None => infeasible => FAILED

# ---------------------------------------------------------------- state rule
def assign_state(conf_live, conds, gaps_enumerable):
    """conds: dict C0..C9 (with C4a..C4c) -> True / False / None (unknown)."""
    if conf_live: return "FAILED"
    required = {"C0", "C1", "C2", "C3", "C4a", "C4b", "C4c", "C5", "C6", "C7", "C8", "C9"}
    if set(conds) == required and all(conds[c] is True for c in required): return "COMPLETE"
    return "BOUNDED" if gaps_enumerable else "INDETERMINATE"

# ---------------------------------------------------------------- property test
SCOPE = {"s0", "s1", "s2"}
FAULTS = ("hide", "stale", "nofence", "tamper", "outscope", "undeclared", "shortH", "compromise",
          "egress", "deliverygap", "authgap", "histgap", "commonmode", "c9common", "clkskew", "gen", "genunsupported")

def world(rng):
    """Ground truth T and observation O for one randomized scenario.

    Each fault perturbs the observation the way the corresponding real failure would,
    and separately sets the admission condition that a correct implementation would report.
    """
    f = {k: rng.random() < 0.15 for k in FAULTS}
    T = nx.DiGraph(); T.add_node("q", kind="origin")
    T.add_node("cred_q", kind="identity", system="s0", creator=None, t_created=0, present=True)
    ids = ["cred_q"]
    for i in range(rng.randint(0, 2)):
        v = f"id{i}"
        T.add_node(v, kind="identity", system=rng.choice(sorted(SCOPE)), creator="cred_q", t_created=rng.randint(1, 5), present=True)
        T.add_edge("q", v, rel="delegates", grade=rng.choice(["A", "B", "C1"])); ids.append(v)
    sysset = sorted(SCOPE | ({"s3"} if f["outscope"] else set()) | ({"x9"} if f["undeclared"] else set()))
    arts = []
    for i in range(rng.randint(2, 7)):
        v = f"a{i}"
        T.add_node(v, kind="artifact", system=rng.choice(sysset), creator=rng.choice(ids), t_created=rng.randint(1, 9), present=rng.random() < 0.85)
        grade = "E" if f["tamper"] and rng.random() < 0.6 else rng.choice(["A", "B", "C1", "C2", "D"])
        T.add_edge("q", v, rel="creates", grade=grade); arts.append(v)
    T.add_node("res", kind="resource", system="s1", creator="admin", t_created=-5, present=True)
    T.add_node("f", kind="effect", system="s1", creator=None, t_created=-5, present=True)
    T.add_edge("res", "f", rel="activates", grade="B")
    for v in arts:
        if rng.random() < 0.5: T.add_edge(v, "res", rel="invokes", grade=rng.choice(["B", "C1", "D"]))
    if f["nofence"]:                                    # created after the snapshot by Auth*(q)
        T.add_node("late", kind="artifact", system="s0", creator="cred_q", t_created=12, present=True)
        T.add_edge("late", "res", rel="invokes", grade="E")
    if f["authgap"]:                                    # delegated identity whose issuer history is incomplete
        T.add_node("hid", kind="identity", system="s2", creator="cred_q", t_created=3, present=True)
        T.add_edge("q", "hid", rel="delegates", grade="B")
        T.add_node("hart", kind="artifact", system="s2", creator="hid", t_created=4, present=True)
        T.add_edge("hart", "res", rel="invokes", grade="B")
    if f["gen"] and arts:                               # future instance generated by a rule on a0
        a0 = arts[0]; T.nodes[a0]["system"] = "s0"; T.nodes[a0]["present"] = True
        if T.has_edge(a0, "res"): T.remove_edge(a0, "res")
        T.add_node("run", kind="instance", system="s0", creator=None, t_created=11, present=True)
        T.add_edge(a0, "run", rel="generates", grade="B"); T.add_edge("run", "res", rel="invokes", grade="B")
    if f["egress"] and arts:
        T.add_node("copy", kind="artifact", system="s3", creator="cred_q", t_created=4, present=True)
        T.add_edge(arts[0], "copy", rel="delivers", grade="B"); T.add_edge("copy", "f", rel="activates", grade="B")
    fires_W, fires_H = {}, {}
    for v in T.nodes:
        fw = rng.random() < 0.5; fires_W[v] = fw
        cut = (f["shortH"] or f["clkskew"]) and rng.random() < 0.5
        fires_H[v] = fw and not cut
    for v in ("res", "f", "run", "copy"):
        if v in T: fires_W[v] = fires_H[v] = True
    # ---- observation
    O = T.copy()
    for v in ("late",): 
        if v in O: O.remove_node(v)
    if f["authgap"]: O.remove_node("hid")               # hart stays: enumeration of s2 is complete
    if "run" in O:
        if f["genunsupported"]: O.remove_node("run")
        else: O.nodes["run"]["present"] = None          # generated instance: presence unknown at t_s
    if "copy" in O and f["deliverygap"]: O.remove_node("copy")
    for v in list(O.nodes):
        if v == "q" or v not in O: continue
        a = O.nodes[v]
        a["refuted"] = not fires_H[v]; a["confirmed"] = fires_H[v] and a.get("present") is True and rng.random() < 0.5
        if f["undeclared"] and a.get("system") == "x9": O.remove_node(v); continue
        if a["kind"] == "artifact" and v != "hart":
            if (f["hide"] or f["commonmode"] or f["c9common"] or f["compromise"]) and rng.random() < 0.5: O.remove_node(v); continue
            if f["histgap"] and rng.random() < 0.5: a["creator"] = None
            if f["stale"] and a["present"] and rng.random() < 0.5: a["present"] = False
    egress_observed = "copy" in O
    return T, O, f, egress_observed, fires_W

def conditions(f, egress_observed, ablate=None):
    """Values a correct implementation reports; an ablation removes one cause from one condition."""
    c4a_causes = {"hide": f["hide"], "commonmode": f["commonmode"], "gen": f["genunsupported"] and f["gen"]}
    if ablate == "heuristic_C4a": c4a_causes["commonmode"] = False
    if ablate == "no_gen": c4a_causes["gen"] = False
    c8_causes = {"shortH": f["shortH"], "clk": f["clkskew"]}
    if ablate == "no_clk_margin": c8_causes["clk"] = False
    if ablate == "no_C8": c8_causes = {}
    conds = {
        "C0": True if ablate == "no_C0" else not f["authgap"],
        "C1": True if ablate == "no_fence" else not f["nofence"],
        "C2": not f["undeclared"],
        "C3": not f["outscope"],
        "C4a": not any(c4a_causes.values()),
        "C4b": True if ablate == "no_C4b" else not f["histgap"],
        "C4c": not (f["deliverygap"] and f["egress"]),
        "C5": True if (ablate == "no_barrier" or not f["stale"]) else None,
        "C6": None,
        "C7": not egress_observed,
        "C8": not any(c8_causes.values()),
        "C9": True if ablate == "no_C9" else not (f["compromise"] or f["c9common"]),
    }
    enumerable = not (f["nofence"] or f["compromise"] or f["c9common"] or f["undeclared"] or f["authgap"])
    return conds, enumerable

def truth_violation(T, fires_W):
    """Ground truth: an effect in F- inside S, reachable from an element authored by Auth_true(q), fires within W."""
    auth = {v for v in T.nodes if T.nodes[v].get("kind") == "identity"}
    src = {v for v, a in T.nodes(data=True) if a.get("creator") in auth and a.get("system") in SCOPE and a.get("present")}
    h = T.subgraph([v for v, a in T.nodes(data=True) if v != "q" and a.get("system") in SCOPE and a.get("present") and fires_W[v]])
    return any(s in h and "f" in (nx.descendants(h, s) | {s}) for s in src)

ABLATIONS = (None, "no_C0", "no_U", "no_C4b", "no_fence", "no_barrier", "no_C8", "no_clk_margin", "heuristic_C4a", "no_C9", "no_gen")

def run(n=20000, seed=7, ablate=None, e_v="D"):
    rng = random.Random(seed); counts, false_complete = {}, 0
    for _ in range(n):
        T, O, f, egress_observed, fW = world(rng)
        r = REG(O, effects={"f"})
        auth = auth_closure(r)
        srcs = d_verify(r, e_v) | (set() if ablate == "no_U" else u_set(r, auth, SCOPE, 0, 10))
        conds, enumerable = conditions(f, egress_observed, ablate)
        conds["C6"] = not p_h_nonempty(r, srcs, SCOPE)
        st = assign_state(p_h_nonempty(r, srcs, SCOPE, confirmed_only=True), conds, enumerable)
        counts[st] = counts.get(st, 0) + 1
        if st == "COMPLETE" and truth_violation(T, fW): false_complete += 1
    return counts, false_complete

def unit_checks():
    assert strictly_below("E", "D") and not strictly_below("C1", "C2") and not strictly_below("C2", "C1")
    assert geq("A", "B") and not geq("C1", "C2")
    # Proposition 2: e_a >= e_v implies D_act subset of D_verify
    g = nx.DiGraph(); g.add_node("q", kind="origin")
    for i, gr in enumerate(["A", "B", "C1", "C2", "D", "E"]):
        g.add_node(f"n{i}", kind="artifact"); g.add_edge("q", f"n{i}", rel="creates", grade=gr)
    r = REG(g)
    for ea, ev in [("B", "D"), ("A", "E"), ("C1", "D")]:
        assert d_act(r, ea) <= d_verify(r, ev)
    # min-cut special case agrees with exhaustive hitting set on a small graph
    g = nx.DiGraph(); g.add_node("q", kind="origin")
    for v in "abcf": g.add_node(v, system="s0", present=True, refuted=False, kind="artifact")
    g.add_edges_from([("a", "f"), ("b", "c"), ("c", "f")])
    r = REG(g, effects={"f"}); cost = {"a": 2, "b": 5, "c": 1}
    cut, val = min_cut_plan(r, {"a", "b"}, {"s0"}, cost)
    best, bc = hitting_set_plan([("a", "f"), ("b", "c", "f")], {m: (cost[m], {m}) for m in cost}, lambda X: True)
    assert val == bc == 3 and cut == best == {"a", "c"}
    # invariant can make synthesis infeasible
    best, _ = hitting_set_plan([("a",)], {"m1": (1, {"a"})}, lambda X: "m1" not in X)
    assert best is None
    # Fail closed on incomplete condition dictionaries: none of the admission keys may be omitted.
    assert assign_state(False, {}, True) != "COMPLETE"
    required = {"C0", "C1", "C2", "C3", "C4a", "C4b", "C4c", "C5", "C6", "C7", "C8", "C9"}
    assert assign_state(False, {k: True for k in required}, True) == "COMPLETE"
    assert assign_state(False, {k: True for k in required if k != "C9"}, True) != "COMPLETE"
    # An unbounded cut is infeasible, not a successful empty remediation.
    g = nx.DiGraph(); g.add_node("a", system="s0", present=True, refuted=False, kind="artifact")
    g.add_node("f", system="s0", present=True, refuted=False, kind="effect")
    g.add_edge("a", "f"); cut, val = min_cut_plan(REG(g, effects={"f"}), {"a"}, {"s0"}, {})
    assert cut is None and val == float("inf")
    print("unit checks: pass")

if __name__ == "__main__":
    unit_checks()
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        total = false = 0
        for seed in range(1, 11):
            c, fc = run(n=20000, seed=seed); total += c.get("COMPLETE", 0); false += fc
        print(f"sweep seeds 1-10 x 20000 worlds: COMPLETE={total} false_COMPLETE={false} "
              f"one-sided 95% upper bound={1 - 0.05 ** (1 / total):.5f}")
        sys.exit(0)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    for ab in ABLATIONS:
        c, fc = run(n=n, ablate=ab)
        print(f"{str(ab or 'full model'):14s} states={dict(sorted(c.items()))} false_COMPLETE={fc}")
