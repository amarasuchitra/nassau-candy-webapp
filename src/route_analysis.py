"""Route clustering and switching-cost decisions (the same logic as web/index.html).

Run from the repo root:  python src/route_analysis.py web/data/dashboard_bundle.json 4
"""
import json, math, sys
import numpy as np

B = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'web/data/dashboard_bundle.json'))
SIM, RECS = B['dashboard_data'], B['recommendations']

def routes():
    agg = {}
    for r in SIM:
        # one row per route: the current factory, Standard Class (the most common ship mode)
        if not r['is_current'] or r['ship_mode'] != 'Standard Class': continue
        agg[(r['product'], r['region'])] = r
    best = {}
    for r in RECS:
        k = (r['Product Name'], r['Region'])
        if k not in best or r['lead_time_reduction_pct'] > best[k]: best[k] = r['lead_time_reduction_pct']
    out = []
    for k, a in agg.items():
        out.append(dict(product=a['product'], region=a['region'], factory=a['factory'], orders=a['orders'],
                        distance=a['distance'], lead_time=a['lead_time'], ship_cost=a['ship_cost'], gain=max(0.0, best.get(k, 0.0))))
    out.sort(key=lambda x: (x['product'], x['region']))
    return out

def feats(R):
    X = np.array([[r['distance'], math.log1p(r['orders']), r['gain']] for r in R])
    mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1
    return (X - mu) / sd

def kmeans(Z, k, iters=100):
    # deterministic init: start at the busiest route, then repeatedly take the farthest point
    first = int(np.argmax(Z[:, 1]))
    C = [Z[first]]
    for _ in range(1, k):
        d = np.min([((Z - c)**2).sum(1) for c in C], axis=0)
        C.append(Z[int(np.argmax(d))])
    C = np.array(C)
    for _ in range(iters):
        lab = np.argmin(((Z[:, None, :] - C[None])**2).sum(2), 1)
        newC = np.array([Z[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
        if np.allclose(newC, C): break
        C = newC
    return lab, C

def silhouette(Z, lab):
    from sklearn.metrics import silhouette_score
    return silhouette_score(Z, lab)

if __name__ == '__main__':
    R = routes(); Z = feats(R)
    print('routes', len(R))
    for k in range(2, 7):
        lab, C = kmeans(Z, k); print('k', k, 'silhouette', round(silhouette(Z, lab), 3), np.bincount(lab))
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 4; lab, C = kmeans(Z, k)
    for j in range(k):
        m = [r for r, l in zip(R, lab) if l == j]
        print(j, len(m), 'centroid z', np.round(C[j], 2), 'mean dist', round(np.mean([r['distance'] for r in m])), 'lt', round(np.mean([r['lead_time'] for r in m]), 2),
              'orders', round(np.mean([r['orders'] for r in m])), 'gain', round(np.mean([r['gain'] for r in m]), 1), 'total orders', sum(r['orders'] for r in m))

def best_moves():
    best = {}
    for r in RECS:
        k = (r['Product Name'], r['Region'])
        if k not in best or r['composite_score'] > best[k]['composite_score']: best[k] = r
    return best

def decide(r, cost, limit, min_orders):
    """Reallocate / Pilot first / Keep current for one route's best move."""
    saving = r['profit_impact_per_order'] * r['orders_affected']          # $ per year (2025 volume)
    faster = r['lead_time_reduction_pct'] > 0
    payback = cost / saving * 12 if saving > 0 else math.inf            # months
    if not faster or saving <= 0 or r['orders_affected'] < min_orders or payback > 2 * limit:
        return 'Keep current', saving, payback
    if payback <= limit and r['confidence_score'] >= 0.3:
        return 'Reallocate', saving, payback
    return 'Pilot first', saving, payback

def decisions(cost=1500, limit=12, min_orders=20):
    out = {}
    for k, r in best_moves().items():
        out[k] = decide(r, cost, limit, min_orders)
    return out


if __name__ == '__main__':
    from collections import Counter
    d = decisions()
    print('decisions (switching cost $1,500, payback 12 months, >= 20 orders):', dict(Counter(v[0] for v in d.values())))
