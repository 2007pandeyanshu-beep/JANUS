"""JANUS Independent Scientific Tool uAgent (Phase 6).

Provides an autonomous, independently running Fetch.ai uAgent dedicated to
bounded, reproducible scientific computation, chemical kinetics modeling,
Arrhenius rate evaluation, kinetic isotope effect (KIE) analysis, and
microkinetic reaction simulation.

Architecture:
- Native Fetch.ai uAgents Protocol (`janus_scientific_computation`, version 1.0.0)
- Independent agent identity and distinct cryptographic address (Port 8012)
- Explicit input schemas, parameter validation, and unit consistency
- Reproducible deterministic calculations with physical bounds checking
- Preserves the Likelihood Invariant Boundary: kinetics parameters theoretically assess
  sensitivity and discriminability without mutating Bayesian likelihood distributions P(y|H).
"""

import sys
import os
import math
import time
from pathlib import Path

# Prevent local backend/agents directory from shadowing standard library 'types' during direct script execution
_script_dir = os.path.dirname(os.path.abspath(__file__))
if sys.path and sys.path[0] == _script_dir:
    sys.path.pop(0)

_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from uagents import Agent, Context, Protocol
from app.schemas.scientific_tool import (
    ArrheniusInput,
    KieInput,
    ReactionSimulationInput,
    ComputationOutputItem,
    ScientificComputationRequest,
    ScientificComputationResponse,
)

scientific_tool_proto = Protocol(
    name="janus_scientific_computation",
    version="1.0.0"
)

# Universal gas constant R in kJ / (mol * K)
R_GAS_CONSTANT_KJ_MOL_K = 8.314462618e-3

SCIENTIFIC_BOUNDARY_DISCLAIMER = (
    "Likelihood Boundary Invariant: Deterministic macroscopic kinetics calculations "
    "theoretically evaluate reaction rate sensitivity and isotopic discriminability; "
    "they do NOT alter or mutate candidate experiment likelihood distributions P(y|H), "
    "which remain strictly grounded in published literature (e.g. Kalamaras 2011)."
)


def calculate_arrhenius(params: ArrheniusInput) -> Tuple[List[ComputationOutputItem], str, List[str], List[str]]:
    """
    Computes Arrhenius reaction rate constant k = A * exp(-Ea / RT),
    first-order half-life, and temperature sensitivity.
    """
    A = params.pre_exponential_A
    Ea = params.activation_energy_kJ_mol
    T = params.temperature_kelvin
    warnings: List[str] = []
    assumptions = [
        "First-order elementary kinetic reaction step",
        "Temperature-independent activation barrier across narrow operational window",
        "Boltzmann thermal distribution of molecular velocities",
    ]

    exponent = -Ea / (R_GAS_CONSTANT_KJ_MOL_K * T)
    if exponent < -700.0:
        k = 0.0
        warnings.append("Arrhenius exponent underflow: rate constant is negligibly small (k ~ 0.0).")
    elif exponent > 700.0:
        raise OverflowError("Arrhenius exponent overflow: activation energy / temperature combination non-physical.")
    else:
        k = float(A * math.exp(exponent))

    t_half = (math.log(2.0) / k) if k > 1e-15 else float("inf")
    # Sensitivity d(ln k)/dT = Ea / (R * T^2)
    dlnk_dT = Ea / (R_GAS_CONSTANT_KJ_MOL_K * (T ** 2))

    items = [
        ComputationOutputItem(
            parameter_name="rate_constant_k",
            value=k,
            unit="s^-1",
            description=f"Arrhenius reaction rate constant at {T:.2f} K",
        ),
        ComputationOutputItem(
            parameter_name="activation_energy",
            value=Ea,
            unit="kJ/mol",
            description="Arrhenius activation barrier",
        ),
        ComputationOutputItem(
            parameter_name="temperature",
            value=T,
            unit="K",
            description="Evaluation temperature in Kelvin",
        ),
        ComputationOutputItem(
            parameter_name="half_life_t_half",
            value=t_half if not math.isinf(t_half) else 1e12,
            unit="s",
            description="First-order characteristic half-life t_1/2 = ln(2)/k",
        ),
        ComputationOutputItem(
            parameter_name="temperature_sensitivity_dlnk_dT",
            value=dlnk_dT,
            unit="K^-1",
            description="Sensitivity of logarithmic rate constant with respect to temperature",
        ),
    ]

    interpretation = (
        f"Arrhenius kinetic computation at T={T:.1f} K (Ea={Ea:.1f} kJ/mol, A={A:.2e} s^-1) "
        f"yields rate constant k = {k:.4e} s^-1. "
        f"Activation barrier corresponds to {'facile' if Ea < 60 else ('moderate' if Ea < 100 else 'high')} "
        f"kinetic barrier."
    )
    return items, interpretation, assumptions, warnings


