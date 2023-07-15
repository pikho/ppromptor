import re
import textwrap
from abc import abstractmethod

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from ppromptor.base.command import CommandExecutor
from ppromptor.base.schemas import PromptCandidate
from ppromptor.config import PP_VERBOSE
from ppromptor.utils import gen_prompt


class BaseProposer(CommandExecutor):
    def __init__(self, llm) -> None:
        self.llm = llm
        self.prompt: PromptTemplate

    @abstractmethod
    def propose(self, dataset, analysis=None, **kwargs) -> PromptCandidate:  # type: ignore[empty-body]
        pass

    def run_cmd(self, **kwargs):
        return self.propose(**kwargs)


class Proposer(BaseProposer):
    def __init__(self, llm) -> None:
        goal = """Your job is to design an LLM AI robot to generate 
        the below ouputs, according to the given inputs. The LLM AI robot
        is equipped with a pretrained LLM to generate outputs. You need to
        speicify the ROLE, GOAL, GUIDELINES, CONSTRAINTS to guide the AI 
        robot to generate correct answers(outputs). Here is the 
        definitation of each propertiy:

        1. ROLE: A job occupation or profession this robot has/is. For example,
                 a senior editor in fashion magzine, a senior product manager 
                 in software company.
        2. GOAL: One sentence to describe what should be done by the AI robot 
                 to generate correct answer. For example, to proof read an 
                 article, to create a travel plan or to summarize an article.
        3. GUIDELINES: A list of precise rules that the AI robot should follow
                       so that it can generate better fit to the answer. Usually
                       they describe the properties of the answer, the 
                       characteristics of the convertion function or the relation
                       between inputs and outputs.
        4. CONSTRAINTS: A list of precise limitations that the AI robot should
                       strictly follow so that it can generate better fit to the answer.
        """
        guidelines = [
            "Do not instruct the AI robot to use external resource",
            "Content of examples must NOT appear in ROLE, GOAL, GUIDELINES and CONSTRAINTS you designed"
        ]

        examples = """
        Below is a list of example input-output pairs:

        {examples}
        """
        examples_prompt = PromptTemplate(
            template=examples, input_variables=["examples"])

        instrutions = """
        Please provide the ROLE, GOAL, GUIDELINES, CONSTRAINTS of the AI robot 
        that can generate above pairs.
        """

        super().__init__(llm)

        self.prompt = gen_prompt(goal=goal,
                                 instrutions=instrutions,
                                 guidelines=guidelines,
                                 examples=examples_prompt)

    def propose(self, dataset, analysis=None, **kwargs):
        if analysis is None:
            chain = LLMChain(llm=self.llm, prompt=self.prompt, verbose=PP_VERBOSE)

            res = chain({"examples": "\n".join([f"{v+1}. {str(x)}" for v, x in enumerate(dataset)])})

            prompt_proposal = res["text"]  # .replace("INSTRUCTION:", "").strip()

            return self._parse(prompt_proposal)
        else:
            return PromptCandidate(
                role=analysis.recommendation.role,
                goal=analysis.recommendation.goal,
                guidelines=analysis.recommendation.guidelines,
                constraints=analysis.recommendation.constraints,
                examples=analysis.recommendation.examples,
                output_format=analysis.recommendation.output_format
            )

    def _parse(self, prompt_proposal):
        role = re.findall("role:(.*?)\n",
                          prompt_proposal,
                          re.IGNORECASE)[0].strip()
        goal = re.findall("goal:(.*?)\n",
                          prompt_proposal,
                          re.IGNORECASE)[0].strip()
        guidelines = re.findall("guidelines:(.*?)constraints",
                                prompt_proposal,
                                re.IGNORECASE | re.DOTALL)[0]
        guidelines = [x.strip() for x in guidelines.split("\n")]
        guidelines = list(filter(lambda x: x != "", guidelines))
        guidelines = [re.findall("[\d|\-|\*]\.(.*)",
                                 x)[0].strip() for x in guidelines]

        constraints = re.findall("constraints:(.*?)$",
                                 prompt_proposal,
                                 re.IGNORECASE | re.DOTALL)[0]
        constraints = [x.strip() for x in constraints.split("\n")]
        constraints = list(filter(lambda x: x != "", constraints))
        constraints = [re.findall("[\d|\-|\*]\.(.*)",
                                  x)[0].strip() for x in constraints]

        res = PromptCandidate(
            role=role,
            goal=goal,
            guidelines=guidelines,
            constraints=constraints,
            examples=[],
            output_format=""
        )
        return res
