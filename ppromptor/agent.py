import argparse
from copy import copy, deepcopy
from typing import Dict, List

import sqlalchemy
from langchain.chains.llm import LLMChain
from ppromptor.analyzers import Analyzer
from ppromptor.base.command import CommandExecutor
from ppromptor.base.schemas import EvalSet, IOPair, PromptCandidate
from ppromptor.config import DEFAULT_PRIORITY
from ppromptor.db import create_engine, get_session, reset_running_cmds
from ppromptor.evaluators import Evaluator
from ppromptor.job_queues import BaseJobQueue, ORMJobQueue, PriorityJobQueue
from ppromptor.loggers import logger
from ppromptor.proposers import Proposer
from ppromptor.scorefuncs import SequenceMatcherScore


class BaseAgent:
    def __init__(self, eval_llm, analysis_llm, db=None):
        self.eval_llm = eval_llm
        self.analysis_llm = analysis_llm
        if isinstance(db, str):
            engine = create_engine(db)
            self.db_sess = get_session(engine)
        elif isinstance(db, sqlalchemy.orm.session.Session):
            self.db_sess = db
        else:
            self.db_sess = None
        self._agent_state = 0  # 0: stoped, 1: running 2: waiting for stopping

    @property
    def state(self):
        return self._agent_state

    @state.setter
    def state(self, state: int):
        assert state in [0, 1, 2]

        self._agent_state = state

    def stop(self):
        self.state = 2
        logger.info(f" agent call stop, state {self.state}")

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
    def __init__(self, eval_llm, analysis_llm, db=None) -> None:
        super().__init__(eval_llm, analysis_llm, db)
        self._queue: BaseJobQueue = ORMJobQueue(session=self.db_sess)

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

        self._next_action = {
            "Evaluator": "Analyzer",
            "Analyzer": "Proposer",
            "Proposer": "Evaluator"
        }

    def get_runner(self, cmd_s: str):
        return self._cmds[cmd_s]

    def add_command(self, cmd_s: str, data: dict, priority: int):
        self._queue.put({
                "cmd": cmd_s,
                "data": data
            }, priority)        

    def run(self, dataset, epochs=-1) -> None:

        self.state = 1

        # FIXME: This is a workround for incompleted commands
        # Background: When a command is popped from the queue,
        # its state is set to 1 (running). However, if the process
        # is interupted before the task finishes, it will
        # be ignored. This workaround will reset all
        # tasks with a stat of 1 to 0 at the begining of run(), which
        # assume that only one agent can access the queue.
        # Using Context Manager should be a better way to fix this.

        reset_running_cmds(self.db_sess)

        data = {
            "candidate": None,
            "dataset": dataset,
            "eval_sets": None,
            "analysis": None
        }

        if self._queue.empty():
            self.add_command("Proposer", data, DEFAULT_PRIORITY)

        acc_epochs = 0

        while self.state == 1 and (not self._queue.empty()):
            priority, task = self._queue.get()

            task_id = task["id"]
            cmd_s = task["cmd"]
            logger.info(f"Execute Command(cmd={cmd_s}, id={task_id})")

            for k, v in task["data"].items():
                if v:
                    data[k] = v

            runner = self.get_runner(cmd_s)
            result = runner.run_cmd(**task["data"])
            logger.info(f"Result: {result}")

            if self.db_sess:
                self.db_sess.add(result)
                self.db_sess.commit()

            data = copy(data)
            # Cannot use deepcopy here since the copied elements are not
            # associatiated with any ORM session, which causes error.
            # Shallow copy() is suitable in this use case to prevent
            # different tasks accessing the same data object

            data[self._cmd_output[cmd_s]] = result

            self.add_command(self._next_action[cmd_s],
                             data,
                             DEFAULT_PRIORITY)
            self._queue.done(task, 2)

            acc_epochs += 1

            if acc_epochs == epochs:
                self.state = 0
                return None

        self.state = 0
