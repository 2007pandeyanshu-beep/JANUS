# Preregistered Evaluation Protocol: CS-OER-002

**Protocol ID:** `EVAL-PROTO-OER-002`  
**Associated Case Study:** `CS-OER-002` (Oxygen Evolution Reaction Mechanism on Perovskite Electrocatalysts)  
**Status:** Preregistered Benchmark Protocol (Frozen Prior to Execution)  
**Protocol Version:** 1.0.0  
**Registration Date:** 2026-10-21  

---

## 1. Primary Evaluation Question & Primary Objective Metric

### 1.1 Primary Evaluation Question
> **Does the JANUS Composite Utility decision policy select experiment sequences that achieve significantly higher Realized Information Gain per unit expenditure than standard heuristic and baseline policies, while guaranteeing non-negative regret against the exact offline combinatorial optimum on the `CS-OER-002` landscape?**

### 1.2 Primary Objective Metric
The primary evaluation metric is **Mean Realized Information Gain (bits)** achieved at campaign termination subject to a fixed budget $B = 10.0$:
$$\text{IG}(S; \omega) = H(P_0) - H(P_{\text{final}})$$
where $P_0$ is the prior distribution over hypotheses ($H_1, H_2, H_3$) and $P_{\text{final}}$ is the posterior distribution resulting from executed experiments $S = \{e_1, \dots, e_K\}$.

### 1.3 Secondary Performance Metrics (Reported Separately)
To prevent metric conflation, the following metrics must be evaluated and reported independently:
1. **Hypothesis Identification Accuracy ($\%$):** Empirical fraction of campaigns where the discrete maximum *a posteriori* hypothesis matches the true hidden hypothesis ($\mathbf{1}[\arg\max_k P(H_k) == H^*]$).
2. **Mean Posterior Confidence $P(H^*)$ ($\%$):** Average continuous Bayesian probability mass allocated to the true hypothesis at campaign termination.
3. **Mean Campaign Cost:** Total expenditure incurred $\sum_{t=1}^K c(e_t)$.
4. **Mean Regret vs. Offline Combinatorial Optimum (bits):** Non-negative deficit $R = \mathcal{O}^*_{\text{offline}}(\omega) - \text{IG}(S; \omega)$.
5. **Zero-EIG Control Pick Rate:** Number of times the uninformative negative control (`EXP-OER-05`) is selected.
6. **Execution Failure Rate:** Number of attempted experiments that fail due to physical feasibility constraints.

---

## 2. Policy Definitions Under Evaluation

All candidate policies operate under identical budgets, candidate libraries, prior beliefs, and stopping criteria:

1. **JANUS Composite Utility Optimization (`janus_utility`):**
   Selects the experiment that maximizes feasibility-regularized, cost-adjusted expected information gain:
   $$e^*_t = \arg\max_{e \in \mathcal{E}_{\text{avail}}, \, c(e) \le B_{\text{rem}}} \frac{\text{feasibility}(e) \cdot \text{EIG}(e \mid P_{t-1})}{1 + \alpha \cdot \text{cost}(e)}$$
   *Default Hyperparameter:* $\alpha = 0.10$.
2. **Raw EIG Maximization (`raw_eig`):**
   Ablation policy that maximizes unadjusted Expected Information Gain, ignoring cost and feasibility:
   $$e^*_t = \arg\max_{e \in \mathcal{E}_{\text{avail}}, \, c(e) \le B_{\text{rem}}} \text{EIG}(e \mid P_{t-1})$$
3. **Naive Cost-Minimization Heuristic (`naive_cheapest`):**
   Greedy baseline that selects the cheapest admissible candidate:
   $$e^*_t = \arg\max_{e \in \mathcal{E}_{\text{avail}}, \, c(e) \le B_{\text{rem}}} \left( - \text{cost}(e) \right)$$
4. **Naive Feasibility-Maximization Heuristic (`feasibility_first`):**
   Greedy baseline that selects the candidate with highest physical feasibility score:
   $$e^*_t = \arg\max_{e \in \mathcal{E}_{\text{avail}}, \, c(e) \le B_{\text{rem}}} \text{feasibility}(e)$$
