#!python3
import argparse
import os
from typing import List

from ppromptor.agent import JobQueueAgent, SimpleAgent
from ppromptor.base.schemas import IOPair
from ppromptor.db import create_engine, get_session
from ppromptor.loggers import logger
from ppromptor.utils import load_lm

if __name__ == '__main__':

    def parse_args():
        parser = argparse.ArgumentParser(
            description='ArgumentParser')
        parser.add_argument(
            '--data',
            required=True,
            help='Path to dataset.')

        parser.add_argument(
            '--eval_llm',
            required=True,
            choices=('wizardlm', 'chatgpt', 'mlego_wizardlm'),
            help='Name of LLM to use as evaluator')

        parser.add_argument(
            '--analysis_llm',
            required=True,
            choices=('wizardlm', 'chatgpt', 'mlego_wizardlm'),
            help='Name of LLM to use as analyzer')

        parser.add_argument(
            '--database_name',
            default=None,
            help='Path or name of databse')

        return parser.parse_args()

    args = parse_args()

    if args.database_name and os.path.exists(args.database_name):
        engine = create_engine(args.database_name)
        sess = get_session(engine)
        dataset = sess.query(IOPair).all()

        logger.success(f"Data loaded from db: {args.database_name}")
    else:
        with open(args.data, 'r') as f:
            jstr = f.read()
            dataset = IOPair.schema().loads(jstr, many=True)  # type: ignore[attr-defined]

        logger.success(f"Data loaded from file: {args.data}")

        engine = create_engine(args.database_name)
        sess = get_session(engine)

        for d in dataset:
            sess.add(d)

        sess.commit()
        logger.success(f"Data successfully inserted into db")

    agent = JobQueueAgent(load_lm(args.eval_llm),
                          load_lm(args.analysis_llm),
                          db=sess)
    agent.run(dataset)
