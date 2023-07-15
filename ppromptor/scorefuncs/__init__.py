from abc import abstractmethod


class BaseScoreFunc:
    def __init__(self, llm=None):
        self.name = "ScoreFunc"
        self.llm = llm

    @classmethod
    @abstractmethod
    def score(cls, candidate, record, prediction) -> float:  # type: ignore[empty-body]
        pass


class SequenceMatcherScore(BaseScoreFunc):
    def __init__(self, llm=None):
        self.name = "SequenceMatcherScore"
        self.llm = llm

    @classmethod
    def score(cls, candidate, record, prediction) -> float:
        import difflib
        seq = difflib.SequenceMatcher(a=record.output.lower(),
                                      b=prediction.lower())
        return seq.ratio()


class SentenceEmbeddingScore(BaseScoreFunc):
    pass


class WordEmbeddingScore(BaseScoreFunc):
    pass
