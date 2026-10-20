# JANUS Comprehensive Evaluation Plan

**Document ID:** `EVAL-PLAN-001`  
**Version:** 1.0.0 (Phase 4 Specification)  
**Target Systems:** JANUS Scientific Decision Engine, Multi-Mechanism Synthetic Benchmarks, and Future Sequential Experimental Design Campaigns

---

## 1. Executive Summary & Evaluation Mission

JANUS is an information-theoretic scientific decision support system designed to select optimal, feasible, and cost-effective experiments to discriminate between competing scientific hypotheses.

While Phase 3 validated JANUS on the discrete, peer-reviewed $\text{Pt/CeO}_2$ Water-Gas Shift benchmark (`BENCH-WGS-001`, $N=5$), evaluating an autonomous scientific planning system requires testing beyond a single case study. 

This document defines a reproducible, leakage-free evaluation protocol to test JANUS across diverse, synthetic mechanism-discrimination scenarios with varying numbers of hypotheses, candidate pools, priors, costs, feasibility constraints, and outcome distributions.

> [!IMPORTANT]
> **Evaluation Premise:** We do not evaluate JANUS by asking whether an LLM produces plausible text. We evaluate whether the decision engine's selected experiments achieve higher realized information gain, lower budget waste, and lower execution failure rates than credible heuristic and baseline policies under identical constraints.

---

## 2. Research Questions

1. **Primary Research Question:** Under identical candidate pools, priors, and operational constraints, does JANUS select candidate experiments that achieve significantly higher information gain and composite utility than credible baseline policies (uniform random, greedy cost minimization, greedy feasibility maximization)?
2. **Ablation Research Question (Cost/Feasibility Value):** How much decision value does composite utility optimization ($U(e) = \text{feasibility} \times \frac{\text{EIG}}{1 + \alpha \cdot \text{cost}}$) provide compared to raw Expected Information Gain (EIG) ranking when candidate assays exhibit asymmetric experimental friction?
3. **Robustness Research Question:** Does JANUS maintain discriminative superiority across varying noise floors, severe candidate pool sparsity (needle-in-a-haystack regimes), and conflicting initial priors?

---

## 3. Evaluated Selection Policies

To ensure a fair and defensible comparison, all policies are evaluated on identical candidate pools $\mathcal{E} = \{e_1, e_2, \dots, e_N\}$:

| Policy Identifier | Policy Name | Decision Rule | Scientific Motivation / Real-World Analogue |
| :--- | :--- | :--- | :--- |
| **`B_RAND`** | Uniform Random Selection | $e \sim \text{Uniform}(\mathcal{E})$ | Unguided trial-and-error; novice researcher choosing without diagnostic modeling. |
| **`B_CHEAP`** | Naive Cost-Minimizer Heuristic | $\arg\min_{e \in \mathcal{E}} \text{Cost}(e)$ | Budget-constrained researcher reflexively selecting the least expensive assay. |
| **`B_FEAS`** | Naive Feasibility-Maximizer | $\arg\max_{e \in \mathcal{E}} \text{Feasibility}(e)$ | Risk-averse researcher picking the easiest, most routine assay regardless of diagnostic power. |
| **`B_RAWEIG`** | Raw Information Maximizer (Ablation) | $\arg\max_{e \in \mathcal{E}} \text{EIG}(e)$ | Pure Bayesian experimental design ignoring laboratory cost, instrument access, and failure risk. |
| **`PI_JANUS`** | JANUS Composite Utility Optimization | $\arg\max_{e \in \mathcal{E}} U(e)$ | Full JANUS policy balancing diagnostic information gain against feasibility and cost. |
| **`ORACLE`** | Ground-Truth Oracle Reference | $\arg\max_{e \in \mathcal{E}} \Delta H_{\text{realized}}(e)$ | Theoretical upper bound evaluated against the true hidden data-generating hypothesis $H^*$. |

---

## 4. Evaluation Benchmark Suite: Synthetic Scenario Design

To evaluate the algorithm across the parameter space without relying on cherry-picked instances, the evaluation suite defines six synthetic scenario archetypes representing distinct real-world research challenges:

```
+----------------------------------------------------------------------------------------------------+
|                                    SYNTHETIC BENCHMARK SUITE                                       |
+------------------------------------+-----------------------------------+---------------------------+
| Scenario Archetype                 | Candidate Space                   | Dominant Friction         |
+------------------------------------+-----------------------------------+---------------------------+
| SYNTH-A: Needle in a Haystack      | 10 Hypotheses, 30 Experiments     | Extreme sparsity (EIG=0)  |
| SYNTH-B: High-Cost Synchrotron     | 3 Hypotheses, 8 Experiments       | 10x cost penalty on top   |
| SYNTH-C: High Execution Risk       | 4 Hypotheses, 10 Experiments      | Feasibility p < 0.40      |
| SYNTH-D: Spectator Trap            | 3 Hypotheses, 6 Experiments       | High signal, zero diag.   |
| SYNTH-E: Multi-State Spectrum      | 3 Hypotheses, 12 Experiments      | 5-outcome multinomials    |
| SYNTH-F: Broad Screening Campaign  | 5 Hypotheses, 50 Experiments      | Uniform noisy candidates  |
+------------------------------------+-----------------------------------+---------------------------+
```

