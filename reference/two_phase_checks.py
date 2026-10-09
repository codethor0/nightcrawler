"""Independent targeted regression checks for the two-phase NIGHTCRAWLER semantics.

This is an executable abstraction, not a real provider adapter or proof of safety.
Evidence completeness is an explicit modeled provider contract. A sealed oracle
tracks effects independent of the analyzed records. Historical guards are never
re-tested during prospective reachability.

Run: python3 reference/two_phase_checks.py
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from hashlib import sha256
from itertools import combinations

@dataclass(frozen=True)
class Event:
    source: str
    target: str
    kind: str                # executed past relation: created/generated/acquired/reset/delivered
    time: float
    evidence: str = 'C1'     # may be below action threshold; do not discard historically

@dataclass(frozen=True)
class Future:
    source: str
    target: str
    possible: bool = True  # UNKNOWN treated as possible
    confirmed: bool = False

@dataclass
class World:
    historical: list[Event] = field(default_factory=list)
    future: list[Future] = field(default_factory=list)
    present: set[str] = field(default_factory=set)
    actors: set[str] = field(default_factory=lambda:{'cred_q'})
    author_history: dict[str,str] = field(default_factory=dict)
    source_identities: set[str] = field(default_factory=lambda:{'cred_q'})
    provider_logs: set[str] = field(default_factory=lambda:{'issuer','provider'})
    covered_logs: set[str] = field(default_factory=lambda:{'issuer','provider'})
    protected_digest: str = 'provider-signed-history-v1'
    corroboration_digest: str = 'provider-signed-history-v1'
    externally_verified: bool = True
    auth_relations: list[tuple[str,str,str]] = field(default_factory=list)  # src,dst, kind
    required_secret_sources: set[str] = field(default_factory=set)
    covered_secret_sources: set[str] = field(default_factory=set)
    required_recovery_sources: set[str] = field(default_factory=set)
    covered_recovery_sources: set[str] = field(default_factory=set)
    required_receivers: set[str] = field(default_factory=set)
    covered_receivers: set[str] = field(default_factory=set)
    fences: dict[str,float] = field(default_factory=lambda:{'cred_q':1.5})
    snapshot: float=2.0
    issue: float=3.0
    window: float=3.0
    horizon: float=10.0
    epsilon: float=.01
    provider_clock_bound: bool=True
    systems: set[str] = field(default_factory=lambda:{'in-scope'})
    supported_systems: set[str] = field(default_factory=lambda:{'in-scope'})
    reachable_systems: set[str] = field(default_factory=lambda:{'in-scope'})
    barrier_ok: bool=True
    complete_historical: bool=True
    complete_objects: bool=True
    complete_delivery: bool=True
    unresolved_egress: bool=False
    truth_violation: bool=False  # sealed oracle; never consulted by evaluate()


def reach(start: set[str], edges: list[tuple[str,str]]) -> set[str]:
    nxt=defaultdict(list)
    for a,b in edges: nxt[a].append(b)
    out=set(start)
    work=deque(out)
    while work:
        for b in nxt[work.popleft()]:
            if b not in out: out.add(b); work.append(b)
    return out


def observed_authority(w:World):
    # Model reads every covered, independently evidenced acquisition/reset/issuance relation.
    return reach(set(w.source_identities),[(a,b) for a,b,_ in w.auth_relations])


def residual_carriers(w:World,auth:set[str]):
    # ALL historical evidence classes, including low-grade C1; no future guard filtering.
    old_edges=[(x.source,x.target) for x in w.historical if x.time <= w.snapshot]
    descendants=reach({'q','cred_q'} | auth,old_edges)
    authored={v for v,identity in w.author_history.items() if identity in auth}
    return (descendants|authored)&set(w.present)


def live_paths(w:World,seed:set[str]):
    possible=[(x.source,x.target) for x in w.future if x.possible]
    return 'effect' in reach(seed,possible)


def conditions(w:World):
    auth=observed_authority(w)
    # C0 is computed from the represented evidence sources and record classes.
    c0=(w.provider_logs <= w.covered_logs
        and w.required_secret_sources <= w.covered_secret_sources
        and w.required_recovery_sources <= w.covered_recovery_sources
        and w.required_receivers <= w.covered_receivers
        and bool(w.protected_digest))
    c1=auth <= set(w.fences) and all(w.fences[a]<w.snapshot for a in auth)
    c2=w.reachable_systems<=w.supported_systems
    c3=w.reachable_systems<=w.systems
    c4a=w.complete_objects
    c4b=w.complete_historical
    c4c=w.complete_delivery
    c5=w.barrier_ok
    carriers=residual_carriers(w,auth)
    c6=not live_paths(w,carriers)
    c7=not w.unresolved_egress
    c8=w.provider_clock_bound and w.horizon >= w.window+(w.issue-w.snapshot)+2*w.epsilon
    c9=w.externally_verified and w.protected_digest==w.corroboration_digest
    return {"C0":c0,"C1":c1,"C2":c2,"C3":c3,"C4a":c4a,"C4b":c4b,"C4c":c4c,
            "C5":c5,"C6":c6,"C7":c7,"C8":c8,"C9":c9},carriers


CONDITIONS = frozenset(('C0','C1','C2','C3','C4a','C4b','C4c','C5','C6','C7','C8','C9'))


def named_gaps(w:World,c:dict,carriers:set[str]):
    """Produce modeled, explicit gaps; mark epistemic gaps unenumerable.

    A named source with missing records does not enumerate the unknown principals
    or messages inside those records. This is not a provider completeness oracle.
    """
    gaps=[]
    def gap(check, name, enumerable):
        gaps.append((check,name,enumerable))
    if not c['C0']:
        for source in sorted(w.provider_logs-w.covered_logs): gap('C0','uncovered issuer/history '+source,False)
        for source in sorted(w.required_secret_sources-w.covered_secret_sources): gap('C0','uncovered readable-secret source '+source,False)
        for source in sorted(w.required_recovery_sources-w.covered_recovery_sources): gap('C0','uncovered recovery provenance '+source,False)
        for source in sorted(w.required_receivers-w.covered_receivers): gap('C0','uncovered accepting-side trust '+source,False)
        if not w.protected_digest: gap('C0','missing provider history digest',False)
    if not c['C1']:
        for identity in sorted(set(observed_authority(w))-set(w.fences)):
            gap('C1','unfenced authority '+identity,False)
        for identity in sorted(set(observed_authority(w)) & set(w.fences)):
            if w.fences[identity]>=w.snapshot: gap('C1','fence not effective before snapshot '+identity,False)
    if not c['C2']:
        for provider in sorted(w.reachable_systems-w.supported_systems):
            gap('C2','unsupported adapter '+provider,True)
    if not c['C3']:
        for provider in sorted(w.reachable_systems-w.systems):
            gap('C3','out-of-scope reachable system '+provider,True)
    if not c['C4a']: gap('C4a','object and generation-rule coverage for named provider',True)
    if not c['C4b']: gap('C4b','historical authorship or handoff coverage for named provider',True)
    if not c['C4c']: gap('C4c','outbound delivery-history coverage for named provider',True)
    if not c['C5']: gap('C5','unknown provider barrier effectiveness',False)
    if not c['C6']:
        for source in sorted(carriers):
            if live_paths(w,{source}): gap('C6','unrefuted future path from '+source,True)
    if not c['C7']: gap('C7','outbound egress to known partner',True)
    if not c['C8']:
        if not w.provider_clock_bound: gap('C8','unknown provider clock bound',False)
        else: gap('C8','insufficient named horizon',True)
    if not c['C9']: gap('C9','conflicting or unauthenticated independent evidence',False)
    for check, value in c.items():
        if not value and not any(g[0] == check for g in gaps):
            gap(check,'unaccounted evidence gap',False)
    return gaps


def evaluate(w:World):
    c,carriers=conditions(w)
    live=not c['C6']
    confirmed_sources={edge.source for edge in w.future if edge.confirmed}
    confirmed_live=live and bool(carriers&confirmed_sources)
    if confirmed_live: state='FAILED'
    elif set(c)==CONDITIONS and all(c[k] is True for k in CONDITIONS): state='COMPLETE'
    else:
        gaps=named_gaps(w,c,carriers)
        state='BOUNDED' if gaps and all(item[2] for item in gaps) else 'INDETERMINATE'
    return state,c,carriers


def baseline():
    w=World()
    w.historical=[Event('q','trigger','creates',.5,'B'), Event('trigger','M','generates',1.0,'C1')]
    w.future=[Future('M','effect',possible=True,confirmed=False)]
    w.present={'trigger','M'}
    w.author_history={'trigger':'cred_q','M':'provider'}
    w.truth_violation=True  # effect fires at true time 4
    return w


def check(name,w,expect,truth=None,contains=()):
    state,c,carriers=evaluate(w)
    assert state==expect,(name,state,c,carriers)
    assert set(contains)<=carriers,(name,carriers)
    if truth is not None:
        assert w.truth_violation is truth
        assert not (state=='COMPLETE' and w.truth_violation), 'false COMPLETE:'+name
    print(f'PASS {name:42s} state={state:13s} C0={c["C0"]} C1={c["C1"]} C4b={c["C4b"]} C6={c["C6"]}')


def cost_check():
    cover={'m1':({'p1','p2'},1),'m2':({'p2'},1),'m3':({'p4'},2),
           'm4':({'p1','p2','p3'},3),'m5':({'p1','p2','p3'},2),'m6':({'p3'},1)}
    paths={'p1','p2','p3','p4'}
    plans=[]
    for k in range(len(cover)+1):
        for names in combinations(cover,k):
            if 'm5' in names: continue  # protected shared runner invariant
            if set().union(*(cover[n][0] for n in names))==paths:
                plans.append((sum(cover[n][1] for n in names), names))
    assert min(plans)==(4,('m1','m3','m6')),min(plans)
    print('PASS remediation minimum feasible cost=4 actions=m1,m3,m6 (m1 disables entire workflow)')


def main():
    w=baseline()
    check('historical fired trigger -> delayed child',w,'BOUNDED',True,('M',))
    w=baseline();w.future=[Future('M','effect',possible=True,confirmed=True)]
    check('confirmed surviving delayed child',w,'FAILED',True)
    w=baseline();w.historical=[w.historical[0]];w.complete_historical=False
    check('missing historical handoff cannot COMPLETE',w,'BOUNDED',True)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False
    check('verified no survivor can COMPLETE',w,'COMPLETE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.required_secret_sources={'vaultA'}
    check('uncovered static-secret read blocks C0',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.required_recovery_sources={'mailbox_reset'}
    check('mailbox recovery without factor log',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.auth_relations=[('cred_q','id2','acquires')]
    check('newly discovered identity not yet fenced',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.auth_relations=[('cred_q','id2','acquires')];w.fences['id2']=1.8
    check('late identity fenced before resnapshot',w,'COMPLETE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.protected_digest='signed-h';w.corroboration_digest='different'
    check('independent evidence digest disagreement',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.reachable_systems={'in-scope','partner'}
    check('partner without adapter fails C2 and C3',w,'BOUNDED',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.unresolved_egress=True;w.complete_delivery=True
    check('C4c coverage TRUE C7 egress FALSE',w,'BOUNDED',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.provider_clock_bound=False
    check('unbounded provider clock forbids COMPLETE',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.provider_logs.add('external-issuer')
    check('uncovered issuer history cannot COMPLETE',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.required_receivers.add('external-trust')
    check('missing accepting trust provenance',w,'INDETERMINATE',False)
    w=baseline();w.future=[];w.present={'trigger'};w.truth_violation=False;w.barrier_ok=False
    check('unknown barrier cannot COMPLETE',w,'INDETERMINATE',False)
    cost_check()
    print('ALL 16 TARGETED TESTS PASS (modeled evidence contracts; no real-provider safety claim)')

if __name__=='__main__':main()
