from sqlalchemy import create_engine as slc_create_engine
from sqlalchemy.orm import Session

from .base.schemas import (Analysis, EvalResult, IOPair, PromptCandidate,
                           Recommendation, association_result_analysis)


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
