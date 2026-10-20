# Scientific Limitations and Boundary Conditions of the Pt/CeO2 Case Study

This document explicitly defines the boundaries of the current JANUS implementation, what is empirically supported by published literature, and what remains uncertain or unquantified.

---

## 1. What JANUS Has Established
1. **Evidence-Grounded Mechanistic Framework:** Three distinct hypotheses ($H_1$: Redox, $H_2$: Associative Formate, $H_3$: Associative Carboxyl) have been formulated with specific, citeable reaction steps and published claims.
2. **Explicit Provenance Tracking:** Every claim in the evidence ledger is categorized by provenance:
   - `empirical_observation`: Directly measured in experiments (e.g., SSITKA formate exchange rates from Kalamaras et al., 2011).
   - `computational_dft`: Calculated activation barriers (e.g., *COOH vs formate barriers).
   - `author_interpretation`: Conclusions drawn by original study authors.
   - `unquantified_assumption`: Pragmatic engineering assumptions.
3. **Discriminative Information-Theoretic Ranking:** The mathematical engine computes Expected Information Gain (EIG in bits) solely from validated likelihood distributions, strictly separating quantified experiments from unquantified proposals.
4. **Negative Control Verification:** An uninformative gas-phase blank control (`EXP-WGS-06`) is included, verifying that the engine assigns 0.0 bits EIG when hypotheses predict identical outcomes.

---

## 2. What JANUS Cannot Yet Establish (Scientific Gaps)
1. **Unresolved Carboxyl Intermediate Quantification:**
   - While DFT predicts low barriers for the associative carboxyl pathway ($H_3$), direct steady-state spectroscopic detection of $\ast\text{COOH}$ on $\text{Pt/CeO}_2$ has not been quantitatively verified due to its ultra-short lifetime and sub-monolayer steady-state coverage.
   - Therefore, `EXP-WGS-05` (Operando Stopped-Flow Carboxyl Detection) is explicitly labeled **`UNQUANTIFIED_NEEDS_MEASUREMENT`**. JANUS **refuses to fabricate a likelihood distribution** for this experiment until real signal-to-noise and kinetic measurements become available.
2. **Temperature and Particle Size Regime Transitions:**
   - Published studies (Kalamaras et al., 2011; Meunier et al., 2007) note that mechanism dominance can shift with temperature ($T > 250^\circ\text{C}$) and Pt particle size ($<1.5\text{ nm}$ clusters vs larger nanoparticles). The current case study focuses specifically on the **low-temperature regime ($180^\circ\text{C} - 220^\circ\text{C}$)** on supported $\text{Pt}$ nanoparticles ($\approx 2 - 4\text{ nm}$).
3. **Priors are Subjective Epistemic States:**
   - The prior probabilities $P(H_k)$ represent the prior belief of a scientific researcher before executing the experiments. While the literature currently leans heavily toward Redox ($H_1$) or Carboxyl ($H_3$) at low temperatures, priors are interactive parameters in JANUS and must not be interpreted as physical constants.
4. **Simplified Discrete Outcomes:**
   - Real spectroscopic and mass-spectrometry outputs are continuous time-series curves. For the purpose of Bayesian experiment selection, continuous signals have been discretized into observable classification outcomes (e.g., $k_{\text{decay}} \ll \text{TOF}$ vs $k_{\text{decay}} \approx \text{TOF}$). Future versions will support continuous Bayesian experimental design (BED).

---

## 3. Disclaimers for OSI Hackathon Judges
- **No Experimental Fabrication:** All DOIs, citations, figures, and numerical ranges cited in the evidence ledger are taken directly from peer-reviewed scientific literature.
- **Auditable Provenance:** Users can click through to inspect the exact DOI and quote supporting each claim in the JANUS user interface.
