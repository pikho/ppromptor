
import re
import textwrap
from typing import List, Union

from langchain.chains.llm import LLMChain
from langchain.llms.base import BaseLLM
from langchain.prompts import PromptTemplate
from ppromptor.base.schemas import (Analysis, EvalResult, PromptCandidate,
                                    Recommendation)
from ppromptor.config import PP_VERBOSE
from ppromptor.loggers import logger
from ppromptor.utils import bulletpointize, get_llm_params


class BaseAnalyzer:
    def __init__(self, llm: BaseLLM) -> None:
        self._prompt: Union[PromptTemplate, None] = None
        self.template: PromptCandidate
        self.llm = llm
        self._prompt_str: str
        self._validate_prompt()

    @property
    def prompt(self):
        if self._prompt is None:
            self._prompt = PromptTemplate(
                template=textwrap.dedent(self._prompt_str),
                input_variables=["role",
                                 "goal",
                                 "guidelines",
                                 "constraints",
                                 "prediction_anwsers",
                                 "evaluation_scores"])
        return self._prompt

    def _validate_prompt(self):
        assert isinstance(self._prompt_str, str)
        assert "{role}" in self._prompt_str
        assert "{goal}" in self._prompt_str
        assert "{guidelines}" in self._prompt_str

    def analyze(self, candidate, results: List[EvalResult]):
        pass

    def _select_results(self, results: List[EvalResult]):
        pass


class Analyzer(BaseAnalyzer):
    def __init__(self, llm):
        self._prompt_str = """
        I create an LLM AI robot that work as a {role} to {goal}. This AI robot
        is equipped with a LLM to generate output and is expected to follow 
        below GUIDELINES and CONSTRAINTS. I expect to get get below answers, 
        however, the AI robot outputs the prediction as provided.

        ROLE:
        {role}

        GOAL:
        {goal}

        GUIDELINES:
        {guidelines}

        CONSTRAINTS:
        {constraints}

        Input, Prediction and Expected Answer triplets:
        {prediction_anwsers}

        Evaluation Scores:
        {evaluation_scores}
        Above score is calculated by a string similarity algorithm. The highest
        score is 1.0, whcih means prediction is exactly the same as the expected
        answer; the lowest score is 0.0 which means prediction is far away closed
        to expected answer.

        Please refer above evaluation scores and describe the difference
        between preditions and expected answers. And explain why the given 
        role, goal, guidelines and constraints produce the predictions 
        instead of expected answers. Write down in "Explaination" Section.

        Then, Base on above thinking, please provide revised ROLE, GOAL, 
        GUIDELINES and CONSTRAINTS that maximize evaluation 
        scores. Write down in "REVISION" section in below format:

        REVISION:

        revised ROLE: ...
        revised GOAL: ...
        revised GUIDELINES:
            1. ...
            2. ...
            ...
        revised CONSTRAINTS:
            1. ...
            2. ...
            ...

        Ok, now, lets think step by step.

        """
        super().__init__(llm)

    def _select_results(self, results: List[EvalResult]):
        return results

    def analyze(self, candidate, results: List[EvalResult]):
        results = self._select_results(results)

        chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=PP_VERBOSE)

        value = {
            "role": candidate.role,
            "goal": candidate.goal,
            "guidelines": bulletpointize(candidate.guidelines),
            "constraints": bulletpointize(candidate.constraints),
            "prediction_anwsers": "\n".join([str(x) for x in results]),
            "evaluation_scores": "\n".join([str(x.scores) for x in results])
        }

        res = chain(value)

        recommendation = self.parse_output(res["text"])

        return Analysis(self.__class__.__name__,
                        candidate, get_llm_params(self.llm),
                        results, recommendation)

    def parse_output(self, output):

        logger.info(f"Output: {output}")

        try:
            res = re.findall('REVISION(.*)',
                             output,
                             re.DOTALL | re.IGNORECASE)[0]
        except IndexError:
            return False

        try:
            role = re.findall('ROLE:(.*?)\n', res, re.IGNORECASE)[0]
        except IndexError:
            role = ""

        try:
            goal = re.findall('GOAL:(.*?)\n', res, re.IGNORECASE)[0]
        except IndexError:
            goal = ""

        try:
            guidelines = re.findall('GUIDELINES:(.*?)CONSTRAINTS',
                                    res,
                                    re.DOTALL | re.IGNORECASE)[0]

            guidelines = re.findall('\d\.(.*?)\n',
                                    guidelines)
        except IndexError:
            guidelines = []

        try:
            constraints = re.findall('CONSTRAINTS:(.*)',
                                     res,
                                     re.DOTALL | re.IGNORECASE)[0]
            constraints = re.findall('\d\.(.*?)\n',
                                     constraints)
        except IndexError:
            constraints = []

        return Recommendation(role, goal, res, guidelines, constraints)
