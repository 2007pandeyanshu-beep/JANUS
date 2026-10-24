"""Pydantic schemas for the JANUS Independent Scientific Tool uAgent (Phase 6).

Defines the message payload contracts for the Fetch.ai `janus_scientific_computation` protocol.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ArrheniusInput(BaseModel):
    """Input parameters for Arrhenius rate constant calculation."""
    pre_exponential_A: float = Field(
        ...,
        gt=0.0,
        description="Pre-exponential frequency factor A (s^-1 or appropriate kinetic unit)",
    )
    activation_energy_kJ_mol: float = Field(
        ...,
        ge=0.0,
        description="Activation energy E_a in kJ/mol",
    )
    temperature_kelvin: float = Field(
        default=473.15,
        gt=0.0,
        le=5000.0,
        description="Absolute temperature T in Kelvin (default 473.15 K = 200 °C)",
    )


class KieInput(BaseModel):
    """Input parameters for Kinetic Isotope Effect (KIE) evaluation."""
    rate_light: float = Field(
        ...,
        gt=0.0,
        description="Reaction rate or rate constant for light isotopologue (e.g. H2O or H)",
    )
    rate_heavy: float = Field(
        ...,
        gt=0.0,
        description="Reaction rate or rate constant for heavy isotopologue (e.g. D2O or D)",
    )
    temperature_kelvin: Optional[float] = Field(
        default=473.15,
        gt=0.0,
        le=5000.0,
        description="Optional operating temperature in Kelvin",
    )
    label_light: str = Field(
        default="H2O",
        description="Chemical or isotopic label for light isotopologue",
    )
    label_heavy: str = Field(
        default="D2O",
        description="Chemical or isotopic label for heavy isotopologue",
    )


class ReactionSimulationInput(BaseModel):
    """Input parameters for microkinetic reaction simulation and rate comparison."""
    case_study_id: str = Field(
        default="CS-CAT-001",
        description="Case study identifier (e.g. CS-CAT-001, CS-OER-002, SYN-001)",
    )
    temperature_kelvin: float = Field(
        default=473.15,
        gt=0.0,
        le=3000.0,
        description="Reactor temperature in Kelvin",
    )
    pressure_bar: float = Field(
        default=1.0,
        gt=0.0,
        le=500.0,
        description="Total operating pressure in bar",
    )
    feed_composition: Dict[str, float] = Field(
        default_factory=lambda: {"CO": 0.10, "H2O": 0.20, "N2": 0.70},
        description="Reactant feed mole fractions (must sum to ~1.0)",
    )
    catalyst_mass_g: float = Field(
        default=0.10,
        gt=0.0,
        description="Catalyst mass in grams",
    )


class ComputationOutputItem(BaseModel):
    """Structured physical or kinetic parameter result."""
    parameter_name: str = Field(..., description="Physical or kinetic quantity name")
    value: float = Field(..., description="Computed numerical value")
    unit: str = Field(..., description="Standard scientific unit (e.g. s^-1, kJ/mol, dimensionless, mol/(g*s))")
    uncertainty: Optional[float] = Field(default=None, description="Estimated 1-sigma uncertainty or standard error")
    description: str = Field(default="", description="Physical explanation or mechanistic relevance")


class ScientificComputationRequest(BaseModel):
    """Inbound request model for the `janus_scientific_computation` protocol."""
    correlation_id: str = Field(..., description="Correlation ID tracing this computational job across uAgents")
    investigation_id: str = Field(..., description="JANUS investigation identifier")
    computation_type: str = Field(
        ...,
        description="Computation mode: ARRHENIUS_RATE, KINETIC_ISOTOPE_EFFECT, REACTION_SIMULATION, or MECHANISTIC_DISCRIMINABILITY",
    )
    case_study_id: Optional[str] = Field(default="CS-CAT-001", description="Associated scenario identifier")
    arrhenius_params: Optional[ArrheniusInput] = Field(default=None, description="Parameters for Arrhenius rate evaluation")
    kie_params: Optional[KieInput] = Field(default=None, description="Parameters for KIE evaluation")
    simulation_params: Optional[ReactionSimulationInput] = Field(default=None, description="Parameters for reaction kinetic simulation")
    assumptions: List[str] = Field(default_factory=list, description="Explicit theoretical assumptions underlying this calculation")


class ScientificComputationResponse(BaseModel):
    """Outbound response model for the `janus_scientific_computation` protocol."""
    correlation_id: str = Field(..., description="Echoes correlation ID from request")
    investigation_id: str = Field(..., description="JANUS investigation identifier")
    status: str = Field(
        ...,
        description="COMPUTATION_COMPLETED, COMPUTATION_PARTIAL, COMPUTATION_UNAVAILABLE, or INVALID_PARAMETERS",
    )
    agent_address: str = Field(..., description="Fetch.ai cryptographic address of the Scientific Tool Agent")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of computation completion")
    computation_type: str = Field(..., description="Echoes computation type evaluated")
    results: List[ComputationOutputItem] = Field(
        default_factory=list,
        description="Structured calculated physical parameters",
    )
    scientific_interpretation: str = Field(
        default="",
        description="Mechanistic interpretation and physical plausibility assessment",
    )
    assumptions_applied: List[str] = Field(
        default_factory=list,
        description="Documented theoretical assumptions applied in this calculation",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Diagnostic warnings or physical boundary notes",
    )
    execution_time_ms: float = Field(
        default=0.0,
        description="Computation runtime in milliseconds",
    )
