"""JANUS Scientific Constraints and Feasibility Checking

Handles physical, resource, and ethical constraints on candidate experiments.
"""

from typing import List, Tuple
from app.schemas.scientific import Experiment


def filter_feasible_experiments(
    experiments: List[Experiment],
    max_cost_budget: float = None
) -> Tuple[List[Experiment], List[str]]:
    """
    Applies hard constraints to candidate experiments.
    
    Returns:
        feasible_experiments, constraint_audit_log
    """
    feasible: List[Experiment] = []
    log: List[str] = []
    
    for exp in experiments:
        if not exp.is_feasible:
            log.append(f"Rejected '{exp.id}' ({exp.name}): Hard feasibility flag set to False.")
            continue
            
        if exp.feasibility <= 0.0:
            log.append(f"Rejected '{exp.id}' ({exp.name}): Feasibility score is {exp.feasibility} <= 0.0.")
            continue
            
        if max_cost_budget is not None and exp.cost > max_cost_budget:
            log.append(
                f"Rejected '{exp.id}' ({exp.name}): Cost {exp.cost} exceeds maximum allowed budget {max_cost_budget}."
            )
            continue
            
        feasible.append(exp)
        
    return feasible, log