5. **Uniform Random Selection Baseline (`uniform_random`):**
   Stochastic baseline that selects uniformly at random from budget-admissible remaining candidates:
   $$P(e_t = e_i) = \frac{1}{|\{e \in \mathcal{E}_{\text{avail}} \mid c(e) \le B_{\text{rem}}\}|}$$
6. **True Offline Combinatorial Optimum (`offline_optimum`):**
   Exact global upper bound computed via branch-and-bound search across all budget-feasible candidate subsets under hindsight knowledge of Nature's counterfactual realizations $\omega$:
   $$\mathcal{O}^*_{\text{offline}}(\omega) = \max_{S \subseteq \mathcal{E}, \, \sum_{e \in S} c(e) \le B} \text{IG}(S; \omega)$$

---

## 3. Campaign Execution, Budgets, and Stopping Criteria

### 3.1 Budget and Parameters
- **Maximum Campaign Budget ($B$):** $10.0$ cost units.
- **Target Posterior Confidence ($\tau$):** $0.95$ ($95\%$).
- **Maximum Sequential Steps ($K_{\max}$):** $5$ steps.
- **Cost Regularization Weight ($\alpha$):** $0.10$ (primary); sensitivity tested across $\alpha \in \{0.00, 0.05, 0.10, 0.25, 0.50, 1.00\}$.

### 3.2 Dynamic Stopping Rules
A sequential campaign terminates dynamically when any of the following mutually exhaustive conditions is met:
1. **Target Confidence Reached:** $\max_k P(H_k \mid y_{1:t}) \ge \tau$.
2. **Budget Exhausted:** Remaining budget $B_{\text{rem}} = B - \sum_{i=1}^t c(e_i) < \min_{e \in \mathcal{E}_{\text{avail}}} c(e)$.
3. **Candidate Pool Exhausted:** No unexecuted candidate experiments remain ($\mathcal{E}_{\text{avail}} = \emptyset$).
4. **Information Exhaustion:** All remaining admissible candidates yield zero Expected Information Gain ($\max_{e} \text{EIG}(e) \le 10^{-6}\text{ bits}$).
5. **Maximum Steps Reached:** Step count $t = K_{\max}$.

---

## 4. Seed Partitioning Strategy (Zero-Leakage Invariant)

To guarantee that benchmark results are not contaminated by seed selection bias or post-hoc hyperparameter tuning:

```text
========================================================================================
                          CS-OER-002 SEED PARTITION MATRIX
========================================================================================
 Partition 1: Development Benchmark Set
   Seeds: {1, 2, 3, ..., 50}  (50 seeds)
   Hypotheses Evaluated: {H1 (AEM), H2 (LOM), H3 (OPM)}
   Total Campaigns per Policy: 50 seeds x 3 hypotheses = 150 matched campaigns
   Role: Algorithm development, baseline calibration, alpha parameter sensitivity sweep

 Partition 2: Held-Out Evaluation Set
   Seeds: {101, 102, 103, ..., 150}  (50 seeds)
   Hypotheses Evaluated: {H1 (AEM), H2 (LOM), H3 (OPM)}
   Total Campaigns per Policy: 50 seeds x 3 hypotheses = 150 matched campaigns
   Role: Preregistered generalization test executed with completely frozen code/parameters

 Disjoint Partition Invariant: dev_seeds ∩ held_out_seeds = ∅ (ZERO OVERLAP)
========================================================================================
```

---

## 5. Statistical Analysis & Multiple Comparisons Plan

### 5.1 Paired Difference Metric
Because counterfactual realizations are strictly matched by seed and true hypothesis $H^*$, all statistical comparisons against baseline policies use paired differences:
$$\Delta \text{IG}_i = \text{IG}(\text{JANUS})_i - \text{IG}(\text{Baseline})_i, \quad i \in \{1, \dots, N\}$$

