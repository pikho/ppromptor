import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, IOPair,
                                    PromptCandidate, Recommendation)


def test_PromptCandidate():
    res = PromptCandidate(
        role="",
        goal="",
        guidelines=[],
        constraints=[],
        examples=[],
        output_format=""
    )
