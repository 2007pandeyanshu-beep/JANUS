"""Tests for JANUS Pydantic Scientific Schemas"""

import pytest
from pydantic import ValidationError
from app.schemas.scientific import Hypothesis, Experiment, PredictedOutcome, Evidence, AnalysisInput


def test_hypothesis_valid():
    h = Hypothesis(
        id="H1",
        name="Hypothesis 1",
        description="Mechanism explanation",
        prior=0.6,
        assumptions=["Assumption 1"]
    )
    assert h.id == "H1"
    assert h.prior == 0.6
    assert h.status == "active"


def test_hypothesis_invalid_prior():
    with pytest.raises(ValidationError):
        # Prior must be <= 1.0 and > 0.0
        Hypothesis(
            id="H1",
            name="Hypothesis 1",
            description="Mechanism",
            prior=1.5
        )

    with pytest.raises(ValidationError):
        Hypothesis(
            id="H1",
            name="Hypothesis 1",
            description="Mechanism",
            prior=0.0
        )


def test_experiment_validation():
    exp = Experiment(
        id="EXP-1",
        name="Assay 1",
        description="Assay description",
        possible_outcomes=["Active", "Inactive"],
        predictions=[
            PredictedOutcome(outcome_label="Active", hypothesis_id="H1", probability=0.9),
            PredictedOutcome(outcome_label="Inactive", hypothesis_id="H1", probability=0.1),
        ],
        cost=1.5,
        feasibility=0.8
    )
    assert len(exp.possible_outcomes) == 2
    assert exp.cost == 1.5
    assert exp.feasibility == 0.8
    assert exp.is_feasible is True


def test_experiment_requires_at_least_two_outcomes():
    with pytest.raises(ValidationError):
        Experiment(
            id="EXP-1",
            name="Assay 1",
            description="Assay description",
            possible_outcomes=["OnlyOneOutcome"],
            predictions=[]
        )
