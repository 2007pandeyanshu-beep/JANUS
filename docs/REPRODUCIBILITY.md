# JANUS Canonical Reproducibility Guide & Benchmark Audit

**Document Version:** 1.0.0 (Release 6.0)  
**Target Repository:** `https://github.com/2007pandeyanshu-beep/JANUS.git`  
**Workspace:** `C:\Users\2007p\OneDrive\Desktop\JANUS`  
**Audited Branch:** `main`  
**Latest Local Verified Commit:** `3300bc1` (ahead of `origin/main` by 7 commits)  
**Verification Date:** 2026-10-21  

---

## 1. Scope & Epistemological Boundaries

This document provides a complete, turnkey reproducibility manual and verification audit for independent researchers seeking to audit, reproduce, or extend the **JANUS Sequential Bayesian Experimental Design (BED)** system.

> [!IMPORTANT]
> **Reproducible Software Execution vs. Independently Validated Scientific Conclusions:**
> - **Reproducible Software Execution:** Every test, simulation loop, Bayesian update, entropy calculation, and statistical aggregation documented herein executes deterministically and reproduces bit-for-bit from the committed codebase using standard Python and Node.js environments.
> - **Scientific Simulation Boundary:** While the probabilistic likelihood models for case study `CS-CAT-001` are derived from peer-reviewed operando catalysis publications, all sequential executions are evaluated within an *in-silico* simulated environment using pseudo-random Bernoulli and categorical observation models.
> - **Independent Real-World Validation:** Reproducing these benchmark scripts verifies the mathematical correctness, algorithmic optimality, and decision-theoretic properties of the software. It does **not** constitute independent empirical or clinical validation of catalytic kinetics in a physical wet lab.

---

## 2. System Prerequisites & Runtime Specifications

### 2.1 Hardware and Operating System
- **Tested Platform:** Windows 11 Enterprise (x64)
- **Cross-Platform Support:** Compatible with Linux (Ubuntu 22.04+) and macOS (13.0+ Sonoma) via POSIX shell and Python 3.12.
- **Recommended Hardware:** 4+ CPU cores, 8 GB RAM, 2 GB free disk space.

### 2.2 Verified Software Runtimes
| Runtime | Verified Version | Minimum Requirement | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `3.12.10 (x64)` | `3.12.0+` | Core scientific engine, Bayesian inference, FastAPI |
| **Node.js** | `24.1.0` | `20.0.0+` | Frontend dashboard build and tooling |
| **npm** | `10.9.0` | `10.0.0+` | Node package manager |
| **PowerShell** | `7.x / 5.1` | `5.1+` | Automation and runner scripts on Windows |

---

## 3. Environment Setup & Dependency Verification

### 3.1 Python Backend Environment Setup

From the repository root (`C:\Users\2007p\OneDrive\Desktop\JANUS`):