def calculate_kie(params: KieInput) -> Tuple[List[ComputationOutputItem], str, List[str], List[str]]:
    """
    Computes Kinetic Isotope Effect (KIE = rate_light / rate_heavy),
    semi-classical zero-point energy limits, and mechanistic interpretation.
    """
    rH = params.rate_light
    rD = params.rate_heavy
    T = params.temperature_kelvin or 473.15
    warnings: List[str] = []
    assumptions = [
        f"Born-Oppenheimer approximation holds between {params.label_light} and {params.label_heavy}",
        "Harmonic oscillator zero-point energy difference governs isotopic shift",
        "Steady-state turnover conditions without transport mass-transfer limitations",
    ]

    if rD <= 0.0 or rH <= 0.0:
        raise ValueError("Both rate_light and rate_heavy must be strictly positive non-zero quantities.")

    kie = float(rH / rD)

    # Semi-classical maximum primary KIE estimation: KIE_max ~ exp(Delta ZPE / RT)
    # Typical Delta ZPE for C-H vs C-D stretch is ~5.0 kJ/mol; for O-H vs O-D is ~5.5 kJ/mol
    delta_zpe_kJ = 5.2
    max_classical_kie = math.exp(delta_zpe_kJ / (R_GAS_CONSTANT_KJ_MOL_K * T))

    if kie > max_classical_kie:
        warnings.append(
            f"Observed KIE ({kie:.2f}) exceeds semi-classical zero-point energy limit ({max_classical_kie:.2f}) "
            f"at T={T:.1f} K. Suggests possible non-classical proton tunneling."
        )

    # Mechanistic categorization
    if kie >= 1.5:
        mech_interp = (
            f"Primary Kinetic Isotope Effect (KIE = {kie:.2f} >= 1.5). "
            f"Demonstrates that {params.label_light}-bond cleavage (C-H or O-H) is kinetically competent "
            f"and involved in the rate-determining step."
        )
    elif kie >= 0.8:
        mech_interp = (
            f"Secondary / near-unity Kinetic Isotope Effect (KIE = {kie:.2f} in [0.8, 1.5]). "
            f"Indicates that {params.label_light}-bond cleavage is NOT rate-determining. "
            f"Supports mechanistic pathways limited by metal-oxygen vacancy dynamics or non-protic steps."
        )
    else:
        mech_interp = (
            f"Inverse Kinetic Isotope Effect (KIE = {kie:.2f} < 0.8). "
            f"Consistent with pre-equilibrium isotopic fractionation or structural coordination changes."
        )

    items = [
        ComputationOutputItem(
            parameter_name="kinetic_isotope_effect_KIE",
            value=round(kie, 4),
            unit="dimensionless",
            description=f"Kinetic Isotope Effect ({params.label_light} / {params.label_heavy})",
        ),
        ComputationOutputItem(
            parameter_name="rate_light_isotopologue",
            value=rH,
            unit="mol/(g*s)",
            description=f"Reaction rate for light isotopologue ({params.label_light})",
        ),
        ComputationOutputItem(
            parameter_name="rate_heavy_isotopologue",
            value=rD,
            unit="mol/(g*s)",
            description=f"Reaction rate for heavy isotopologue ({params.label_heavy})",
        ),
        ComputationOutputItem(
            parameter_name="semi_classical_limit_KIE_max",
            value=round(max_classical_kie, 2),
            unit="dimensionless",
            description=f"Semi-classical harmonic maximum KIE bound at {T:.1f} K",
        ),
    ]

    return items, mech_interp, assumptions, warnings


