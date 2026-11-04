import sys
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from casm_memory_engine import CounterexampleAwareMemoryEngine

mem = CounterexampleAwareMemoryEngine()
tasks = [
    {'id': 'Task_L', 'env': [95.0, 55.0], 'Fy': 9.0, 'dy': 2.20},
    {'id': 'Task_M', 'env': [50.0, 35.0], 'Fy': 1.0, 'dy': 1.80},
    {'id': 'Task_N', 'env': [70.0, 40.0], 'Fy': 2.5, 'dy': 1.70},
    {'id': 'Task_O', 'env': [90.0, 35.0], 'Fy': 4.5, 'dy': 2.50}
]

for t in tasks:
    q = mem.query_principles(t['env'], t['Fy'], t['dy'])
    print(f"\n=== {t['id']} ===")
    print(f"  Regime: Force={q['regime']['force_regime']}, Scale={q['regime']['scale_regime']}, Aspect={q['regime']['aspect_ratio']:.2f}")
    print(f"  Applicable: {[p['principle_id'] for p in q['applicable_principles']]}")
    print(f"  Rejected: {[r['principle_id'] for r in q['rejected_principles']]}")
    for rp in q['rejected_principles']:
        print(f"    {rp['principle_id']} rejected: {rp['reasons']}")
