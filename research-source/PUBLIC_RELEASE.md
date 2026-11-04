# Neodustria public source snapshot

This repository is a clean source and evidence snapshot for the Meta Global AI
Developer Hackathon. It contains no private repository history or API keys.

Live studio: https://neodustria-studio.onrender.com

Start with `START_HERE_INTENT.md`, `INTENT_SCIENTIST_VERDICT.md`, and
`DEMO_CAPTURE_3_MINUTES.md`. The core implementation is in
`engineering_intent.py`, `server.py`, `open_ended_structural_discovery_engine.py`,
`engineering_runtime/`, and `frontend/`.

Offline reproduction:

```sh
python -m pip install -r requirements.txt
python audit_engineering_intent.py
python verify_intent_corruption.py
```

The current Intent Lab asks one missing-input question using deterministic
rules. Recorded Muse examples are replayed with their receipts. The hosted app
does not make new model calls or run FEA. The C01 1.0 mm candidate passed four
joint thickness/modulus corner cases in the 2D beam model. Clearance and
fabrication validation were not performed. The full 20-task clarification
comparison requested after this release was not completed before the deadline.
