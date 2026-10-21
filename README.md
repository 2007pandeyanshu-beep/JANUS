# JANUS — Scientific Intelligence Core

**Closed-Loop Sequential Bayesian Experimental Design (BED) for Competing Scientific Hypotheses**  
*Open Scientific Intelligence (OSI) Evaluation System*

---

## Mission & Purpose

JANUS is a scientific intelligence system engineered to identify high-yield, cost-efficient, and physically feasible candidate experiments capable of disambiguating rival scientific hypotheses.

Unlike generative LLMs that produce unstructured text or hallucinate experiment outcomes, JANUS implements a **deterministic, information-theoretic decision policy** based on Shannon entropy, Bayesian updating, and composite utility optimization:

$$U(e) = \frac{\text{feasibility}(e) \cdot \text{EIG}(e)}{1 + \alpha \cdot \text{cost}(e)}$$

where the Expected Information Gain (EIG) measures mutual information between hypothesis space $H$ and observation space $Y$:

$$\text{EIG}(e) = H(P) - \mathbb{E}_{y \sim P(y \mid e)} \left[ H(P(\cdot \mid y, e)) \right]$$

### Key Scientific Principles:
1. **Mathematical Determinism & Reproducibility:** Experiment scoring and ranking are computed strictly via Bayesian calculus and Shannon entropy—never via stochastic LLM text generation.
2. **Sequential Closed-Loop BED:** Simulates multi-step experimental campaigns where each completed observation updates posterior beliefs and dynamically re-scores remaining candidate assays.
3. **Data Provenance & Scientific Traceability:** Clearly separates simulated counterfactual outcomes from peer-reviewed operando catalysis literature (`CS-CAT-001`).
4. **Fair Multi-Policy Benchmarking:** Benchmarks JANUS Composite Utility against Raw EIG maximization, naive heuristics (Cheapest First, Feasibility First), uniform random selection, and an exact branch-and-bound combinatorial upper bound.
5. **Rigorous Statistical Verification:** Evaluates paired differences using bootstrap confidence intervals, Cohen's $d_z$, permutation testing, and family-wise error rate control (Holm-Bonferroni).

---

## Repository Architecture

```text
JANUS/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py         # FastAPI endpoints (/health, /scenarios, /sequential/*)
│   │   ├── schemas/
│   │   │   └── scientific.py        # Strict Pydantic v2 schemas
│   │   └── main.py                  # Application entrypoint & CORS configuration
│   ├── scientific/
│   │   ├── sequential_engine.py     # Closed-loop sequential BED engine & Nature simulator
│   │   ├── synthetic_scenarios.py   # Procedural benchmark generators (SYNTH-A to SYNTH-F)
│   │   ├── scoring.py               # Shannon entropy, Bayes updates & EIG scoring
│   │   ├── evidence_ingestion.py    # CS-CAT-001 Pt/CeO2 catalysis scenario ingestion
│   │   ├── validation.py            # Probability simplex normalization & constraint checks
│   │   └── constraints.py           # Feasibility filtering & thresholding
│   ├── evaluation/
│   │   ├── sequential_evaluation.py # Multi-seed campaigns, paired permutation tests, CIs
│   │   ├── benchmark_evaluation.py  # Single-step analytical benchmark evaluation
│   │   └── baselines.py             # Random selection baseline
│   ├── tests/                       # Pytest automated test suite (60 tests passing)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.ts                   # Backend API client
│   │   ├── types.ts                 # TypeScript data contracts
│   │   ├── App.tsx                  # Interactive BED dashboard & campaign explorer
│   │   └── index.css                # Clean, accessible dashboard styling
│   ├── package.json
│   └── vite.config.ts               # Vite bundler & reverse proxy configuration
├── docs/
│   ├── phase5_4_release_readiness_report.md # Final release readiness report
│   ├── phase5_3_robustness_report.md        # Robustness audit & held-out evaluation
│   ├── phase5_2_evaluation_report.md        # Paired statistics & synthetic suite
│   ├── phase5_1_audit_report.md             # Invariant checks & oracle regret audit
│   ├── evaluation_plan.md                   # Formal multi-phase evaluation plan
│   └── scientific_assumptions.md            # Traceability ledger for CS-CAT-001
├── scripts/
│   ├── run_sequential_benchmark.py          # Sequential BED benchmark runner (8 sections)
│   ├── run_evaluation.py                    # Single-step analytical benchmark runner
│   ├── run_backend.ps1                      # Windows PowerShell backend launcher
│   └── run_frontend.ps1                     # Windows PowerShell frontend launcher
├── pytest.ini
└── README.md
```

---

## Local Setup & Turnkey Reproduction

### Prerequisites
- Python 3.12 (x64)
- Node.js 20+ and npm
- Windows PowerShell (or bash on Linux/macOS)

