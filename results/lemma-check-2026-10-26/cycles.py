import networkx as nx
from qiskit_ibm_runtime.fake_provider import FakeMarrakesh, FakeTorino, FakeFez, FakeKingston
for F in (FakeMarrakesh, FakeTorino, FakeFez, FakeKingston):
    try: b=F()
    except Exception as e: print(F.__name__, e); continue
    G=nx.Graph(); G.add_edges_from(tuple(e) for e in b.coupling_map.get_edges())
    cnt={}
    for c in nx.simple_cycles(G, length_bound=22): cnt[len(c)]=cnt.get(len(c),0)+1
    deg3=[e for e in G.edges if G.degree[e[0]]==3 and G.degree[e[1]]==3]
    print(F.__name__, G.number_of_nodes(), dict(sorted(cnt.items())), "deg3-deg3 couplers:", len(deg3))
