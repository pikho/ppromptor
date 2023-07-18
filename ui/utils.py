import pandas as pd
import sqlalchemy
from st_aggrid import (AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder,
                       GridUpdateMode)


def _render_data_as_table(records, multiple_selection=False):
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