def simulate_reaction_kinetics(params: ReactionSimulationInput) -> Tuple[List[ComputationOutputItem], str, List[str], List[str]]:
    """
    Executes microkinetic reaction rate simulation for competing mechanistic pathways
    under specified temperature, pressure, and gas composition.
    """
    case_study = params.case_study_id
    T = params.temperature_kelvin
    P = params.pressure_bar
    composition = params.feed_composition
    warnings: List[str] = []
    assumptions = [
        "Plug-flow differential reactor operation with negligible axial dispersion",
        "Equilibrium adsorption of gas species described by competitive Langmuir isotherms",
        "Isothermal catalyst bed with zero external boundary-layer mass-transfer gradient",
    ]

    # Normalize partial pressures
    sum_y = sum(composition.values())
    if abs(sum_y - 1.0) > 0.05:
        warnings.append(f"Feed composition mole fractions sum to {sum_y:.3f} != 1.0; normalizing to 1.0.")
    norm_comp = {k: v / sum_y for k, v in composition.items()} if sum_y > 0 else composition

    if case_study in ("CS-CAT-001", "WGS"):
        # Low-temperature WGS on Pt/CeO2
        p_CO = P * norm_comp.get("CO", 0.10)
        p_H2O = P * norm_comp.get("H2O", 0.20)

        # 1. Redox / Mars-van Krevelen rate law
        # r_redox = (k_red * p_CO * k_ox * p_H2O) / (k_red * p_CO + k_ox * p_H2O)
        # Activation energies: E_red ~ 52 kJ/mol, E_ox ~ 44 kJ/mol (Kalamaras 2011)
        k_red = 2.5e3 * math.exp(-52.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))
        k_ox = 3.8e3 * math.exp(-44.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))
        denom_redox = (k_red * p_CO) + (k_ox * p_H2O)
        r_redox = (k_red * p_CO * k_ox * p_H2O) / denom_redox if denom_redox > 0 else 0.0

        # 2. Formate pathway rate law (inhibition by strong CO and HCOO adsorption)
        # r_form = k_form * K_CO * p_CO * K_OH * p_H2O / (1 + K_CO * p_CO + K_OH * p_H2O)^2
        k_form = 1.2e2 * math.exp(-85.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))  # High formate decomp barrier
        K_CO = 4.5 * math.exp(22.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))
        K_OH = 1.8 * math.exp(15.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))
        denom_form = (1.0 + K_CO * p_CO + K_OH * p_H2O) ** 2
        r_form = (k_form * K_CO * p_CO * K_OH * p_H2O) / denom_form if denom_form > 0 else 0.0

        # 3. Associative Carboxyl pathway
        k_carb = 1.8e3 * math.exp(-56.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))  # Low 0.58 eV barrier
        denom_carb = 1.0 + 2.0 * p_CO
        r_carb = (k_carb * p_CO * math.sqrt(max(1e-6, p_H2O))) / denom_carb

        rate_ratio = (r_redox / r_form) if r_form > 1e-12 else 999.0
        tof = r_redox  # Reference turnover frequency

        items = [
            ComputationOutputItem(
                parameter_name="simulated_rate_redox_MvK",
                value=round(r_redox, 6),
                unit="mol/(g_cat*s)",
                description="Simulated rate under Redox / Mars-van Krevelen mechanism",
            ),
            ComputationOutputItem(
                parameter_name="simulated_rate_associative_formate",
                value=round(r_form, 6),
                unit="mol/(g_cat*s)",
                description="Simulated rate under Associative Formate decomposition mechanism",
            ),
            ComputationOutputItem(
                parameter_name="simulated_rate_associative_carboxyl",
                value=round(r_carb, 6),
                unit="mol/(g_cat*s)",
                description="Simulated rate under Associative Carboxyl (*COOH) mechanism",
            ),
            ComputationOutputItem(
                parameter_name="branching_ratio_redox_vs_formate",
                value=round(rate_ratio, 2),
                unit="dimensionless",
                description="Predicted rate ratio r_redox / r_formate (>10 favors redox)",
            ),
            ComputationOutputItem(
                parameter_name="turnover_frequency_TOF",
                value=round(tof, 4),
                unit="s^-1",
                description="Predicted apparent catalyst turnover frequency",
            ),
        ]

        interpretation = (
            f"Pt/CeO2 WGS kinetics at T={T:.1f} K, P={P:.1f} bar: "
            f"Redox pathway rate ({r_redox:.4e} mol/(g*s)) dominates unassisted formate decomposition "
            f"({r_form:.4e} mol/(g*s)) by a factor of {rate_ratio:.1f}x. "
            f"High surface formate coverage acts as spectator reservoir rather than reactive turnover path."
        )
    elif case_study in ("CS-OER-002", "OER"):
        # Perovskite OER kinetics
        overpotential_V = 0.35
        j_AEM = 10.0 * math.exp(overpotential_V / 0.060)  # Tafel slope ~60 mV/dec
        j_LOM = 25.0 * math.exp(overpotential_V / 0.040)  # Tafel slope ~40 mV/dec
        ratio = j_LOM / j_AEM

        items = [
            ComputationOutputItem(
                parameter_name="simulated_current_density_AEM",
                value=round(j_AEM, 2),
                unit="mA/cm^2",
                description="Simulated OER current density under conventional AEM",
            ),
            ComputationOutputItem(
                parameter_name="simulated_current_density_LOM",
                value=round(j_LOM, 2),
                unit="mA/cm^2",
                description="Simulated OER current density under Lattice Oxygen Mechanism",
            ),
            ComputationOutputItem(
                parameter_name="rate_ratio_LOM_vs_AEM",
                value=round(ratio, 2),
                unit="dimensionless",
                description="Predicted activity enhancement ratio j_LOM / j_AEM",
            ),
        ]
        interpretation = (
            f"Perovskite OER microkinetics at eta={overpotential_V:.2f} V: LOM predicts {ratio:.2f}x higher "
            f"current density than AEM due to favorable O-O coupling thermodynamics bypassing *OOH scaling."
        )
    else:
        # Synthetic Kinase Benchmark
        k_cat = 45.0 * math.exp(-40.0 / (R_GAS_CONSTANT_KJ_MOL_K * T))
        items = [
            ComputationOutputItem(
                parameter_name="benchmark_k_cat",
                value=round(k_cat, 4),
                unit="s^-1",
                description="Benchmark catalytic turnover rate constant",
            ),
        ]
        interpretation = f"Synthetic benchmark kinetics at T={T:.1f} K: k_cat = {k_cat:.4f} s^-1."

    return items, interpretation, assumptions, warnings


