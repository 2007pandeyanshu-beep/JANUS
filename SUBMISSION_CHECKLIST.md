# JANUS — Final Hackathon Submission Checklist

> **Project:** JANUS — Closed-Loop Sequential Bayesian Experimental Design for Competing Hypotheses  
> **Repository:** `https://github.com/2007pandeyanshu-beep/JANUS.git`  
> **Status:** Feature Freeze Complete / Ready for Evaluation

---

## 1. Required Deliverables Checklist

- [x] **Working Autonomous Agent:** Public Coordinator uAgent deployed with deterministic identity address `agent1q0hmkpdw4v28hmkkfqa56u2zwx3pzly44z7r8048pjtgw4lq8r5my29pn3t`.
- [x] **Agentverse Mailbox Integration:** Mailbox mode operational via `JANUS_USE_MAILBOX=true` and dedicated launcher `scripts/run_coordinator.ps1`.
- [x] **Agent Chat Protocol (ACP v0.3.0) Compliance:** Fully implements `ChatMessage`, `ChatAcknowledgement`, `TextContent`, `MetadataContent`, and session-terminating `EndSessionContent` so the chat UI displays the response cleanly.
- [x] **Almanac Manifest Publishing:** Automatically publishes `AgentChatProtocol` v0.3.0 manifest to the Fetch.ai Almanac registry upon mailbox startup.
- [x] **Authoritative Mathematical BED Engine:** Deterministic computation of Shannon entropy, Expected Information Gain (EIG), composite utility, and closed-form Bayesian updates without LLM hallucination.
- [x] **Evidence-Grounded Literature Provenance:** Verified DOI links from peer-reviewed physical literature via the Research Agent and Crossref tools.
- [x] **Full Interactive Web Interface:** React 18 + Vite frontend dashboard (`http://localhost:5173`) with live tool execution inspectors, experiment ranking tables, and dynamic belief shift badges.
- [x] **FastAPI REST API Core:** High-performance backend on `http://127.0.0.1:8000` with comprehensive `/api/health`, `/api/scenarios/*`, and `/api/sequential/*` endpoints.

---

## 2. Repository Quality & Hygiene Checks

- [x] **Zero Exposed Secrets:** `.env` and `*.key` files are untracked and excluded in `.gitignore`. Only sanitized templates (`.env.example`) are present.
- [x] **Clean Dependency Manifests:** `backend/requirements.txt` and `frontend/package.json` define exact, reproducible dependency trees.
- [x] **Clean Windows Launchers:**
  - `scripts/run_coordinator.ps1`: Starts the public Coordinator in Agentverse Mailbox mode.
  - `scripts/run_specialists.ps1`: Starts all 5 internal specialist workers on ports 8009–8013.
  - `scripts/run_backend.ps1`: Starts FastAPI uvicorn server on port 8000.
  - `scripts/run_frontend.ps1`: Starts React Vite frontend dev server on port 5173.
- [x] **Zero Untracked Temporary DB Files:** SQLite WAL and shared memory files (`*.db-shm`, `*.db-wal`) excluded via `.gitignore`.
- [x] **No Phantom/Shadowing Standard Library Conflicts:** `backend/agents/fetch_agent.py` contains path sanitization to prevent shadowing of Python's standard `types` module.

---

## 3. Automated Test Verification Summary

| Test Suite | File | Tests | Status |
| :--- | :--- | :---: | :---: |
| **Coordinator & Chat Protocol** | `backend/tests/test_fetch_agent.py` | 37 | **PASSED** (150s) |
| **Auditor Specialist Agent** | `backend/tests/test_auditor_agent.py` | 16 | **PASSED** |
| **Research Specialist Agent** | `backend/tests/test_research_agent.py` | 10 | **PASSED** |
| **Hypothesis Analyst Specialist** | `backend/tests/test_hypothesis_analyst.py` | 17 | **PASSED** |
| **Scientific Tool Specialist** | `backend/tests/test_scientific_tool_agent.py` | 12 | **PASSED** |
| **Experiment Designer Specialist** | `backend/tests/test_experiment_designer_agent.py` | 12 | **PASSED** |
| **Multi-Agent Collaboration** | `backend/tests/test_agent_workflow.py` | 8 | **PASSED** |
| **FastAPI Core Endpoints** | `backend/tests/test_api.py` | 7 | **PASSED** (3s) |
| **Total Automated Suite** | **All Tests** | **112** | **100% PASSED** |

---

## 4. Live Demonstration Checks

- [x] **Investigation Initialization:** Recognized query on CS-CAT-001 WGS catalysis and initialized prior simplex $\sum P = 1.0$.
- [x] **Decisive Assay Ranking:** Selected `EXP-WGS-02` (Isotopic Pulse MS) as the #1 diagnostic experiment with maximum EIG ($0.5593\text{ bits}$).
- [x] **Dual-Ranking Divergence:** Identified that high-cost synchrotron experiments (`EXP-WGS-03`) are penalized by utility, preventing budget exhaustion.
- [x] **Sequential Observation Conditioning:** Evaluated `observe EXP-WGS-02 Initial_CO2_Mainly_Lattice_16O` and updated beliefs dynamically ($P(H_1) \to 89.8\%$).
- [x] **Dynamic Re-Ranking:** Retired `EXP-WGS-02` and promoted `EXP-WGS-01` (SSITKA DRIFTS) to Rank #1.
- [x] **Auditor Verification:** Zero-trust Auditor uAgent verified 14/14 mathematical invariant checks (`AUDIT_PASSED`).

---

## 5. Known Limitations & Scope Boundaries

1. **Discrete Categorical Outcomes:** Diagnostic outcomes are discretized into physically calibrated qualitative bins (e.g., `Mainly_Lattice_16O` vs `Mainly_Gas_18O`) rather than streaming continuous functional spectra.
2. **Local Specialist Architecture:** In accordance with zero-trust isolation, specialist uAgents operate exclusively over local HTTP IPC (`127.0.0.1:8009-8013`) and are intentionally not published to public almanacs.
3. **Chat Client LaTeX Rendering:** Probability formulas are formatted in standard notation (e.g., `P(H1 | y) = 89.8%`); clients without MathJax display the notation as clean inline text.

---

## 6. Deferred Optional Enhancements (Post-Hackathon)

- **Continuous Spectral Bayesian Updating:** Ingesting raw continuous mass-spectrometer and FTIR spectral timeseries via Gaussian Process likelihoods.
- **Physical Robotics Integration:** Direct Python drivers for automated micro-reactor liquid handlers and gas manifold controllers.
- **On-Chain Attestation:** Minting cryptographic proof-of-scientific-verification on the Fetch.ai Ledger for each completed investigation report.
