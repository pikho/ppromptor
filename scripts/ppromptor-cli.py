#!python3
import argparse
import os
from typing import List

from ppromptor.agent import SimpleAgent
from ppromptor.base.schemas import IOPair
from ppromptor.db import create_engine, get_session
from ppromptor.loggers import logger

if __name__ == '__main__':

    def load_lm(name):
        if name == "mlego_wizardlm":
            from ppromptor.llms.mlego_llm import WizardLLM

            return WizardLLM()
        elif name == "wizardlm":
            from ppromptor.llms.wizardlm import WizardLLM

            return WizardLLM()
        elif name == "chatgpt":
            from langchain.chat_models import ChatOpenAI

            return ChatOpenAI(model_name='gpt-3.5-turbo',
                              temperature=0.1)

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

    agent = SimpleAgent(load_lm(args.eval_llm),
                        load_lm(args.analysis_llm),
                        db_name=args.database_name)
    agent.run(dataset)
