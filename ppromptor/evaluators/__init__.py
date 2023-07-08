import textwrap

from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from ppromptor.base.schemas import Result
from ppromptor.loggers import logger
from ppromptor.utils import bulletpointize


class BaseEvaluator:
    def __init__(self):
        self.score_funcs: List[ScoreFunc] = []

    def evaluate(self) -> Result:  # type: ignore[empty-body]
        pass


class Evaluator:
    def __init__(self):
        self.score_funcs = []

    def add_score_func(self, score_func):
        self.score_funcs.append(score_func)

    def eval(self, record, candidate, llm):
        prompt = f"You are a {candidate.role}. Base on below INPUT, {candidate.goal}\n" + """
        INPUT:
        {input}

        GUIDELINES:
        {guidelines}

        CONSTRAINTS:
        {constraints}

        Please strictly follow above guidelines and constraints.
        Answer:
        """

        # scores = []

        prompt = PromptTemplate(
            template=textwrap.dedent(prompt), input_variables=["input",
                                              "guidelines",
                                              "constraints"])

        chain = LLMChain(llm=llm, prompt=prompt)

        data = {
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

        res = Result(candidate,
                     record,
                     pred,
                     rec_scores,
                     llm_params={})

        return res