```powershell
# 1. Create virtual environment (if starting in a clean checkout)
python -m venv .venv

# 2. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS bash:
# source .venv/bin/activate

# 3. Upgrade pip and install pinned dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### Core Python Dependencies in `backend/requirements.txt`:
- `fastapi >= 0.110.0` (REST API framework)
- `uvicorn[standard] >= 0.29.0` (ASGI web server)
- `pydantic >= 2.6.0` (Strict schema and probability validation)
- `numpy >= 1.26.0` (Array operations, bootstrap sampling, PRNG)
- `pytest >= 8.0.0` (Test execution framework)
- `pytest-cov >= 4.1.0` (Test coverage reporting)
- `httpx >= 0.27.0` (API client for endpoint testing)
- `python-dotenv >= 1.0.0` (Environment variable handling)

### 3.2 Frontend Environment Setup

```powershell
# Navigate to frontend and install npm dependencies
cd frontend
npm ci  # Or: npm install
cd ..
```

---

## 4. Execution Commands & Benchmark Verification Cheatsheet

### 4.1 Automated Backend Test Suite (62 Tests)
Executes all unit, integration, ranking consistency, edge-case, and mathematical invariant tests:

```powershell
pytest backend/tests -v
```

- **Expected Exit Code:** `0`
- **Expected Runtime:** $\approx 6.0\text{ seconds}$
- **Expected Outcome:** `62 passed` (100% pass rate)

#### Summary of Test Modules:
1. `backend/tests/test_scientific_engine.py` (7 tests): Shannon entropy, Bayesian updating, prior normalization, zero-information proofs, and infeasible candidate handling.
2. `backend/tests/test_schemas.py` (4 tests): Pydantic data contract validation, simplex bounds, and invalid prior rejections.
3. `backend/tests/test_ranking_consistency.py` (5 tests): Dual-ranking divergence proofs (EIG vs. Composite Utility on `EXP-WGS-03` vs. `EXP-WGS-04`).
4. `backend/tests/test_case_study.py` (5 tests): `CS-CAT-001` evidence ledger parsing, deterministic scoring, and assumption documentation.
5. `backend/tests/test_api.py` (7 tests): FastAPI endpoints (`/scenarios`, `/evaluate`, `/sequential/run`, `/sequential/compare`).
6. `backend/tests/test_analytical_edge_cases.py` (6 tests): Closed-form entropy limits, boundary likelihoods, extreme priors, and non-negativity.
7. `backend/tests/test_sequential_bed.py` (28 tests): Closed-loop multi-step campaigns, budget stopping, counterfactual fairness, offline combinatorial bound optimality, paired statistics, alpha sensitivity, held-out suite structure, and strict bound assertions.

---

### 4.2 Single-Step Analytical Benchmark (`CS-CAT-001`)

```powershell
python scripts/run_evaluation.py
```

- **Expected Exit Code:** `0`
- **Expected Runtime:** $< 2.0\text{ seconds}$
- **Key Expected Outputs:**
  - Evaluated Candidate Pool: $N = 5$ peer-reviewed operando assays.
  - Top Candidate: `EXP-WGS-02` (Transient $\text{H}_2^{18}\text{O} / \text{C}^{16}\text{O}$ Pulse).
  - Top Candidate EIG: **$0.5593\text{ bits}$** (EIG Rank #1).
  - Top Candidate Utility: **$0.4171$** (Utility Rank #1, $\alpha = 0.10$).
  - Uniform Random Baseline EIG: **$0.3506 \pm 0.194\text{ bits}$** (Exact analytical expectation).
  - JANUS vs. Random EIG Multiplier: **$1.60\times$** ($+0.2086\text{ bits}$, $+59.5\%$).
  - Waste Elimination: $20.0\% \to 0.0\%$ (Zero-EIG quartz blank `EXP-WGS-06` completely avoided).

---

### 4.3 Sequential Closed-Loop BED Benchmark (Full 8-Section Suite)

```powershell
python scripts/run_sequential_benchmark.py
```

- **Expected Exit Code:** `0`
- **Expected Runtime:** $\approx 25 - 35\text{ seconds}$ (evaluates $> 840$ individual sequential campaigns).
- **Benchmark Sections Executed:**
  1. **Section 1:** Single matched seed 42 reproduction on `CS-CAT-001` under hidden truth $H_1$.
  2. **Section 2:** Multi-seed statistical audit on `CS-CAT-001` across 50 seeds $\times 3$ hypotheses ($N=150$ matched campaigns per policy).
  3. **Section 3:** Cost-penalty parameter sensitivity sweep ($\alpha \in \{0.00, 0.05, 0.10, 0.25, 0.50, 1.00\}$).
  4. **Section 4:** Procedural synthetic challenge suites (`SYNTH-A` through `SYNTH-F`).
  5. **Section 5:** Paired statistical comparisons with 95% bootstrap CIs, Cohen's $d_z$, and Holm-Bonferroni correction.
  6. **Section 6:** Target hypothesis identification accuracy and discrete decision attainment.
  7. **Section 7:** Held-out robustness evaluation on unseen seeds (`101..150`, $N=150$ campaigns).
  8. **Section 8:** Stress tests (budget variations $B \in [5, 20]$, stopping thresholds $\tau \in [0.80, 0.99]$, cost doubling, and feasibility degradation).

#### Key Target Reproduction Metrics:
| Metric / Comparison | Expected Value | Certified Bound / Status |
| :--- | :---: | :--- |
| **`CS-CAT-001` Offline Combinatorial Upper Bound** | **$1.1275 \pm 0.224\text{ bits}$** | Exact theoretical bound |
| **JANUS Development Mean Realized IG ($N=150$)** | **$0.9568 \pm 0.366\text{ bits}$** | Bound invariant satisfied |
| **JANUS Development Mean Cost** | **$7.83$** | Within budget $B = 10.0$ |
| **JANUS Development Identification Accuracy** | **$86.7\%$** | Correct hypothesis identified |
| **JANUS Held-Out Mean Realized IG ($N=150$)** | **$0.9745 \pm 0.354\text{ bits}$** | Generalizes cleanly |
| **JANUS Held-Out Identification Accuracy** | **$86.7\%$** | Exact match with dev set |
| **Offline Bound Invariant Violations** | **$0 / 840+$ campaigns** | Non-negative regret ($R \ge 0$) |

---

### 4.4 Frontend Production Build & Developer Server

```powershell
# 1. Build frontend production bundle
npm --prefix frontend run build
# Expected: Vite builds dist/ in < 2s with 0 errors.

