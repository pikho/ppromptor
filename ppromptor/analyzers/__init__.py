
import re
import textwrap
from abc import abstractmethod
from typing import List, Union

from langchain.chains.llm import LLMChain
from langchain.llms.base import BaseLLM
from langchain.prompts import PromptTemplate
from ppromptor.base.command import CommandExecutor
from ppromptor.base.schemas import (Analysis, EvalResult, EvalSet,
                                    PromptCandidate, Recommendation)
from ppromptor.config import PP_VERBOSE
from ppromptor.loggers import logger
from ppromptor.scorefuncs import score_func_selector
from ppromptor.utils import bulletpointize, get_llm_params


class BaseAnalyzer(CommandExecutor):
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
                                 "evaluation_scores",
                                 "score_funcs"])
        return self._prompt

    def _validate_prompt(self):
        assert isinstance(self._prompt_str, str)
        assert "{role}" in self._prompt_str
        assert "{goal}" in self._prompt_str
        assert "{guidelines}" in self._prompt_str

    @abstractmethod
    def analyze(self, candidate, eval_sets: List[EvalSet], **kwargs):
        pass

    def run_cmd(self, **kwargs):
        return self.analyze(**kwargs)

    def _select_results(self, eval_sets: List[EvalSet]):
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
        
        Description of Evaluation Functions:
        {score_funcs}

        Please refer above evaluation scores and describe the difference
        between preditions and expected answers. And explain why the given 
        role, goal, guidelines and constraints produce the predictions 
        instead of expected answers. Write down in "THOUGHTS" Section.

        Then, Base on above thoughts, please provide revised ROLE, GOAL, 
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

    def _select_results(self, eval_sets: List[EvalSet]):
        return eval_sets

    def analyze(self, candidate, eval_sets: List[EvalSet], **kwargs):
        if isinstance(eval_sets, EvalSet):
            eval_sets = [eval_sets]

        results = self._select_results(eval_sets)

        chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=PP_VERBOSE)

        pred = "\n".join(["\n".join([str(x) for x in r_set.results]) for r_set in results])
        eval_scores = "\n".join(["\n".join([str(x.scores) for x in r_set.results]) for r_set in results])

        used_scorefunc_names = set()
        for r_set in results:
            for result in r_set.results:
                for key in result.scores.keys():
                    used_scorefunc_names.add(key)

        score_funcs = score_func_selector(list(used_scorefunc_names))
        score_funcc_desc = [f"{func.__name__}: {func().description}" for func in score_funcs]  # type: ignore[attr-defined, operator]
        value = {
            "role": candidate.role,
            "goal": candidate.goal,
            "guidelines": bulletpointize(candidate.guidelines),
            "constraints": bulletpointize(candidate.constraints),
            "prediction_anwsers": pred,
            "evaluation_scores": eval_scores,
            "score_funcs": bulletpointize(score_funcc_desc)
        }

        res = chain(value)

        recommendation = self.parse_output(res["text"])

        return Analysis(self.__class__.__name__,
                        results, recommendation)

    def parse_output(self, output):

        logger.info(f"Output: {output}")

        try:
            thoughts = re.findall('(.*)REVISION',
                                  output,
                                  re.DOTALL | re.IGNORECASE)[0]
        except IndexError:
            thoughts = output

        try:
            res = re.findall('REVISION(.*)',
                             output,
                             re.DOTALL | re.IGNORECASE)[0]
            revision = res

        except IndexError:
            revision = ""

        try:
            role = re.findall('ROLE:(.*?)\n', output, re.IGNORECASE)[0]
        except IndexError:
            role = ""

        try:
            goal = re.findall('GOAL:(.*?)\n', output, re.IGNORECASE)[0]
        except IndexError:
            goal = ""

        try:
            guidelines = re.findall('GUIDELINES:(.*?)CONSTRAINTS',
                                    output,
                                    re.DOTALL | re.IGNORECASE)[0]

            guidelines = re.findall('\d\.(.*?)\n',
                                    guidelines)
        except IndexError:
            guidelines = []

        try:
            constraints = re.findall('CONSTRAINTS:(.*)',
                                     output,
                                     re.DOTALL | re.IGNORECASE)[0]
            constraints = re.findall('\d\.(.*?)\n',
                                     constraints)
        except IndexError:
            constraints = []

        return Recommendation(thoughts, revision, role, goal,
                              guidelines, constraints,
                              examples=[], output_format="")
