from ppromptor.base.schemas import IOPair
from ppromptor.scorefuncs import SequenceMatcherScore, score_func_selector


def test_SequenceMatcherScore():

    rec = IOPair(None, "aaa bbb ccc")
    pred = "aaa bbb ccc"
    s = SequenceMatcherScore.score(None, rec, pred)
    assert s == 1.0


def test_selector():
    res = score_func_selector('SequenceMatcherScore')
    assert len(res) == 1


if __name__ == '__main__':
    test_SequenceMatcherScore()
