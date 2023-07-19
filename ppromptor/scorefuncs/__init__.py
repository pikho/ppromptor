from abc import abstractmethod
from typing import List


class ScoreFuncRegistry(type):

    REGISTRY: List = []

    def __new__(cls, name, bases, attrs):

        new_cls = type.__new__(cls, name, bases, attrs)
        cls.REGISTRY.append(new_cls)
        return new_cls


class BaseScoreFunc(metaclass=ScoreFuncRegistry):
    def __init__(self, llm=None):
        self.llm = llm

    @property
    def name(self):
        return self.__class__.__name__

    @property
    @abstractmethod
    def description(self):
        pass

    @classmethod
    @abstractmethod
    def score(cls, candidate, record, prediction) -> float:  # type: ignore[empty-body]
        pass

    @classmethod
    def is_me(cls, query):
        return query == cls.__name__


def score_func_selector(names: List[str]) -> List[BaseScoreFunc]:
    score_funcs = []
    for func in BaseScoreFunc.REGISTRY:
        if func.is_me(names):
            score_funcs.append(func)
    return score_funcs


class SequenceMatcherScore(BaseScoreFunc):

    def __init__(self, llm=None):
        self.llm = llm

    @property
    def description(self):
        return """score is calculated by a string similarity algorithm which
        compare prediction and expected answer word by word and calculate the
        edit distance. The highest score is 1.0, whcih means prediction is
        exactly the same as the expected answer; the lowest score is 0.0 which
        means prediction is far away closed to expected answer."""

    @classmethod
    def score(cls, candidate, record, prediction) -> float:
        import difflib
        seq = difflib.SequenceMatcher(a=record.output.lower(),
                                      b=prediction.lower())
        return seq.ratio()


# class SentenceEmbeddingScore(BaseScoreFunc):
#     pass


# class WordEmbeddingScore(BaseScoreFunc):
#     pass
