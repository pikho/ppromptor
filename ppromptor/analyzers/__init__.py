
import re
import textwrap
from typing import List

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from ppromptor.base.schemas import Analysis, Recommendation, Result
from ppromptor.loggers import logger
from ppromptor.utils import bulletpointize


class BaseAnalyzer:
    def __init__(self):
        self.template: PromptCandidate
        self.llm: BaseLLM

    def analyze(self, resultset: List[Result]):
        pass


class Analyzer:
    def __init__(self, llm):
        self.llm = llm

    def analyze(self, candidate, results: List[Result]):
        prompt_str = """
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
        prompt = PromptTemplate(
            template=textwrap.dedent(prompt_str),
            input_variables=["role",
                             "goal",
                             "guidelines",
                             "constraints",
                             "prediction_anwsers",
                             "evaluation_scores"])

        chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False)

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

        return Analysis(candidate, results, recommendation)

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
