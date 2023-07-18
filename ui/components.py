import os

import pandas as pd
import sqlalchemy
import streamlit as st
from diff_viewer import diff_viewer
from ppromptor.db import (add_iopair, create_engine, get_analysis,
                          get_analysis_by_id, get_candidate_by_id,
                          get_result_by_id, update_iopair)
from st_aggrid import (AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder,
                       GridUpdateMode)


def render_data_as_table(records, multiple_selection=False):
    if len(records) == 0:
        st.text("No data")
        return []

    if isinstance(records[0], sqlalchemy.engine.row.Row):
        data = [dict(x._mapping) for x in records]
    elif isinstance(records[0], dict):
        data = records
    else:
        data = [x.to_dict() for x in records]

    df = pd.DataFrame(data)

    gb = GridOptionsBuilder.from_dataframe(df)
    # configure selection
    if multiple_selection:
        gb.configure_selection(selection_mode="multiple",
                               use_checkbox=True)
    else:
        gb.configure_selection(selection_mode="single")

    gb.configure_pagination(enabled=True,
                            paginationAutoPageSize=False,
                            paginationPageSize=10)
    gridOptions = gb.build()

    data = AgGrid(df,
                  edit=False,
                  gridOptions=gridOptions,
                  allow_unsafe_jscode=True,
                  fit_columns_on_grid_load=False,
                  # update_mode=GridUpdateMode.SELECTION_CHANGED,
                  columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)

    selected_rows = data["selected_rows"]

    return selected_rows


def render_config(cfg_data):

    target_llm = st.selectbox(
        "Target LLM",
        (cfg_data["target_llm"], "mlego_wizardlm", "wizardlm", "chatgpt")
    )

    analysis_llm = st.selectbox(
        "Analysis LLM",
        (cfg_data["analysis_llm"], "mlego_wizardlm", "wizardlm", "chatgpt")
    )

    openai_key = st.text_input("OpenAI Key", value=cfg_data["openai_key"])

    if "chatgpt" in (analysis_llm, target_llm) and not openai_key:
        st.warning("Please set OpenAI Key for using ChatGPT")

    return {"openai_key": openai_key,
            "target_llm": target_llm,
            "analysis_llm": analysis_llm
            }




def render_candidate(id_, sess):
    rec = get_candidate_by_id(sess, id_)

    cdd_role = st.text_input("Role", value=rec.role, key=f"cdd_role{id_}")
    cdd_goal = st.text_input('Goal', value=rec.goal, key=f"cdd_goal{id_}")
    cdd_guidelines = st.text_area('Guidelines',
                                  value="\n\n".join(rec.guidelines),
                                  key=f"cdd_guide{id_}")
    cdd_constraints = st.text_area('Constraints',
                                   value="\n\n".join(rec.constraints),
                                   key=f"cdd_cons{id_}")
    cdd_examples = st.text_input('Examples', value=rec.examples,
                                 key=f"cdd_examp{id_}")
    cdd_output_format = st.text_input('Output Format',
                                      value=rec.output_format,
                                      key=f"cdd_output{id_}")

    return {
        "role": cdd_role,
        "goal": cdd_goal,
        "guidelines": cdd_guidelines.split("\n\n"),
        "constraints": cdd_constraints.split("\n\n"),
        "examples": cdd_examples,
        "output_format": cdd_output_format
    }


