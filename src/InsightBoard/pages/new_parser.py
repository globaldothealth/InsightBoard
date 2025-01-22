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

# DataTable supports a maximum of 512 conditional formatting rules,
#  so stop adding rules after this limit is reached
MAX_CONDITIONAL_FORMATTING = 512

# Register the page
dash.register_page(__name__, path="/new_parser")
projectObj = None
autoParser = None


def layout():
    return html.Div(
        [
            # Store
            dcc.Store(id="project"),  # project selection
            dcc.Store(id="parser-id"),  # unique id (project-table)
            dcc.Store(id="ap-output-store"),  # autoparser output
            dcc.Store(id="edited-ap-output-store"),  # edited data dict
            dcc.Store(id="generate-descriptions-with-llm"),  # Setting: LLm descriptions
            # dcc.Store(id="show-full-validation-log"),  # Setting: Show full log
            # dcc.Store(id="update-existing-records"),  # Setting: Update records
            dcc.Store(id="unmapped-fields"),
            dcc.Store(id="edited-unmapped-fields", data=[]),
            # Page rendering
            html.H1("Create a new parser"),
            # dcc.Location(id="url-refresh", refresh=True),
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
                            dcc.RadioItems(
                                options=[
                                    {"label": "English", "value": "en"},
                                    {"label": "French", "value": "fr"},
                                ],
                                value="fr",
                                id="data-language",
                                style={"marginTop": "10px", "marginBottom": "10px"},
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
                            # {"label": "Show full validation log", "value": 2},
                            # {"label": "Update existing records", "value": 3},
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
                        id="editable-ap-table",
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
            html.Div(id="parser-output"),
            html.Div(
                [
                    dbc.Button(
                        "Confirm & continue",
                        id="mapping-button",
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
                ],
                style={
                    "display": "flex",
                    "flexDirection": "row",
                    "alignItems": "center",  # Vertically align items
                },
            ),
            dcc.ConfirmDialog(id="confirm-parser-dialog", message=""),
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


# # Update state when settings are changed: Update Existing Records
# @callback(
#     Output("update-existing-records", "value"),  # Update the 'update records' setting
#     Input("upload-settings", "value"),  # Triggered by settings switch changes
# )
# def update_update_existing_records(value):
#     return 3 in value


# Update page size of the DataTable based on dropdown selection
@callback(
    Output("editable-ap-table", "page_size"),  # Update the DataTable page size
    Input("fields-dropdown", "value"),  # Triggered by 'rows per page' dropdown
)
def update_page_size(page_size):
    return page_size


# triggered when the active cell changes?
@callback(
    Output("editable-ap-table", "columns"),  # Update DataTable
    Output("editable-ap-table", "data"),
    Output("editable-ap-table", "active_cell"),
    Output("data-dict-stats", "children"),
    Input("parser-id", "data"),
    Input("generate-descriptions-with-llm", "value"),
    Input("editable-ap-table", "active_cell"),
    State("project", "data"),
    # PL: the non-edited store is used here, and is the one that works.
    # But think it possibly should be the non-edited one.
    State("ap-output-store", "data"),  # Populate with table from edited-data store
)
def update_table(
    parser_id,
    llm_descriptions,
    active_cell,
    project,
    edited_datasets,
):
    # Callback is triggered before edited_datasets is populated on first run
    datasets = edited_datasets
    if not datasets:
        raise dash.exceptions.PreventUpdate

    ctx = dash.callback_context
    trig_active_cell = ctx_trigger(ctx, "editable-ap-table.active_cell")
    # trig_remove_empty_ids = ctx_trigger(ctx, "remove-empty-ids-button.n_clicks")
    # trig_remove_error_rows = ctx_trigger(ctx, "remove-error-rows-button.n_clicks")
    # trig_restore_deleted_rows = ctx_trigger(ctx, "restore-deleted-rows-button.n_clicks")

    # The only active cell we want to respond to is the delete button
    if trig_active_cell and active_cell:
        raise dash.exceptions.PreventUpdate

    data = datasets

    data_stats = f"Total fields: {len(data)}"
    # projectObj = utils.get_project(project)
    # primary_key = projectObj.database.get_primary_key(selected_table)

    # # Convert any lists to strings for display
    # data = clean_dataset(data, project, selected_table, lists_to_strings=True)
    keys = next(iter(data)).keys()
    columns = [{"name": col, "id": col, "editable": True} for col in keys]
    # columns = utils.ensure_schema_ordering(columns, project, selected_table)

    # Move 'Row' column to the front
    columns = [
        {"name": "Row", "id": "Row", "editable": False},
        *[col for col in columns if col["id"] not in ["Row"]],
    ]

    # hidden_columns = []
    # data_stats += f", Showing: {len(data)}"
    # if deleted_rows:
    #     data_stats += f", Deleted: {deleted_rows}"

    # return columns, hidden_columns, data, active_cell, data_stats
    return columns, data, active_cell, data_stats


# When edits are made in the DataTable, update the edited-data-store & missing fields
# triggered by changing the page, but not by editing the table
@callback(
    Output("edited-ap-output-store", "data"),  # Update the edited data store
    Output("edited-unmapped-fields", "data"),  # Update the missing fields store
    Input("ap-output-store", "data"),  # Triggered by new autoparser data ...
    Input("editable-ap-table", "data"),  # ... or DataTable edits
    State("project", "data"),
    State("edited-ap-output-store", "data"),  # PL: still right?
    State("unmapped-fields", "data"),
    State("edited-unmapped-fields", "data"),
)
def update_edited_data(
    parsed_data,
    edited_table_data,
    project,
    datasets,
    unmapped_fields,
    edited_unmapped_fields,
):
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
    Output("autoparser-messages", "children"),  # Output message
    Output("ap-output-store", "data"),  # Update autoparser data store,
    Output("unmapped-fields", "data"),  # unmapped fields, and ...
    Output("parser-id", "data"),
    Output("autoparser-file-settings", "style"),  # ... GUI elements
    Input("make-dict-button", "n_clicks"),  # Triggered by 'Create Dict' button click ..
    Input("mapping-button", "n_clicks"),  # ... or 'Confirm & Continue' button click
    State("project", "data"),
    State("ap-upload-data", "contents"),
    State("ap-upload-data", "filename"),
    State("schema-dropdown", "value"),
    State("edited-ap-output-store", "data"),
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
        (
            Output("mapping-button", "children"),
            [dbc.Spinner(size="sm"), " Mapping dictionary to schema..."],
            "Confirm and Continue",
        ),
        (
            Output("mapping-button", "disabled"),
            True,
            False,
        ),
    ],
)
def parse_file_to_data_dict(
    parse_n_clicks,
    map_n_clicks,
    project,
    contents,
    filename,
    schema,
    edited_data_store,
    api_key,
    llm_choice,
    llm_descriptions,
    language,
):
    # if not parse_n_clicks and not update_n_clicks:
    if not parse_n_clicks:
        return (
            "",
            None,
            [],
            [],
            {"display": "block"},
            # {"display": "none"},
        )
    ctx = dash.callback_context
    trig_parse_btn = ctx_trigger(ctx, "make-dict-button.n_clicks")
    trig_mapping_btn = ctx_trigger(ctx, "mapping-button.n_clicks")
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
                [],
                rtn,
                {"display": "none"},
                # {"display": "block"},
            )
        else:
            # If there was an error, return the error message
            return (
                msg,
                data_dict,
                [],
                rtn,
                {"display": "block"},
                # {"display": "none"},
            )
    # Generate a mapping file
    if trig_mapping_btn:
        msg, mapping, errors, rtn = dict_to_mapping_file(
            project,
            edited_data_store,
            filename,
            schema,
            api_key,
            llm_choice,
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
            )
        else:
            # If there was an error, return the error message
            return (
                msg,
                mapping,
                [],
                rtn,
                {"display": "none"},
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
            dbc.Alert(
                "Please select both a schema, and a data file to use.",
                color="warning",
            ),
            None,
            # [],
            "",
        )

    # Process the uploaded file
    try:
        projectObj = utils.get_project(project)
        # 'schema' is <table>.schema
        table = schema.split(".")[0]
        schema_file = projectObj.get_schema(table)
        schema_path = projectObj.get_schemas_folder()

        # it's probaly this; once the 'autoparser' global class is created,
        # even if the llm or api key is changed it will still be the same object.
        global autoParser
        if autoParser is None:
            autoParser = utils.get_autoparser(llm, key, schema_file, table, schema_path)

        ready, msg = autoParser.is_autoparser_ready
        if not ready:
            return (
                dbc.Alert(msg, color="warning"),
                None,
                # [],
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
            f"Data dictionary for file '{filename}' created successfully.\n"
            "Please check this carefully, and once you are satisfied click 'Confirm & Continue'.",  # noqa
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


def dict_to_mapping_file(project, contents, filename, schema, key, llm, language):
    """
    Returns
    message, dictionary, schema name, file name string
    """

    try:
        dd = pd.DataFrame(contents)
        dd.drop(columns=["Row"], inplace=True)

        mapping_frame, missing_fields = autoParser.create_mapping(dd, language)
        mapping_frame.reset_index(inplace=True)

        # Dash cannot store DataFrames directly, so convert them to dictionaries
        mapping = mapping_frame.to_dict("records")

        # Populate 'Row' and '_delete' columns
        for i, row in enumerate(mapping):
            row["Row"] = i + 1

        return (
            f"Mapping for file '{filename}' created successfully.\n"
            "Please check this carefully, and once you are satisfied define the parser name and click 'Generate Parser'.",  # noqa
            mapping,
            missing_fields,
            schema,
            # f"{project}-{schema['name']}",
        )

    except Exception as e:
        return (
            dbc.Alert(
                f"There was an error while mapping: {e}. ",
                color="danger",
            ),
            None,
            [],
            # [],
            "",
        )


# Apply table highlights and tooltips to show changes
def highlight_and_tooltip_changes(
    original_data,
    data,
    page_current,
    page_size,
    missing_fields,
):
    """Highlight missing fields and show tooltips."""
    if not page_size:
        return [], []
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
    tooltip_data = [{} for _ in range(start_idx)]
    keys = next(iter(data)).keys()
    data_cols = [k for k in keys if k not in ["Row"]]

    error_rows = []

    # Iterate over each row in the modified data
    try:
        # Ensure rows with errors are highlighted before placing cell-level highlights
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
            row_tooltip = {}  # Store tooltips for the row
            idx = row["Row"] - 1
            errors = missing_fields[idx]
            # Show validation errors per cell and show tooltip
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
                    row_tooltip[error["path"]] = {
                        "value": error["message"],
                        "type": "text",
                    }
            else:
                # Then, if the cell values differ, highlight and add a tooltip
                for column in data_cols:
                    original_value = original_data[idx].get(column, None)
                    modified_value = row.get(column, None)
                    if str(modified_value) != str(original_value):
                        if len(style_data_conditional) <= MAX_CONDITIONAL_FORMATTING:
                            style_data_conditional.append(
                                {
                                    "if": {
                                        "filter_query": f"{{Row}} = {idx + 1}",
                                        "column_id": column,
                                    },
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
        logging.error(f"missing fields: {missing_fields}")
        return [], []

    return style_data_conditional, tooltip_data


# Update the table style and tooltips based on missing fields
@callback(
    Output("editable-ap-table", "style_data_conditional"),  # Update the table style ...
    Output("editable-ap-table", "tooltip_data"),  # ... and tooltips
    Input("editable-ap-table", "data"),  # Triggered by any change in the table data ...
    Input("editable-ap-table", "page_current"),
    Input("editable-ap-table", "page_size"),
    State("ap-output-store", "data"),
    State("unmapped-fields", "data"),
    State("edited-unmapped-fields", "data"),
)
def update_table_style_and_validate(
    data,
    page_current,
    page_size,
    original_data,
    missing_fields,
    edited_missing_fields,
):
    if not data:
        return [], []

    # Highlight changes and create tooltips showing original data
    style_data_conditional, tooltip_data = highlight_and_tooltip_changes(
        original_data,
        data,
        page_current,
        page_size,
        edited_missing_fields or missing_fields,
    )

    return style_data_conditional, tooltip_data


# Downloading Data Dict/Mapping file as CSV
@callback(
    Output("download-dict-csv", "data"),  # Download the CSV file
    Input("download-dict-button", "n_clicks"),  # Triggered by 'Download as CSV' button
    State("editable-ap-table", "data"),
    prevent_initial_call=True,  # Only trigger when the button is clicked
)
def download_csv(n_clicks, data):
    if n_clicks > 0 and data:
        df = pd.DataFrame(data)
        df.drop(columns=["Row"], inplace=True)
        now = datetime.now()
        datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"autoparser_file_{datetime_str}.csv"
        return dcc.send_data_frame(df.to_csv, filename, index=False)


# Display a confirmation dialog when the 'generate parser' button is clicked
@callback(
    Output("confirm-parser-dialog", "displayed"),  # Show the dialog
    Output("confirm-parser-dialog", "message"),
    Input("make-parser-button", "n_clicks"),  # Triggered by 'Commit' button click
    State("ap-upload-data", "filename"),
    State("schema-dropdown", "value"),
)
def display_parser_dialog(n_clicks, data_file_name, schema_name):  # , table_names
    if n_clicks > 0:
        return True, (
            "You are about to write a parser for the following data file and schema:\n"
            f"Data: {data_file_name}\nSchema: {schema_name}\n\nWrite parser now?"
        )
    return False, ""


# Write a new parser
@callback(
    Output("parser-output", "children"),  # Update the commit output message ...
    Input("confirm-parser-dialog", "submit_n_clicks"),  # Triggered by 'Confirm' dialog
    State("parser-name", "value"),  # Parser name
    State("project", "data"),
    State("edited-ap-output-store", "data"),
)
def write_a_parser(submit_n_clicks, parser_name, project, datasets):
    if submit_n_clicks and project and datasets:
        try:
            parser_folder = projectObj.get_parsers_folder()

            mapping = pd.DataFrame(datasets)
            mapping.drop(columns=["Row"], inplace=True)

            autoParser.create_parser(mapping, parser_folder, name=parser_name)

            # make asociated python file
            content = f"""import pandas as pd
from pathlib import Path
from InsightBoard.parsers import parse_adtl

SPECIFICATION_FILE = "adtl/{parser_name}.toml"

def parse(df: pd.DataFrame) -> list[dict]:
    spec_file = Path(__file__).parent / SPECIFICATION_FILE
    return parse_adtl(df, spec_file, ["linelist"])
"""

            file = Path(parser_folder, f"adtl-{parser_name}.py")
            # Create parent directories if they don't exist
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)

            return dbc.Alert("Parser generated.", color="success")
        except Exception as e:
            logging.error(f"Error writing the parser: {str(e)}")
            logging.error(traceback.format_exc())
            return dbc.Alert(f"Error writing the parser: {str(e)}", color="danger")

    return "No parser written yet."


# TODO:
# * Use arcmapper style of 'containers' to allow the bottom section/buttons to
# change with the stage of transformation we're in

# *on autoparser side: throw recognisable error if a source_field is not found in the
# data (prob typed incorrectly by the user)
