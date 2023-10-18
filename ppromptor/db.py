from ppromptor.base.schemas import (Analysis, Command, EvalResult, EvalSet,
                                    IOPair, PromptCandidate, Recommendation,
                                    association_result_set,
                                    association_resultset_analysis)
from sqlalchemy import create_engine as slc_create_engine
from sqlalchemy.orm import Session

CMD_STATE_CODE = {
    0: "W",
    1: "R",
    2: "S",
    3: "F"
}

def create_engine(db_path, echo=False):
    engine = slc_create_engine(f"sqlite+pysqlite:///{db_path}", echo=echo)

    Analysis.__table__.create(engine, checkfirst=True)
    EvalResult.__table__.create(engine, checkfirst=True)
    EvalSet.__table__.create(engine, checkfirst=True)
    IOPair.__table__.create(engine, checkfirst=True)
    PromptCandidate.__table__.create(engine, checkfirst=True)
    Recommendation.__table__.create(engine, checkfirst=True)
    Command.__table__.create(engine, checkfirst=True)
    association_result_set.create(engine, checkfirst=True)
    association_resultset_analysis.create(engine, checkfirst=True)

    return engine


def get_session(engine):
    session = Session(engine)
    return session


def get_dataset(sess):
    return sess.query(IOPair).all()


def get_iopair_by_id(sess, id):
    return sess.query(IOPair).filter_by(id=id).one()


def add_iopair(sess, input_, output_):
    iopair = IOPair(input=input_, output=output_)
    sess.add(iopair)
    sess.commit()


def update_iopair(sess, id, input_, output_):
    iopair = get_iopair_by_id(sess, id)
    iopair.input = input_
    iopair.output = output_
    sess.add(iopair)
    sess.commit()

def get_candidates(sess):
    return sess.query(PromptCandidate).all()


def get_candidate_by_id(sess, id):
    return sess.query(PromptCandidate).filter_by(id=id).one()


def get_results(sess):
    return sess.query(EvalResult).all()


def get_result_by_id(sess, id):
    return sess.query(EvalResult).filter_by(id=id).one()


def get_eval_sets(sess):
    return sess.query(EvalSet).all()


def get_analysis(sess):
    return sess.query(Analysis).all()


def get_analysis_by_id(sess, id):
    return sess.query(Analysis).filter_by(id=id).one()


def get_analysis_by_candidate_id(sess, candidate_id):
    res = sess.query(Analysis).join(EvalSet, Analysis.eval_sets).filter(
        EvalSet.candidate_id == candidate_id).one()
    return res


def get_candidates_with_score(sess):
    return sess.query(PromptCandidate.id,
                      EvalSet.final_score,
                      PromptCandidate.role,
                      PromptCandidate.goal) \
               .join(EvalSet) \
               .order_by(EvalSet.final_score.desc())\
               .all()


def get_commands_as_dict(sess, limit=10):
    cmds = (sess.query(Command)
            # .order_by(Command.priority.asc())
            .order_by(Command.id.desc())
            .limit(limit)
            .all()
            )
    cmds = [{"id": x.id,
             "cmd": x.cmd["cmd"],
             "state": CMD_STATE_CODE[x.state],
             "priority": x.priority,
             # "owner": x.owner
             } for x in cmds]
    return cmds


def reset_running_cmds(sess):
    """
    Reset state of running cmds to 0 (waiting)
    """
    cmds = sess.query(Command).filter_by(state=1).all()

    for cmd in cmds:
        cmd.state = 0
        sess.add(cmd)
        logger.debug(f"Command(id={cmd.id}, state={cmd.state}) state reseted")

    sess.commit()


if __name__ == '__main__':
    engine = create_engine('test3.db')
    sess = get_session(engine)
    dataset = get_dataset(sess)
    breakpoint()
    print(dataset[0])
