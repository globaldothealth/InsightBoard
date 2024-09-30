import io
import dash
import base64
import pandas as pd
import dash_bootstrap_components as dbc

from pathlib import Path
from dash import dcc, html, dash_table, Input, Output, State, callback

import InsightBoard.utils as utils

# Register the page
dash.register_page(__name__, path="/upload")
projectObj = None


def layout():
    return html.Div(
        [
            dcc.Store(id="project"),  # Store the project name
            dcc.Store(id="parsed-data-store"),  # Store parsed DataFrame(s)
            dcc.Store(id="edited-data-store"),  # Store edited DataFrame(s)
            html.H1("Upload data"),
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
            html.Div(id="output-upload-data"),
            # Parse Button to start file parsing
            dbc.Button("Parse File", id="parse-button", n_clicks=0),
            # Dropdown for imported tables
            dcc.Dropdown(
                id="imported-tables-dropdown",
                options=[],
                placeholder="Select a table",
                clearable=False,
                style={"float": "right", "width": "50%"},
            ),
            # DataTable for editing
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
                    "minWidth": "100%",  # Format fix after freezing first column
                    "min-height": "300px",
                    "overflowY": "auto",
                },
                fixed_columns={"headers": True, "data": 1},  # Freeze first column
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
            html.Hr(),
            html.Div(id="output-container"),
        ],
        style={"width": "100%"},
    )


# Callback to update parser dropdown based on selected dataset
@callback(
    Output("parser-dropdown", "options"),
    Input("project", "data"),
)
def update_parser_dropdown(project):
    if project:
        # Return list of parsers for the selected dataset
        global projectObj
        projectObj = utils.get_project(project)
        parsers = projectObj.get_project_parsers()
        return [parser["label"] for parser in parsers]
    return []


@callback(
    Output("upload-data-filename", "children"),
    Input("upload-data", "filename"),
)
def update_filename(filename):
    if filename:
        return f"Selected file: {filename}"
    return "Select a data file"


# Callback to update the page size of the DataTable based on dropdown selection
@callback(Output("editable-table", "page_size"), Input("rows-dropdown", "value"))
def update_page_size(page_size):
    return page_size


@callback(
    Output("editable-table", "columns"),
    Output("editable-table", "data"),
    Input("imported-tables-dropdown", "options"),
    Input("imported-tables-dropdown", "value"),
    State("edited-data-store", "data"),
    State("parsed-data-store", "data"),
)
def update_table(options, selected_table, edited_datasets, parsed_datasets):
    # callback is triggered before edited_datasets is populated on first run
    datasets = edited_datasets
    if not datasets:
        datasets = parsed_datasets
    if not datasets:
        return [], []

    data = datasets[options.index(selected_table)]
    columns = [{"name": col, "id": col, "editable": True} for col in data[0].keys()]

    # Prepend non-edtable 'Row' column
    columns.insert(0, {"name": "Row", "id": "Row", "editable": False})
    for i, row in enumerate(data):
        row["Row"] = i + 1

    return columns, data


@callback(
    Output("edited-data-store", "data"),
    Input("parsed-data-store", "data"),
    Input("editable-table", "data"),
    State("imported-tables-dropdown", "options"),
    State("imported-tables-dropdown", "value"),
    State("edited-data-store", "data"),
)
def update_edited_data(
    parsed_data, edited_table_data, tables, selected_table, datasets
):
    ctx = dash.callback_context
    if any(k["prop_id"] == "parsed-data-store.data" for k in ctx.triggered):
        # Parsed data has changed, so reset to the newly parsed data
        return parsed_data
    # Otherwise, update to the latest table edits
    new_edited_data_store = datasets
    # Remove the 'Row' column before saving
    for row in edited_table_data:
        row.pop("Row", None)
    new_edited_data_store[tables.index(selected_table)] = edited_table_data
    return new_edited_data_store


def error_report_message(errors: []) -> str:
    # Expecting a list of string/None validation errors
    if not any(errors):
        return "No validation errors."
    errors = list(map(lambda s: s if s else "", errors))
    errors = "\n".join(errors)
    return errors


def text_to_html(text: str) -> html.Div:
    return html.Div(
        [html.Pre(text, style={"white-space": "pre-wrap", "word-wrap": "break-word"})]
    )


