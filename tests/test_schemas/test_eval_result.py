import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, IOPair,
                                    PromptCandidate, Recommendation)


def test_EvalResult():
    res = EvalResult(
            evaluator_name="evaluator",
            prompt=None,
            data="",
            prediction="",
            scores={},
            llm_params={}
    )
