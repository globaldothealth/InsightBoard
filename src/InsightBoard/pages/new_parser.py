import logging
import traceback
from datetime import datetime
from typing import Literal

import dash
import dash_bootstrap_components as dbc
import InsightBoard.utils as utils
import pandas as pd
from dash import callback
from dash import dash_table
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import State

# DataTable supports a maximum of 512 conditional formatting rules,
#  so stop adding rules after this limit is reached
MAX_CONDITIONAL_FORMATTING = 512

# Register the page
dash.register_page(__name__, path="/new_parser")
projectObj = None
autoParser = None

# different bottom layouts
bottom_buttons_data_dict = [
    dbc.Button(
        "Create Mapping File",
        id="mapping-button",
        n_clicks=None,  # 0
        style={"marginRight": "5px"},
    ),
    # Buttons for downloading CSV and committing changes
    dbc.Button(
        "Download as CSV",
        id="download-dict-button",
        n_clicks=0,
        style={"margin": "5px"},
    ),
    dcc.Download(id="download-dict-csv"),
]

bottom_buttons_mapping = [
    dbc.Button(
        "Create Mapping File",
        id="disabled-mapping-button",
        n_clicks=None,  # 0
        style={"marginRight": "5px"},
        disabled=True,
    ),
    # Buttons for downloading CSV and committing changes
    dbc.Button(
        "Download as CSV",
        id="download-mapping-button",
        n_clicks=0,
        style={"margin": "5px"},
    ),
    dcc.Download(id="download-mapping-csv"),
    html.Div(
        [
            dcc.Input(
                id="parser-name",
                type="text",
                placeholder="Parser Name",
                style={"marginRight": "5px"},
            ),
            dbc.Button(
                "Generate Parser",
                id="make-parser-button",
                n_clicks=0,
            ),
        ],
        style={
            "marginLeft": "auto",
            "display": "flex",
            "flexDirection": "row",
            "alignItems": "flex-end",  # Align items to the right
            "justifyContent": "flex-end",  # Right-align the whole div
        },
    ),
]