# 2. Launch developer server (optional)
npm --prefix frontend run dev
# Expected: Local Vite server at http://localhost:5173
```

---

## 5. Seed Partitions and Determinism Architecture

To prevent data snooping, benchmark leakage, and cherry-picking, random seed allocations are strictly partitioned and frozen:

```text
========================================================================================
                         SEED PARTITION ARCHITECTURE
========================================================================================
 [1] Development Benchmark Set:
     Seeds: range(1, 51) -> {1, 2, 3, ..., 50}
     Hypotheses: {H1, H2, H3}
     Total Matched Campaigns: 50 seeds x 3 hypotheses = 150 campaigns per policy.
     Used for: Policy tuning, alpha parameter sweeps, and algorithm refinement.

 [2] Held-Out Evaluation Set:
     Seeds: range(101, 151) -> {101, 102, 103, ..., 150}
     Hypotheses: {H1, H2, H3}
     Total Matched Campaigns: 50 seeds x 3 hypotheses = 150 campaigns per policy.
     Used for: Final unbiased generalization evaluation and robustness stress testing.

 [3] Synthetic Challenge Suite:
     Fixed Seed: 42 (seed=42)
     Scenarios: SYNTH-A, SYNTH-B, SYNTH-C, SYNTH-D, SYNTH-E, SYNTH-F
     Used for: Procedural stress-testing against degenerate experimental landscapes.

 Disjoint Invariant: dev_seeds ∩ held_out_seeds = ∅ (ZERO OVERLAP GUARANTEED)
