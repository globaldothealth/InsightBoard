import math
import dash
import pandas as pd
import dash_bootstrap_components as dbc
import logging

from pathlib import Path
from datetime import datetime
from dash import dcc, html, dash_table, Input, Output, State, callback

import InsightBoard.utils as utils

# Register the page
dash.register_page(__name__, path="/upload")
projectObj = None


def layout():
    return html.Div(
        [
            # Store
            dcc.Store(id="project"),  # current project (from navbar)
            dcc.Store(id="unique-table-id"),  # unique id (project-table)
            dcc.Store(id="parsed-data-store"),  # parsed data (multi-table support)
            dcc.Store(id="edited-data-store"),  # edited data (multi-table support)
            dcc.Store(id="validation-errors"),  # validation errors (current table)
            dcc.Store(id="validation-warnings"),  # validation warnings (current table)
            dcc.Store(id="show-full-validation-log"),  # Setting: Show full log
            # Page rendering
            html.H1("Upload data"),
            dcc.Location(id="url-refresh", refresh=True),
            html.Div(id="output-upload-data"),
            html.Div(
                [
                    # Parser dropdown list (context-dependent on dataset)
                    dbc.Col(
                        dcc.Dropdown(
                            id="parser-dropdown",
                            options=[],
                            placeholder="Select a parser",
                            style={"width": "100%"},
                        ),
                        width=6,
                    ),
                    # Upload drop-space
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            ["Drag and Drop or ", html.A("Select a File")],
                            id="upload-data-filename",
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
                    dbc.Button("Parse File", id="parse-button", n_clicks=0),
                ],
                id="file-settings",
                style={"display": "block"},
            ),
            html.Div(
                [
                    dbc.Button("Close File", id="close-button", n_clicks=0),
                    # Dropdown for imported tables
                    dcc.Dropdown(
                        id="imported-tables-dropdown",
                        options=[],
                        placeholder="Select a table",
                        clearable=False,
                        style={"float": "right", "width": "50%"},
                    ),
                ],
                id="close-settings",
                style={"display": "none"},
            ),
            # DataTable for editing
            dcc.Loading(
                type="default",
                children=[
                    dash_table.DataTable(
                        id="editable-table",
                        columns=[],
                        data=[],
                        editable=True,
                        row_deletable=True,
                        style_data_conditional=[],
                        tooltip_data=[],
                        page_size=25,
                        style_table={
                            "minWidth": "100%",  # Format fix for freezing first column
                            "min-height": "300px",
                            "overflowY": "auto",
                        },
                        fixed_columns={
                            "headers": True,
                            "data": 1,
                        },  # Freeze first column
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
                    html.Label("Records per page:"),
                    dcc.Dropdown(
                        id="rows-dropdown",
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
            # Button for reparsing edited data
            dbc.Button("Revalidate", id="update-button", n_clicks=0),
            # Buttons for downloading CSV and committing changes
            dbc.Button(
                "Download as CSV",
                id="download-button",
                n_clicks=0,
                style={"margin": "10px"},
            ),
            dcc.Download(id="download-csv"),
            # Commit Button moved to the right-hand side
            dbc.Button(
                "Commit to Database",
                id="commit-button",
                n_clicks=0,
                disabled=True,
                style={"float": "right", "margin": "10px"},
            ),
            html.Div(id="commit-output"),
            dcc.ConfirmDialog(id="confirm-commit-dialog", message=""),
            dbc.Checklist(
                id="upload-settings",
                options=[
                    {"label": "Show full validation log", "value": 2},
                ],
                value=[],  # list of 'value's are are 'on', e.g. [2]
                inline=True,
                switch=True,
                style={"margin": "10px"},
            ),
            html.Hr(),
            html.Div(id="output-container"),
        ],
        style={"width": "100%"},
    )


# Force reload of the page
@callback(
    Output("url-refresh", "href"),  # Refresh the page
    Input("close-button", "n_clicks"),  # Triggered by 'Close File' button
)
def refresh_url(n_clicks):
    if n_clicks:
        return "/upload"
    return None


# Update parser dropdown based on selected project
@callback(
    Output("parser-dropdown", "options"),  # Update parser dropdown options
    Input("project", "data"),  # Triggered by project selection in navbar
)
def update_parser_dropdown(project):
    if project:
        global projectObj
        projectObj = utils.get_project(project)
        parsers = projectObj.get_project_parsers()
        return list(sorted([parser["label"] for parser in parsers]))
    return []


# Display selected data file to user
@callback(
    Output("upload-data-filename", "children"),  # Update the filename display
    Input("upload-data", "filename"),  # Triggered by file selection
)
def update_filename(filename):
    if filename:
        return f"Selected file: {filename}"
    return "Select a data file"


# Update state when settings are changed: Show Full Validation Log
@callback(
    Output("show-full-validation-log", "value"),  # Update the 'show full log' setting
    Input("upload-settings", "value"),  # Triggered by settings switch changes
)
def update_show_full_validation_log(value):
    return 2 in value


# Update page size of the DataTable based on dropdown selection
@callback(
    Output("editable-table", "page_size"),  # Update the DataTable page size
    Input("rows-dropdown", "value"),  # Triggered by 'rows per page' dropdown
)
def update_page_size(page_size):
    return page_size


# When a table name is selected from the dropdown, update the DataTable display
@callback(
    Output("editable-table", "columns"),  # Update DataTable
    Output("editable-table", "data"),
    Input("imported-tables-dropdown", "options"),  # Triggered by 'table' selection ...
    Input("imported-tables-dropdown", "value"),
    Input("unique-table-id", "data"),
    State("project", "data"),
    State("edited-data-store", "data"),  # Populate with table from edited-data store
    State("parsed-data-store", "data"),
)
def update_table(
    options, selected_table, unique_table_id, project, edited_datasets, parsed_datasets
):
    # Callback is triggered before edited_datasets is populated on first run
    datasets = edited_datasets
    if not datasets:
        datasets = parsed_datasets
    if not datasets:
        return [], []

    data = datasets[options.index(selected_table)]

    # Convert any lists to strings for display
    data = clean_dataset(data, project, selected_table, lists_to_strings=True)
    keys = next(iter(data)).keys()
    columns = [{"name": col, "id": col, "editable": True} for col in keys]
    columns = utils.ensure_schema_ordering(columns, project, selected_table)

    # Prepend non-editable 'Row' column
    columns.insert(0, {"name": "Row", "id": "Row", "editable": False})
    for i, row in enumerate(data):
        row["Row"] = i + 1

    return columns, data


# Utility function to remove quotes from strings
def remove_quotes(x):
    if isinstance(x, str) and x.startswith('"') and x.endswith('"'):
        return x[1:-1]
    if isinstance(x, str) and x.startswith("'") and x.endswith("'"):
        return x[1:-1]
    return x


# Utility function to clean data values, coercing to target type if specified
def clean_value(x, key_name=None, dtypes={}):
    """Clean a value, coercing to target type if specified.

    The DataTable accepts mainly strings, so this function attempts to
    coerce the value to the target type specified in the schema. If the value
    cannot be coerced, it is returned as a string.

    Params:
        x (str): The value to clean.
        key_name (str): The key name of the value in the dataset.
        dtypes (dict): A dictionary of key names and target types.
               (list): A list of target types.
               "any": Any type is allowed.
    """

    # Target type can be not specified if, e.g. enum or 'Rows' column
    if isinstance(dtypes, str) and dtypes == "any":
        target_types = [
            "string",
            "number",
            "integer",
            "boolean",
            "array",
            "object",
            "null",
        ]
    elif isinstance(dtypes, dict):
        target_types = dtypes.get(key_name, {}).get("type", None)
        if not isinstance(target_types, list):
            target_types = [target_types]
    elif isinstance(dtypes, list):
        target_types = dtypes
    else:
        target_types = []

    # String pre-processing
    if isinstance(x, str):
        x = x.strip()

    if "array" in target_types and isinstance(x, str):
        if x.startswith("[") and x.endswith("]"):
            return list(
                map(
                    remove_quotes,
                    map(lambda x: clean_value(x, None, "any"), x[1:-1].split(",")),
                )
            )
        elif isinstance(x, str) and "," in x:
            return list(
                map(
                    remove_quotes,
                    map(lambda x: clean_value(x, None, "any"), x.split(",")),
                )
            )

    if "number" in target_types:
        if isinstance(x, int) or isinstance(x, float):
            return x
        elif isinstance(x, str):
            try:
                if "." in x:
                    n = float(x)
                    if math.isnan(n):
                        return None
                else:
                    n = int(x)
                return n
            except Exception:
                pass

    if "integer" in target_types:
        if isinstance(x, int):
            return x
        elif isinstance(x, str):
            try:
                return int(x)  # int cannot be nan
            except Exception:
                pass

    if "boolean" in target_types and isinstance(x, str):
        try:
            if x.lower() in ["true", "false"]:
                return x.lower() == "true"
        except Exception:
            pass

    if "object" in target_types:
        # Object is a valid json schema type, but not supported by DataTable
        ...

    if "null" in target_types and not x:
        return None

    # Return the original value if no coercion can be applied
    return x


# Utility function to clean a dataset
def clean_dataset(dataset, project, selected_table, lists_to_strings=True):
    projectObj = utils.get_project(project)
    schema = projectObj.database.get_table_schema(selected_table)
    for row in dataset:
        for k, v in row.items():
            row[k] = clean_value(v, k, schema["properties"])
            if lists_to_strings and isinstance(row[k], list):
                row[k] = "[" + ", ".join([x for x in row[k] if x]) + "]"
    return dataset


# When edits are made in the DataTable, update the edited-data-store
@callback(
    Output("edited-data-store", "data"),  # Update the edited data store
    Input("parsed-data-store", "data"),  # Triggered by new 'parsed data' ...
    Input("editable-table", "data"),  # ... or DataTable edits
    State("project", "data"),
    State("imported-tables-dropdown", "options"),
    State("imported-tables-dropdown", "value"),
    State("edited-data-store", "data"),
)
def update_edited_data(
    parsed_data, edited_table_data, project, tables, selected_table, datasets
):
    ctx = dash.callback_context
    trig_parsed_data_store = ctx_trigger(ctx, "parsed-data-store.data")
    if trig_parsed_data_store:
        # Parsed data has changed, so reset to the newly parsed data
        new_edited_data_store = parsed_data
    else:
        # Otherwise, update to the latest table edits
        new_edited_data_store = datasets
    if not new_edited_data_store:
        return []

    # Remove the 'Row' column before saving
    for row in edited_table_data:
        row.pop("Row", None)
    # Clean data
    edited_table_data = clean_dataset(
        edited_table_data, project, selected_table, lists_to_strings=True
    )
    new_edited_data_store[tables.index(selected_table)] = edited_table_data
    return new_edited_data_store


# Utility function to format validation errors for display
def error_report_message(errors: []) -> str:
    # Expecting a list of string/None validation errors
    if not any(errors):
        return "No validation errors."
    errors = list(map(lambda s: s if s else "", errors))
    errors = "\n".join(errors)
    return errors


# Utility function to convert text to HTML for display
def text_to_html(text: str) -> html.Div:
    return html.Div(
        [html.Pre(text, style={"white-space": "pre-wrap", "word-wrap": "break-word"})]
    )


# Utility function to convert a list of errors to a sentence for display
def errorlist_to_sentence(errorlist: []) -> str:
    return "; ".join(
        [f"'{error['path']}': {error['message']}" for error in errorlist if error]
    )


# Utility function to convert schema validation errors to a serializable dictionary
def errors_to_dict(errors):
    return [
        [
            {
                "path": str(next(iter(x.path)) if x.path else ""),
                "message": str(x.message),
            }
            for x in error
        ]
        for error in errors
    ]


# Validate the stored data against a target schema
@callback(
    Output("validation-errors", "data"),  # Ouput error and warning data structures
    Output("validation-warnings", "data"),
    Input("parsed-data-store", "data"),  # Triggered by new parsed data ...
    Input("imported-tables-dropdown", "options"),  # ... or new 'table' selection
    Input("imported-tables-dropdown", "value"),
    State("project", "data"),
)
def validate_errors(
    parsed_dbs_dict,
    parsed_dbs,
    selected_table,
    project,
):
    if not parsed_dbs_dict:
        return [], []

    selected_table_index = parsed_dbs.index(selected_table)
    table_name = parsed_dbs[selected_table_index]
    df_dict = parsed_dbs_dict[selected_table_index]
    df_dict = clean_dataset(df_dict, project, selected_table, lists_to_strings=False)
    df = pd.DataFrame.from_records(df_dict)

    # Ensure that base schema file exists
    schema_file = Path(projectObj.get_schemas_folder()) / f"{table_name}.schema.json"
    if not schema_file.exists():
        return [], []

    # Check whether a relaxed schema file exists
    schema_file_relaxed = (
        Path(projectObj.get_schemas_folder()) / f"{table_name}.schema.relaxed.json"
    )
    if schema_file_relaxed.exists():
        # If a relaxed schema exists, use base schema as the strict / warning schema
        schema_file_strict = schema_file
    else:
        # If no relaxed schema exists, use base schema as the relaxed / error schema
        schema_file_relaxed = schema_file
        schema_file_strict = None

    # Validate the data against the schema
    df = df.where(pd.notnull(df), None)
    errors = errors_to_dict(utils.validate_against_jsonschema(df, schema_file_relaxed))

    # If a strict schema exists, validate against that too
    warns = []
    if schema_file_strict:
        schema_file_strict = (
            Path(projectObj.get_schemas_folder()) / f"{table_name}.schema.json"
        )
        warns = errors_to_dict(
            utils.validate_against_jsonschema(df, schema_file_strict)
        )

    return errors, warns


# Display the validation error log
@callback(
    Output("output-container", "children"),  # Update the validation log display
    Input("validation-errors", "data"),  # Triggered by any change in errors ...
    Input("validation-warnings", "data"),  # ... or table view
    Input("parsed-data-store", "data"),
    Input("imported-tables-dropdown", "options"),
    Input("imported-tables-dropdown", "value"),
    Input("show-full-validation-log", "value"),
    Input("editable-table", "page_current"),
    Input("editable-table", "page_size"),
    State("project", "data"),
)
def validate_log(
    errors,
    warns,
    parsed_dbs_dict,
    parsed_dbs,
    selected_table,
    show_full_validation_log,
    page_current,
    page_size,
    project,
):
    if not errors and not warns:
        return html.P("No validation errors.")

    # Validate the data against the schema
    parsed_errors = [
        f"Row {idx + 1} - {errorlist_to_sentence(x)}" for idx, x in enumerate(errors)
    ]
    rows_with_errors = len([x for x in errors if x])
    comment = []
    start_idx = 0
    end_idx = -1
    if not show_full_validation_log:
        page_current = page_current or 0
        start_idx = page_current * page_size
        end_idx = (page_current + 1) * page_size
        errors = errors[start_idx:end_idx]
        parsed_errors = parsed_errors[start_idx:end_idx]
        comment.extend(
            [
                html.Br(),
                html.I(
                    "Only showing errors visible in table - "
                    "Toggle 'Show full validation log' to view all",
                ),
            ]
        )
    parsed_errors = [x for x, y in zip(parsed_errors, errors) if y]

    # If a strict schema exists, validate against that too
    parsed_warns = []
    if warns:
        parsed_warns = [
            f"Row {idx + 1} - {errorlist_to_sentence(x)}"
            for idx, x in enumerate(warns)
            if x
        ]

    # Construct validation messages
    if not rows_with_errors and not any(parsed_warns):
        return html.P("Validation passed successfully.")
    msg_errors = [
        html.H3("Validation errors:", style={"color": "red"}),
        html.P(
            [
                f"Total rows with errors: {rows_with_errors}",
                *comment,
            ],
            style={"color": "red"},
        ),
        html.P(
            text_to_html(error_report_message(parsed_errors)), style={"color": "red"}
        ),
    ]
    msg_warns = []
    if parsed_warns:
        msg_warns = [
            html.H3("Validation warnings:", style={"color": "orange"}),
            html.P(
                text_to_html(error_report_message(parsed_warns)),
                style={"color": "orange"},
            ),
        ]

    return html.Div([*msg_errors, *msg_warns])


def ctx_trigger(ctx, event):
    return any(k["prop_id"] == event for k in ctx.triggered)


# Parse the select data file when "Parse" button is pressed
@callback(
    Output("output-upload-data", "children"),  # Update parsed data store and ...
    Output("parsed-data-store", "data"),  # ... GUI elements
    Output("imported-tables-dropdown", "options"),
    Output("imported-tables-dropdown", "value"),
    Output("unique-table-id", "data"),
    Output("file-settings", "style"),
    Output("close-settings", "style"),
    Input("parse-button", "n_clicks"),  # Triggered by 'Parse' button click ...
    Input("update-button", "n_clicks"),  # ... or 'Update' button click
    State("project", "data"),
    State("upload-data", "contents"),
    State("upload-data", "filename"),
    State("parser-dropdown", "value"),
    State("edited-data-store", "data"),
    State("imported-tables-dropdown", "options"),
    State("imported-tables-dropdown", "value"),
)
def parse_file(
    parse_n_clicks,
    update_n_clicks,
    project,
    contents,
    filename,
    selected_parser,
    edited_data_store,
    tables_list,
    selected_table,
):
    if not parse_n_clicks and not update_n_clicks:
        return (
            "Please select a parser and file to parse.",
            None,
            [],
            "",
            "",
            {"display": "block"},
            {"display": "none"},
        )
    ctx = dash.callback_context
    trig_parse_btn = ctx_trigger(ctx, "parse-button.n_clicks")
    trig_update_btn = ctx_trigger(ctx, "update-button.n_clicks")
    # Parse the data (read from files)
    if trig_parse_btn:
        msg, parsed_data_store, *rtn = parse_data(
            project, contents, filename, selected_parser
        )
        if parsed_data_store:
            # Update the table dropdown
            return (
                msg,
                parsed_data_store,
                *rtn,
                {"display": "none"},
                {"display": "block"},
            )
        else:
            # If there was an error, return the error message
            return (
                msg,
                parsed_data_store,
                *rtn,
                {"display": "block"},
                {"display": "none"},
            )
    # Update the data (make the current 'edited' buffer the new 'parsed' buffer)
    if trig_update_btn:
        return (
            "Validation run.",
            edited_data_store,  # move edited data into parsed data store
            tables_list,  # pass-through
            selected_table,  # pass-through
            f"{project}-{selected_table}",
            {"display": "none"},
            {"display": "block"},
        )


# Utility function to read and parse a data file
def parse_data(project, contents, filename, selected_parser):
    if not contents or not selected_parser:
        return (
            "Please select a parser, and file to parse.",
            None,
            [],
            "",
            "",
        )

    # Process the uploaded file
    try:
        projectObj = utils.get_project(project)
        parsed_df_list = projectObj.load_and_parse(filename, contents, selected_parser)

        parsed_dbs = [d["database"] for d in parsed_df_list]
        parsed_dfs = [d["data"] for d in parsed_df_list]

        # Dash cannot store DataFrames directly, so convert them to dictionaries
        parsed_dbs_dict = [df.to_dict("records") for df in parsed_dfs]

        # Clean data for datatables
        for i, table in enumerate(parsed_dbs_dict):
            parsed_dbs_dict[i] = clean_dataset(
                table, project, parsed_dbs[i], lists_to_strings=True
            )
        table_name = next(iter(parsed_dbs))

        return (
            f"File '{filename}' uploaded successfully.",
            parsed_dbs_dict,
            parsed_dbs,
            table_name,
            f"{project}-{table_name}",
        )

    except Exception as e:
        return (
            f"There was an error processing the file: {str(e)}",
            None,
            [],
            "",
            "",
        )


# Apply table highlights and tooltips to show changes
def highlight_and_tooltip_changes(
    original_data, data, page_current, page_size, validation_errors
):
    """Compare the original and edited data, highlight changes, and show tooltips."""
    if not page_size:
        return [], []
    page_current = page_current or 0

    paginate = True
    start_idx = page_current * page_size if paginate else 0
    end_idx = (page_current + 1) * page_size if paginate else len(data)

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
    tooltip_data = [{} for _ in range(start_idx)]
    keys = next(iter(data)).keys()
    data_cols = [k for k in keys if k != "Row"]

    # Iterate over each row in the modified data
    try:
        for i, row in enumerate(data[start_idx:end_idx]):
            row_tooltip = {}  # Store tooltips for the row
            errors = validation_errors[i + start_idx]
            # First, check for validation errors and highlight row
            if any(errors):
                style_data_conditional.append(
                    {
                        "if": {"row_index": i},
                        "backgroundColor": "#FFCCCC",
                        "color": "black",
                    }
                )
                # Show validation errors per cell and show tooltip
                for error in errors:
                    if error["path"] in data_cols:
                        style_data_conditional.append(
                            {
                                "if": {"row_index": i, "column_id": error["path"]},
                                "border": "2px solid red",
                            }
                        )
                        row_tooltip[error["path"]] = {
                            "value": error["message"],
                            "type": "text",
                        }
            else:
                # Then, if the cell values differ, highlight and add a tooltip
                for column in data_cols:
                    original_value = original_data[i + start_idx].get(column, None)
                    modified_value = row.get(column, None)
                    if str(modified_value) != str(original_value):
                        style_data_conditional.append(
                            {
                                "if": {"row_index": i, "column_id": column},
                                "backgroundColor": "#FFDDC1",
                                "color": "black",
                            }
                        )
                        # Show original content as a tooltip
                        row_tooltip[column] = {
                            "value": f'Original: "{original_value}"',
                            "type": "text",
                        }
            tooltip_data.append(row_tooltip)

    except Exception as e:
        # Callback can sometimes be called on stale data causing key errors
        logging.error(f"Error in highlight_and_tooltip_changes: {str(e)}")
        return [], []

    return style_data_conditional, tooltip_data


# Update the table style and tooltips based on validation errors
@callback(
    Output("editable-table", "style_data_conditional"),  # Update the table style ...
    Output("editable-table", "tooltip_data"),  # ... and tooltips
    Input("editable-table", "data"),  # Triggered by any change in the table data ...
    Input("editable-table", "page_current"),
    Input("editable-table", "page_size"),
    Input("validation-errors", "data"),  # ... or validation errors
    State("parsed-data-store", "data"),
    State("imported-tables-dropdown", "options"),
    State("imported-tables-dropdown", "value"),
)
def update_table_style_and_validate(
    data,
    page_current,
    page_size,
    validation_errors,
    original_data,
    tables,
    selected_table,
):
    if not data:
        return [], []

    # Convert original data from dict to DataFrame
    original_df = original_data[tables.index(selected_table)]

    # Highlight changes and create tooltips showing original data
    style_data_conditional, tooltip_data = highlight_and_tooltip_changes(
        original_df, data, page_current, page_size, validation_errors
    )

    return style_data_conditional, tooltip_data


# Downloading DataTable as CSV
@callback(
    Output("download-csv", "data"),  # Download the CSV file
    Input("download-button", "n_clicks"),  # Triggered by 'Download as CSV' button
    State("editable-table", "data"),
    State("imported-tables-dropdown", "value"),
    prevent_initial_call=True,  # Only trigger when the button is clicked
)
def download_csv(n_clicks, data, table_name):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        df.drop(columns=["Row"], inplace=True)
        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"import_{table_name}_{datetime_str}.csv"
        return dcc.send_data_frame(df.to_csv, filename, index=False)


# Display a confirmation dialog when the commit button is clicked
@callback(
    Output("confirm-commit-dialog", "displayed"),  # Show the dialog
    Output("confirm-commit-dialog", "message"),
    Input("commit-button", "n_clicks"),  # Triggered by 'Commit' button click
    State("imported-tables-dropdown", "options"),
)
def display_confirm_dialog(n_clicks, table_names):
    if n_clicks > 0:
        return True, (
            "You are able to write data to the following tables:\n"
            f"{', '.join([t for t in table_names])}\n\nCommit data now?"
        )
    return False, ""


# Commit changes to the database
@callback(
    Output("commit-output", "children"),  # Update the commit output message ...
    Output("commit-button", "disabled"),  # ... and disable the commit button
    Input("confirm-commit-dialog", "submit_n_clicks"),  # Triggered by 'Confirm' dialog
    State("project", "data"),
    State("imported-tables-dropdown", "options"),
    State("edited-data-store", "data"),
)
def commit_to_database(submit_n_clicks, project, table_names, datasets):
    if submit_n_clicks and project and table_names and datasets:
        try:
            projectObj.database.commit_tables_dict(table_names, datasets)
            return "Data committed to database.", True
        except Exception as e:
            return f"Error committing data to file: {str(e)}", False

    return "No data committed yet.", False