# Page layout
def layout():
    return html.Div(
        [
            # Store
            dcc.Store(id="project"),  # project selection
            dcc.Store(id="parser-id"),  # unique id (project-table)
            dcc.Store(id="ap-output-store"),  # autoparser output
            dcc.Store(id="edited-ap-output-store"),  # edited data dict
            dcc.Store(id="generate-descriptions-with-llm"),  # Setting: LLm descriptions
            dcc.Store(id="unmapped-fields"),
            dcc.Store(id="edited-unmapped-fields", data=[]),
            # Page rendering
            html.H1("Create a new parser"),
            html.Div(id="autoparser-messages"),
            html.Div(
                [
                    dbc.Col(
                        [
                            # Choose LLM
                            html.H6(
                                children="""
        Choose which LLM to use for generating your parser, and provide a corresponding API key:
    """  # noqa
                            ),
                            dcc.RadioItems(
                                options=[
                                    {"label": "gpt-4o-mini", "value": "openai"},
                                    {"label": "gemini-1.5-flash", "value": "gemini"},
                                ],
                                value="openai",
                                id="llm-choice",
                                style={"marginTop": "10px", "marginBottom": "10px"},
                            ),
                            # API key input
                            dcc.Input(
                                id="api-key",
                                type="password",
                                placeholder="API Key",
                                value=None,
                                style={"marginTop": "5px", "marginBottom": "10px"},
                            ),
                            # Set data language
                            html.H6(
                                children="""
        Select which language your data is in:
    """
                            ),
                            dcc.Dropdown(
                                id="data-language",
                                options=[
                                    {"label": "English", "value": "en"},
                                    {"label": "French", "value": "fr"},
                                ],
                                placeholder="Select a language",
                                style={
                                    "marginTop": "10px",
                                    "marginBottom": "10px",
                                },
                            ),
                        ],
                        width=6,
                    ),
                    html.Div(
                        children="""
        Please select a schema, and the data file you want to create a parser for.
    """
                    ),
                    # Schema dropdown list (context-dependent on dataset)
                    dbc.Col(
                        dcc.Dropdown(
                            id="schema-dropdown",
                            options=[],
                            placeholder="Select a schema",
                            style={"width": "100%"},
                        ),
                        width=6,
                    ),
                    # Upload drop-space
                    dcc.Upload(
                        id="ap-upload-data",
                        children=html.Div(
                            ["Drag and Drop or ", html.A("Select a File")],
                            id="ap-upload-data-filename",
                        ),
                        style={
                            "width": "50%",
                            "height": "60px",
                            "lineHeight": "60px",
                            "borderWidth": "1px",
                            "borderStyle": "dashed",
                            "borderRadius": "5px",
                            "textAlign": "center",
                            "marginTop": "10px",
                            "marginBottom": "10px",
                        },
                        multiple=False,  # Only allow one file to be uploaded
                    ),
                    # autoparser settings
                    dbc.Checklist(
                        id="autoparser-settings",
                        options=[
                            {"label": "Generate descriptions with LLM", "value": 1},
                        ],
                        value=[1],  # list of 'value's that are 'on' by default
                        inline=True,
                        switch=True,
                        style={"margin": "10px"},
                    ),
                    # Parse Button to start file parsing
                    dbc.Button(
                        children=["Create Dictionary"],
                        id="make-dict-button",
                        n_clicks=0,
                    ),
                ],
                id="autoparser-file-settings",
                style={"display": "block"},
            ),
            # DataTable for editing
            dcc.Loading(
                type="default",
                children=[
                    dash_table.DataTable(
                        id="editable-ap-table",
                        columns=[],
                        data=[],
                        editable=True,
                        hidden_columns=[],
                        column_selectable=None,
                        style_data_conditional=[
                            {  # Highlight the selected cell
                                "if": {"state": "active"},
                                "backgroundColor": "lightblue",
                                "border": "1px solid blue",
                                "color": "black",
                            },
                            {  # Mark the 'Row' column in light grey
                                "if": {"column_id": "Row"},
                                "backgroundColor": "#F0F0F0",
                                "color": "#A0A0A0",
                            },
                        ],
                        css=[
                            {  # Hide the annoying `Toggle Columns` button
                                "selector": ".show-hide",
                                "rule": "display: none",
                            },
                        ],
                        tooltip_data=[],
                        page_size=25,
                        style_table={
                            "minWidth": "100%",  # Format fix for freezing first column
                            "min-height": "300px",
                            "overflowY": "auto",
                        },
                        # Freeze 'Row' and first data (either field name or target_field) columns # noqa
                        fixed_columns={
                            "headers": True,
                            "data": 2,
                        },
                    ),
                ],
                style={
                    "position": "absolute",
                    "top": 0,
                    "z-index": 9999,
                },
                color="var(--bs-primary)",
            ),
            html.Div(
                [
                    html.Label("Fields per page:"),
                    dcc.Dropdown(
                        id="fields-dropdown",
                        options=[
                            {"label": "10", "value": 10},
                            {"label": "25", "value": 25},
                            {"label": "50", "value": 50},
                            {"label": "100", "value": 100},
                            {"label": "All", "value": 250},
                        ],
                        value=25,
                        clearable=False,
                        style={"width": "80px", "margin": "10px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-end",
                },
            ),
            # Buttons for row operations (on the next line)
            html.Div(id="data-dict-stats"),
            html.Div(id="parser-output"),
            html.Div(
                id="ap-bottom-controls",
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "alignItems": "center",  # Vertically align items
                },
            ),
            dcc.ConfirmDialog(id="confirm-parser-dialog", message=""),
            html.Hr(),
        ],
        style={"width": "100%"},
    )


@callback(
    Output("schema-dropdown", "options"),  # Update schema dropdown options
    Input("project", "data"),  # Triggered by project selection in navbar
)
def update_schema_dropdown(project):
    """
    Fills in the list of options for the schema dropdown based on the selected project.
    """
    if project:
        global projectObj
        projectObj = utils.get_project(project)
        schemas = projectObj.get_project_schemas()
        return list(sorted([schema["label"] for schema in schemas]))
    return []


@callback(
    Output("ap-upload-data-filename", "children"),  # Update the filename display
    Output("ap-upload-data", "style"),
    Input("ap-upload-data", "filename"),  # Triggered by file selection
    State("ap-upload-data", "style"),
)
def update_filename(filename, style):
    """
    Updates the data upload box to display the selected file name
    """
    if filename:
        update_styles = {
            "borderStyle": "solid",
            "borderWidth": "2px",
        }
        return f"Selected file: {filename}", {**style, **update_styles}
    update_styles = {
        "borderStyle": "dashed",
        "borderWidth": "1px",
    }
    return "Select a data file", {**style, **update_styles}


# Update state when settings are changed: Generate-descriptions-with-LLM
@callback(
    Output(
        "generate-descriptions-with-llm", "value"
    ),  # Update 'only show errors' setting
    Input("autoparser-settings", "value"),  # Triggered by settings switch changes
)
def update_llm_descriptions(value):
    return 1 in value


@callback(Input("llm-choice", "value"))
def update_llm_choice(value):
    if autoParser is not None:
        autoParser.model = value


@callback(Input("api-key", "value"))
def update_api_key(value):
    if autoParser is not None:
        autoParser.api_key = value


# Update page size of the DataTable based on dropdown selection
@callback(
    Output("editable-ap-table", "page_size"),  # Update the DataTable page size
    Input("fields-dropdown", "value"),  # Triggered by 'rows per page' dropdown
)
def update_page_size(page_size):
    return page_size


@callback(
    Output("editable-ap-table", "columns"),  # Update DataTable
    Output("editable-ap-table", "data"),
    Output("editable-ap-table", "active_cell"),
    Output("data-dict-stats", "children"),
    # in the original code, this is the table ID so if there are multiple data tables
    # the dropdown allows the viewable data to change.
    # However if I delete this line, the table does not update.
    # It's inadvertently updating the table when the data updates after calling
    # autoparser.
    Input("parser-id", "data"),
    Input("editable-ap-table", "active_cell"),
    State("ap-output-store", "data"),
    State("edited-ap-output-store", "data"),
)
def update_table(
    parser_id,
    active_cell,
    autoparser_data,
    edited_ap_data,
):
    """
    Updates the data being displayed in the editable table.
    Triggered by changes in the parser_id, or by the user selecting a cell.
    """
    data = edited_ap_data
    if not data:
        # Callback is triggered before edited_datasets is populated on first run
        data = autoparser_data
    if not data:
        raise dash.exceptions.PreventUpdate

    if autoparser_data and (data[0].keys() != autoparser_data[0].keys()):
        # on the second loop, force the data to be the mapping file
        data = autoparser_data

    ctx = dash.callback_context
    trig_active_cell = ctx_trigger(ctx, "editable-ap-table.active_cell")

    # The only active cell we want to respond to is the delete button
    if trig_active_cell and active_cell:
        raise dash.exceptions.PreventUpdate

    data_stats = f"Total fields: {len(data)}"

    keys = next(iter(data)).keys()
    columns = [{"name": col, "id": col, "editable": True} for col in keys]

    # Move 'Row' column to the front
    columns = [
        {"name": "Row", "id": "Row", "editable": False},
        *[col for col in columns if col["id"] not in ["Row"]],
    ]

    return columns, data, active_cell, data_stats


@callback(
    Output("edited-ap-output-store", "data"),  # Update the edited data store
    Output("edited-unmapped-fields", "data"),  # Update the missing fields store
    Input("ap-output-store", "data"),  # Triggered by new autoparser data ...
    Input("editable-ap-table", "data"),  # ... or DataTable edits
    State("edited-ap-output-store", "data"),  # PL: still right?
    State("unmapped-fields", "data"),
    State("edited-unmapped-fields", "data"),
)
def update_edited_data(
    parsed_data,
    edited_table_data,
    datasets,
    unmapped_fields,
    edited_unmapped_fields,
):
    """
    Updates the stored data and missing fields list with any changes made in the
    DataTable, or by the table first being populated.
    Triggered by new data from the autoparser (parse_file_to_data_dict or
    map_data_dict_to_schema), or by changes in the DataTable.
    """
    new_edited_data_store = parsed_data
    if not new_edited_data_store:
        raise dash.exceptions.PreventUpdate

    # Merge full data with edited data based on Row number
    full_edited_data = new_edited_data_store
    for row in edited_table_data:
        row_idx = row.get("Row", None)
        if row_idx:
            full_edited_data[row_idx - 1] = row

    if unmapped_fields or edited_unmapped_fields:
        # Check for missing fields that have been added in by user

        missing_fields = edited_unmapped_fields or unmapped_fields
        for i, row in enumerate(full_edited_data):
            idx = row["Row"] - 1
            if row["source_field"] is not None and missing_fields[idx] is not None:
                missing_fields[idx] = []
    else:
        missing_fields = []

    return full_edited_data, missing_fields


def ctx_trigger(ctx, event):
    return any(k["prop_id"] == event for k in ctx.triggered)


@callback(
    Output("autoparser-messages", "children", allow_duplicate=True),  # Output message
    Output(
        "ap-output-store", "data", allow_duplicate=True
    ),  # Update autoparser data store,
    Output("parser-id", "data", allow_duplicate=True),
    Output(
        "autoparser-file-settings", "style", allow_duplicate=True
    ),  # ... GUI elements
    Output("ap-bottom-controls", "children", allow_duplicate=True),  # ... GUI elements
    Input("make-dict-button", "n_clicks"),  # Triggered by 'Create Dict' button click ..
    State("project", "data"),
    State("ap-upload-data", "contents"),
    State("ap-upload-data", "filename"),
    State("schema-dropdown", "value"),
    State("api-key", "value"),
    State("llm-choice", "value"),
    State("generate-descriptions-with-llm", "value"),
    State("data-language", "value"),
    running=[
        (
            Output("make-dict-button", "children"),
            [dbc.Spinner(size="sm"), " Creating Dictionary..."],
            "Create Dictionary",
        ),
        (
            Output("make-dict-button", "disabled"),
            True,
            False,
        ),
    ],
    prevent_initial_call=True,
)
def parse_file_to_data_dict(
    parse_n_clicks,
    project,
    contents,
    filename,
    schema,
    api_key,
    llm_choice,
    llm_descriptions,
    language,
):
    """
    Calls the autoparser 'create_dict' function when the 'Create Dictionary' button is
    clicked.

    Returns
    ----------------
    message: str|dbc.Alert
    dictionary: list[dict]|None
    parser_id: list[None]
    autoparser dictionary settings style: dict[str]
    bottom_controls: list
    """
    if not parse_n_clicks:
        return (
            "",
            None,
            [],
            {"display": "block"},
            [],
        )
    ctx = dash.callback_context
    trig_parse_btn = ctx_trigger(ctx, "make-dict-button.n_clicks")
    # Generate a data dictionary
    if trig_parse_btn:
        msg, data_dict, rtn = parse_data_to_dict(
            project,
            contents,
            filename,
            schema,
            api_key,
            llm_choice,
            llm_descriptions,
            language,
        )
        if data_dict:
            # Update the table dropdown
            return (
                msg,
                data_dict,
                rtn,
                {"display": "none"},
                bottom_buttons_data_dict,
            )
        else:
            # If there was an error, return the error message
            return (
                msg,
                data_dict,
                rtn,
                {"display": "block"},
                [],
            )


# Parse the select data file when "Parse" button is pressed
@callback(
    Output("autoparser-messages", "children", allow_duplicate=True),  # Output message
    Output(
        "ap-output-store", "data", allow_duplicate=True
    ),  # Update autoparser data store,
    Output("unmapped-fields", "data"),  # unmapped fields, and ...
    Output("parser-id", "data", allow_duplicate=True),
    Output(
        "autoparser-file-settings", "style", allow_duplicate=True
    ),  # ... GUI elements
    Output("ap-bottom-controls", "children", allow_duplicate=True),  # ... GUI elements
    Input("mapping-button", "n_clicks"),  # ... or 'Confirm & Continue' button click
    State("ap-upload-data", "filename"),
    State("schema-dropdown", "value"),
    State("edited-ap-output-store", "data"),
    State("data-language", "value"),
    running=[
        (
            Output("mapping-button", "children"),
            [dbc.Spinner(size="sm"), " Mapping dictionary to schema..."],
            "Create Mapping File",
        ),
        (
            Output("mapping-button", "disabled"),
            True,
            False,
        ),
    ],
    prevent_initial_call=True,
)
def map_data_dict_to_schema(
    map_n_clicks,
    filename,
    schema,
    edited_data_store,
    language,
):
    if not map_n_clicks:
        raise dash.exceptions.PreventUpdate

    ctx = dash.callback_context
    trig_mapping_btn = ctx_trigger(ctx, "mapping-button.n_clicks")

    # Generate a mapping file
    if trig_mapping_btn:
        msg, mapping, errors, rtn = dict_to_mapping_file(
            edited_data_store,
            filename,
            schema,
            language,
        )
        if mapping:
            # Update the table dropdown
            return (
                msg,
                mapping,
                errors,
                rtn,
                {"display": "none"},
                bottom_buttons_mapping,
            )
        else:
            # If there was an error, return the error message
            return (
                msg,
                mapping,
                [],
                rtn,
                {"display": "none"},
                bottom_buttons_data_dict,
            )


# Utility function to read and parse a data file
def parse_data_to_dict(
    project,
    contents,
    filename: str,
    schema: str,
    key: str,
    llm: Literal["openai", "gemini"],
    llm_descriptions: bool,
    language: Literal["fr", "en"],
):
    """
    Utility function to create, then call the autoParser class

    Returns
    message, dictionary, schema name
    """

    if not contents or not schema:
        return (
            dbc.Alert(
                "Please select both a schema, and a data file to use.",
                color="warning",
            ),
            None,
            "",
        )

    # Process the uploaded file
    try:
        projectObj = utils.get_project(project)
        # 'schema' is <table>.schema
        table = schema.split(".")[0]
        schema_file = projectObj.get_schema(table)
        schema_path = projectObj.get_schemas_folder()

        global autoParser
        autoParser = utils.get_autoparser(llm, key, schema_file, table, schema_path)

        ready, msg = autoParser.is_autoparser_ready
        if not ready:
            return (
                dbc.Alert(msg, color="warning"),
                None,
                "",
            )

        data_dict_frame = autoParser.create_dict(
            filename, contents, llm_descriptions, language
        )

        # Dash cannot store DataFrames directly, so convert them to dictionaries
        data_dict = data_dict_frame.to_dict("records")

        # Populate 'Row' and '_delete' columns
        for i, row in enumerate(data_dict):
            row["Row"] = i + 1

        return (
            dbc.Alert(
                f"Data dictionary for file '{filename}' created successfully.\n"
                "Please check this carefully, and once you are satisfied click 'Create Mapping File'.",  # noqa
                color="success",
            ),
            data_dict,
            schema,
        )

    except Exception as e:
        return (
            dbc.Alert(
                f"There was an error processing the file: {str(e)}. ",
                color="danger",
            ),
            None,
            "",
        )


def dict_to_mapping_file(
    contents, filename: str, schema: str, language: str
) -> tuple[dbc.Alert, list[dict] | None, list, str]:
    """
    Returns
    message, dictionary, missing fields, file name string
    """

    try:
        mapping_frame, missing_fields = autoParser.create_mapping(contents, language)
        mapping_frame.reset_index(inplace=True)

        # Dash cannot store DataFrames directly, so convert them to dictionaries
        mapping = mapping_frame.to_dict("records")

        # Populate 'Row' and '_delete' columns
        for i, row in enumerate(mapping):
            row["Row"] = i + 1

        return (
            dbc.Alert(
                f"Mapping for file '{filename}' created successfully.\n"
                "Please check this carefully, and once you are satisfied define the parser name and click 'Generate Parser'.",  # noqa
                color="success",
            ),
            mapping,
            missing_fields,
            schema,
        )

    except Exception as e:
        return (
            dbc.Alert(
                f"There was an error while mapping: {e}. ",
                color="danger",
            ),
            None,
            [],
            "",
        )


# Apply table highlights and tooltips to show changes
def highlight_and_tooltip_changes(
    data,
    page_current,
    page_size,
    missing_fields,
) -> tuple[list[dict | None], list[dict | None]]:
    """Highlight missing fields and show tooltips."""
    if not page_size:
        return []
    page_current = page_current or 0

    start_idx = page_current * page_size
    end_idx = (page_current + 1) * page_size

    # Default higlights
    style_data_conditional = [
        {  # Highlight the selected cell
            "if": {"state": "active"},
            "backgroundColor": "lightblue",
            "border": "1px solid blue",
            "color": "black",
        },
        {  # Mark the 'Row' column in light grey
            "if": {"column_id": "Row"},
            "backgroundColor": "#F0F0F0",
            "color": "#A0A0A0",
        },
    ]
    keys = next(iter(data)).keys()
    data_cols = [k for k in keys if k not in ["Row"]]

    error_rows = []

    # Iterate over each row in the modified data
    try:
        # Ensure rows with errors are highlighted before placing cell-level highlights
        if missing_fields:
            for i, row in enumerate(data[start_idx:end_idx]):
                idx = row["Row"] - 1
                errors = missing_fields[idx]
                if any(errors):
                    error_rows.append(idx + 1)
            if error_rows:
                style_data_conditional.append(
                    {
                        "if": {
                            "filter_query": " || ".join(
                                [f"{{Row}} = {k}" for k in error_rows]
                            ),
                        },
                        "backgroundColor": "#FFCCCC",
                        "color": "black",
                    }
                )

        for i, row in enumerate(data[start_idx:end_idx]):
            idx = row["Row"] - 1
            errors = missing_fields[idx] if missing_fields else []
            # Show validation errors per cell
            for error in errors:
                if error["path"] in data_cols:
                    if len(style_data_conditional) <= MAX_CONDITIONAL_FORMATTING:
                        style_data_conditional.append(
                            {
                                "if": {
                                    "filter_query": f"{{Row}} = {idx + 1}",
                                    "column_id": error["path"],
                                },
                                "border": "2px solid red",
                            }
                        )

    except Exception as e:
        # Callback can sometimes be called on stale data causing key errors
        logging.error(f"Error in highlight_and_tooltip_changes: {str(e)}")
        return []

    return style_data_conditional


# Update the table style and tooltips based on missing fields
@callback(
    Output("editable-ap-table", "style_data_conditional"),  # Update the table style ...
    Input("editable-ap-table", "data"),  # Triggered by any change in the table data ...
    Input("editable-ap-table", "page_current"),
    Input("editable-ap-table", "page_size"),
    State("unmapped-fields", "data"),
    State("edited-unmapped-fields", "data"),
)
def update_table_style_and_validate(
    data,
    page_current,
    page_size,
    missing_fields,
    edited_missing_fields,
):
    """
    Updates the row highlighting and tooltips (text that shows when you hover) in the
    editable table.
    Triggered by changes in the table data, the page showing or the page size.
    """

    if not data:
        return []

    # Highlight changes and create tooltips showing original data
    style_data_conditional = highlight_and_tooltip_changes(
        data,
        page_current,
        page_size,
        edited_missing_fields or missing_fields,
    )

    return style_data_conditional


# Downloading Data Dict as CSV
@callback(
    Output("download-dict-csv", "data"),  # Download the CSV file
    Input("download-dict-button", "n_clicks"),  # Triggered by 'Download as CSV' button
    State("editable-ap-table", "data"),
    prevent_initial_call=True,  # Only trigger when the button is clicked
)
def download_dict_csv(n_clicks, data):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        df.drop(columns=["Row"], inplace=True)
        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"data_dict_{datetime_str}.csv"
        return dcc.send_data_frame(df.to_csv, filename, index=False)


# Downloading Mapping file as CSV
@callback(
    Output("download-mapping-csv", "data"),  # Download the CSV file
    Input("download-mapping-button", "n_clicks"),
    State("editable-ap-table", "data"),
    prevent_initial_call=True,  # Only trigger when the button is clicked
)
def download_mapping_csv(n_clicks, data):
    """
    Download the mapping file as a csv if 'Download as CSV' button is clicked
    """
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        df.drop(columns=["Row"], inplace=True)
        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"mapping_file_{datetime_str}.csv"
        return dcc.send_data_frame(df.to_csv, filename, index=False)


@callback(
    Output("confirm-parser-dialog", "displayed"),  # Show the dialog
    Output("confirm-parser-dialog", "message"),
    Input("make-parser-button", "n_clicks"),  # Triggered by 'Commit' button click
    State("ap-upload-data", "filename"),
    State("schema-dropdown", "value"),
    State("parser-name", "value"),
)
def display_parser_dialog(n_clicks, data_file_name, schema_name, parser_name):
    """
    Display a confirmation dialog when the 'generate parser' button is clicked
    """
    if n_clicks > 0:
        return True, (
            "You are about to write a parser for the following data file and schema:\n"
            f"Data: {data_file_name}\nSchema: {schema_name}\n"
            f"Parser Name: {parser_name}\n\nWrite parser now?"
        )
    return False, ""


# Write a new parser
@callback(
    Output("parser-output", "children"),  # Update the commit output message ...
    Input("confirm-parser-dialog", "submit_n_clicks"),  # Triggered by 'Confirm' dialog
    State("parser-name", "value"),  # Parser name
    State("project", "data"),
    State("edited-ap-output-store", "data"),
    prevent_initial_call=True,
)
def write_a_parser(
    submit_n_clicks: int, parser_name: str, project: str, datasets: list[dict]
) -> str | dbc.Alert:
    """
    Triggers autoparser to genenerate a parser based on the mapping file being shown
    after the 'confirm' dialoge triggered by clicking the 'generate parser' button.
    Outputs a confirmation message or error alert.
    """
    if submit_n_clicks and project and datasets:
        try:
            parser_folder = projectObj.get_parsers_folder()

            autoParser.create_parser(datasets, parser_folder, name=parser_name)

            return dbc.Alert(f"Parser '{parser_name}.toml' generated.", color="success")
        except Exception as e:
            logging.error(f"Error writing the parser: {str(e)}")
            logging.error(traceback.format_exc())
            return dbc.Alert(f"Error writing the parser: {str(e)}", color="danger")

    return "No parser written yet."


# TODO:
# * Add ability to upload your own data dictionary (use arcmapper as a guide)

# *on autoparser side: throw recognisable error if a source_field is not found in the
# data (prob typed incorrectly by the user)
