import sys
import numpy as np
from pathlib import Path
BASE_DIR = Path('.').resolve()
sys.path.insert(0, str(BASE_DIR / 'generative-engineering'))
sys.path.insert(0, str(BASE_DIR / 'generative_engineering_src'))
from topology_innovation_engine_v2 import TopologyInnovationEngineV2
import test_folded_shuttle

spec = test_folded_shuttle.spec
eng = TopologyInnovationEngineV2(env_x=0.070, env_y=0.040)
mesh = eng.compiler.compile(spec, n_elem_per_beam=2)
for idx, el in enumerate(mesh['elements']):
    p0 = mesh['nodes'][el[0]]
    p1 = mesh['nodes'][el[1]]
    w = mesh['widths'][idx]
    print(f"el {idx:2d}: nodes {el[0]:2d}->{el[1]:2d} | pos [{p0[0]:.3f}, {p0[1]:.3f}] -> [{p1[0]:.3f}, {p1[1]:.3f}] | width={w*1000:.2f}mm")