### Archetype Specifications:

1. **`SYNTH-A` (Needle in a Haystack):**
   - $M=10$ competing hypotheses, $N=30$ candidate assays.
   - 25 assays are uninformative controls ($\text{EIG} < 0.01\text{ bits}$).
   - 5 assays provide varying disambiguation power ($0.2\text{--}1.5\text{ bits}$).
   - *Test Objective:* Can the policy reliably avoid uninformative budget sinks in noisy screening pools?

2. **`SYNTH-B` (High-Cost Facility Dilemma):**
   - $M=3$ hypotheses, $N=8$ assays.
   - Assay 1 has the highest EIG ($1.2\text{ bits}$), but high cost ($15.0$) and moderate feasibility ($0.60$).
   - Assay 2 has high EIG ($1.0\text{ bits}$), but low cost ($1.5$) and high feasibility ($0.95$).
   - *Test Objective:* Verifies whether composite utility appropriately favors Assay 2 over Assay 1, preventing budget exhaustion.

3. **`SYNTH-C` (High-Risk Experimental Frontier):**
   - $M=4$ hypotheses, $N=10$ assays.
   - Several high-EIG assays carry low feasibility ($p_{\text{feas}} = 0.25\text{--}0.40$), representing unproven methods.
   - *Test Objective:* Verifies that feasibility weighting down-ranks fragile experiments in favor of robust, executable protocols.

4. **`SYNTH-D` (Spectator Intermediate Trap):**
   - $M=3$ hypotheses, $N=6$ assays.
   - One assay produces an intense spectroscopic band under all hypotheses (analogous to inert surface formates), but identical likelihoods.
   - *Test Objective:* Confirms that intense spectroscopic signal is not mistaken for diagnostic information gain.

5. **`SYNTH-E` (Multi-State Multinomial Outcomes):**
   - $M=3$ hypotheses, $N=12$ assays with $K=5$ discrete outcome bins (e.g., fractional conversion deciles).
   - Tests Shannon entropy reduction over multinomial distributions.

6. **`SYNTH-F` (Combinatorial High-Throughput Screening):**
   - $M=5$ hypotheses, $N=50$ candidate assays generated via parameterized Dirichlet priors and beta-distributed costs/feasibilities.
   - Tests decision latency and asymptotic ranking stability.

---

## 5. Ground Truth & Avoidance of Algorithmic Circularity

> [!CAUTION]
> **Circularity Trap:** Never evaluate a ranking algorithm using its own internal scoring function ($U(e)$ or $\text{EIG}$) as the independent ground truth. Doing so merely tests whether an algorithm maximizes its own definition, rather than measuring genuine scientific utility.

### Independent Ground-Truth Protocol:

To establish an objective ground-truth metric:

1. **Hidden World State ($H^*$):** For each evaluation run, the benchmark environment designates one hypothesis $H^* \in \{H_1, \dots, H_M\}$ as the true physical mechanism generating laboratory data.
2. **Stochastic Nature Simulation:** When a policy selects experiment $e$, the environment samples a realized outcome $y_{\text{realized}} \sim P(y \mid H^*, e)$.
3. **Execution Failure Simulation:** The environment simulates whether the experiment physically succeeds by drawing $F \sim \text{Bernoulli}(\text{Feasibility}(e))$. If $F = 0$, the experiment fails: zero data is collected, but the cost $\text{Cost}(e)$ is expended.
4. **Realized Epistemic Update:** If successful, the experimenter's prior is updated via Bayes' rule:
   $$P(H_k \mid y_{\text{realized}}) = \frac{P(H_k) P(y_{\text{realized}} \mid H_k)}{\sum_m P(H_m) P(y_{\text{realized}} \mid H_m)}$$
5. **Realized Information Gain ($\Delta H_{\text{realized}}$):**
   $$\Delta H_{\text{realized}} = H(H)_{\text{initial}} - H(H \mid y_{\text{realized}})$$
   If the experiment failed ($F=0$), $\Delta H_{\text{realized}} = 0.0$.
6. **Sequential Campaign Convergence:** The sequential decision process repeats until:
   $$P(H^*) \ge 0.95 \quad \text{or} \quad \text{Budget} \le 0$$
   This measures how many experiments and how much total cost each policy requires to discover the true mechanism.

---

## 6. Evaluation Metrics

For each policy $\pi$ evaluated across $S$ independent benchmark runs:

