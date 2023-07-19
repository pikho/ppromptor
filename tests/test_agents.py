from fake_llms import FakeListLLM
from ppromptor.analyzers import Analyzer
from ppromptor.base.schemas import (Analysis, EvalResult, EvalSet, IOPair,
                                    PromptCandidate, Recommendation)
from ppromptor.evaluators import Evaluator
from ppromptor.proposers import Proposer
from ppromptor.scorefuncs import SequenceMatcherScore, score_func_selector

dataset = [IOPair(input="1", output="2"),
           IOPair(input="2", output="4")]


def test_proposer():
    proposal = """
    ROLE: test role

    GOAL: test goal

    GUIDELINES:
    1. guideline1
    2. guideline2

    CONSTRAINTS:
    1. constraint1
    2. constraint2
    """
    llm = FakeListLLM(responses=[proposal])
    proposer = Proposer(llm)
    res = proposer.propose(dataset)
    assert isinstance(res, PromptCandidate)
    assert res.role == 'test role'
    assert res.goal == 'test goal'
    assert res.guidelines == ['guideline1', 'guideline2']
    assert res.constraints == ['constraint1', 'constraint2']

    return res


def test_evaluator():
    candidate = PromptCandidate(role='test', goal='test',
                                guidelines=['test'], constraints=['test'])
    llm = FakeListLLM(responses=['2', '1'])
    evaluator = Evaluator(llm, [SequenceMatcherScore(None)])
    res = evaluator.evaluate(dataset, candidate)

    assert isinstance(res, EvalSet)
    assert res.final_score == 2

    return res

def test_analyzer():
    report = """
    THOUGHTS:
    test thoughts

    REVISION:
    revised ROLE: test role

    revised GOAL: test goal

    revised GUIDELINES:
    1. guideline1
    2. guideline2

    revised CONSTRAINTS:
    1. constraint1
    2. constraint2
    """
    candidate = test_proposer()
    eval_set = test_evaluator()

    llm = FakeListLLM(responses=[report])
    test_analyzer = Analyzer(llm)
    report = test_analyzer.analyze(candidate=candidate,
                                   eval_sets=[eval_set])
    assert isinstance(report, Analysis)


# if __name__ == '__main__':
#     res = test_evaluator()
#     print(res)
