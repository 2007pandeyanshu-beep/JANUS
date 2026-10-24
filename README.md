# JANUS — Scientific Intelligence System

**Autonomous Multi-Agent System for Closed-Loop Bayesian Experimental Design (BED)**  
*Deciding the Most Decisive Physical Experiment to Disambiguate Competing Scientific Hypotheses*

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Fetch.ai uAgents](https://img.shields.io/badge/Fetch.ai-uAgents%200.26-orange.svg)](https://fetch.ai/)
[![Protocol](https://img.shields.io/badge/ACP-v0.3.0-purple.svg)](https://innovationlab.fetch.ai/)
[![Tests](https://img.shields.io/badge/Tests-112%20Passed-brightgreen.svg)](backend/tests/)

---

## 1. Problem & Core Thesis

### The Core Scientific Bottleneck
In physical sciences (catalysis, electrochemistry, drug discovery), the bottleneck is **not** forward property prediction ($x \to y$). Researchers already possess models that predict band gaps or binding affinities.

The real lab bottleneck is **inverse experiment selection under rival mechanistic hypotheses**:
> *"Given $K$ competing, physically plausible hypotheses ($H_1, H_2, \dots, H_K$), which decisive experiment should we conduct next under constrained laboratory budget and physical feasibility?"*

### The Flaw with Pure LLMs
Generative LLMs hallucinate numerical probabilities, fail probability simplex conservation ($\sum P(H_k) \neq 1.0$), and produce arbitrary, uncalibrated experimental recommendations.

### The JANUS Solution
JANUS integrates **qualitative multi-agent evidence synthesis** with an **authoritative, closed-form Python Bayesian Experimental Design engine**:
1. **Multi-Agent Reasoning:** Specialized uAgents ingest primary literature, validate publisher DOIs via Crossref, structure competing mechanistic hypotheses, and execute real kinetic calculations.
2. **Deterministic Mathematical Authority:** Expected Information Gain (EIG), Shannon entropy reduction, composite utility rankings, and posterior probability updates are computed strictly using closed-form calculus in Python — **never via stochastic LLM guessing**.

$$\text{EIG}(e) = H(P) - \mathbb{E}_{y \sim P(y \mid e)} \left[ H(P(\cdot \mid y, e)) \right]$$

$$U(e) = \frac{\text{feasibility}(e) \cdot \text{EIG}(e)}{1 + \alpha \cdot \text{cost}(e)}$$

---

## 2. Multi-Agent Architecture

JANUS employs an asymmetric, decoupled architecture:
- **Public Coordinator uAgent:** Connects to the Fetch.ai Agentverse Mailbox via the standardized **Agent Chat Protocol (ACP v0.3.0)** for conversational interactions with researchers and the ASI:One ecosystem.
- **5 Internal Specialist uAgents:** Operate on dedicated local HTTP IPC ports, isolated from the public network, performing independent verification, retrieval, and analysis.

```mermaid
flowchart TD
    User([Researcher / Agentverse Chat / ASI:One]) <-->|Agent Chat Protocol v0.3.0| Coord[JANUS Coordinator uAgent<br/>Port 8008 / Agentverse Mailbox]

    subgraph Internal_Specialists["Internal Specialist uAgents (Local HTTP IPC)"]
        Res[1. Research Agent<br/>Port 8010<br/>Crossref DOI Validation]
        Hyp[2. Hypothesis Analyst<br/>Port 8011<br/>Simplex Invariants & Evidence Mapping]
        Tool[3. Scientific Tool Agent<br/>Port 8012<br/>Empirical Kinetics & KIE]
        Des[4. Experiment Designer<br/>Port 8013<br/>Candidate Assay Space]
        Aud[5. Auditor Agent<br/>Port 8009<br/>Zero-Trust Invariant Verification]
    end

    subgraph Deterministic_Core["Authoritative Mathematical Core (Python)"]
        BED[ScientificEngine & SequentialEngine<br/>• Shannon Entropy: H = -∑ P log₂ P<br/>• Mutual Information: EIG = H - E[H|y]<br/>• Composite Utility Optimization<br/>• Exact Bayesian Belief Updating]
    end

    subgraph Web_Stack["Web Workbench Stack"]
        API[FastAPI Backend Server<br/>Port 8000 / REST API] <--> UI[React + Vite Frontend<br/>Port 5173 / Interactive Dashboard]
    end

    Coord -->|janus_scientific_research| Res
    Coord -->|janus_scientific_hypothesis| Hyp
    Coord -->|janus_scientific_tool| Tool
    Coord -->|janus_scientific_designer| Des
    Coord -->|janus_scientific_audit| Aud

    Coord <--> BED
    API <--> BED
```

### Specialist Agent Directory

| Agent | Port | Fetch.ai Address | Native Protocol | Primary Responsibility |
| :--- | :--- | :--- | :--- | :--- |
| **Coordinator Agent** | `8008` | `agent1q0hmkpdw4v...` | `AgentChatProtocol` v0.3.0 | Agentverse Mailbox gateway, user session orchestration |
| **Auditor Agent** | `8009` | `agent1qtce9c74t0...` | `janus_scientific_audit` | Zero-trust verification of simplex sums, bounds, and rankings |
| **Research Agent** | `8010` | `agent1q0hhnepntx...` | `janus_scientific_research` | Primary literature retrieval and live Crossref DOI metadata verification |
| **Hypothesis Analyst** | `8011` | `agent1qfmmvna5ff...` | `janus_scientific_hypothesis` | Discrete hypothesis framing, prior normalization, and evidence tagging |
| **Scientific Tool Agent** | `8012` | `agent1q2lmglm5n5...` | `janus_scientific_tool` | Empirical Arrhenius and Kinetic Isotope Effect (KIE) execution |
| **Experiment Designer** | `8013` | `agent1q0qpwtcrpp...` | `janus_scientific_designer` | Diagnostic assay space compilation and cost/feasibility attributes |

---

## 3. Calibrated Scientific Benchmarks

JANUS operates under strict scientific integrity: it refuses to fabricate likelihood matrices for arbitrary, unvalidated domains. It supports three fully calibrated, peer-reviewed benchmarks:

1. **CS-CAT-001: Low-Temperature Water-Gas Shift on $\text{Pt}/\text{CeO}_2$**
   - *Rival Hypotheses:* **H1 (Redox / Mars-van Krevelen)** vs. **H2 (Associative Formate)** vs. **H3 (Associative Carboxyl)**.
   - *Diagnostic Benchmark:* Demonstrates that isotope pulse MS (`EXP-WGS-02`) maximizes EIG, and simulated observation collapses uncertainty onto the Redox mechanism ($P(H_1) \to 89.8\%$).
   - *Literature Baseline:* Kalamaras et al., *J. Catal.* 2011; Meunier et al., *J. Catal.* 2007.

2. **CS-OER-002: Oxygen Evolution Electrocatalysis on Perovskites**
   - *Rival Hypotheses:* **H1 (Adsorbate Evolution Mechanism - AEM)** vs. **H2 (Lattice Oxygen Mechanism - LOM)** vs. **H3 (Oxo-Coupling Mechanism - OPM)** on $\text{La}_{1-x}\text{Sr}_x\text{CoO}_{3-\delta}$.
   - *Diagnostic Benchmark:* Operando $^{18}\text{O}$ isotope labeling DEMS (`EXP-OER-01`) discriminates lattice oxygen participation.
   - *Literature Baseline:* Mefford et al., *Nat. Commun.* 2016; Grimaud et al., *Nat. Energy* 2017.

3. **SYN-001: Kinase Pathway Disambiguation (Synthetic Benchmark)**
   - *Rival Hypotheses:* **H1 (Allosteric Modulation)** vs. **H2 (ATP-Competitive)** vs. **H3 (Targeted Degradation)** for lead compound JNS-401.

---

## 4. Quickstart & Windows Execution

### Prerequisites
- Windows 10/11 x64
- Python 3.12 (virtual environment located in `.venv`)
- Node.js 20+ and npm

### 1. Launch the Public Coordinator (Agentverse Mailbox Mode)
Starts the Fetch.ai Coordinator agent in Mailbox mode connected to `https://agentverse.ai`:
```powershell
.\scripts\run_coordinator.ps1
```
*(Uses the existing project virtual-environment Python executable and explicitly enables mailbox mode via `JANUS_USE_MAILBOX=true`).*

### 2. Launch the 5 Internal Specialist uAgents (Local IPC Mode)
Starts the 5 specialist agents as background workers on ports `8009` through `8013`:
```powershell
.\scripts\run_specialists.ps1
```

### 3. Launch the Web Interface & Backend API
In separate PowerShell terminals:
```powershell
# Terminal A: Start FastAPI Backend (Port 8000)
.\scripts\run_backend.ps1

# Terminal B: Start React + Vite Frontend (Port 5173)
.\scripts\run_frontend.ps1
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser to access the interactive investigation workbench.

---

## 5. Automated Testing & Verification

The test suite validates mathematical determinism, Bayesian calculations, agent isolation, and Agent Chat Protocol compliance:

```powershell
# Run the complete test suite (112 tests):
.\.venv\Scripts\python.exe -m pytest backend/tests/

# Or run targeted sub-suites:
# 1. Coordinator & Agent Chat Protocol Lifecycle (37 tests)
.\.venv\Scripts\python.exe -m pytest backend/tests/test_fetch_agent.py

# 2. Specialist IPC & Multi-Agent Collaboration (75 tests)
.\.venv\Scripts\python.exe -m pytest backend/tests/test_auditor_agent.py backend/tests/test_research_agent.py backend/tests/test_hypothesis_analyst.py backend/tests/test_scientific_tool_agent.py backend/tests/test_experiment_designer_agent.py backend/tests/test_agent_workflow.py

# 3. FastAPI Web API Endpoints (7 tests)
.\.venv\Scripts\python.exe -m pytest backend/tests/test_api.py
```

---

## 6. Known Capabilities & Scope Boundaries

### Verified Capabilities
- **Exact Mathematical Invariants:** 100% verified probability simplex conservation ($\sum P = 1.0$), non-negative Shannon entropy bounds ($0 \le \text{EIG} \le H$), and row-stochastic likelihood matrices.
- **Dual-Ranking Divergence Auditing:** Automatically detects when raw information gain divergence conflicts with laboratory budget/feasibility constraints (e.g., beamline synchrotron assays penalized by cost).
- **Persistent State Continuity:** Bayesian posterior state is preserved across conversational turns without resetting priors.
- **Agent Chat Protocol v0.3.0:** Full compatibility with ASI:One and Agentverse chat clients via typed `ChatMessage`, `ChatAcknowledgement`, `TextContent`, `MetadataContent`, and `EndSessionContent`.

### Known Limitations
- **Discrete Outcome Space:** Experimental outcomes are modeled as discrete categorical bins (e.g., `Mainly_Lattice_16O` vs `Mainly_Gas_18O`) rather than continuous real-time functional spectra.
- **Local Specialist IPC:** In compliance with the zero-trust architecture, specialist agents are kept private on localhost HTTP IPC and are not registered on public discovery almanacs.
- **Math Formatting in Chat:** Probability formulas are styled in standardized notation (e.g., `P(H1 | y) = 89.8%`); clients lacking MathJax render the notation as inline text.
