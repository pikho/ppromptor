import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, IOPair,
                                    PromptCandidate, Recommendation)


def test_Recommendation():
    recomm = Recommendation(
        thoughts="",
        revision="",
        role="",
        goal="",
        guidelines=[],
        constraints=[],
        examples=[],
        output_format=""
    )
