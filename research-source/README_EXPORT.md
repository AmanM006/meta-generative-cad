# Neodustria: Autonomous Generative Engineering Scientist

**Meta Global AI Developer Hackathon 2026**  
**Track:** Indie Developer — Push the Frontier  
**Baseline Git Commit:** `bf8797a` (Tag: `phase23-5-final-freeze`)

---

## 1. Quick Start & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Node.js 18+ and npm
- (Optional) Meta AI API key (`MODEL_API_KEY`) for live model inference; all offline and replay modes run without credentials.

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# (Optional) Configure environment
cp .env.example .env
# Edit .env with your MODEL_API_KEY if running live inference

# Start FastAPI backend server
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```
Backend Swagger API documentation will be live at: `http://127.0.0.1:8000/docs`

### Frontend Setup
```bash
cd frontend

# Install Node dependencies (uses existing package-lock.json)
npm install

# Build production assets
npm run build

# Start Next.js server
npm run start -- -p 3000
```
Frontend WebGL / Three.js CAD Studio will be live at: `http://127.0.0.1:3000`

---

## 2. Scientific Reproduction & Verification Commands

Neodustria includes a unified reproduction harness supporting both instant ledger audits and fresh numerical non-linear FEA recomputations:

```bash
# 1. Fast Ledger & Data Consistency Check (Instant)
python reproduce_phase23_5_evidence.py --fast

# 2. Recompute Non-Linear Beam FEA & Real 2D Q4 Continuum Solver
# Executes fresh mesh refinement (80, 320, 720, 1280 elements) and Richardson extrapolation
python reproduce_phase23_5_evidence.py --physics

# 3. Seven-Arm Causal Benchmark Evaluation
# Runs deterministic arms live and replays authentic model proposals with live FEA
python reproduce_phase23_5_evidence.py --causal

# 4. Blinded Inductive Discovery & Hypothesis Revision
# Generates 35 fresh FEA points and validates 83.92% RMSE reduction
python reproduce_phase23_5_evidence.py --discovery

# 5. Master Authentic Meta Muse Request-Level Receipts Audit
# Audits 130 authentic API calls with SHA-256 prompt/response hashes
python reproduce_phase23_5_evidence.py --replay

# 6. Run Complete Pipeline
python reproduce_phase23_5_evidence.py --full

# 7. Run Adversarial Scientific Integrity Auditor
# Validates 7 gates + 3 adversarial corruption sensitivity tests
python audit_phase23_5_scientific_integrity.py
```

---

## 3. Project Structure

- `frontend/` - Next.js 15, React 19, Three.js, Lucide icons, Tailwind CSS CAD Studio.
- `server.py` - FastAPI backend orchestrating the autonomous cycle and GLB export.
- `reproduce_phase23_5_evidence.py` - Unified command-line reproduction harness.
- `audit_phase23_5_scientific_integrity.py` - Adversarial integrity verification suite.
- `audit_continuum_hierarchy.py` - 2D Total Lagrangian Q4 continuum nonlinear solver.
- `dedicated_folded_continuum_solver.py` - Specialized folded shuttle continuum engine.
- `topology_innovation_engine_v2.py` - Corotational non-linear beam FEA solver.
- `compositional_graph_engine.py` - Kinematic graph compiler for multi-stage flexures.
- `neodustria_gp_first_scientist.py` - GP-first hybrid autonomous engineering scientist.
- `phase21_autonomous_scientist.py` - Authenticated Meta Muse (`muse-spark-1.3`) API client.
- `PHASE23_5_*.json` - Verified experimental and computational evidence ledgers.
- `NEODUSTRIA_PHASE23_5_COMPLETE_REPRODUCIBILITY.zip` - Standalone reproducibility archive.