@callback(
    Output("output-container", "children"),
    Input("parsed-data-store", "data"),
    Input("imported-tables-dropdown", "options"),
    Input("imported-tables-dropdown", "value"),
    State("project", "data"),
)
def validate_tables(parsed_dbs_dict, parsed_dbs, selected_table, project):
    if not parsed_dbs_dict:
        return "Validation checks not yet run."

    selected_table_index = parsed_dbs.index(selected_table)
    table_name = parsed_dbs[selected_table_index]
    df_dict = parsed_dbs_dict[selected_table_index]
    df = pd.DataFrame.from_records(df_dict)

    # Ensure that base schema file exists
    schema_file = Path(projectObj.get_schemas_folder()) / f"{table_name}.schema.json"
    if not schema_file.exists():
        return html.Div(
            [
                html.H3("Validation errors:", style={"color": "red"}),
                html.P(
                    f"Schema file '{schema_file}' not found - cannot validate table.",
                    style={"color": "red"},
                ),
            ]
        )

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

    # Validate the data against the schema (removing empty rows)
    parsed_errors = [
        x for x in utils.validate_against_jsonschema(df, schema_file_relaxed) if x
    ]

    # If a strict schema exists, validate against that too
    parsed_warns = []
    if schema_file_strict:
        schema_file_strict = (
            Path(projectObj.get_schemas_folder()) / f"{table_name}.schema.json"
        )
        parsed_warns = [
            x for x in utils.validate_against_jsonschema(df, schema_file_strict) if x
        ]

    # Construct validation messages
    if not any(parsed_errors) and not any(parsed_warns):
        return html.P("Validation passed successfully.")
    msg_errors = [
        html.H3("Validation errors:", style={"color": "red"}),
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


# Callback to parse the file when "Parse" button is pressed
@callback(
    Output("output-upload-data", "children"),
    Output("parsed-data-store", "data"),
    Output("imported-tables-dropdown", "options"),
    Output("imported-tables-dropdown", "value"),
    Input("parse-button", "n_clicks"),
    Input("update-button", "n_clicks"),
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
            "No parse requested.",
            None,
            [],
            None,
        )
    ctx = dash.callback_context
    # Parse the data (read from files)
    if any(k["prop_id"] == "parse-button.n_clicks" for k in ctx.triggered):
        return parse_data(project, contents, filename, selected_parser)
    # Update the data (make the current 'edited' buffer the new 'parsed' buffer)
    if any(k["prop_id"] == "update-button.n_clicks" for k in ctx.triggered):
        return (
            "Validation run.",
            edited_data_store,  # move edited data into parsed data store
            tables_list,  # pass-through
            selected_table,  # pass-through
        )


def parse_data(project, contents, filename, selected_parser):
    if not contents or not selected_parser:
        return (
            "Please select a dataset, parser, and file to parse.",
            None,
            [],
            None,
        )

    # Process the uploaded file
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        ext = filename.split(".")[-1].lower()
        if ext == "csv":
            raw_df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif ext == "xlsx":
            raw_df = pd.read_excel(io.BytesIO(decoded))
        else:
            return "Unsupported file type.", None, [], None

        # Parse the data using the selected parser
        parsers_folder = projectObj.get_parsers_folder()
        parser_module = utils.load_module(
            selected_parser, f"{parsers_folder}/{selected_parser}.py"
        )
        parsed_df_list = parser_module.parse(raw_df)
        if not isinstance(parsed_df_list, list):
            parsed_df_list = [parsed_df_list]
        parsed_dbs = [d["database"] for d in parsed_df_list]
        parsed_dfs = [d["data"] for d in parsed_df_list]

        # Dash cannot store DataFrames directly, so convert them to dictionaries
        parsed_dbs_dict = [df.to_dict("records") for df in parsed_dfs]

        return (
            f"File '{filename}' uploaded successfully.",
            parsed_dbs_dict,
            parsed_dbs,
            parsed_dbs[0],
        )

    except Exception as e:
        return (
            f"There was an error processing the file: {str(e)}",
            None,
            [],
            None,
        )


def highlight_and_tooltip_changes(original_df, data):
    """Compare the original and edited data, highlight changes, and show tooltips."""
    style_data_conditional = []
    tooltip_data = []

    # Iterate over each row in the modified data
    try:
        # Highlight first column ('Row') in light grey
        style_data_conditional.append(
            {
                "if": {"column_id": "Row"},
                "backgroundColor": "#F0F0F0",
                "color": "#A0A0A0",
            }
        )
        for i, row in enumerate(data):
            row_tooltip = {}  # Store tooltips for the row
            for column in original_df.columns:
                original_value = original_df.iloc[i][column]
                modified_value = row[column]
                # If the cell value differs from the original, highlight it and add tooltip
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
                        "type": "markdown",
                    }
            tooltip_data.append(row_tooltip)
    except Exception:
        # Callback can sometimes be called on stale data causing key errors
        return [], []

    return style_data_conditional, tooltip_data


# Callback to highlight changes, show tooltips, and validate the data
@callback(
    Output("editable-table", "style_data_conditional"),
    Output("editable-table", "tooltip_data"),
    Input("editable-table", "data"),
    State("parsed-data-store", "data"),
    State("imported-tables-dropdown", "options"),
    State("imported-tables-dropdown", "value"),
)
def update_table_style_and_validate(data, original_data, tables, selected_table):
    if not data:
        return [], []

    # Convert original data from dict to DataFrame
    original_df = pd.DataFrame(original_data[tables.index(selected_table)])

    # Highlight changes and create tooltips showing original data
    style_data_conditional, tooltip_data = highlight_and_tooltip_changes(
        original_df, data
    )

    return style_data_conditional, tooltip_data


# Callback for downloading data as CSV
@callback(
    Output("download-csv", "data"),
    Input("download-button", "n_clicks"),
    State("editable-table", "data"),
    prevent_initial_call=True,  # Only trigger when the button is clicked
)
def download_csv(n_clicks, data):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        df.drop(columns=["Row"], inplace=True)
        return dcc.send_data_frame(df.to_csv, "modified_data.csv", index=False)


@callback(
    Output("confirm-commit-dialog", "displayed"),
    Output("confirm-commit-dialog", "message"),
    Input("commit-button", "n_clicks"),
    State("imported-tables-dropdown", "options"),
)
def display_confirm_dialog(n_clicks, table_names):
    if n_clicks > 0:
        return True, (
            "You are able to write data to the following tables:\n"
            f"{', '.join([t for t in table_names])}\n\nCommit data now?"
        )
    return False, ""


# Callback for committing changes to the database
@callback(
    Output("commit-output", "children"),
    Output("commit-button", "disabled"),
    Input("confirm-commit-dialog", "submit_n_clicks"),
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
