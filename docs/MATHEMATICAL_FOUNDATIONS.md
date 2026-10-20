# Mathematical Foundations of JANUS

## 1. Problem Formulation
Let $\mathcal{H} = \{H_1, H_2, \dots, H_K\}$ denote an exhaustive, mutually exclusive set of competing scientific hypotheses.
Each hypothesis $H_k$ has an assigned prior probability:
$$P(H_k) \in (0, 1], \quad \sum_{k=1}^K P(H_k) = 1$$

Prior uncertainty is quantified by the Shannon entropy:
$$H(\mathcal{H}) = -\sum_{k=1}^K P(H_k) \log_2 P(H_k) \quad \text{[bits]}$$

## 2. Experimental Likelihoods
A candidate experiment $e$ produces a discrete observable outcome $y \in \mathcal{Y}_e$.
Under hypothesis $H_k$, the probability distribution of observing outcome $y$ is:
$$P(y \mid H_k, e), \quad \sum_{y \in \mathcal{Y}_e} P(y \mid H_k, e) = 1$$

The marginal probability of observing outcome $y$ under experiment $e$ across all hypotheses is:
$$P(y \mid e) = \sum_{k=1}^K P(H_k) P(y \mid H_k, e)$$

## 3. Bayesian Updating & Posterior Entropy
Upon observing outcome $y$, Bayes' theorem yields the posterior distribution over hypotheses:
$$P(H_k \mid y, e) = \frac{P(H_k) P(y \mid H_k, e)}{P(y \mid e)}$$

The posterior entropy given outcome $y$ is:
$$H(\mathcal{H} \mid y, e) = -\sum_{k=1}^K P(H_k \mid y, e) \log_2 P(H_k \mid y, e)$$

## 4. Expected Information Gain (EIG)
Before executing the experiment, the outcome $y$ is unknown. The expected posterior entropy is:
$$\mathbb{E}_{y \sim P(y \mid e)} \left[ H(\mathcal{H} \mid y, e) \right] = \sum_{y \in \mathcal{Y}_e} P(y \mid e) H(\mathcal{H} \mid y, e)$$

The Expected Information Gain (EIG)—equivalent to the Mutual Information $I(\mathcal{H}; \mathcal{Y}_e)$—is:
$$EIG(e) = H(\mathcal{H}) - \mathbb{E}_{y} \left[ H(\mathcal{H} \mid y, e) \right]$$

### Key Mathematical Guarantees:
- **Non-negativity:** $EIG(e) \ge 0$ (Information never hurts in expectation).
- **Zero Information:** If $P(y \mid H_i, e) = P(y \mid H_j, e)$ for all hypotheses, then $P(H_k \mid y, e) = P(H_k)$ and $EIG(e) \equiv 0.0$ bits.
- **Maximal Disambiguation:** If each hypothesis predicts a unique, non-overlapping outcome, $H(\mathcal{H} \mid y, e) = 0$ for all $y$, and $EIG(e) = H(\mathcal{H})$.

## 5. Composite Utility Under Constraints
To balance information gain against real-world feasibility and costs:
$$\text{Utility}(e) = \text{Feasibility}(e) \times \frac{EIG(e)}{1 + \alpha \cdot \text{Cost}(e)}$$
where $\text{Feasibility}(e) \in [0, 1]$ and $\alpha \ge 0$ is the cost-penalty factor.
Experiments with hard infeasibility flags (`is_feasible = False`) are assigned $\text{Utility} = 0$.
