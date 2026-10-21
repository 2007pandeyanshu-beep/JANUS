# JANUS Parameter Provenance & Evidence Ledger: CS-OER-002

**Case Study ID:** `CS-OER-002`  
**System:** Transition-Metal Perovskite Electrocatalysis ($\text{La}_{1-x}\text{Sr}_x\text{CoO}_{3-\delta}$)  
**Document Purpose:** Source-to-claim evidence ledger and epistemological parameter classification for independent scientific evaluation.  
**Classification Version:** 1.0.0  

---

## 1. Epistemological Classification Taxonomy

Every model input is rigorously categorized into one of five epistemological classes:

1. **`LITERATURE_DERIVED`**: Directly measured numerical parameter or qualitative finding reported in peer-reviewed publications with verified DOI.
2. **`QUANTITATIVELY_DERIVED`**: Computed from literature values via an explicit mathematical formula (e.g., Shannon entropy, Bayes theorem).
3. **`DOMAIN_ASSUMPTION`**: Expert-specified model structure, physical noise floor, or relative cost parameter requiring physical justification; not directly measured.
4. **`ILLUSTRATIVE`**: Parameter assigned for exploratory sensitivity analysis or baseline simulation; represents an epistemic state of belief.
5. **`UNQUANTIFIED`**: Known knowledge gap where published literature lacks sufficient quantitative data; explicitly excluded from decision ranking.

---

## 2. Hypothesis Priors Audit

Hypothesis priors reflect the decision-maker's epistemic uncertainty before executing discriminative experiments.

| Hypothesis ID | Mechanism Name | Assigned Prior | Classification | Provenance & Scientific Justification |
| :--- | :--- | :---: | :--- | :--- |
| **$H_1$** | Adsorbate Evolution Mechanism (AEM) | $0.35$ | **`ILLUSTRATIVE`** | Classical mechanistic framework for metal oxide electrocatalysis (Suntivich 2011). Serves as a standard baseline hypothesis. |
| **$H_2$** | Lattice Oxygen-Mediated Mechanism (LOM) | $0.45$ | **`ILLUSTRATIVE`** | Strongly supported for highly covalent cobaltite perovskites ($\text{SrCoO}_{2.7}$, $\text{La}_{0.5}\text{Sr}_{0.5}\text{CoO}_{3-\delta}$) by OEMS isotopic data (Grimaud 2017; Mefford 2016). Assigned highest illustrative prior. |
| **$H_3$** | Oxide Path / Surface Radical Coupling (OPM) | $0.20$ | **`ILLUSTRATIVE`** | Proposed by theoretical DFT models (Rong & Kolpak 2016) as an alternative route to bypass scaling without bulk lattice collapse. Skeptical prior reflects limited direct operando spectroscopic observation. |
| **$H(P_0)$** | Initial Shannon Entropy | **$1.5129\text{ bits}$** | **`QUANTITATIVELY_DERIVED`** | Calculated directly via Shannon formula: $H(P_0) = -\sum_{k=1}^3 P(H_k) \log_2 P(H_k) = -[0.35 \log_2 0.35 + 0.45 \log_2 0.45 + 0.20 \log_2 0.20]$. |

> [!NOTE]
> **Priors are Epistemic States, Not Physical Constants:**
> Priors model the experimenter's prior state of knowledge. A robust BED engine must remain stable under alternative prior assignments (verified via sensitivity analysis across flat, extreme, and biased prior configurations).

---

## 3. Candidate Experiment Outcome Likelihoods & Measurement Uncertainties

For each experiment $e_i$, observable outcomes $y_j$, and hypothesis $H_k$, the likelihood $P(y_j \mid H_k, e_i)$ represents the conditional observation distribution.

### EXP-OER-01: Operando $^{18}\text{O}$-Labeled DEMS
* **Outcomes:**
  - $y_1$: `Significant_Lattice_18O_In_O2` ($I_{34}/I_{32} > 0.05$)
  - $y_2$: `Predominantly_Electrolyte_16O` ($I_{34}/I_{32} \le 0.05$)

| Hypothesis | $P(y_1 \mid H)$ | $P(y_2 \mid H)$ | Classification | Derivation Record & Confounders |
| :--- | :---: | :---: | :--- | :--- |
| **$H_1$ (AEM)** | $0.08$ | $0.92$ | **`LITERATURE_DERIVED`** + **`DOMAIN_ASSUMPTION`** | In ideal AEM, evolved $\text{O}_2$ comes 100% from water. The $0.08$ likelihood on $y_1$ represents a realistic physical noise floor capturing background heterogeneous isotope exchange at the solid-liquid interface and mass spectrometer baseline noise (Grimaud 2017). |
| **$H_2$ (LOM)** | $0.88$ | $0.12$ | **`LITERATURE_DERIVED`** + **`DOMAIN_ASSUMPTION`** | Evolved $\text{O}_2$ incorporates lattice oxygen. Grimaud (2017) observed sustained $^{34}\text{O}_2$ signals accounting for $10 - 20\%$ of total $\text{O}_2$. The $0.12$ residual on $y_2$ accounts for incomplete lattice $^{18}\text{O}$ pre-enrichment and potential-dependent onset delays. |
| **$H_3$ (OPM)** | $0.15$ | $0.85$ | **`DOMAIN_ASSUMPTION`** | Surface radicals couple directly without extracting subsurface bulk lattice oxygen. A $0.15$ probability on $y_1$ captures rapid surface oxygen atom exchange during intermediate radical lifetimes (Rong 2016). |