def perform_scientific_computation(
    request: ScientificComputationRequest,
    agent_address: str,
) -> ScientificComputationResponse:
    """
    Executes structured scientific computation based on request mode.
    Guarantees physical sanity checks, strict error handling, and complete traceability.
    """
    t0 = time.perf_counter()
    now_iso = datetime.now(timezone.utc).isoformat()
    ctype = request.computation_type.upper()
    all_warnings: List[str] = [SCIENTIFIC_BOUNDARY_DISCLAIMER]

    try:
        if ctype == "ARRHENIUS_RATE":
            if not request.arrhenius_params:
                return ScientificComputationResponse(
                    correlation_id=request.correlation_id,
                    investigation_id=request.investigation_id,
                    status="INVALID_PARAMETERS",
                    agent_address=agent_address,
                    timestamp=now_iso,
                    computation_type=ctype,
                    results=[],
                    scientific_interpretation="Computation rejected: missing 'arrhenius_params' in request.",
                    assumptions_applied=[],
                    warnings=["Missing mandatory ArrheniusInput parameters."],
                    execution_time_ms=(time.perf_counter() - t0) * 1000.0,
                )
            items, interp, assumptions, warns = calculate_arrhenius(request.arrhenius_params)
            all_warnings.extend(warns)

        elif ctype == "KINETIC_ISOTOPE_EFFECT":
            if not request.kie_params:
                return ScientificComputationResponse(
                    correlation_id=request.correlation_id,
                    investigation_id=request.investigation_id,
                    status="INVALID_PARAMETERS",
                    agent_address=agent_address,
                    timestamp=now_iso,
                    computation_type=ctype,
                    results=[],
                    scientific_interpretation="Computation rejected: missing 'kie_params' in request.",
                    assumptions_applied=[],
                    warnings=["Missing mandatory KieInput parameters."],
                    execution_time_ms=(time.perf_counter() - t0) * 1000.0,
                )
            items, interp, assumptions, warns = calculate_kie(request.kie_params)
            all_warnings.extend(warns)

        elif ctype in ("REACTION_SIMULATION", "SIMULATION"):
            sim_params = request.simulation_params or ReactionSimulationInput(
                case_study_id=request.case_study_id or "CS-CAT-001"
            )
            items, interp, assumptions, warns = simulate_reaction_kinetics(sim_params)
            all_warnings.extend(warns)

        elif ctype == "MECHANISTIC_DISCRIMINABILITY":
            # Evaluates 3-sigma statistical discriminability between competing rate laws
            sim_params = request.simulation_params or ReactionSimulationInput(
                case_study_id=request.case_study_id or "CS-CAT-001"
            )
            sim_items, _, assumptions, warns = simulate_reaction_kinetics(sim_params)
            all_warnings.extend(warns)

            r_redox = next((it.value for it in sim_items if "redox" in it.parameter_name), 1.0)
            r_form = next((it.value for it in sim_items if "formate" in it.parameter_name), 0.1)

            # Experimental noise sigma ~ 10% of mean rate
            mean_rate = (r_redox + r_form) / 2.0
            sigma_exp = max(1e-6, 0.10 * mean_rate)
            z_score = abs(r_redox - r_form) / sigma_exp
            is_disc = 1.0 if z_score >= 3.0 else 0.0

            items = [
                ComputationOutputItem(
                    parameter_name="z_score_separation",
                    value=round(z_score, 2),
                    unit="sigma",
                    description="Statistical separation between competing hypothesis predictions",
                ),
                ComputationOutputItem(
                    parameter_name="is_statistically_discriminable",
                    value=is_disc,
                    unit="binary (1=True, 0=False)",
                    description="Whether separation exceeds 3.0 sigma threshold",
                ),
                ComputationOutputItem(
                    parameter_name="experimental_noise_sigma",
                    value=round(sigma_exp, 6),
                    unit="mol/(g*s)",
                    description="Assumed 10% experimental measurement standard error",
                ),
            ]
            interp = (
                f"Mechanistic discriminability analysis: Z = {z_score:.2f} sigma. "
                f"{'Separation is statistically decisive (Z >= 3.0 sigma) to distinguish competing mechanisms.' if is_disc == 1.0 else 'Separation is marginal (< 3.0 sigma); Bayesian experimental design required to maximize information gain.'}"
            )

        else:
            return ScientificComputationResponse(
                correlation_id=request.correlation_id,
                investigation_id=request.investigation_id,
                status="INVALID_PARAMETERS",
                agent_address=agent_address,
                timestamp=now_iso,
                computation_type=ctype,
                results=[],
                scientific_interpretation=f"Unsupported computation_type '{ctype}'. Supported types: ARRHENIUS_RATE, KINETIC_ISOTOPE_EFFECT, REACTION_SIMULATION, MECHANISTIC_DISCRIMINABILITY.",
                assumptions_applied=[],
                warnings=[f"Unknown computation mode '{ctype}'."],
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ScientificComputationResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="COMPUTATION_COMPLETED",
            agent_address=agent_address,
            timestamp=now_iso,
            computation_type=ctype,
            results=items,
            scientific_interpretation=interp,
            assumptions_applied=assumptions,
            warnings=all_warnings,
            execution_time_ms=elapsed,
        )

    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ScientificComputationResponse(
            correlation_id=request.correlation_id,
            investigation_id=request.investigation_id,
            status="INVALID_PARAMETERS",
            agent_address=agent_address,
            timestamp=now_iso,
            computation_type=ctype,
            results=[],
            scientific_interpretation=f"Computational calculation exception: {str(exc)}",
            assumptions_applied=[],
            warnings=[f"Computation aborted due to exception: {str(exc)}"],
            execution_time_ms=elapsed,
        )


