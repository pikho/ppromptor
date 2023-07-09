import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

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
class EvalResult:
    evaluator_name: str
    prompt: PromptCandidate
    data: IOPair
    prediction: str
    scores: Dict[str, float]
    llm_params: Dict[str, Any]

    def __str__(self):
        return (f"Input: [{self.data.input}],"
                f" Prediction: [{self.prediction}],"
                f" Answer: [{self.data.output}]")


@dataclass
class Recommendation():
    thoughts: str
    revision: str

    role: str
    goal: str
    guidelines: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    output_format: str = field(default="")


@dataclass
class Analysis:
    analyzer_name: str
    original_prompt: PromptCandidate
    llm_params: Dict
    results: List[EvalResult]
    recommendation: Recommendation
