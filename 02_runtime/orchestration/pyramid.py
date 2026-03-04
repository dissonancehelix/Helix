import random

def degree_preserving_random_rewire(g_dict, n_swaps=100):
    g = {k: list(v) for k, v in g_dict.items()}
    edges = []
    for u in g:
        for v in g[u]:
            if u < v: edges.append((u, v))
    if len(edges) < 2: return g_dict
    for _ in range(n_swaps):
        i, j = random.sample(range(len(edges)), 2)
        u, v = edges[i]
        x, y = edges[j]
        if len({u, v, x, y}) == 4:
            if random.random() < 0.5:
                if x not in g[u] and y not in g[v]:
                    g[u].remove(v); g[v].remove(u)
                    g[x].remove(y); g[y].remove(x)
                    g[u].append(x); g[x].append(u)
                    g[v].append(y); g[y].append(v)
                    edges[i] = (min(u,x), max(u,x))
                    edges[j] = (min(v,y), max(v,y))
            else:
                if y not in g[u] and x not in g[v]:
                    g[u].remove(v); g[v].remove(u)
                    g[x].remove(y); g[y].remove(x)
                    g[u].append(y); g[y].append(u)
                    g[v].append(x); g[x].append(v)
                    edges[i] = (min(u,y), max(u,y))
                    edges[j] = (min(v,x), max(v,x))
    return {k: set(v) for k, v in g.items()}
