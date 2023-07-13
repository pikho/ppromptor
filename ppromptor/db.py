from ppromptor.base.schemas import (Analysis, EvalResult, IOPair,
                                    PromptCandidate, Recommendation,
                                    association_result_analysis)
from sqlalchemy import create_engine as slc_create_engine
from sqlalchemy.orm import Session


def create_engine(db_path, echo=False):
    engine = slc_create_engine(f"sqlite+pysqlite:///{db_path}", echo=echo)

    Analysis.__table__.create(engine, checkfirst=True)
    EvalResult.__table__.create(engine, checkfirst=True)
    IOPair.__table__.create(engine, checkfirst=True)
    PromptCandidate.__table__.create(engine, checkfirst=True)
    Recommendation.__table__.create(engine, checkfirst=True)
    association_result_analysis.create(engine, checkfirst=True)

    return engine


def get_session(engine):
    session = Session(engine)
    return session


def get_dataset(sess):
    return sess.query(IOPair).all()


def get_candidates(sess):
    return sess.query(PromptCandidate).all()


def get_candidate_by_id(sess, id):
    return sess.query(PromptCandidate).filter_by(id=id)[0]


def get_results(sess):
    return sess.query(EvalResult).all()


def get_analysis(sess):
    return sess.query(Analysis).all()


if __name__ == '__main__':
    engine = create_engine('test3.db')
    sess = get_session(engine)
    dataset = get_dataset(sess)
    breakpoint()
    print(dataset[0])
