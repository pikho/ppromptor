import argparse
from copy import copy, deepcopy
from typing import Dict, List

from langchain.chains.llm import LLMChain
from ppromptor.analyzers import Analyzer
from ppromptor.base.command import CommandExecutor
from ppromptor.base.schemas import EvalSet, IOPair, PromptCandidate
from ppromptor.db import create_engine, get_session
from ppromptor.evaluators import Evaluator
from ppromptor.job_queues import BaseJobQueue, PriorityJobQueue
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

            eval_set = evaluator.evaluate(dataset, candidate)

            if self.db_sess:
                self.db_sess.add(eval_set)
                for res in eval_set.results:
                    self.db_sess.add(res)
                self.db_sess.commit()

            logger.info(f"Final score: {eval_set.final_score}")

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


class JobQueueAgent(BaseAgent):
    def __init__(self, eval_llm, analysis_llm, db_name=None) -> None:
        super().__init__(eval_llm, analysis_llm, db_name)
        self.queue: BaseJobQueue = PriorityJobQueue()

        self._cmds: Dict[str, CommandExecutor] = {
            "Evaluator": Evaluator(self.eval_llm,
                                   [SequenceMatcherScore(llm=None)]),
            "Analyzer": Analyzer(self.analysis_llm),
            "Proposer": Proposer(self.analysis_llm)
        }

        self._cmd_output = {
            "Evaluator": "eval_sets",
            "Analyzer": "analysis",
            "Proposer": "candidate"
        }

        self._follow_action = {
            "Evaluator": "Analyzer",
            "Analyzer": "Proposer",
            "Proposer": "Evaluator"
        }

    def run(self, dataset) -> None:

        data = {
            "candidate": None,
            "dataset": dataset,
            "eval_sets": None,
            "analysis": None
        }

        if self.queue.empty():
            proposer = Proposer(self.analysis_llm)
            candidate = proposer.propose(dataset)

            self.queue.put({
                    "cmd": "Proposer",
                    "data": data
                }, 0)

        while not self.queue.empty():
            # breakpoint()
            task = self.queue.get()[1]

            cmd = task["cmd"]
            logger.info(f"Execute cmd: {cmd}")

            executor = self._cmds[cmd]
            result = executor.run_cmd(**task["data"])
            logger.info(f"Result: {result}")

            if self.db_sess:
                self.db_sess.add(result)
                self.db_sess.commit()

            data = copy(data)
            # Cannot use deepcopy here since the copied elements are not
            # associatiated with any ORM session, which causes error.
            # Shallow copy() is suitable in this use case to prevent
            # different tasks accessing the same data object

            data[self._cmd_output[cmd]] = result

            self.queue.put({"cmd": self._follow_action[cmd],
                            "data": data}, 0)
