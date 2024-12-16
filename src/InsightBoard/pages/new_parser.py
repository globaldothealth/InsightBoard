import logging
import math
import traceback
from datetime import datetime
from pathlib import Path

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
from InsightBoard.database import WritePolicy

# DataTable supports a maximum of 512 conditional formatting rules,
#  so stop adding rules after this limit is reached
MAX_CONDITIONAL_FORMATTING = 512

# Due to formatting constraints we store the _delete column (which doubles as a button)
# as a string
_DELETE_COLUMN = "_delete"
_DELETE_TRUE = "↺"
_DELETE_FALSE = "✖"

# Register the page
dash.register_page(__name__, path="/new_parser")
projectObj = None


def layout():
    return html.Div(
        [
            # Store
            dcc.Store(id="project"),  # project selection
            dcc.Store(id="parser-id"),  # unique id (project-table)
            dcc.Store(id="data-dict-store"),  # parsed data dict (multi-table support)
            dcc.Store(id="edited-dict-store"),  # edited data dict (multi-table support)
            dcc.Store(
                id="generate-descriptions-with-llm"
            ),  # Setting: use LLm to generate descriptions
            # dcc.Store(id="show-full-validation-log"),  # Setting: Show full log
            # dcc.Store(id="update-existing-records"),  # Setting: Update records
            # Page rendering
            html.H1("Create a new parser"),
            # dcc.Location(id="url-refresh", refresh=True),
            html.Div(id="autoparser-upload-data"),
            html.Div(
                [
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
                    dbc.Col(
                        [
                            # API key input
                            dcc.Input(
                                id="api-key",
                                type="password",
                                placeholder="API Key",
                                value=None,
                            ),
                            # Choose LLM
                            dcc.RadioItems(
                                ["openai", "google"], "openai", id="llm-choice"
                            ),
                            # Set data language
                            dcc.RadioItems(["fr", "en"], "fr", id="data-language"),
                        ],
                        width=6,
                    ),
                    # autoparser settings
                    dbc.Checklist(
                        id="autoparser-settings",
                        options=[
                            {"label": "Generate descriptions with LLM", "value": 1},
                            # {"label": "Show full validation log", "value": 2},
                            # {"label": "Update existing records", "value": 3},
                        ],
                        value=[1],  # list of 'value's that are 'on' by default
                        inline=True,
                        switch=True,
                        style={"margin": "10px"},
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
                    # Parse Button to start file parsing
                    dbc.Button("Create Dictionary", id="make-dict-button", n_clicks=0),
                ],
                id="autoparser-file-settings",
                style={"display": "block"},
            ),
            #         html.Div(
            #             [
            #                 dbc.Button("Close File", id="close-button", n_clicks=0),
            #                 # Dropdown for imported tables
            #                 dcc.Dropdown(
            #                     id="imported-tables-dropdown",
            #                     options=[],
            #                     placeholder="Select a table",
            #                     clearable=False,
            #                     style={"float": "right", "width": "50%"},
            #                 ),
            #             ],
            #             id="close-settings",
            #             style={"display": "none"},
            #         ),
            # DataTable for editing
            dcc.Loading(
                type="default",
                children=[
                    dash_table.DataTable(
                        id="editable-data-dict",
                        columns=[],
                        data=[],
                        editable=True,
                        hidden_columns=[],
                        column_selectable=None,
                        style_data_conditional=[],
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
                        # Freeze 'delete' and 'Row' columns
                        fixed_columns={
                            "headers": True,
                            "data": 2,
                        },
                        style_header_conditional=[
                            {
                                "if": {"column_id": _DELETE_COLUMN},
                                "color": "transparent",
                            },
                        ],
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
                            {"label": "250", "value": 250},
                            {"label": "500", "value": 500},
                            {"label": "1000", "value": 1000},
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
            # html.Div(id="commit-output"),
            html.Div(
                [
                    dbc.Button(
                        "Confirm & continue",
                        id="confirm-dict-button",
                        n_clicks=0,
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
                    # # Commit Button moved to the right-hand side
                    # dbc.Button(
                    #     "Commit to Database",
                    #     id="commit-button",
                    #     n_clicks=0,
                    #     style={
                    #         "float": "right",
                    #         "margin": "10px",
                    #         "verticalAlign": "middle",
                    #     },
                    # ),
                ]
            ),
            #         dcc.ConfirmDialog(id="confirm-commit-dialog", message=""),
            html.Hr(),
            #         html.Div(id="output-container"),
        ],
        style={"width": "100%"},
    )


# # Force reload of the page
# @callback(
#     Output("url-refresh", "href"),  # Refresh the page
#     Input("close-button", "n_clicks"),  # Triggered by 'Close File' button
#     Input("project", "data"),  # Triggered by project selection in navbar
# )
# def refresh_url(n_clicks, project):
#     if n_clicks:
#         return "/upload"
#     raise dash.exceptions.PreventUpdate


# Update schema dropdown based on selected project
@callback(
    Output("schema-dropdown", "options"),  # Update schema dropdown options
    Input("project", "data"),  # Triggered by project selection in navbar
)
def update_schema_dropdown(project):
    if project:
        global projectObj
        projectObj = utils.get_project(project)
        schemas = projectObj.get_project_schemas()
        return list(sorted([schema["label"] for schema in schemas]))
    return []


# Display selected data file to user
@callback(
    Output("ap-upload-data-filename", "children"),  # Update the filename display
    Output("ap-upload-data", "style"),
    Input("ap-upload-data", "filename"),  # Triggered by file selection
    State("ap-upload-data", "style"),
)
def update_filename(filename, style):
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
def update_only_show_errors(value):
    return 1 in value


# # Update state when settings are changed: Update Existing Records
# @callback(
#     Output("update-existing-records", "value"),  # Update the 'update records' setting
#     Input("upload-settings", "value"),  # Triggered by settings switch changes
# )
# def update_update_existing_records(value):
#     return 3 in value


# Update page size of the DataTable based on dropdown selection
@callback(
    Output("editable-data-dict", "page_size"),  # Update the DataTable page size
    Input("fields-dropdown", "value"),  # Triggered by 'rows per page' dropdown
)
def update_page_size(page_size):
    return page_size


# When a table name is selected from the dropdown, update the DataTable display
@callback(
    Output("editable-data-dict", "columns"),  # Update DataTable
    # Output("editable-data-dict", "hidden_columns"),
    Output("editable-data-dict", "data"),
    Output("editable-data-dict", "active_cell"),
    Output("data-dict-stats", "children"),
    # Input("imported-tables-dropdown", "options"),  # Triggered by 'table' selection ...
    # Input("imported-tables-dropdown", "value"),
    Input("parser-id", "data"),
    Input("generate-descriptions-with-llm", "value"),
    # Input("update-existing-records", "value"),
    # Input("remove-empty-ids-button", "n_clicks"),
    # Input("remove-error-rows-button", "n_clicks"),
    # Input("restore-deleted-rows-button", "n_clicks"),
    Input("editable-data-dict", "active_cell"),
    State("project", "data"),
    # State("edited-dict-store", "data"),  # Populate with table from edited-data store
    State("data-dict-store", "data"),  # Populate with table from edited-data store
    # State("parsed-data-store", "data"),
    # State("validation-errors", "data"),
)
def update_table(
    # options,
    # selected_table,
    parser_id,
    # only_show_validation_errors,
    # update_existing_records,
    # remove_empty_ids_n_clicks,
    # remove_error_rows_n_clicks,
    # restore_deleted_rows_n_clicks,
    llm_descriptions,
    active_cell,
    project,
    edited_datasets,
    # parsed_datasets,
    # errors,
):
    # Callback is triggered before edited_datasets is populated on first run
    print("update table triggered")
    datasets = edited_datasets
    if not datasets:
        raise dash.exceptions.PreventUpdate

    ctx = dash.callback_context
    trig_active_cell = ctx_trigger(ctx, "editable-data-dict.active_cell")
    # trig_remove_empty_ids = ctx_trigger(ctx, "remove-empty-ids-button.n_clicks")
    # trig_remove_error_rows = ctx_trigger(ctx, "remove-error-rows-button.n_clicks")
    # trig_restore_deleted_rows = ctx_trigger(ctx, "restore-deleted-rows-button.n_clicks")

    # The only active cell we want to respond to is the delete button
    if (
        trig_active_cell
        and active_cell
        and not active_cell.get("column_id") == _DELETE_COLUMN
    ):
        raise dash.exceptions.PreventUpdate

    data = datasets

    # data = datasets[options.index(selected_table)]
    data_stats = f"Total fields: {len(data)}"
    # projectObj = utils.get_project(project)
    # primary_key = projectObj.database.get_primary_key(selected_table)

    # # Convert any lists to strings for display
    # data = clean_dataset(data, project, selected_table, lists_to_strings=True)
    keys = next(iter(data)).keys()
    columns = [{"name": col, "id": col, "editable": True} for col in keys]
    # columns = utils.ensure_schema_ordering(columns, project, selected_table)

    # # Respond to delete button clicks
    # if active_cell and active_cell.get("column_id") == _DELETE_COLUMN:
    #     i = active_cell.get("row")
    #     row = data[i]
    #     active_cell = False  # Permits the button to be clicked again straight away
    #     row[_DELETE_COLUMN] = (
    #         _DELETE_FALSE
    #         if row.get(_DELETE_COLUMN, _DELETE_FALSE) == _DELETE_TRUE
    #         else _DELETE_TRUE
    #     )

    # # Mark rows with errors for deletion
    # if trig_remove_error_rows:
    #     for row in data:
    #         i = row["Row"] - 1
    #         if any(errors[i]):
    #             row[_DELETE_COLUMN] = _DELETE_TRUE

    # # Restore deleted rows
    # if trig_restore_deleted_rows:
    #     for row in data:
    #         row[_DELETE_COLUMN] = _DELETE_FALSE

    # # Check how many visible rows are marked for deletion
    # deleted_rows = len(
    #     [row for row in data if row.get(_DELETE_COLUMN, _DELETE_FALSE) == _DELETE_TRUE]
    # )

    # Move columns '_delete' and 'Row' to the front
    columns = [
        {"name": _DELETE_COLUMN, "id": _DELETE_COLUMN, "editable": False},
        {"name": "Row", "id": "Row", "editable": False},
        *[col for col in columns if col["id"] not in [_DELETE_COLUMN, "Row"]],
    ]

    # hidden_columns = []
    # data_stats += f", Showing: {len(data)}"
    # if deleted_rows:
    #     data_stats += f", Deleted: {deleted_rows}"

    # return columns, hidden_columns, data, active_cell, data_stats
    return columns, data, active_cell, data_stats


# # Utility function to remove quotes from strings
# def remove_quotes(x):
#     if isinstance(x, str) and x.startswith('"') and x.endswith('"'):
#         return x[1:-1]
#     if isinstance(x, str) and x.startswith("'") and x.endswith("'"):
#         return x[1:-1]
#     return x


# # Utility function to clean data values, coercing to target type if specified
# def clean_value(x, key_name=None, dtypes={}):
#     """Clean a value, coercing to target type if specified.

#     The DataTable accepts mainly strings, so this function attempts to
#     coerce the value to the target type specified in the schema. If the value
#     cannot be coerced, it is returned as a string.

#     Params:
#         x (str): The value to clean.
#         key_name (str): The key name of the value in the dataset.
#         dtypes (dict): A dictionary of key names and target types.
#                (list): A list of target types.
#                "any": Any type is allowed.
#     """

#     # Target type can be not specified if, e.g. enum or 'Row' column
#     if isinstance(dtypes, str) and dtypes == "any":
#         target_types = [
#             "string",
#             "number",
#             "integer",
#             "boolean",
#             "array",
#             "object",
#             "null",
#         ]
#     elif isinstance(dtypes, dict):
#         target_types = dtypes.get(key_name, {}).get("type", None)
#         if not isinstance(target_types, list):
#             target_types = [target_types]
#     elif isinstance(dtypes, list):
#         target_types = dtypes
#     else:
#         target_types = []

#     # String pre-processing
#     if isinstance(x, str):
#         x = x.strip()

#     if "array" in target_types and isinstance(x, str):
#         if x.startswith("[") and x.endswith("]"):
#             return list(
#                 map(
#                     remove_quotes,
#                     map(lambda x: clean_value(x, None, "any"), x[1:-1].split(",")),
#                 )
#             )
#         elif isinstance(x, str) and "," in x:
#             return list(
#                 map(
#                     remove_quotes,
#                     map(lambda x: clean_value(x, None, "any"), x.split(",")),
#                 )
#             )

#     if "number" in target_types:
#         if isinstance(x, int) or isinstance(x, float):
#             return x
#         elif isinstance(x, str):
#             try:
#                 if "." in x:
#                     n = float(x)
#                     if math.isnan(n):
#                         return None
#                 else:
#                     n = int(x)
#                 return n
#             except Exception:
#                 pass

#     if "integer" in target_types:
#         if isinstance(x, int):
#             return x
#         elif isinstance(x, str):
#             try:
#                 return int(x)  # int cannot be nan
#             except Exception:
#                 pass

#     if "boolean" in target_types:
#         if isinstance(x, bool):
#             return x
#         elif isinstance(x, str):
#             try:
#                 if x.lower() in ["true", "false"]:
#                     return x.lower() == "true"
#             except Exception:
#                 pass

#     if "object" in target_types:
#         # Object is a valid json schema type, but not supported by DataTable
#         ...

#     if "null" in target_types and not x:
#         return None

#     # Return the original value if no coercion can be applied
#     return x


# # Utility function to clean a dataset
# def clean_dataset(dataset, project, selected_table, lists_to_strings=True):
#     projectObj = utils.get_project(project)
#     schema = projectObj.database.get_table_schema(selected_table)
#     for row in dataset:
#         for k, v in row.items():
#             row[k] = clean_value(v, k, schema["properties"])
#             if lists_to_strings and isinstance(row[k], list):
#                 row[k] = "[" + ", ".join([x for x in row[k] if x]) + "]"
#     return dataset


# When edits are made in the DataTable, update the edited-data-store
@callback(
    Output("edited-dict-store", "data"),  # Update the edited data store
    Input("data-dict-store", "data"),  # Triggered by new 'parsed data' ...
    Input("editable-data-dict", "data"),  # ... or DataTable edits
    State("project", "data"),
    # State("imported-tables-dropdown", "options"),
    # State("imported-tables-dropdown", "value"),
    State("edited-dict-store", "data"),
)
# def update_edited_data(
#     parsed_data, edited_table_data, project, tables, selected_table, datasets
# ):
def update_edited_data(parsed_data, edited_table_data, project, datasets):
    new_edited_data_store = parsed_data
    if not new_edited_data_store:
        raise dash.exceptions.PreventUpdate

    # Merge full data with edited data based on Row number
    full_edited_data = new_edited_data_store
    for row in edited_table_data:
        row_idx = row.get("Row", None)
        if row_idx:
            full_edited_data[row_idx - 1] = row

    return full_edited_data


# # Utility function to convert text to HTML for display
# def text_to_html(text: str) -> html.Div:
#     return html.Div(
#         [html.Pre(text, style={"white-space": "pre-wrap", "word-wrap": "break-word"})]
#     )


# # Display the validation error log
# @callback(
#     Output("output-container", "children"),  # Update the validation log display
#     Input("validation-errors", "data"),  # Triggered by any change in errors ...
#     Input("validation-warnings", "data"),  # ... or table view
#     Input("imported-tables-dropdown", "options"),
#     Input("imported-tables-dropdown", "value"),
#     Input("only-show-validation-errors", "value"),
#     Input("show-full-validation-log", "value"),
#     Input("editable-table", "page_current"),
#     Input("editable-table", "page_size"),
#     Input("editable-table", "data"),
#     State("parsed-data-store", "data"),
#     State("project", "data"),
# )
# def validate_log(
#     errors,
#     warns,
#     tables_list,
#     current_table,
#     only_show_validation_errors,
#     show_full_validation_log,
#     page_current,
#     page_size,
#     editable_data,
#     parsed_dbs_dict,
#     project,
# ):
#     if not errors and not warns:
#         return html.P("No validation errors.")

#     # Validate the data against the schema
#     parsed_errors = [
#         f"Row {idx + 1} - {errorlist_to_sentence(x)}" for idx, x in enumerate(errors)
#     ]
#     rows_with_errors = len([x for x in errors if x])
#     comment = []
#     start_idx = 0
#     end_idx = -1
#     if not show_full_validation_log:
#         page_current = page_current or 0
#         start_idx = page_current * page_size
#         end_idx = (page_current + 1) * page_size
#         if only_show_validation_errors:
#             # Determine indices from visible data
#             visible_data = editable_data[start_idx:end_idx]
#             start_idx = visible_data[0]["Row"] - 1
#             end_idx = visible_data[-1]["Row"]
#         errors = errors[start_idx:end_idx]
#         parsed_errors = parsed_errors[start_idx:end_idx]
#         comment.extend(
#             [
#                 html.Br(),
#                 html.I(
#                     "Only showing errors visible in table - "
#                     "Toggle 'Show full validation log' to view all",
#                 ),
#             ]
#         )
#     parsed_errors = [x for x, y in zip(parsed_errors, errors) if y]

#     # If a strict schema exists, validate against that too
#     parsed_warns = []
#     if warns:
#         parsed_warns = [
#             f"Row {idx + 1} - {errorlist_to_sentence(x)}"
#             for idx, x in enumerate(warns)
#             if x
#         ]

#     # Construct validation messages
#     if not rows_with_errors and not any(parsed_warns):
#         return html.P("Validation passed successfully.")
#     msg_errors = [
#         html.H3("Validation errors:", style={"color": "red"}),
#         html.P(
#             [
#                 f"Total rows with errors: {rows_with_errors}",
#                 *comment,
#             ],
#             style={"color": "red"},
#         ),
#         html.P(
#             text_to_html(error_report_message(parsed_errors)), style={"color": "red"}
#         ),
#     ]
#     msg_warns = []
#     if parsed_warns:
#         msg_warns = [
#             html.H3("Validation warnings:", style={"color": "orange"}),
#             html.P(
#                 text_to_html(error_report_message(parsed_warns)),
#                 style={"color": "orange"},
#             ),
#         ]

#     return html.Div([*msg_errors, *msg_warns])


def ctx_trigger(ctx, event):
    return any(k["prop_id"] == event for k in ctx.triggered)


# Parse the select data file when "Parse" button is pressed
@callback(
    Output("autoparser-upload-data", "children"),  # Update parsed data store and ...
    Output("data-dict-store", "data"),  # ... GUI elements
    # Output("imported-tables-dropdown", "options"),
    # Output("imported-tables-dropdown", "value"),
    Output("parser-id", "data"),
    Output("autoparser-file-settings", "style"),
    # Output("close-settings", "style"),
    Input("make-dict-button", "n_clicks"),  # Triggered by 'Parse' button click ...
    # Input("update-button", "n_clicks"),  # ... or 'Update' button click
    State("project", "data"),
    State("ap-upload-data", "contents"),
    State("ap-upload-data", "filename"),
    State("schema-dropdown", "value"),
    State("edited-dict-store", "data"),
    State("api-key", "value"),
    State("llm-choice", "value"),
    State("generate-descriptions-with-llm", "value"),
    State("data-language", "value"),
    # State("imported-tables-dropdown", "options"),
    # State("imported-tables-dropdown", "value"),
)
def parse_file_to_data_dict(
    parse_n_clicks,
    # update_n_clicks,
    project,
    contents,
    filename,
    schema,
    edited_data_store,
    api_key,
    llm_choice,
    llm_descriptions,
    language,
    # tables_list,
    # selected_table,
):
    # if not parse_n_clicks and not update_n_clicks:
    if not parse_n_clicks:
        return (
            "Please select a schema and file to parse.",
            None,
            [],
            {"display": "block"},
            # {"display": "none"},
        )
    ctx = dash.callback_context
    trig_parse_btn = ctx_trigger(ctx, "make-dict-button.n_clicks")
    # trig_update_btn = ctx_trigger(ctx, "update-button.n_clicks")
    # Parse the data (read from files)
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
                # {"display": "block"},
            )
        else:
            # If there was an error, return the error message
            return (
                msg,
                data_dict,
                rtn,
                {"display": "block"},
                # {"display": "none"},
            )
    # # Update the data (make the current 'edited' buffer the new 'parsed' buffer)
    # if trig_update_btn:
    #     return (
    #         "Validation run.",
    #         edited_data_store,  # move edited data into parsed data store
    #         tables_list,  # pass-through
    #         selected_table,  # pass-through
    #         f"{project}-{selected_table}",
    #         {"display": "none"},
    #         {"display": "block"},
    #     )


# Utility function to read and parse a data file
def parse_data_to_dict(
    project, contents, filename, schema, key, llm, llm_descriptions, language
):
    """
    Returns
    message, dictionary, schema name, file name string
    """

    if not contents or not schema:
        return (
            "Please select a schema, and file to use.",
            None,
            # [],
            "",
        )

    # Process the uploaded file
    try:
        projectObj = utils.get_project(project)
        # schema name is <table>.schema
        schema_file = projectObj.get_schema(schema.split(".")[0])
        data_dict_frame = projectObj.create_data_dict(
            filename, contents, schema_file, key, llm, llm_descriptions, language
        )

        # Dash cannot store DataFrames directly, so convert them to dictionaries
        data_dict = data_dict_frame.to_dict("records")

        # Populate 'Row' and '_delete' columns
        for i, row in enumerate(data_dict):
            row["Row"] = i + 1
            row[_DELETE_COLUMN] = _DELETE_FALSE

        return (
            f"Data dictionary for file '{filename}' created successfully.",
            data_dict,
            schema,
            # f"{project}-{schema['name']}",
        )

    except Exception as e:
        return (
            dbc.Alert(
                f"There was an error processing the file: {str(e)}. ",
                color="danger",
            ),
            None,
            # [],
            "",
        )


# # Apply table highlights and tooltips to show changes
# def highlight_and_tooltip_changes(
#     original_data,
#     data,
#     page_current,
#     page_size,
#     validation_errors,
#     only_show_validation_errors,
# ):
#     """Compare the original and edited data, highlight changes, and show tooltips."""
#     if not page_size:
#         return [], []
#     page_current = page_current or 0

#     paginate = not only_show_validation_errors
#     start_idx = page_current * page_size if paginate else 0
#     end_idx = (page_current + 1) * page_size if paginate else len(data)

#     # Default higlights
#     style_data_conditional = [
#         {  # Highlight the selected cell
#             "if": {"state": "active"},
#             "backgroundColor": "lightblue",
#             "border": "1px solid blue",
#             "color": "black",
#         },
#         {  # Mark the 'Row' column in light grey
#             "if": {"column_id": "Row"},
#             "backgroundColor": "#F0F0F0",
#             "color": "#A0A0A0",
#         },
#     ]
#     tooltip_data = [{} for _ in range(start_idx)]
#     keys = next(iter(data)).keys()
#     data_cols = [k for k in keys if k not in ["Row", _DELETE_COLUMN]]

#     deleted_rows = []
#     error_rows = []

#     # Iterate over each row in the modified data
#     try:
#         # Ensure rows with errors are highlighted before placing cell-level highlights
#         for i, row in enumerate(data[start_idx:end_idx]):
#             idx = row["Row"] - 1
#             errors = validation_errors[idx]
#             # Check for deleted rows
#             if row[_DELETE_COLUMN] == _DELETE_TRUE:
#                 deleted_rows.append(idx + 1)
#             # Check for validation errors and highlight row
#             if any(errors) and row[_DELETE_COLUMN] == _DELETE_FALSE:
#                 error_rows.append(idx + 1)
#         if deleted_rows:
#             style_data_conditional.append(
#                 {
#                     "if": {
#                         "filter_query": " || ".join(
#                             [f"{{Row}} = {k}" for k in deleted_rows]
#                         ),
#                     },
#                     "backgroundColor": "#CCCCCC",
#                     "color": "#A0A0A0",
#                 }
#             )
#         if error_rows:
#             style_data_conditional.append(
#                 {
#                     "if": {
#                         "filter_query": " || ".join(
#                             [f"{{Row}} = {k}" for k in error_rows]
#                         ),
#                     },
#                     "backgroundColor": "#FFCCCC",
#                     "color": "black",
#                 }
#             )

#         for i, row in enumerate(data[start_idx:end_idx]):
#             row_tooltip = {}  # Store tooltips for the row
#             idx = row["Row"] - 1
#             errors = validation_errors[idx]
#             # Show validation errors per cell and show tooltip
#             for error in errors:
#                 if error["path"] in data_cols:
#                     if len(style_data_conditional) <= MAX_CONDITIONAL_FORMATTING:
#                         style_data_conditional.append(
#                             {
#                                 "if": {
#                                     "filter_query": f"{{Row}} = {idx + 1}",
#                                     "column_id": error["path"],
#                                 },
#                                 "border": "2px solid red",
#                             }
#                         )
#                     row_tooltip[error["path"]] = {
#                         "value": error["message"],
#                         "type": "text",
#                     }
#             else:
#                 # Then, if the cell values differ, highlight and add a tooltip
#                 for column in data_cols:
#                     original_value = original_data[idx].get(column, None)
#                     modified_value = row.get(column, None)
#                     if str(modified_value) != str(original_value):
#                         if len(style_data_conditional) <= MAX_CONDITIONAL_FORMATTING:
#                             style_data_conditional.append(
#                                 {
#                                     "if": {
#                                         "filter_query": f"{{Row}} = {idx + 1}",
#                                         "column_id": column,
#                                     },
#                                     "backgroundColor": "#FFDDC1",
#                                     "color": "black",
#                                 }
#                             )
#                         # Show original content as a tooltip
#                         row_tooltip[column] = {
#                             "value": f'Original: "{original_value}"',
#                             "type": "text",
#                         }
#             tooltip_data.append(row_tooltip)

#     except Exception as e:
#         # Callback can sometimes be called on stale data causing key errors
#         logging.error(f"Error in highlight_and_tooltip_changes: {str(e)}")
#         return [], []

#     return style_data_conditional, tooltip_data


# # Update the table style and tooltips based on validation errors
# @callback(
#     Output("editable-table", "style_data_conditional"),  # Update the table style ...
#     Output("editable-table", "tooltip_data"),  # ... and tooltips
#     Input("editable-table", "data"),  # Triggered by any change in the table data ...
#     Input("editable-table", "page_current"),
#     Input("editable-table", "page_size"),
#     Input("validation-errors", "data"),  # ... or validation errors
#     Input("only-show-validation-errors", "value"),
#     State("parsed-data-store", "data"),
#     State("imported-tables-dropdown", "options"),
#     State("imported-tables-dropdown", "value"),
# )
# def update_table_style_and_validate(
#     data,
#     page_current,
#     page_size,
#     validation_errors,
#     only_show_validation_errors,
#     original_data,
#     tables,
#     selected_table,
# ):
#     if not data:
#         return [], []

#     # Convert original data from dict to DataFrame
#     original_df = original_data[tables.index(selected_table)]

#     # Highlight changes and create tooltips showing original data
#     style_data_conditional, tooltip_data = highlight_and_tooltip_changes(
#         original_df,
#         data,
#         page_current,
#         page_size,
#         validation_errors,
#         only_show_validation_errors,
#     )

#     return style_data_conditional, tooltip_data


# # Downloading DataTable as CSV
# @callback(
#     Output("download-csv", "data"),  # Download the CSV file
#     Input("download-button", "n_clicks"),  # Triggered by 'Download as CSV' button
#     State("editable-table", "data"),
#     State("imported-tables-dropdown", "value"),
#     prevent_initial_call=True,  # Only trigger when the button is clicked
# )
# def download_csv(n_clicks, data, table_name):
#     if n_clicks > 0 and data:
#         df = pd.DataFrame(data)
#         df = df[df[_DELETE_COLUMN] == _DELETE_FALSE]
#         df.drop(columns=["Row", _DELETE_COLUMN], inplace=True)
#         now = datetime.now()
#         datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
#         filename = f"import_{table_name}_{datetime_str}.csv"
#         return dcc.send_data_frame(df.to_csv, filename, index=False)


# # Display a confirmation dialog when the commit button is clicked
# @callback(
#     Output("confirm-commit-dialog", "displayed"),  # Show the dialog
#     Output("confirm-commit-dialog", "message"),
#     Input("commit-button", "n_clicks"),  # Triggered by 'Commit' button click
#     State("imported-tables-dropdown", "options"),
# )
# def display_confirm_dialog(n_clicks, table_names):
#     if n_clicks > 0:
#         return True, (
#             "You are able to write data to the following tables:\n"
#             f"{', '.join([t for t in table_names])}\n\nCommit data now?"
#         )
#     return False, ""


# # Commit changes to the database
# @callback(
#     Output("commit-output", "children"),  # Update the commit output message ...
#     Input("confirm-commit-dialog", "submit_n_clicks"),  # Triggered by 'Confirm' dialog
#     State("project", "data"),
#     State("imported-tables-dropdown", "options"),
#     State("edited-data-store", "data"),
#     State("update-existing-records", "value"),
# )
# def commit_to_database(
#     submit_n_clicks, project, table_names, datasets, update_existing_records
# ):
#     if submit_n_clicks and project and table_names and datasets:
#         try:
#             projectObj.database.set_write_policy(
#                 WritePolicy.UPSERT if update_existing_records else WritePolicy.APPEND
#             )
#             # Remove _delete rows and ['Row', '_delete'] columns before committing
#             for i, table in enumerate(datasets):
#                 datasets[i] = [
#                     row for row in table if row[_DELETE_COLUMN] == _DELETE_FALSE
#                 ]
#                 datasets[i] = [
#                     {k: v for k, v in row.items() if k not in ["Row", _DELETE_COLUMN]}
#                     for row in datasets[i]
#                 ]
#             projectObj.database.commit_tables_dict(table_names, datasets)
#             return dbc.Alert("Data committed to database.", color="success")
#         except Exception as e:
#             logging.error(f"Error committing data to database: {str(e)}")
#             logging.error(traceback.format_exc())
#             return dbc.Alert(f"Error committing data to file: {str(e)}", color="danger")

#     return "No data committed yet."
