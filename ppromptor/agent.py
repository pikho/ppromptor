import argparse
from typing import List

from langchain.chains.llm import LLMChain
from ppromptor.analyzers import Analyzer
from ppromptor.base.schemas import IOPair, PromptCandidate
from ppromptor.evaluators import Evaluator
from ppromptor.loggers import logger
from ppromptor.proposers import Proposer
from ppromptor.scorefuncs import SequenceMatcherScore


class BaseAgent:
    def __init__(self, eval_llm, analysis_llm):
        self.eval_llm = eval_llm
        self.analysis_llm = analysis_llm

    def run(self, dataset):
        pass


class SimpleAgent(BaseAgent):
    def run(self, dataset):
        candidates: List[PromptCandidate] = []

        while True:
            if len(candidates) <= 0:
                proposer = Proposer(self.analysis_llm)
                candidate = proposer.propose(dataset)
            else:
                candidate = candidates.pop()

            evaluatee_prompt = candidate.prompt

            print("evaluatee_prompt", evaluatee_prompt)

            evaluator = Evaluator()
            evaluator.add_score_func(SequenceMatcherScore(llm=None))
            results = []

            for rec in dataset:
                res = evaluator.eval(rec, candidate, self.eval_llm)
                results.append(res)

            final_score = 0
            for res in results:
                for key, value in res.scores.items():
                    final_score += value

            logger.info(f"Final score: {final_score}")

            reports = []

            analyzer = Analyzer(llm=self.analysis_llm)

            analysis = analyzer.analyze(candidate, results)
            reports.append(analysis)

            print("\n*** Role ***")
            for rp in reports:
                if rp.recommendation:
                    print(rp.recommendation.role)

            print("\n*** Goal ***")
            for rp in reports:
                if rp.recommendation:
                    print(rp.recommendation.goal)

            for i in range(len(reports)):
                idx = (i + 1) * -1
                report = reports[idx]
                if report.recommendation:
                    revised_candidate = PromptCandidate(
                        report.recommendation.role,
                        report.recommendation.goal,
                        report.recommendation.guidelines,
                        report.recommendation.constraints
                    )
                candidates.append(revised_candidate)
                break
