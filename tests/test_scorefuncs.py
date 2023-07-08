from ppromptor.base.schemas import IOPair
from ppromptor.scorefuncs import SequenceMatcherScore


def test_SequenceMatcherScore():

    rec = IOPair(None, "aaa bbb ccc")
    pred = "aaa bbb ccc"
    s = SequenceMatcherScore.score(None, rec, pred)
    assert s == 1.0


if __name__ == '__main__':
    test_SequenceMatcherScore()
