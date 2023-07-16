import os
import tempfile

from ppromptor.base.schemas import (Analysis, EvalResult, EvalSet, IOPair,
                                    PromptCandidate, Recommendation)
from ppromptor.db import create_engine, get_session


def test_create_engine():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, 'test1.db')
        engine = create_engine(db_path)


def test_sess():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, 'test1.db')
        engine = create_engine(db_path)

        sess = get_session(engine)


def test_objs():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, 'test1.db')
        engine = create_engine(db_path)

        sess = get_session(engine)

        iopair = IOPair(
                input="1",
                output="2"
        )

        candidate = PromptCandidate(
            role="",
            goal="",
            guidelines=["1"],
            constraints=["1"],
            examples=["1"],
            output_format=""
        )

        eval_result = EvalResult(
                evaluator_name="evaluator",
                candidate=candidate,
                data=iopair,
                prediction="",
                scores={},
                llm_params={}
        )

        eval_set = EvalSet(candidate, [eval_result],
                           scores={}, final_score=0.1)

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

        analysis = Analysis(
            analyzer_name="test1",
            eval_sets=[eval_set],
            recommendation=recomm
        )

        sess.add(iopair)
        sess.commit()

        sess.add(candidate)
        sess.commit()

        sess.add(eval_result)

        sess.add(recomm)
        sess.commit()

        sess.add(analysis)
        sess.commit()
