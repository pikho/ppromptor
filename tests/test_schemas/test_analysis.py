import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, EvalSet, IOPair,
                                    PromptCandidate, Recommendation)


def test_Analysis_1():
    a = Analysis(
        analyzer_name="test1",
        eval_sets=[],
        recommendation=None
    )


def test_Analysis_req_params():
    with pytest.raises(TypeError):
        a = Analysis(
            analyzer_name="test1",
            eval_sets=[]
        )

    with pytest.raises(TypeError):
        a = Analysis(
            analyzer_name="test1"
        )


def test_Analysis_3():
    res = EvalResult(
            evaluator_name="evaluator",
            candidate=None,
            data=[],
            prediction="",
            scores={},
            llm_params={}
        )

    eset = EvalSet(candidate=None,
                   results=[res],
                   scores={},
                   final_score=0.1)

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

    a = Analysis(
        analyzer_name="test1",
        eval_sets=[res],
        recommendation=recomm
    )
