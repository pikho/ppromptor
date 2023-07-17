import textwrap
from abc import abstractmethod
from typing import List, Optional

from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.llms.base import BaseLLM
from langchain.prompts import PromptTemplate
from ppromptor.base.command import CommandExecutor
from ppromptor.base.schemas import EvalResult, EvalSet, IOPair, PromptCandidate
from ppromptor.config import PP_VERBOSE
from ppromptor.loggers import logger
from ppromptor.scorefuncs import BaseScoreFunc
from ppromptor.utils import bulletpointize, get_llm_params


class BaseEvaluator(CommandExecutor):
    def __init__(self,
                 llm: BaseLLM,
                 score_funcs: Optional[List[BaseScoreFunc]] = None) -> None:
        if score_funcs is None:
            self.score_funcs = []
        else:
            self.score_funcs = score_funcs

        self._prompt_str: str
        self._validate_prompt()
        self.llm = llm
        self._prompt = None

    @property
    def prompt(self):
        if self._prompt is None:
            self._prompt = PromptTemplate(
                template=textwrap.dedent(self._prompt_str),
                input_variables=["role",
                                 "goal",
                                 "input",
                                 "guidelines",
                                 "constraints"]
                )
        return self._prompt

    def _validate_prompt(self):
        assert isinstance(self._prompt_str, str)
        assert "{input}" in self._prompt_str
        assert "{guidelines}" in self._prompt_str
        assert "{constraints}" in self._prompt_str

    def add_score_func(self, score_func):
        self.score_funcs.append(score_func)

    @abstractmethod
    def evaluate(self, dataset: List[IOPair],  # type: ignore[empty-body]
                 candidate: PromptCandidate,
                 **kwargs) -> EvalSet:
        pass

    def run_cmd(self, **kwargs):
        return self.evaluate(**kwargs)


class Evaluator(BaseEvaluator):
    def __init__(self,
                 llm: BaseLLM,
                 score_funcs: Optional[List[BaseScoreFunc]] = None) -> None:

        self._prompt_str = ("You are a {role}."
                            " Base on below INPUT, {goal}\n") + """
        INPUT:
        '{input}'

        GUIDELINES:
        {guidelines}

        CONSTRAINTS:
        {constraints}

        Please strictly follow above guidelines and constraints.
        Answer:
        """
        super().__init__(llm, score_funcs)

    def _get_scores(self, results) -> dict:
        res = {}

        for res in results:
            for key, value in res.items():
                if key not in res:
                    res[key] = value
                else:
                    res[key] += value
        return res

    def _get_final_score(self, results) -> float:
        score = 0.0

        for res in results:
            for key, value in res.items():
                score += value
        return score

    def evaluate(self,
                 dataset: List[IOPair],
                 candidate: PromptCandidate,
                 **kwargs) -> EvalSet:

        chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=PP_VERBOSE)

        results = []

        for record in dataset:
            data = {
                "role": candidate.role,
                "goal": candidate.goal,
                "input": record.input,
                "guidelines": bulletpointize(candidate.guidelines),
                "constraints": bulletpointize(candidate.constraints)
            }

            pred = chain(data)["text"].strip()

            rec_scores = {}
            for sf in self.score_funcs:
                rec_scores[sf.name] = sf.score(candidate,
                                               record,
                                               pred)

            logger.debug(f"Evaluator Prediction: {pred}")
            logger.debug(f"Evaluator Answer: {record.output}")
            logger.debug(f"Score: {rec_scores}")

            res = EvalResult(self.__class__.__name__,
                             candidate,
                             record,
                             pred,
                             rec_scores,
                             llm_params=get_llm_params(self.llm))
            results.append(res)

        scores = [x.scores for x in results]
        res_set = EvalSet(candidate=candidate,
                          results=results,
                          scores=self._get_scores(scores),
                          final_score=self._get_final_score(scores)
                          )
        return res_set