---

### EXP-OER-02: Multi-pH Overpotential Titration on RHE Scale
* **Outcomes:**
  - $y_1$: `Non_Nernstian_pH_Shift` ($|\Delta \eta / \Delta \text{pH}| \ge 35\text{ mV/pH}$)
  - $y_2$: `Near_Nernstian_pH_Invariance` ($|\Delta \eta / \Delta \text{pH}| < 35\text{ mV/pH}$)

| Hypothesis | $P(y_1 \mid H)$ | $P(y_2 \mid H)$ | Classification | Derivation Record & Confounders |
| :--- | :---: | :---: | :--- | :--- |
| **$H_1$ (AEM)** | $0.10$ | $0.90$ | **`LITERATURE_DERIVED`** + **`DOMAIN_ASSUMPTION`** | Concerted PCET yields ideal Nernstian behavior ($0\text{ mV/pH}$ on RHE scale). The $0.10$ probability on $y_1$ models residual uncompensated resistance ($iR$) distortion and trace iron impurity artifacts (Suntivich 2011). |
| **$H_2$ (LOM)** | $0.85$ | $0.15$ | **`LITERATURE_DERIVED`** + **`DOMAIN_ASSUMPTION`** | Grimaud (2017) demonstrated that activating lattice oxygen produces a pronounced non-Nernstian shift ($\approx 40 - 60\text{ mV/pH}$) due to decoupled chemical deprotonation steps. $0.15$ noise floor assigned for buffer/diffusion limits. |
| **$H_3$ (OPM)** | $0.40$ | $0.60$ | **`DOMAIN_ASSUMPTION`** | Surface radical coupling involves intermediate surface coverage effects that can yield mild non-Nernstian shifts ($\approx 20 - 30\text{ mV/pH}$) under varying alkaline concentrations (Rong 2016). The split likelihood reflects this intermediate regime. |

---

### EXP-OER-03: Operando EQCM Mass Loss Monitoring
* **Outcomes:**
  - $y_1$: `Continuous_Electrode_Mass_Loss` ($> 5.0\ \mu\text{g/cm}^2\text{/hr}$)
  - $y_2$: `Stable_Electrode_Mass` ($\le 5.0\ \mu\text{g/cm}^2\text{/hr}$)

| Hypothesis | $P(y_1 \mid H)$ | $P(y_2 \mid H)$ | Classification | Derivation Record & Confounders |
| :--- | :---: | :---: | :--- | :--- |
| **$H_1$ (AEM)** | $0.05$ | $0.95$ | **`DOMAIN_ASSUMPTION`** | Metal active sites remain embedded in the stable oxide matrix; minimal steady-state dissolution. $0.05$ probability captures double-layer hydration shifts and micro-stress relaxation on the quartz crystal. |
| **$H_2$ (LOM)** | $0.82$ | $0.18$ | **`LITERATURE_DERIVED`** + **`DOMAIN_ASSUMPTION`** | Lattice oxygen extraction creates under-coordinated cobalt cations that rapidly dissolve into alkaline media, resulting in continuous mass loss and surface amorphization (Mefford 2016; Rong 2016). The $0.18$ residual accounts for potential vacancy refilling by water before irreversible cation detachment. |
| **$H_3$ (OPM)** | $0.12$ | $0.88$ | **`DOMAIN_ASSUMPTION`** | Oxo-radical coupling occurs between surface species without pulling bulk structural oxygens into the gas phase; lattice framework remains predominantly intact (Rong 2016). |

---

### EXP-OER-04: In Situ Soft X-ray Absorption Spectroscopy (sXAS) at O K-edge
* **Outcomes:**
  - $y_1$: `Dynamic_Pre_Edge_Intensity_Growth` ($> 15\%$ intensity increase prior to OER)
  - $y_2$: `Static_Or_Minimal_Pre_Edge_Shift` ($\le 15\%$ change)

