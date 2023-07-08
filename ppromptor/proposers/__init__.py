import re
import textwrap

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from ppromptor.base.schemas import PromptCandidate
from ppromptor.utils import gen_prompt


class BaseProposer:
    def __init__(self, llm):
        self.llm = llm

    def propose(self, data) -> PromptCandidate:  # type: ignore[empty-body]
        pass


class Proposer(BaseProposer):
    def __init__(self, llm):
        self.llm = llm

    # def propose(self, data):
    #     goal = """
    #     Your job is to create a prompt or instruction in human language
    #     that can guide an language model to generate the given ouput,
    #     according to the given inputs.
    #     """

    #     guidelines = [
    #         "Generate the instruction in an abstract and generalized manner.",
    #         "Never disclose any example in the instruction",
    #         "Your final answer should be limited to 8 words",
    #     ]

    #     examples = """
    #     Below is a list of example input-output pairs:

    #     {examples}
    #     """

    #     examples_prompt = PromptTemplate(
    #         template=examples, input_variables=["examples"])

    #     instrutions = """
    #     Please provide the prompt/instruction used to generate these pairs.
    #     Let’s think step by step and then write down the final anwser
    #     in the form of :"INSTRUCTION: the final instruction".
    #     """

    #     prompt = gen_prompt(goal=goal, instrutions=instrutions,
    #                         guidelines=guidelines, examples=examples_prompt)

    #     chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False)
    #     res = chain({"examples": "\n".join([f"{v+1}. {str(x)}" for v, x in enumerate(data)])})

    #     evaluatee_prompt = res["text"].replace("INSTRUCTION:", "").strip()

    #     return evaluatee_prompt
    def propose(self, data):
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

        prompt = gen_prompt(goal=goal, instrutions=instrutions,
                            guidelines=guidelines, examples=examples_prompt)

        chain = LLMChain(llm=self.llm, prompt=prompt, verbose=False)
        res = chain({"examples": "\n".join([f"{v+1}. {str(x)}" for v, x in enumerate(data)])})

        prompt_proposal = res["text"]  # .replace("INSTRUCTION:", "").strip()

        return self._parse(prompt_proposal)

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
