# JANUS Case Study: Mechanism of the Low-Temperature Water-Gas Shift Reaction on Pt/CeO2

**Case Study ID:** `CS-CAT-001`  
**Domain:** Heterogeneous Catalysis / Surface Reaction Kinetics  
**Status:** Published Scientific Benchmark (Evidence-Grounded)  

---

## 1. Central Scientific Question

> **By what chemical mechanism does the low-temperature water-gas shift reaction ($\text{CO} + \text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + \text{H}_2$) proceed over platinum supported on ceria ($\text{Pt/CeO}_2$)?**

Specifically:
- Does the reaction proceed via a **Redox (Mars–van Krevelen)** mechanism where $\text{CO}$ abstracts lattice oxygen from the reducible $\text{CeO}_2$ support at the $\text{Pt-CeO}_2$ interface, generating an oxygen vacancy that is subsequently replenished by $\text{H}_2\text{O}$ dissociation?
- Or does it proceed via an **Associative Formate** mechanism where $\text{CO}$ reacts with support hydroxyls ($\text{Ce-OH}$) to form surface formates ($\text{HCOO-Ce}$) that act as the primary reactive intermediates decomposing into $\text{CO}_2 + \text{H}_2$?
- Or does it proceed via an **Associative Carboxyl** mechanism where transient carboxyls ($\ast\text{COOH}$) are the true active intermediate, and the abundant formates observed by infrared spectroscopy are unreactive **spectators**?

---

## 2. Scientific Context & Significance

The Water-Gas Shift (WGS) reaction is a fundamental chemical transformation utilized globally for hydrogen production, ammonia synthesis, and fuel cell gas cleanup (removing trace CO from H2 feedstocks to prevent PEM fuel cell Pt-anode poisoning).

Ceria-supported noble metals, particularly $\text{Pt/CeO}_2$, exhibit exceptional low-temperature catalytic activity ($150^\circ\text{C} - 300^\circ\text{C}$). However, despite over two decades of intense international investigation, researchers have reported contradictory conclusions:
1. **Infrared (DRIFTS) studies** readily detect high concentrations of surface formate ($\text{HCOO}^*$) bands under operando conditions, leading many groups to assert an associative formate pathway.
2. **Transient isotopic kinetic studies (SSITKA)** and isotopic oxygen exchange ($\text{H}_2^{18}\text{O}$) demonstrate that in many regimes, formate decomposition is several times slower than the overall turnover frequency (TOF), meaning formates are spectators and lattice oxygen participation (redox) dominates.
3. **Density functional theory (DFT) and microkinetic modeling** suggest that carboxyl ($\ast\text{COOH}$) intermediates have lower activation barriers than formates, offering an alternative associative explanation.

This makes $\text{Pt/CeO}_2$ an ideal real-world test case for **JANUS discriminative experiment selection**: the competing theories generate distinct, measurable predictions under specific transient isotopic and operando spectroscopic interventions.

---

## 3. Investigation and Selection of Candidate Case Studies

In Task 1, three candidate scientific case studies were investigated according to the hackathon selection criteria:

| Evaluation Dimension | Candidate 1: WGS on $\text{Pt/CeO}_2$ (Selected) | Candidate 2: $\text{CO}_2\text{RR}$ on $\text{Cu}$ ($\ast\text{CO}-\ast\text{CO}$ vs $\ast\text{CO}-\ast\text{CHO}$) | Candidate 3: $\text{CH}_4 \rightarrow \text{CH}_3\text{OH}$ on $\text{Cu}$-Zeolites |
| :--- | :--- | :--- | :--- |
| **Scientific Fit** | **Outstanding:** 3 clearly defined, mutually exclusive mechanistic hypotheses. | **High:** Active debate over C-C coupling intermediate. | **Moderate:** Active site structural debate (mono/di/tri-nuclear). |
| **Primary Source Availability** | **Abundant & Accessible:** Multiple peer-reviewed papers with quantitative transient isotopic data. | **Accessible:** Growing literature, but high variability in experimental cell configurations. | **Moderate:** Complex spectroscopy clouded by zeolite Al-distribution heterogeneity. |
| **Quantitative Evidence Quality** | **Defensible:** Explicit measured TOFs ($\approx 10^{-2}\text{ s}^{-1}$), activation energies ($55-75\text{ kJ/mol}$), and isotopic exchange times. | **Variable:** Operando intermediate concentrations often below signal-to-noise detection limits; heavy reliance on DFT. | **Uncertain:** Reaction cycles are quasi-stoichiometric rather than truly catalytic steady-state. |
| **Distinguishing Experiments** | **Well-defined:** SSITKA $^{12}\text{C}/^{13}\text{C}$ exchange, $\text{H}_2^{18}\text{O}$ oxygen tracking, operando Ce $L_3$-edge XAS. | **Challenging:** Low-frequency ATR-SEIRAS band overlap between $\ast\text{OCCO}$ and $\ast\text{COCHO}$. | **Challenging:** Direct spectroscopic differentiation in operando conditions remains contentious. |
| **Decision** | **SELECTED** | **REJECTED for Phase 2** | **REJECTED for Phase 2** |

