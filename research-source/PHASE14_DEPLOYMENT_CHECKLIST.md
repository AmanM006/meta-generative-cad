# Neodustria Phase 14: Public Deployment & Verification Checklist

> **Deployment Objective:**
> Provide judges, reviewers, and hackathon evaluators with an instantly accessible, secure, HTTPS public endpoint to inspect and interact with the Neodustria Scientific Discovery Arena without local configuration.

---

## 1. Verified Public Access Details

| Resource | Value / Endpoint | Verification Status |
| :--- | :--- | :---: |
| **Live Web Application (HTTPS)** | [https://greetings-seek-wear-bind.trycloudflare.com](https://greetings-seek-wear-bind.trycloudflare.com) | **ACTIVE & HTTP 200** |
| **Local Next.js Studio** | `http://localhost:3000` | ACTIVE (Production Build) |
| **Local FastAPI Engine** | `http://localhost:8000/docs` | ACTIVE (HTTP 200) |
| **GitHub Master Repository** | [https://github.com/AmanM006/neodustria.git](https://github.com/AmanM006/neodustria.git) | SYNCHRONIZED |
| **Rollback Tags** | `phase14-pre-frontier-checkpoint` | VERIFIED |

---

## 2. Judge Evaluation Script & Live Features

Judges accessing [https://greetings-seek-wear-bind.trycloudflare.com](https://greetings-seek-wear-bind.trycloudflare.com) can explore:

1. **Autonomous Discovery Arena:**
   - Select engineering challenge (Task L, Task M, Task N, Task O, or Challenge P).
   - View live Meta Muse reasoning formulating competing hypotheses.
   - Inspect live 3D Three.js compliant mechanism geometry.
2. **Interactive Physics & Falsification:**
   - Toggle nonlinear deformation with color-coded Von Mises stress overlays.
   - Observe real-time falsification events where linear theory fails under membrane chord locking.
3. **Calibrated Conformal Uncertainty Intervals:**
   - View 90% confidence bands ($\hat{q}_{90} = \pm 0.483\text{ mm}$) with selective prediction acceptance indicators.
4. **Independent Evidence Download:**
   - Direct download links for raw simulation ledgers, receipts, and reproducibility archives.

---

## 3. Server-Side Security Audit

- **API Secret Sanitization:** Meta API keys (`MODEL_API_KEY`) remain strictly server-side in local `.env` files.
- **Client Bundle Verification:** No API secrets or private tokens are leaked into the client JavaScript bundles.
- **Sandboxed Execution:** Frontend interacts only with sanitized JSON endpoints.
