import json
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ID_DIR = ROOT / 'data' / 'domains_identity_pack'

def load_domains():
    if not ID_DIR.exists(): return []
    res = []
    for p in ID_DIR.glob('*.json'):
        with open(p, 'r', encoding='utf-8') as f:
            d = json.load(f)
            # determine regime
            txt = (d.get('stability_condition', '') + ' ' + d.get('failure_mode', '')).lower()
            if 'drift' in txt or 'degrade' in txt: regime = 'DRIFTS'
            elif 'flip' in txt or 'switch' in txt or 'alternat' in txt: regime = 'FLIPS'
            elif 'shatter' in txt or 'diverge' in txt or 'catastroph' in txt or 'cascade' in txt or 'explosion' in txt: regime = 'SHATTERS'
            else: regime = 'PERSISTS'
            
            # get constraints
            mem = 'memory' in txt or 'trace' in txt or 'state' in txt or 'accumulator' in txt
            ctrl = 'control' in txt or 'feedback' in txt or 'homeostat' in txt or 'adapt' in txt
            commit = 'lock' in txt or 'latch' in txt or 'irreversibl' in txt or 'absorb' in txt
            branch = 'branch' in txt or 'rout' in txt or 'arbitrat' in txt or 'polic' in txt
            slack = 'slack' in txt or 'buffer' in txt or 'redundanc' in txt
            
            res.append({
                'id': d['id'],
                'regime': regime,
                'memory': mem,
                'control': ctrl,
                'commit': commit,
                'branch': branch,
                'slack': slack
            })
    return res

def find_minimal_constraints(domains):
    print("Running Minimal Constraint Ablation Test on 24 Identity Domains\n")
    
    regime_counts = {}
    for d in domains:
        regime_counts[d['regime']] = regime_counts.get(d['regime'], 0) + 1
    
    print("Regime Baseline:")
    for k, v in regime_counts.items():
        print(f"  {k}: {v}")
    print("\n--- Testing Constraints for 'PERSISTS' ---")
    
    features = ['memory', 'control', 'commit', 'branch', 'slack']
    for k in range(1, 4):
        for combo in itertools.combinations(features, k):
            # check domains that have all these features
            subset = [d for d in domains if all(d[f] for f in combo)]
            if not subset: continue
            
            persists = sum(1 for d in subset if d['regime'] == 'PERSISTS')
            shatters = sum(1 for d in subset if d['regime'] == 'SHATTERS')
            
            win_rate = persists / len(subset)
            shatter_rate = shatters / len(subset)
            
            if win_rate >= 0.7:
                print(f"[HIGH PERSISTENCE] {combo}: N={len(subset)} | PERSISTS={persists} ({win_rate*100:.0f}%) | SHATTERS={shatters}")
            elif shatter_rate >= 0.7:
                print(f"[HIGH VULNERABILITY] {combo}: N={len(subset)} | SHATTERS={shatters} ({shatter_rate*100:.0f}%) | PERSISTS={persists}")

if __name__ == '__main__':
    domains = load_domains()
    if domains:
        find_minimal_constraints(domains)
    else:
        print("Identity pack not found.")