### 5.2 Inferential Statistics
1. **Effect Size:** Cohen's paired effect size $d_z = \frac{\bar{D}}{s_D}$, where $\bar{D}$ is the sample mean difference and $s_D$ is the sample standard deviation of paired differences.
2. **Bootstrap Confidence Intervals:** Two-sided $95\%$ bootstrap confidence intervals generated via $B = 10,000$ resamples with replacement.
3. **Hypothesis Testing:** Non-parametric two-sided paired permutation tests ($M = 10,000$ sign-flip iterations) testing null hypothesis $H_0: \mathbb{E}[\Delta \text{IG}] = 0$.
4. **Multiplicity Correction:** Family-wise error rate (FWER) controlled at $\alpha_{\text{FWER}} = 0.05$ across all 5 baseline comparisons using the **Holm-Bonferroni step-down procedure**:
   $$p_{(k)} \le \frac{\alpha_{\text{FWER}}}{m - k + 1}$$

---

## 6. Preregistered Decision Rules: Success, Failure, and Inconclusive Criteria

To maintain scientific integrity and avoid post-hoc justification of poor outcomes, explicit decision criteria are established before benchmarking:

### 6.1 Certified Success Criteria
JANUS Composite Utility will be declared **empirically superior** on `CS-OER-002` if and only if all of the following conditions are simultaneously met:
1. **Statistical Significance vs. Random:** Paired advantage over Uniform Random is positive and statistically significant after FWER correction:
   $$\bar{\Delta} \text{IG}_{\text{vs. Random}} > 0, \quad p_{\text{adj}} < 0.05$$
2. **Discrete Accuracy Threshold:** Achieves $\ge 80.0\%$ hypothesis identification accuracy across the held-out seed partition ($N=150$).
3. **Strict Non-Negative Regret:** Regret against the Offline Combinatorial Upper Bound is non-negative for 100% of campaigns ($R \ge 0.0$), with zero mathematical invariant violations.
4. **Waste Minimization:** Zero-EIG control pick rate on `EXP-OER-05` is strictly lower than Uniform Random ($\mathbb{E}[\text{Picks}_{\text{JANUS}}] < \mathbb{E}[\text{Picks}_{\text{Random}}]$).

### 6.2 Certified Failure Criteria
JANUS will be declared **deficient** on `CS-OER-002` if any of the following occurs:
1. **Offline Bound Invariant Violation:** Any campaign yields $\text{IG}(\text{JANUS}) > \mathcal{O}^*_{\text{offline}} + 10^{-6}$ (mathematical defect).
2. **Underperformance vs. Random:** $\bar{\Delta} \text{IG}_{\text{vs. Random}} < 0$ with $p_{\text{adj}} < 0.05$.
3. **Severe Waste Susceptibility:** JANUS selects the uninformative negative control `EXP-OER-05` when informative candidates are budget-admissible.
4. *Clarification on Cost Heuristic:* Selecting fewer bits than `naive_cheapest` is **NOT** classified as an automatic failure if the difference arises because `naive_cheapest` exhausts remaining budget on low-utility assays while JANUS stops early upon reaching target confidence $\tau = 0.95$. In such cases, cost-efficiency and early stopping are evaluated independently.

### 6.3 Inconclusive Criteria
If $\bar{\Delta} \text{IG} > 0$ with raw $p < 0.05$ but adjusted $p_{\text{adj}} \ge 0.05$ after Holm-Bonferroni correction, the finding must be classified strictly as **inconclusive / borderline**, and cannot be claimed as a confirmed superiority.

---

## 7. Epistemological Boundary Certification

> [!WARNING]
> **Boundary: In-Silico Simulation vs. Wet-Lab Reality**
> 1. **In-Silico Benchmark Simulation:** The evaluation protocol described herein specifies a simulated computational experiment where Nature's outcomes are generated via pseudo-random draws from parametric likelihood tables.
> 2. **Retrospective Evaluation:** Comparing JANUS selections against historical publications (e.g. Grimaud 2017) tests whether the algorithm would historically prioritize experiments that successfully resolved the debate.
> 3. **Prospective Laboratory Execution:** This protocol does **NOT** validate physical electrochemical performance in an actual electrolyzer. Laboratory deployment requires separate engineering risk assessments, toxic gas venting protocols, potentiostat calibration, and human oversight.
