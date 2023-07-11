import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, IOPair,
                                    PromptCandidate, Recommendation)


def test_IOPair():
    res = IOPair(
            input="1",
            output="2"
    )