| Hypothesis | $P(y_1 \mid H)$ | $P(y_2 \mid H)$ | Classification | Derivation Record & Confounders |
| :--- | :---: | :---: | :--- | :--- |
| **$H_1$ (AEM)** | $0.20$ | $0.80$ | **`DOMAIN_ASSUMPTION`** | Oxidation of surface $\text{Co}^{3+} \to \text{Co}^{4+}$ creates modest pre-edge changes. A $0.20$ likelihood on $y_1$ captures spectral overlap and beam-induced photoreduction artifacts. |
| **$H_2$ (LOM)** | $0.85$ | $0.15$ | **`LITERATURE_DERIVED`** + **`DOMAIN_ASSUMPTION`** | Significant ligand hole formation on oxygen $2p$ states hybridized with cobalt $3d$ prior to OER onset produces a sharp increase in pre-edge absorption intensity (Grimaud 2017; Mefford 2016). |
| **$H_3$ (OPM)** | $0.45$ | $0.55$ | **`DOMAIN_ASSUMPTION`** | Surface oxyl radicals produce ligand holes restricted to the top monolayer. Because soft X-ray fluorescence yield probes $10 - 50\text{ nm}$ into the bulk, the surface radical signal is substantially diluted by bulk spectator absorption. |

---

### EXP-OER-05: Ex-Situ HR-TEM Morphology Inspection (Negative Control)
* **Outcomes:**
  - $y_1$: `Particle_Sintering_Observed`
  - $y_2$: `No_Morphological_Sintering`

| Hypothesis | $P(y_1 \mid H)$ | $P(y_2 \mid H)$ | Classification | Derivation Record |
| :--- | :---: | :---: | :--- | :--- |
| **All ($H_1, H_2, H_3$)** | $0.50$ | $0.50$ | **`DOMAIN_ASSUMPTION`** | Ex-situ morphology is invariant to the dynamic in-situ reaction mechanism. Likelihood is identical across all hypotheses, guaranteeing mathematical Expected Information Gain: $\text{EIG}(\text{EXP-OER-05}) \equiv 0.0000\text{ bits}$. |

---

## 4. Cost and Feasibility Ledger

Assay costs and feasibility ratings represent realistic operational trade-offs between benchtop and synchrotron facilities:

| Candidate ID | Name | Cost | Feasibility | Cost Basis | Feasibility Basis | Classification |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **`EXP-OER-01`** | Operando $^{18}\text{O}$-DEMS | $5.5$ | $0.75$ | High: $^{18}\text{O}_2$ gas, flow cell, turbo pumps. | Membrane wetting risks, flow clogging. | **`DOMAIN_ASSUMPTION`** |
| **`EXP-OER-02`** | RHE pH-Titration | $1.2$ | $0.95$ | Low: Standard RDE, potentiostat, KOH. | High robustness, routine benchtop assay. | **`DOMAIN_ASSUMPTION`** |
| **`EXP-OER-03`** | Operando EQCM | $2.0$ | $0.88$ | Moderate: Specialized crystals, flow chamber. | Viscoelastic damping, bubble noise. | **`DOMAIN_ASSUMPTION`** |
| **`EXP-OER-04`** | Synchrotron O K-edge sXAS | $7.0$ | $0.65$ | Extreme: Synchrotron travel, beamtime fee. | Competitive beamtime, thin membrane rupture. | **`DOMAIN_ASSUMPTION`** |
| **`EXP-OER-05`** | Ex-Situ HR-TEM | $0.8$ | $0.98$ | Low: Routine hourly TEM session. | High reliability, routine imaging. | **`DOMAIN_ASSUMPTION`** |

---

## 5. Summary of Epistemological Traceability & Model Status

### 5.1 Explicit Epistemological Distinctions
To preserve absolute scientific integrity, the parameters in this proposal are categorized into their true epistemological roles:
1. **Literature-Supported Qualitative Trends:** Directional mechanistic phenomena—such as lattice oxygen participation ($^{34}\text{O}_2$ evolution) and non-Nernstian pH-dependence in LOM vs. near-Nernstian behavior in AEM—are directly supported by peer-reviewed literature (Grimaud 2017, Mefford 2016, Rong 2016).
2. **Expert-Assumed Numerical Likelihoods:** The specific two-decimal conditional probabilities (e.g., $P(y_1 \mid H_2) = 0.88$) are **expert domain assumptions** chosen to simulate realistic assay sensitivity; they are **NOT** experimentally calibrated frequentist probabilities from a published statistical cohort.
3. **Illustrative Costs & Feasibilities:** Assigned relative cost units ($0.8 - 7.0$) and feasibility scores ($65\% - 98\%$) reflect illustrative operational resource constraints comparing benchtop and synchrotron access.
4. **Operational Discretization Thresholds:** Cutoff boundaries (e.g., $I_{34}/I_{32} > 0.05$, $|\Delta \eta / \Delta \text{pH}| \ge 35\text{ mV/pH}$, or mass drift $> 5.0\ \mu\text{g/cm}^2\text{/hr}$) are operational definitions used to discretize continuous physical data into categorical outcomes; they are not universal physical constants.
5. **No Direct Empirical Calibration:** This observation model has **NOT** been empirically calibrated against physical laboratory multi-technique datasets.

> [!WARNING]
> **Simulation Boundary:**  
> Any benchmark results generated using this observation model demonstrate the mathematical and algorithmic behavior of decision policies under **specified simulation assumptions**. They do **not** constitute independent physical experimental validation of electrochemical reaction mechanisms.
