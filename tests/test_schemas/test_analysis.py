import pytest
from ppromptor.base.schemas import (Analysis, EvalResult, IOPair,
                                    PromptCandidate, Recommendation)


def test_Analysis_1():
    a = Analysis(
        analyzer_name="test1",
        results=[],
        recommendation=None
    )


def test_Analysis_req_params():
    with pytest.raises(TypeError):
        a = Analysis(
            analyzer_name="test1",
            results=[]
        )

    with pytest.raises(TypeError):
        a = Analysis(
            analyzer_name="test1"
        )


def test_Analysis_3():
    res = EvalResult(
            evaluator_name="evaluator",
            prompt=None,
            data=[],
            prediction="",
            scores={},
            llm_params={}
        )

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
        results=[res],
        recommendation=recomm
    )
