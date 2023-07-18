import json
import os
import time
from copy import copy
from datetime import datetime
from io import StringIO
from threading import Thread

import pandas as pd
import sqlalchemy
import streamlit as st
from components import (render_candidate, render_config, render_data_as_table,
                        render_iopair, render_report, render_result,
                        show_candidte_comp)
from config import DEFAULT_CONFIG
from ppromptor.agent import JobQueueAgent
from ppromptor.base.schemas import IOPair, PromptCandidate
from ppromptor.config import DEFAULT_PRIORITY
from ppromptor.db import (add_iopair, create_engine, get_analysis,
                          get_analysis_by_candidate_id, get_analysis_by_id,
                          get_candidate_by_id, get_candidates,
                          get_candidates_with_score, get_commands_as_dict,
                          get_dataset, get_result_by_id, get_results,
                          get_session, update_iopair)
from ppromptor.loggers import logger
from ppromptor.utils import load_lm
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

global engine
global sess
global db_path

os.environ["OPENAI_API_KEY"] = "NONE"


def save_config(cfg_data, path):
    with open(path, 'w') as f:
        f.write(json.dumps(cfg_data, indent=4))


def load_config(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            cfg_data = json.loads(f.read())
    else:
        cfg_data = DEFAULT_CONFIG
    return cfg_data


def enable_config(cfg_data):
    if cfg_data["analysis_llm"]:
        analysis_llm = load_lm(cfg_data["analysis_llm"])
        st.session_state['analysis_llm'] = analysis_llm

    if cfg_data["target_llm"]:
        target_llm = load_lm(cfg_data["target_llm"])
        st.session_state['target_llm'] = target_llm

    if cfg_data["openai_key"]:
        os.environ["OPENAI_API_KEY"] = cfg_data["openai_key"]


def render_db_cfg():
    db_path = st.text_input('Database Name/Path', 'examples/antonyms.db')
    if os.path.exists(db_path):
        btn_db = st.button('Load')
    else:
        btn_db = st.button('Create')

    if btn_db:
        st.session_state['db_path'] = db_path
        st.session_state['engine'] = create_engine(db_path)
        st.session_state['sess'] = get_session(st.session_state['engine'])

        if 'target_llm' in st.session_state:
            st.experimental_rerun()

    if 'sess' in st.session_state and st.session_state['sess']:
        st.divider()

        cfg_data = load_config(st.session_state['db_path']+".cfg")
        cfg_data = render_config(cfg_data)
        enable_config(cfg_data)

        save_cfg = st.button('Save')

        if save_cfg:
            save_config(cfg_data, st.session_state['db_path']+'.cfg')
            st.success("Config was saved successfully")

        return True

    return False


if not ('sess' in st.session_state and st.session_state['sess']):
    st.header("Welcome to Prompt-Promptor")
    if render_db_cfg():
        st.experimental_rerun()

else:
    with st.sidebar:

        db_path = st.session_state['db_path']
        target_llm = st.session_state['target_llm']
        analysis_llm = st.session_state['analysis_llm']

        if "agent" not in st.session_state:
            agent = JobQueueAgent(target_llm, analysis_llm, db_path)
            st.session_state['agent'] = agent

        if 'run_state' not in st.session_state:
            st.session_state['run_state'] = False

        refresh_btn = st.sidebar.button('Refresh Page')

        if refresh_btn:
            st.experimental_rerun()

        ckb_auto = st.checkbox("Auto-Refesh")
        if ckb_auto:
            st_autorefresh(interval=2000, key="dataframerefresh")

        st.divider()

        st.write("Command Queue")

        if st.session_state['agent'].state == 1:
            run_btn = st.sidebar.button('Stop')
            if run_btn:
                st.session_state['run_state'] = False
                st.session_state['agent'].stop()
                with st.spinner(text="Wait for agent to stop..."):
                    while True:
                        if st.session_state['agent'].state == 0:
                            break
                        else:
                            time.sleep(0.5)

                st.experimental_rerun()

        elif st.session_state['agent'].state == 0:
            run_btn = st.sidebar.button('Start')
            if run_btn:
                dataset = get_dataset(st.session_state['sess'])
                st.session_state['run_state'] = True

                agent = st.session_state['agent']
                agent_thread = Thread(target=agent.run,
                                      kwargs={"dataset": dataset})
                agent_thread.start()
                st.session_state['agent_thread'] = agent_thread
                st.experimental_rerun()

        cmds = get_commands_as_dict(st.session_state['sess'])
        df = pd.DataFrame(cmds)
        st.dataframe(df, use_container_width=True, hide_index=True)
        # selected_rows = render_data_as_table(cmds)

    if not st.session_state['sess']:
        st.text("Please load or create database")

    else:
        sess = st.session_state['sess']

        tab_candidate, tab_analysis, tab_data, tab_config = st.tabs([
            "Prompt Candidates", "Analysis", "Dataset", "Configuration"])

        with tab_candidate:
            st.header("Prompt Candidates")

            # candidates = get_candidates(sess)
            candidates = get_candidates_with_score(sess)

            selected_rows = render_data_as_table(candidates,
                                                  multiple_selection=True)
            selected_candidates = copy(selected_rows)
            st.divider()

            if len(selected_rows) == 1:

                id_ = selected_rows[0]["id"]
                # input_ = selected_rows[0]["input"]
                # output_ = selected_rows[0]["output"]

                cdd_data = render_candidate(id_, sess)

                cdd_add_btn = st.button('Create Candidate')
                if cdd_add_btn:
                    candidate = PromptCandidate(**cdd_data)

                    sess.add(candidate)
                    sess.commit()

                    __data = {
                        "candidate": candidate,
                        "dataset": get_dataset(sess),
                        "eval_sets": None,
                        "analysis": None
                    }

                    st.session_state['agent'].add_command("Evaluator",
                                                          __data,
                                                          DEFAULT_PRIORITY-100)

                    st.success("PromptCandidate was created successfully")
                    st.experimental_rerun()
            elif len(selected_rows) == 2:
                id_1 = selected_rows[1]["id"]
                id_2 = selected_rows[0]["id"]

                score_1 = selected_rows[1]["final_score"]
                score_2 = selected_rows[0]["final_score"]

                # score of id_2 is always lower than id_1
                # for UX reason, order id_2 on left and id_1 on the right
                show_candidte_comp([id_1, score_1], [id_2, score_2], sess)

            elif len(selected_rows) > 2:
                st.write("Comparison only availabe for two candidates")

        with tab_analysis:

            st.header("Analysis Reports")

            analysis_mode = st.radio(
                "What analysis reports to show?",
                ('Selected', 'All'))

            if analysis_mode == 'All':
                reports = get_analysis(sess)

                selected_rows = render_data_as_table(reports)

                if len(selected_rows) > 1:
                    id_ = selected_rows[0]["id"]
                    render_report(id_, sess)

            elif analysis_mode == 'Selected':
                cdd_ids = [x["id"] for x in selected_candidates]

                if len(cdd_ids) == 0:
                    st.write("Please select Prompt Candidate(s) first")
                elif len(cdd_ids) == 1:
                    try:
                        report = get_analysis_by_candidate_id(sess, cdd_ids[0])
                        render_report(report.id, sess)
                    except sqlalchemy.exc.NoResultFound:
                        st.text(("Report not found. (Maybe still "
                                 "waiting for analyzing?)"))

                elif len(cdd_ids) > 1:
                    st.text(("Warning: Multiple candidates are selected, "
                             f"below only show candidate id=={cdd_ids[0]}"))

                    # for cdd_id in cdd_ids:
                    try:
                        report = get_analysis_by_candidate_id(sess, cdd_ids[0])
                        render_report(report.id, sess)
                    except sqlalchemy.exc.NoResultFound:
                        st.text("Report not found. (Maybe still analyzing?)")

        with tab_data:
            st.header("Dataset")

            uploaded_file = st.file_uploader("Import Dataset")
            if uploaded_file:
                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                jstr = stringio.read()
                dataset = IOPair.schema().loads(jstr, many=True)  # type: ignore[attr-defined]

                st.write(dataset)

                btn_import = st.button("Import")
                if btn_import:
                    for d in dataset:
                        sess.add(d)
                    sess.commit()

                    uploaded_file = None
                    st.experimental_rerun()

            dataset = get_dataset(sess)    
            selected_rows = render_data_as_table(dataset)

            if len(selected_rows) > 0:
                id_ = selected_rows[0]["id"]
                input_ = selected_rows[0]["input"]
                output_ = selected_rows[0]["output"]

                render_iopair([id_, input_, output_], sess)
            else:
                render_iopair([None, "", ""], sess)

        with tab_config:
            render_db_cfg()
