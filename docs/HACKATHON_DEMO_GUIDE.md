# JANUS Hackathon Presentation Guide & Judge Briefing

> **Core Thesis:** *Predicting scientific properties is not the bottleneck in science — deciding which decisive experiment to run next is.*  
> JANUS combines evidence-grounded multi-agent reasoning with an authoritative, closed-form Python Bayesian Experimental Design engine to distinguish competing mechanistic hypotheses.

---

## A. 3-Minute Live Demo Script (CS-CAT-001 Primary Walkthrough)

### [0:00 – 0:30] Stage A: Scientific Question & Scenario Setup
- **Action:** Open JANUS web interface (default tab: `🚀 AI Scientific Investigation`).
- **Select Scenario:** Click the **CS-CAT-001** preset card (*Pt/CeO₂ Low-Temperature Water-Gas Shift Catalysis*).
- **Point out to Judges:**
  - Notice the 3 competing mechanistic hypotheses: **H1 (Redox / Mars-van Krevelen)**, **H2 (Associative Formate)**, and **H3 (Associative Carboxyl)**.
  - Notice the uninformative priors initialized from literature: $P(H_1)=0.50$, $P(H_2)=0.20$, $P(H_3)=0.30$ (Initial Shannon Entropy = $1.4855\text{ bits}$).
- **Select Mode:** Choose **Deterministic Offline Demo** (or toggle to **Live Gemini 3 Flash Loop** if demonstrating live Google AI synthesis).
- **Click:** `Start Multi-Agent Scientific Investigation 🚀`.

---

### [0:30 – 1:15] Stage B: Coordinated Agents & Inspectable Tools
- **Point out to Judges:**
  - **Research Agent:** Ingested 4 peer-reviewed evidence claims with verified DOIs (Kalamaras 2011, Meunier 2007) — *zero hallucinated citations*.
  - **Scientific Tool Agent:** Executed real Python kinetic tools (calculated empirical Kinetic Isotope Effect $\text{KIE} = 1.60$).
  - **Critic Agent:** Audited the mathematical simplex axiom ($\sum P(H_k) = 1.000000$) and flagged `EXP-WGS-05` (uncalibrated stopped-flow carboxyl detection) to prevent fabricated likelihoods.
- **Action (Crucial):** Click on any tool execution badge (e.g., `janus_information_theoretic_ranking` or `chemical_kinetics_kie`) in the Tool Execution Inspector.
  - Expand the JSON view to show real inputs, outputs, runtime latency ($< 2\text{ ms}$), and provenance metadata.

---

