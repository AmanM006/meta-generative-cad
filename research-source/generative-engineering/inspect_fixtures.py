import json

for fid in ["muse_exp01_a_feasible_fixture.json", "muse_exp02_d_feasible_fixture.json"]:
    with open(fid) as f:
        d = json.load(f)
    print(fid, "conns:")
    for i, c in enumerate(d["connections"]):
        th = c["thickness"] * 1000.0
        print(f"  [{i}] {c['from_type']}_{c['from_index']}:{c['from_port']} -> {c['to_type']}_{c['to_index']}:{c['to_port']} h={th:.4f}mm")
    print(fid, "stages:")
    for i, s in enumerate(d["stages"]):
        print(f"  Stage {i}: center={s['center']}, height={s['height']}")
    print(fid, "anchors:", d["anchors"])