### Justification for Choosing Candidate 1:
- The $\text{Pt/CeO}_2$ WGS system provides mathematically transparent observable outcomes where the hypotheses diverge categorically:
  - In a $^{12}\text{CO} \rightarrow \,^{13}\text{CO}$ SSITKA experiment, if the formate exchange rate matches the TOF, $H_2$ (Associative Formate) is supported; if formate exchange is significantly slower than TOF, $H_2$ is refuted.
  - In an $\text{H}_2^{18}\text{O} / \text{C}^{16}\text{O}$ transient pulse, if the initial $\text{CO}_2$ formed contains exclusively lattice $^{16}\text{O}$ from ceria, $H_1$ (Redox) is directly supported.
- This allows JANUS to compute mathematically defensible Expected Information Gain (EIG) based on real published detection thresholds and kinetic rates, without inventing synthetic probabilities.

---

## 4. Authoritative Primary Sources

1. **C. M. Kalamaras, S. Americanou, A. M. Efstathiou**, *"Redox" vs "associative formate with -OH group regeneration" WGS reaction mechanism on Pt/CeO2: Effect of platinum particle size*, **Journal of Catalysis**, 279(2), 2011, 287–300.  
   DOI: [10.1016/j.jcat.2011.01.024](https://doi.org/10.1016/j.jcat.2011.01.024)
2. **F. C. Meunier, A. Goguet, C. Hardacre, R. Burch, D. Thompsett**, *Quantitative DRIFTS investigation of possible reaction mechanisms for the water-gas shift reaction on high-activity Pt- and Au-based catalysts*, **Journal of Catalysis**, 252(1), 2007, 18–22.  
   DOI: [10.1016/j.jcat.2007.09.006](https://doi.org/10.1016/j.jcat.2007.09.006)
3. **R. Burch**, *Differences in the interaction of CO and H2O with Au and Pt catalysts and their relevance to the water-gas shift reaction*, **Phys. Chem. Chem. Phys.**, 8, 2006, 5483–5494.  
   DOI: [10.1039/B611217A](https://doi.org/10.1039/B611217A)
4. **J. A. Rodriguez et al.**, *Activity of CeOx and TiOx Nanoparticles on Au(111) in the Water-Gas Shift Reaction*, **Science**, 318(5857), 2007, 1757–1760.  
   DOI: [10.1126/science.1150038](https://doi.org/10.1126/science.1150038)
5. **C. M. Kalamaras, P. Panagiotopoulou, D. I. Kondarides, A. M. Efstathiou**, *Kinetic and SSITKA study of the water-gas shift reaction on Pt/TiO2 and Pt/CeO2 catalysts*, **Journal of Catalysis**, 264(2), 2009, 117–129.  
   DOI: [10.1016/j.jcat.2009.03.013](https://doi.org/10.1016/j.jcat.2009.03.013)

---

## 5. Traceability & Epistemological Boundaries

* Detailed model parameter classifications (`LITERATURE_REPORTED`, `DERIVED`, `DOMAIN_ASSUMPTION`, `ILLUSTRATIVE`, `UNQUANTIFIED`): see [Scientific Assumptions Ledger](file:///C:/Users/2007p/OneDrive/Desktop/JANUS/docs/case_study/scientific_assumptions.md).
* Statistical benchmark audit and dual ranking metrics: see [Case Study Limitations & Audit](file:///C:/Users/2007p/OneDrive/Desktop/JANUS/docs/case_study/limitations.md).