### [1:15 – 1:50] Stage C: Authoritative Experiment Selection
- **Action:** Click `Proceed to Experiment Selection (Stage C) &rarr;`.
- **Point out to Judges:**
  - Look at the Experiment Comparison Table.
  - Highlight `#1 Recommended Assay`: **`EXP-WGS-02`** (*Transient $\text{H}_2(^{18}\text{O}) / \text{C}(^{16}\text{O})$ Isotopic Pulse MS*).
  - **The Mathematical Difference:** Explain why `EXP-WGS-02` wins: It delivers the maximum Expected Information Gain ($\text{EIG} = 0.5593\text{ bits}$) and Composite Utility ($U = 0.4171$).
  - **Dual-Ranking Divergence Notice:** Point to `EXP-WGS-03` (Operando AP-XPS, synchrotron beamline). It has pure $\text{EIG Rank \#3}$, but drops to $\text{Utility Rank \#4}$ because synchrotron cost ($6.5$) and lower feasibility ($70\%$) penalize its utility. Python calculates this trade-off explicitly — *no LLM guesswork*.

---

### [1:50 – 2:30] Stage D: Simulated Observation & Bayesian Belief Shift
- **Action:** Click `Proceed to Simulated Observation (Stage D) &rarr;`.
- **Point out to Judges:** Notice the disclaimer badge: *Simulated Observation Preview*. JANUS is an active decision system; we simulate observing the outcome of the selected experiment.
- **Action:**
  - Assay to Execute: Select `EXP-WGS-02`.
  - Observed Outcome: Select `Initial_CO2_Mainly_Lattice_16O` (abstracting native support oxygen).
  - Click `Apply Observation & Recompute Beliefs &rarr;`.
- **Highlight the Result:**
  - Look at the **Epistemic Probability Shift**:
    - **H1 (Redox)** surges from $50.0\% \to 84.8\%$ ($\Delta P = +34.8\%$, emerald badge).
    - **H2 (Formate)** drops from $20.0\% \to 3.7\%$ ($\Delta P = -16.3\%$, rose badge).
    - **H3 (Carboxyl)** drops from $30.0\% \to 11.5\%$ ($\Delta P = -18.5\%$, rose badge).
  - **Budget Decontamination:** Budget decreases from $10.0 \to 8.2\text{ units}$.
  - **Dynamic Re-Ranking:** `EXP-WGS-02` is retired. The next recommended diagnostic assay (`EXP-WGS-01` SSITKA DRIFTS) automatically takes Rank #1!

---

### [2:30 – 3:00] Stage E: Final Synthesis & Consensus Report
- **Action:** Click `View Final Investigation Summary (Stage E) &rarr;`.
- **Point out to Judges:**
  - **Identified Mechanism:** `H1 (Redox / Mars-van Krevelen)` at $84.8\%$ posterior confidence.
  - **Uncertainty Reduction:** Shannon entropy dropped by $-0.8038\text{ bits}$ (from $1.4855\text{ b} \to 0.6817\text{ b}$).
  - **Limitations & Provenance:** Unquantified proposals and physical limitations are recorded transparently.
- **Action:** Click `📋 Copy Report to Clipboard` to show export readiness for wet-lab scientists.

---

## B. Problem and Novelty

### 1. Property Prediction vs. Decisive Experiment Selection
- **The Conventional AI Bottleneck:** Almost all "AI for Science" systems focus on *forward property prediction* ($x \to y$): predicting molecular binding affinity, band gaps, or crystal structures.
- **The Real Lab Bottleneck:** In physical laboratories, researchers face competing, incompatible mechanistic explanations ($H_1, H_2, H_3$). Running every conceivable assay is impossible due to budget, beamline availability, and sample degradation.
- **JANUS's Role:** JANUS solves the *inverse decision problem*: **"Given $N$ competing hypotheses, which physical experiment $e^*$ minimizes Shannon entropy and disambiguates the ground truth with the fewest experiments and lowest budget?"**

### 2. Multi-Agent Reasoning + Python Numerical Authority
- LLMs are outstanding at qualitative reasoning, literature ingestion, extracting mechanistic proposals, and identifying edge cases.
- LLMs are notoriously unreliable at probabilistic calculations: they hallucinate likelihoods, fail simplex constraints ($\sum P_k \neq 1$), and make arbitrary ranking choices.
- **JANUS Architecture:** LLM agents retrieve context and propose structured hypotheses, but **authoritative Python code** computes all entropy, mutual information, EIG, and Bayesian updates using exact closed-form calculus.

### 3. What is Demonstrated vs. What Remains Unvalidated
- **Demonstrated & Verified:**
  - Closed-form Bayesian Experimental Design engine with zero non-negative regret violations against the true combinatorial upper bound across 150 matched campaigns.
  - Auditable live Gemini 3 Flash execution trace with 100% verified citation lineages.
  - Automated detection of dual-ranking divergence between pure EIG and cost-penalized utility.
- **Unvalidated Boundary Conditions:**
  - The current demo uses discretized diagnostic outcomes derived from published literature, not real-time streaming data from an active robotic wet-lab interface.
  - Assays lacking published quantitative error distributions (e.g., `EXP-WGS-05`) are withheld from ranking rather than having synthetic noise fabricated.

---

## C. Architecture & Workflow

```
[ Scientific Question / Literature ]
                 │
                 ▼
     [ 1. Research Agent ]  ──► Verified Literature Ledger (DOIs, Provenance)
                 │
                 ▼
    [ 2. Hypothesis Agent ] ──► Formulates Discrete Hypotheses H_1, ..., H_K
                 │
                 ▼
   [ 3. Scientific Tool Agent ] ──► Executes Python Tools (KIE, Arrhenius)
                 │
                 ▼
 [ 4. Experiment Strategy Agent ] ──► Compiles Candidate Assays & Outcomes
                 │
                 ▼
   ┌─────────────────────────────────────────────────────────┐
   │  AUTHORITATIVE PYTHON BED ENGINE (ScientificEngine)    │
   │  • Shannon Entropy: H(P) = - ∑ P(H) log₂ P(H)           │
   │  • Expected Info Gain: EIG(e) = H(P) - E_y[H(P|y)]      │
   │  • Composite Utility: U(e) = Feas * [EIG / (1 + α*Cost)]│
   └─────────────────────────────────────────────────────────┘
                 │
                 ▼
       [ 5. Critic Agent ]  ──► Audits Simplex, Catches Cost Divergences
                 │
                 ▼
  [ Interactive Observation Update ] ──► Bayes Theorem: P(H|y) ∝ P(y|H) * P(H)
                 │
                 ▼
    [ Re-ranking of Remaining Assays & Next Experiment Selection ]
```

---

## D. Frequently Asked Judge Questions & Answers

#### Q1: Why use agents instead of a conventional Bayesian optimization pipeline?
> **Answer:** Bayesian optimization optimizes continuous parameters for a single objective (e.g., maximizing reaction yield). It cannot formulate qualitative mechanistic hypotheses, parse literature contradictions, distinguish direct observations from author interpretation, or explain *why* an assay is diagnostically decisive. JANUS uses agents for qualitative synthesis and problem framing, and Bayesian Experimental Design for decision math.

#### Q2: What does Gemini contribute that Python does not?
> **Answer:** Gemini extracts mechanistic claims from unstructured primary literature, identifies unstated physical assumptions, formulates structured candidate hypotheses, and synthesizes consensus narratives for researchers. Python provides the deterministic math: numerical probabilities, information gain, and constraint enforcement.

#### Q3: How is hallucination controlled?
> **Answer:** Through strict structural boundaries:
> 1. LLMs are never asked to estimate or calculate numerical probabilities or rankings.
> 2. Literature claims require verified DOI references from curated ledgers.
> 3. The Critic Agent verifies the probability simplex ($\sum P = 1.000000$) via deterministic Python before any update is accepted.
> 4. Unquantified experimental proposals are explicitly excluded from ranking.

#### Q4: How are priors and likelihoods obtained?
> **Answer:** In published benchmarks (CS-CAT-001, CS-OER-002), priors and likelihoods are derived from peer-reviewed experimental papers and calibrated DFT microkinetic models with explicitly reported noise margins. In exploratory scenarios, unquantified assays are flagged as uncalibrated and held out until experimental noise models are supplied.

#### Q5: What does Expected Information Gain (EIG) measure?
> **Answer:** EIG measures the expected reduction in Shannon entropy regarding the true hypothesis after observing the outcome of an experiment:
> $$\text{EIG}(e) = H(\Theta) - \mathbb{E}_{y \sim P(y|e)}\left[H(\Theta \mid y)\right] = I(\Theta; Y \mid e)$$
> It quantifies how many bits of diagnostic uncertainty the experiment will eliminate on average.

#### Q6: How does JANUS respond when an experiment fails or returns an ambiguous result?
> **Answer:** The Bayesian engine models outcome uncertainty directly in the likelihood matrix $P(y \mid H_k)$. If an outcome has non-zero likelihood under multiple hypotheses, the posterior updates proportionally, reflecting the residual ambiguity without crashing. If an assay fails physically (feasibility failure), the campaign records the failure, deducts the cost, and re-ranks the remaining candidate assays.

#### Q7: Why can a zero-EIG negative control still be useful in a wet lab?
> **Answer:** A zero-EIG assay (like a blank quartz reactor `EXP-WGS-06` or ex-situ HR-TEM `EXP-OER-05`) provides zero diagnostic discrimination between competing mechanisms because all hypotheses predict the exact same background outcome. However, in physical chemistry, negative controls validate instrument calibration. JANUS's Critic Agent explicitly flags zero-EIG controls so researchers know they validate equipment, not mechanisms.

#### Q8: Has the system been validated in a real laboratory?
> **Answer:** JANUS is validated against published physical literature (e.g., Kalamaras et al. J. Catal. 2011 for WGS; Mefford et al. Nat. Commun. 2016 for OER). It reproduces the exact historical sequence of decisive experiments that resolved these controversies. Physical in-the-loop robotic wet-lab execution is the immediate next engineering milestone.

#### Q9: What is genuinely novel, and what is still a limitation?
> **Answer:**
> - **Genuinely Novel:** The integration of LLM-driven scientific agent critique with closed-form Bayesian Experimental Design and dual-ranking divergence auditing.
> - **Current Limitation:** Outcomes are currently discretized into categorical bins rather than continuous functional spectra, and campaign budgets are synthetic linear models.

---

## E. Backup Plan & Recovery Checklist

### 1. Instant Offline Fallback Sequence
If WiFi fails, API credits expire, or Google AI endpoints experience rate limiting:
1. On **Stage A**, ensure the mode radio button is set to **Deterministic Offline Demo**.
2. Click **Start Multi-Agent Scientific Investigation**.
3. All 5 agents, the tool executions, Bayesian ranking, sequential belief updates, and reports run 100% locally in Python ($< 5\text{ ms}$ response time).
4. Clearly state to judges: *"We are running in Deterministic Offline Mode — the exact same Python Bayesian math executes locally without external API latency."*

### 2. Network & Server Recovery Checklist
- If frontend fails to connect:
  - Check backend terminal: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - Verify health check: `curl http://localhost:8000/api/health`
  - Rebuild frontend if needed: `npm --prefix frontend run build`
- If Gemini API key is missing or invalid:
  - The interface displays an alert: *"Live agent loop requested, but no valid LLM API key was detected... switch to deterministic_offline_demo mode."*
  - Simply toggle the radio button to **Deterministic Offline Demo** and proceed immediately.
