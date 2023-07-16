import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, EvalSet, IOPair,
                                    PromptCandidate, Recommendation)


def test_EvalResult():
    res = EvalResult(
            evaluator_name="evaluator",
            candidate=None,
            data="",
            prediction="",
            scores={},
            llm_params={}
    )


def test_EvalSet():
    res1 = EvalResult(
            evaluator_name="evaluator",
            candidate=None,
            data="",
            prediction="",
            scores={},
            llm_params={}
    )

    res2 = EvalResult(
            evaluator_name="evaluator",
            candidate=None,
            data="",
            prediction="",
            scores={},
            llm_params={}
    )

    eval_set = EvalSet(candidate=None,
                       results=[res1, res2],
                       scores={},
                       final_score=0.0)