def show_candidte_comp(value1, value2, sess):
    id_1, score_1 = value1
    id_2, score_2 = value2

    rec_1 = get_candidate_by_id(sess, id_1)
    rec_2 = get_candidate_by_id(sess, id_2)

    col_cmp1, col_cmp2 = st.columns(2)

    with col_cmp1:
        cdd_id = st.text_input('ID',
                               value=id_1,
                               key=f"cdd_id{id_1}")
        cdd_score = st.text_input('Score',
                                  value=score_1,
                                  key=f"cdd_score{id_1}")
    with col_cmp2:
        cdd_id = st.text_input('ID',
                               value=id_2,
                               key=f"cdd_id{id_2}")
        cdd_score = st.text_input('Score',
                                  value=score_2,
                                  key=f"cdd_score{id_2}")
    if rec_2.role != rec_1.role:
        st.write("Role")
        diff_viewer(old_text=rec_1.role,
                    new_text=rec_2.role,
                    lang="none")
    else:
        cdd_role = st.text_input("Role",
                                 value=rec_2.role,
                                 key=f"cdd_role{id_1}")
    if rec_2.goal != rec_1.goal:
        st.write("Goal")
        diff_viewer(old_text=rec_1.goal,
                    new_text=rec_2.goal,
                    lang="none")
    else:
        cdd_goal = st.text_input('Goal',
                                 value=rec_2.goal,
                                 key=f"cdd_goal{id_1}")
    if rec_2.guidelines != rec_1.guidelines:
        st.write("Gguidelines")
        diff_viewer(old_text="\n".join(rec_1.guidelines),
                    new_text="\n".join(rec_2.guidelines),
                    lang="none")
    else:
        cdd_guidelines = st.text_area('Guidelines',
                                      value="\n\n".join(rec_2.guidelines),
                                      key=f"cdd_guide{id_1}")
    if rec_2.constraints != rec_1.constraints:
        st.write("Constraints")
        diff_viewer(old_text="\n".join(rec_1.constraints),
                    new_text="\n".join(rec_2.constraints),
                    lang="none")
    else:
        cdd_constraints = st.text_area('Constraints',
                                       value="\n\n".join(rec_2.constraints),
                                       key=f"cdd_cons{id_1}")
    if rec_2.examples != rec_1.examples:
        st.write("Examples")
        diff_viewer(old_text=rec_1.examples,
                    new_text=rec_2.examples,
                    lang="none")
    else:

        cdd_examples = st.text_input('Examples', value=rec_2.examples,
                                     key=f"cdd_examp{id_1}")

    if rec_2.output_format != rec_1.output_format:
        st.write("Output Format")
        diff_viewer(old_text=rec_1.output_format,
                    new_text=rec_2.output_format,
                    lang="none")
    else:
        cdd_output_format = st.text_input('Output Format',
                                          value=rec_2.output_format,
                                          key=f"cdd_output{id_1}")


def render_result(id_, sess):
    rec = get_result_by_id(sess, id_)

    rst_input = st.text_area("Input", value=rec.data.input)

    col1, col2 = st.columns(2)

    with col1:
        rst_output = st.text_area("Correct Answer", value=rec.data.output)

    with col2:
        rst_prediction = st.text_area("LLM Prediction", value=rec.prediction)

    st.text("Evaluation Scores")
    st.json(rec.scores)

    st.text("Evaluator LLM")
    st.json(rec.llm_params)


def render_report(report_id, sess):
    try:
        report = get_analysis_by_id(sess, report_id)
        __show_report_continue = True
    except sqlalchemy.exc.NoResultFound:
        __show_report_continue = False
        st.write(f"Unable to get report: {report_id}")

    if __show_report_continue:
        st.divider()
        st.subheader("Recommendation")

        rcmm = report.recommendation

        rst_thoughts = st.text_area("Thoughts", value=rcmm.thoughts)
        rst_revision = st.text_area("Revision", value=rcmm.revision)

        st.divider()
        st.subheader("Evaluation Results")
        selected_rows = render_data_as_table(report.eval_sets[0].results)

        if len(selected_rows) > 0:
            id_ = selected_rows[0]["id"]

            render_result(id_, sess)


def render_iopair(data, sess):
    io_input = st.text_area("Input",
                            value=data[1],
                            key="io_input_1")
    io_output = st.text_area("Output",
                             value=data[2],
                             key="io_output_1")

    col_io_1, col_io_2, col_io_3, col_io_4 = st.columns(4)
    with col_io_1:
        io_new_btn = st.button("Create")
        if io_new_btn:
            add_iopair(sess, io_input, io_output)
            st.experimental_rerun()

    with col_io_2:
        if data[0]:
            io_update_btn = st.button("Update")
            if io_update_btn:
                update_iopair(sess, data[0], io_input, io_output)
                st.success("Record was updated successfully")