========================================================================================
```

### Deterministic Counterfactual Routing
Within each campaign, pseudo-random outcomes are pre-generated using a dedicated, isolated `numpy.random.RandomState(seed)` instance:
- **Fairness:** All evaluated policies (`janus_utility`, `raw_eig`, `naive_cheapest`, `feasibility_first`, `uniform_random`, `privileged_oracle`) observe identical counterfactual outcomes and execution successes for any given experiment.
- **Hidden Truth Isolation:** The true hypothesis $H^*$ and its physical realizations $\omega$ are encapsulated inside the `NatureSimulator` and are strictly inaccessible to ordinary decision policies.

---

## 6. Mathematical and Algorithmic Invariants

Every release build of JANUS must satisfy three foundational mathematical invariants:

### Invariant 1: Offline Combinatorial Bound Optimality
For any candidate pool $\mathcal{E}$, budget $B$, realization vector $\omega$, and sequential policy $\pi$:
$$\text{IG}(S_\pi; \omega) \le \mathcal{O}^*_{\text{offline}}(\omega) = \max_{S \subseteq \mathcal{E}, \; \sum_{e \in S} c(e) \le B} \text{IG}(S; \omega)$$
- Enforced programmatically in `backend/evaluation/sequential_evaluation.py` via an explicit assertion with numerical tolerance $\epsilon = 10^{-6}$.
- Any campaign yielding $\text{IG}(S_\pi) > \mathcal{O}^* + 10^{-6}$ immediately raises an unrecoverable `AssertionError` with diagnostic context.

### Invariant 2: Exact Bayesian Evidence Commutativity
Bayesian evidence updates must be commutative under arbitrary sequence ordering:
$$P(H \mid y_1, y_2) \equiv P(H \mid y_2, y_1)$$
- Enforced via exact IEEE-754 double-precision simplex normalization (`compute_bayesian_posterior_update` in `backend/scientific/sequential_engine.py`).
- Lossy intermediate rounding is prohibited. Discrepancy across update orders is $< 10^{-16}$.

### Invariant 3: Telescoping Entropy Conservation
Sequential information gain across $T$ campaign steps must telescope exactly to the initial Shannon entropy minus final Shannon entropy:
$$\sum_{t=1}^T \Delta H_t = \sum_{t=1}^T \left[ H(P_{t-1}) - H(P_t) \right] \equiv H(P_0) - H(P_T)$$
- Enforced and tested across all sequential campaigns to machine precision.

---

## 7. Epistemological Parameter Classification Taxonomy

Every parameter entering the JANUS engine is classified into exactly one of five epistemological categories to prevent opinion from being disguised as empirical fact:

| Category | Definition | Repository Example (`CS-CAT-001`) |
| :--- | :--- | :--- |
| **`LITERATURE_REPORTED`** | Directly measured or observed value from peer-reviewed literature with verified DOI. | Kalamaras 2011 SSITKA formate exchange ratio ($r_{\text{for}} / \text{TOF} = 0.14$). |
| **`DERIVED`** | Mathematically calculated from literature values via a documented deterministic formula. | Shannon entropy $H(P_0) = 1.4855\text{ bits}$; EIG values. |
| **`DOMAIN_ASSUMPTION`** | Expert-informed structural parameter requiring scientific justification; not directly measured. | Relative equipment costs (synchrotron = 6.5, benchtop = 1.1–1.8); detector noise floors ($\sigma = 0.04$). |
| **`ILLUSTRATIVE`** | Value assigned for scenario demonstration or parameter sensitivity analysis. | Baseline hypothesis priors ($P(H_1)=0.50, P(H_2)=0.20, P(H_3)=0.30$). |
| **`UNQUANTIFIED`** | Insufficient published data available to assign a defensible numerical distribution; excluded from ranking. | `EXP-WGS-05` (Stopped-flow carboxyl detection; excluded to preserve integrity). |

---

## 8. Troubleshooting & FAQ

1. **Warning on pytest:** `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`  
   *Explanation:* This is an upstream informational warning from Starlette/FastAPI regarding future TestClient interfaces. It does not affect test correctness or test results.
2. **Execution Runtimes:**  
   - `run_sequential_benchmark.py` takes $\sim 25\text{s}$ because it runs $> 840$ complete multi-step campaigns, paired bootstrap permutations, alpha sweeps, and budget variations.
3. **Reproducing Seed 42 Discrepancies:**  
   Ensure your Python virtual environment is activated and `numpy` version is $\ge 1.26.0$. Seed handling uses deterministic NumPy PRNG states.