| Metric Identifier | Metric Name | Mathematical Definition | Evaluation Purpose |
| :--- | :--- | :--- | :--- |
| **`M_EIG_EXP`** | Expected Information Gain | $\mathbb{E}[\text{EIG}(e_\pi)]$ (bits) | Expected diagnostic power under model priors. |
| **`M_REAL_IG`** | Realized Information Gain | $\frac{1}{S} \sum_{s=1}^S \Delta H_{\text{realized}}^{(s)}$ (bits) | True entropy reduction achieved under nature's sampled outcomes. |
| **`M_COST_EFF`** | Realized Cost Efficiency | $\frac{\mathbb{E}[\Delta H_{\text{realized}}]}{\mathbb{E}[\text{Cost}(e_\pi)]}$ (bits / cost) | Information yield per unit experimental expenditure. |
| **`M_FAIL_RATE`** | Infeasibility Failure Rate | $\frac{1}{S} \sum_{s=1}^S \mathbb{I}(F^{(s)} = 0)$ | Proportion of selected experiments that abort due to feasibility barriers. |
| **`M_ZERO_RATE`** | Zero-Information Waste Rate | $\frac{1}{S} \sum_{s=1}^S \mathbb{I}(\text{EIG}(e_\pi) < 0.01)$ | Proportion of budget spent on uninformative controls or indistinguishable assays. |
| **`M_STEPS_CONV`**| Steps to Discovery | $\mathbb{E}[\text{Campaign Steps to } P(H^*) \ge 0.95]$ | Efficiency in multi-step sequential discovery campaigns. |
| **`M_COST_CONV`** | Cumulative Cost to Discovery | $\mathbb{E}[\sum_{t=1}^{T_{\text{conv}}} \text{Cost}(e_t)]$ | Total economic resource expenditure required to resolve the mechanism. |
| **`M_REGRET`** | Policy Regret vs. Oracle | $\mathbb{E}[U(\mathcal{O}^*) - U(e_\pi)]$ | Expected suboptimality margin relative to the omniscient oracle. |
| **`M_LATENCY`** | Computational Runtime | Wall-clock execution time (ms) | Algorithmic efficiency for interactive web dashboard response. |

---

## 7. Experimental Rigor, Uncertainty, and Leakage Prevention

### Uncertainty Quantification:
* **Sample Size:** $S = 200$ independent Monte Carlo runs per scenario archetype.
* **Random Seeding:** Independent pseudo-random seeds ($42, 43, \dots, 241$) using `numpy.random.default_rng(seed)`.
* **Confidence Intervals:** 95% bootstrap confidence intervals (10,000 resamples with replacement) reported for all summary statistics.
* **Statistical Significance:** Paired two-sided Wilcoxon signed-rank test comparing JANUS realized information gain against each baseline on identical candidate instances.

### Leakage Prevention Protocol:
1. **Separation of Generation and Decision:** Scenario generation parameters (Dirichlet hyper-parameters, true hypothesis assignments $H^*$, noise distributions) are strictly isolated from policy decision inputs.
2. **No Policy Tuning on Test Archetypes:** Cost penalty weight $\alpha = 0.1$ is held constant across all synthetic benchmarks without post-hoc tuning to favor JANUS.
3. **No Retrospective Priors:** Likelihood matrices supplied to the decision engine represent the pre-experiment model; nature's sampled true outcome is generated independently.

---

## 8. Defensible Scientific Boundaries & What Synthetic Evaluation Cannot Establish

> [!WARNING]
> **Methodological Honesty:** While synthetic benchmarking rigorously evaluates the mathematical correctness and optimization efficiency of the decision engine, it does not replace physical wet-lab chemistry.

* **What the Benchmark Proves:**
  - Proves whether JANUS's information-theoretic scoring algorithm is mathematically sound.
  - Proves that composite utility selection prevents budget waste on cheap but uninformative controls.
  - Proves that feasibility weighting protects campaigns from high-risk experimental aborts.
  - Proves that JANUS converges to the correct hypothesis in fewer steps than random or naive heuristic baselines.
* **What the Benchmark Does Not Prove:**
  - Does not validate that a physical catalyst will behave as modeled if the underlying kinetic likelihood matrix was incorrect.
  - Does not replace peer-reviewed literature curation or primary laboratory spectroscopy.
  - Does not eliminate the need for expert domain scientists to formulate hypotheses and validate instrument noise bounds.

---

## 9. Next Scientifically Meaningful Milestone (Phase 5+)

Following the execution of this evaluation plan, the next meaningful engineering milestones for JANUS are:

1. **Sequential Bayesian Experimental Design (BED) Loop:** Implement the multi-step closed-loop engine where an experimental outcome $y_{\text{obs}}$ automatically updates the posterior $P(H \mid y)$, dynamically re-ranks remaining candidates, and halts upon achieving target confidence.
2. **Continuous Reaction Kinetics Integration:** Extend discrete diagnostic categories to continuous kinetic rate curves using Gaussian Process regression or microkinetic ordinary differential equations (ODEs).
3. **Second Literature Case Study (`CS-ELEC-001`):** Ingest an independent electrochemical $\text{CO}_2$ reduction ($\text{CO}_2\text{RR}$) case study on Cu catalysts to demonstrate domain transferability.