# ==============================================================================
# Protocol Handler
# ==============================================================================

@scientific_tool_proto.on_message(
    model=ScientificComputationRequest,
    replies={ScientificComputationResponse}
)
async def handle_computation_request(ctx: Context, sender: str, msg: ScientificComputationRequest):
    """
    Handles incoming computation requests from the primary JANUS Coordinator.
    """
    ctx.logger.info(
        f"Received ScientificComputationRequest from {sender} "
        f"[Investigation: {msg.investigation_id}, Mode: {msg.computation_type}, Case Study: {msg.case_study_id}]"
    )

    response = perform_scientific_computation(msg, agent_address=ctx.agent.address)
    ctx.logger.info(
        f"Scientific computation complete: {response.status} "
        f"({len(response.results)} output parameters, {response.execution_time_ms:.1f}ms). Replying to {sender}..."
    )

    await ctx.send(sender, response)


def create_scientific_tool_uagent(
    name: str = "janus_scientific_tool_agent",
    seed: Optional[str] = None,
    port: int = 8012,
    endpoint: Optional[List[str]] = None,
    use_mailbox: Optional[bool] = None,
    agentverse_url: Optional[str] = None,
) -> Agent:
    """
    Constructs and returns the configured JANUS Independent Scientific Tool uAgent (Phase 6).
    """
    effective_seed = seed or os.getenv("JANUS_SCIENTIFIC_TOOL_SEED")
    raw_env_mailbox = os.getenv("JANUS_SCIENTIFIC_TOOL_USE_MAILBOX")

    if use_mailbox is not None:
        is_mailbox = bool(use_mailbox)
    elif raw_env_mailbox is not None and raw_env_mailbox.strip():
        is_mailbox = raw_env_mailbox.strip().lower() in ("true", "1", "yes")
    else:
        is_mailbox = False

    if is_mailbox:
        if not effective_seed:
            raise ValueError(
                "Agentverse mailbox mode requires a securely configured, persistent identity seed. "
                "Please set the 'JANUS_SCIENTIFIC_TOOL_SEED' environment variable."
            )
    elif not effective_seed:
        effective_seed = "janus_tool_agent_isolated_evaluation_seed_phase6"

    agent_kwargs: Dict[str, Any] = {
        "name": name,
        "seed": effective_seed,
        "port": port,
    }

    try:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        agent_kwargs["loop"] = loop
    except Exception:
        pass

    if is_mailbox:
        agent_kwargs["mailbox"] = True
        effective_agentverse = agentverse_url or os.getenv("AGENTVERSE_URL")
        if effective_agentverse:
            agent_kwargs["agentverse"] = effective_agentverse
    else:
        agent_kwargs["mailbox"] = False
        agent_kwargs["endpoint"] = endpoint or [f"http://127.0.0.1:{port}/submit"]

    agent = Agent(**agent_kwargs)
    agent.include(scientific_tool_proto)
    return agent


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).resolve().parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()
    except ImportError:
        pass

    tool_port = int(os.getenv("JANUS_SCIENTIFIC_TOOL_PORT", "8012"))
    agent_instance = create_scientific_tool_uagent(port=tool_port)

    print("=" * 80)
    print(" JANUS Independent Scientific Tool uAgent (Phase 6 Daemon)")
    print("=" * 80)
    print(f"Agent Name:    {agent_instance.name}")
    print(f"Agent Address: {agent_instance.address}")
    print(f"Agent Port:    {tool_port}")
    print(f"Protocol:      janus_scientific_computation (v1.0.0)")
    print("Starting daemon server...")
    agent_instance.run()
