import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from dataclasses_json import dataclass_json
from langchain.prompts import PromptTemplate
from ppromptor.utils import bulletpointize
from sqlalchemy import JSON, Column, ForeignKey, Table
from sqlalchemy.orm import (DeclarativeBase, Mapped, MappedAsDataclass,
                            mapped_column, relationship)


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""


@dataclass_json
class PromptCandidate(Base):
    __tablename__ = "prompt_candidate"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    role: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()
    guidelines: Mapped[List[str]] = Column(JSON)
    constraints: Mapped[List[str]] = Column(JSON)
    examples: Mapped[List[str]] = Column(JSON)
    output_format: Mapped[str] = mapped_column(default="")

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
class IOPair(Base):
    __tablename__ = "io_pair"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    input: Mapped[str] = mapped_column()
    output: Mapped[str] = mapped_column()

    def __str__(self):
        return f"Input: {self.input}; Output: {self.output}"


association_result_set = Table(
    "association_result_set",
    Base.metadata,
    Column("eval_set_id", ForeignKey("eval_set.id")),
    Column("eval_result_id", ForeignKey("eval_result.id")),
)


@dataclass_json
class EvalResult(Base):
    __tablename__ = "eval_result"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    evaluator_name: Mapped[str] = mapped_column()

    candidate: Mapped["PromptCandidate"] = relationship()
    data: Mapped["IOPair"] = relationship()

    prediction: Mapped[str] = mapped_column()

    scores: Mapped[Dict[str, float]] = Column(JSON)
    llm_params: Mapped[Dict[str, Any]] = Column(JSON)

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_candidate.id"), default=None)
    data_id: Mapped[int] = mapped_column(
        ForeignKey("io_pair.id"), default=None)

    def __str__(self):
        return (f"Input: [{self.data.input}],"
                f" Prediction: [{self.prediction}],"
                f" Answer: [{self.data.output}]")


@dataclass_json
class EvalSet(Base):
    __tablename__ = "eval_set"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    candidate: Mapped["PromptCandidate"] = relationship()
    results: Mapped[List[EvalResult]] = relationship(
        secondary=association_result_set, default_factory=list)
    scores: Mapped[Dict[str, float]] = Column(JSON, default={})
    final_score: Mapped[float] = mapped_column(default=None)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_candidate.id"), default=None)


@dataclass_json
class Recommendation(Base):
    __tablename__ = "recommendation"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    thoughts: Mapped[str] = mapped_column()
    revision: Mapped[str] = mapped_column()

    role: Mapped[str] = mapped_column()
    goal: Mapped[str] = mapped_column()
    guidelines: Mapped[List[str]] = Column(JSON)
    constraints: Mapped[List[str]] = Column(JSON)
    examples: Mapped[List[str]] = Column(JSON)
    output_format: Mapped[Optional[str]] = mapped_column(default=None)


association_resultset_analysis = Table(
    "association_resultset_analysis",
    Base.metadata,
    Column("analysis_id", ForeignKey("analysis.id")),
    Column("eval_set_id", ForeignKey("eval_set.id")),
)


@dataclass_json
class Analysis(Base):
    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    analyzer_name: Mapped[str] = mapped_column()

    eval_sets: Mapped[List[EvalSet]] = relationship(
        secondary=association_resultset_analysis)

    recommendation: Mapped["Recommendation"] = relationship()

    rcm_id: Mapped[int] = mapped_column(ForeignKey("recommendation.id"),
                                        default=None)


@dataclass_json
class Command(Base):
    __tablename__ = "command"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)

    cmd: Mapped[str] = Column(JSON)
    """
    {
        "cls": str,
        "params": {
            "key": value
        }
    }
    """
    data: Mapped[str] = Column(JSON)

    """
    {
        "param_key": {
            "data_cls": str,
            "data_id": List[int]
        }
    }
    """
    owner: Mapped[str] = mapped_column(default=None)
    priority: Mapped[int] = mapped_column(default=0)
    state: Mapped[int] = mapped_column(default=0)
    # 0: waiting, 1: running, 2: successful 3: failed

    @property
    def data_obj(self):
        return None

    @property
    def cmd_obj(self):
        return None


TABLE_MAP = {
    "PromptCandidate": PromptCandidate,
    "IOPair": IOPair,
    "EvalResult": EvalResult,
    "EvalSet": EvalSet,
    "Recommendation": Recommendation,
    "Analysis": Analysis
}
