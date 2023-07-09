import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Union

from dataclasses_json import dataclass_json
from langchain.prompts import PromptTemplate
from ppromptor.utils import bulletpointize


@dataclass
class PromptCandidate:
    role: str
    goal: str
    guidelines: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    output_format: str = field(default="")

    @property
    def prompt(self):
        guidelines = bulletpointize(self.guidelines)
        constraints = bulletpointize(self.constraints)

        prompt_str = (f"You are a {self.role}. Your job is to {self.goal}.",
                      "Always follow below guidelines:",
                      "",
                      "Guideline:",
                      f"{guidelines}",
                      "",
                      "Strickly follow below constraints:",
                      "",
                      "Constraints:",
                      f"{constraints}",
                      "",
                      "Input:",
                      "{input}",
                      "",
                      "Now, generate output accordingly:")

        print(prompt_str)
        return PromptTemplate(template=textwrap.dedent("\n".join(prompt_str)),
                              input_variables=["input"])


@dataclass_json
@dataclass
class IOPair:
    input: str
    output: str

    def __str__(self):
        return f"Input: {self.input}; Output: {self.output}"


@dataclass
class Result:
    prompt: PromptCandidate
    data: IOPair
    prediction: str
    scores: Dict[str, float]
    llm_params: Dict[str, Union[float, str]]

    def __str__(self):
        return (f"Input: [{self.data.input}],"
                f" Prediction: [{self.prediction}],"
                f" Answer: [{self.data.output}]")


@dataclass
class Recommendation():
    role: str
    goal: str
    revision: str
    guidelines: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    output_format: str = field(default="")


@dataclass
class Analysis:
    original_prompt: PromptCandidate
    results: List[Result]
    recommendation: Recommendation


@dataclass
class Scrapchbook:
    analyses: List[Analysis]