### 1. Backend Environment Setup & Verification

```powershell
# Navigate to workspace root
cd C:\Users\2007p\OneDrive\Desktop\JANUS

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# (Optional) Install dependencies if setting up in fresh environment:
pip install -r backend/requirements.txt

# Run the complete automated test suite (60 tests passing):
pytest backend/tests -v
```

### 2. Run the Benchmark Evaluations

#### A. Single-Step Benchmark (`CS-CAT-001`)
```powershell
python scripts/run_evaluation.py
```
*Evaluates analytical expected information gain, optimal pick probabilities, and waste elimination over a discrete 5-candidate operando catalysis library.*

#### B. Sequential BED Benchmark & Statistical Audit (Full 8-Section Suite)
```powershell
python scripts/run_sequential_benchmark.py
```
*Executes:*
1. Matched single-seed analysis (Seed 42).
2. Comparative policy evaluation vs. Exact Offline Combinatorial Upper Bound.
3. Multi-seed & multi-hypothesis statistical audit ($N=150$ matched campaigns on `CS-CAT-001`).
4. Paired differences with 95% bootstrap CIs, Cohen's $d_z$, and Holm-Bonferroni correction.
5. Synthetic scenario suite (`SYNTH-A` through `SYNTH-F`).
6. Cost-penalty parameter sensitivity sweep ($\alpha \in [0.0, 1.0]$).
7. Held-out evaluation seeds (`101..150`, $N=150$ campaigns) testing generalization.
8. Budget sweeps ($B \in [5, 10, 15, 20]$), confidence threshold sweeps ($\tau \in [0.80, 0.99]$), and stress-test scenarios.

### 3. Launch the Application

#### A. Start the FastAPI Backend (Port 8000)
```powershell
.\scripts\run_backend.ps1
# Or directly:
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`

#### B. Start the React Frontend Dashboard (Port 5173)
```powershell
.\scripts\run_frontend.ps1
# Or directly:
npm --prefix frontend run dev
```
Open browser to: `http://localhost:5173`

#### C. Build Frontend for Production
```powershell
npm --prefix frontend run build
```

---

## Benchmark Scenarios: Real vs. Synthetic Separation

| Scenario ID | Name & Description | Candidates / Hypotheses | Data Provenance |
| :--- | :--- | :---: | :--- |
| **`CS-CAT-001`** | **Pt/CeO2 Water-Gas Shift Catalysis** | $5\text{ exps} \times 3\text{ hypos}$ | **Literature-Derived:** Priors, likelihoods, and costs grounded in peer-reviewed operando DRIFTS, SSITKA, isotopic transient, and AP-XPS studies (Meunier 2007; Kalamaras 2009). Physical outcomes are simulated via Nature. |
| **`SYNTH-A`** | **Needle in a Haystack** | $30\text{ exps} \times 10\text{ hypos}$ | **Synthetic:** 25 uninformative low-cost blank controls vs. 5 diagnostic assays; tests filter robustness against cheap control traps. |
| **`SYNTH-B`** | **High-Cost Facility Dilemma** | $8\text{ exps} \times 3\text{ hypos}$ | **Synthetic:** 1 expensive synchrotron beamline assay vs. 7 benchtop alternatives; tests cost efficiency. |
| **`SYNTH-C`** | **High-Risk Experimental Frontier** | $10\text{ exps} \times 4\text{ hypos}$ | **Synthetic:** 4 high-EIG but fragile frontier assays ($p_{\text{feas}} = 0.25$) vs. 6 robust benchtop assays ($p_{\text{feas}} = 0.92$); tests feasibility regularization. |
| **`SYNTH-D`** | **Spectator Intermediate Trap** | $6\text{ exps} \times 3\text{ hypos}$ | **Synthetic:** 1 prominent, inexpensive spectator assay ($EIG = 0.0\text{ b}$) vs. 5 diagnostic assays; tests avoidance of non-discriminating intermediates. |
| **`SYNTH-E`** | **Multinomial Outcome States** | $12\text{ exps} \times 3\text{ hypos}$ | **Synthetic:** Assays with 5 categorical outcome bins; tests multinomial entropy and likelihood generalizability. |
| **`SYNTH-F`** | **Broad Screening Campaign** | $50\text{ exps} \times 5\text{ hypos}$ | **Synthetic:** High-throughput screening pool of 50 candidates; tests branch-and-bound optimization scalability. |

---

## Scientific Scope & Limitations

> [!IMPORTANT]
> **Simulation Boundary:**  
> While the likelihood models in `CS-CAT-001` are curated from published literature, all sequential executions are evaluated in computer simulation using pseudo-random Bernoulli and categorical sampling. JANUS demonstrates computational correctness and decision-theoretic superiority under defined mathematical models; it does not replace physical laboratory experimentation.
