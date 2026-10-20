from .engine import ScientificEngine
from .scoring import compute_shannon_entropy, evaluate_experiment_information_gain, rank_experiments
from .validation import validate_and_normalize_priors, validate_experiment_predictions, ScientificValidationError
from .scenarios import get_demo_scenario

__all__ = [
    "ScientificEngine",
    "compute_shannon_entropy",
    "evaluate_experiment_information_gain",
    "rank_experiments",
    "validate_and_normalize_priors",
    "validate_experiment_predictions",
    "ScientificValidationError",
    "get_demo_scenario",
]
