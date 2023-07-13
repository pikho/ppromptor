import argparse
from typing import List

from langchain.chains.llm import LLMChain
from ppromptor.analyzers import Analyzer
from ppromptor.base.schemas import EvalSet, IOPair, PromptCandidate
from ppromptor.db import create_engine, get_session
from ppromptor.evaluators import Evaluator
from ppromptor.loggers import logger
from ppromptor.proposers import Proposer
from ppromptor.scorefuncs import SequenceMatcherScore


class BaseAgent:
    def __init__(self, eval_llm, analysis_llm, db_name=None):
        self.eval_llm = eval_llm
        self.analysis_llm = analysis_llm
        if db_name:
            engine = create_engine(db_name)
            self.db_sess = get_session(engine)
        else:
            self.db_sess = None

    def run(self, dataset) -> None:
        pass


class SimpleAgent(BaseAgent):
    def run(self, dataset) -> None:
        candidates: List[PromptCandidate] = []

        while True:

            # 1. Propose Candidates
            if len(candidates) <= 0:
                proposer = Proposer(self.analysis_llm)
                candidate = proposer.propose(dataset)
            else:
                candidate = candidates.pop()

            if self.db_sess:
                self.db_sess.add(candidate)
                self.db_sess.commit()

            evaluatee_prompt = candidate.prompt
            print("evaluatee_prompt", evaluatee_prompt)

            # 2. Evaluate Candidates and Generate EvalResults
            evaluator = Evaluator(self.eval_llm)
            evaluator.add_score_func(SequenceMatcherScore(llm=None))
            # results = []
            eval_set = EvalSet(candidate)
            scores = {}

            for rec in dataset:
                res = evaluator.eval(rec, candidate)
                eval_set.results.append(res)

            final_score: float = 0.0
            for res in eval_set.results:
                for key, value in res.scores.items():
                    final_score += value
                    if key not in scores:
                        scores[key] = value
                    else:
                        scores[key] += value

            eval_set.scores = scores
            eval_set.final_score = final_score

            self.db_sess.add(eval_set)
            self.db_sess.commit()

            if self.db_sess:
                for res in eval_set.results:
                    self.db_sess.add(res)
                self.db_sess.commit()

            logger.info(f"Final score: {final_score}")

            # 3. Analyze EvalResults and Generate Analysis and Recommendation
            reports = []
            analyzer = Analyzer(llm=self.analysis_llm)

            analysis = analyzer.analyze(candidate, [eval_set])
            reports.append(analysis)

            print("\n*** Role ***")
            for rp in reports:
                print(rp.recommendation.role)

            print("\n*** Goal ***")
            for rp in reports:
                print(rp.recommendation.goal)

            for i in range(len(reports)):
                idx = (i + 1) * -1
                report = reports[idx]
                if report.recommendation:
                    revised_candidate = PromptCandidate(
                        report.recommendation.role,
                        report.recommendation.goal,
                        report.recommendation.guidelines,
                        report.recommendation.constraints,
                        examples=[],
                        output_format=""
                    )
                candidates.append(revised_candidate)
                break

            if self.db_sess:
                self.db_sess.add(analysis)
                self.db_sess.commit()
