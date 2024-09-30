import dash
import dash_bootstrap_components as dbc

from dash import dcc, html, dash_table
from dash import Input, Output, State, callback

import InsightBoard.utils as utils

# Register the page
dash.register_page(__name__, path="/data")
projectObj = None


# Layout for the Data Page
def layout():
    return html.Div(
        [
            html.H1("Project Data Table"),
            dcc.Store(id="project", storage_type="memory"),  # Store the project name
            html.H3("Select a table to view"),
            dcc.Dropdown(id="table-dropdown", placeholder="Select a table"),
            html.Div("", id="datatable-report-length"),
            dash_table.DataTable(
                id="datatable-table",
                columns=[],
                data=[],
                page_size=10,
                style_table={"overflowY": "auto"},
                style_cell={"textAlign": "left"},
                style_header={"backgroundColor": "lightgray", "fontWeight": "bold"},
                style_data={"backgroundColor": "white"},
            ),
            html.Div(
                [
                    # Button for downloading CSV
                    dbc.Button(
                        "Download table as CSV",
                        id="download-table-button",
                        n_clicks=0,
                    ),
                    dcc.Download(id="download-table-data"),
                    # Dropdown for selecting number of rows per page
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
                            "justifyContent": "center",
                            "alignItems": "center",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                },
            ),
        ]
    )


# Callback to update the page size of the DataTable based on dropdown selection
@callback(Output("datatable-table", "page_size"), Input("rows-dropdown", "value"))
def update_page_size(page_size):
    return page_size


@callback(
    Output("download-table-data", "data"),
    Input("download-table-button", "n_clicks"),
    State("table-dropdown", "value"),
)
def download_table(n_clicks, selected_table):
    if not selected_table or n_clicks == 0:
        return None

    filename = f"{selected_table}.csv"
    df = projectObj.database.read_table(selected_table)
    return dcc.send_data_frame(df.to_csv, filename, index=False)


# Callback to load the available database tables and populate the dropdown
@callback(Output("table-dropdown", "options"), Input("project", "data"))
def update_table_list(selected_project):
    if not selected_project:
        return []

    # Get the selected project
    global projectObj
    projectObj = utils.get_project(selected_project)

    # List tables in the project
    tables = projectObj.database.get_tables_list()
    return [
        {
            "label": table,
            "value": table,
        }
        for table in tables
    ]


# Callback to load the selected table and display it as a DataTable
@callback(
    Output("datatable-table", "columns"),
    Output("datatable-table", "data"),
    Output("datatable-report-length", "children"),
    Input("table-dropdown", "value"),
)
def load_selected_table(selected_table):
    if not selected_table:
        return [], [], ""

    # Load the table into a Pandas DataFrame
    try:
        df = projectObj.database.read_table(selected_table)
    except Exception as e:
        return [], [], f"Error loading table: {str(e)}"

    # Dynamically create the DataTable
    return (
        [{"name": col, "id": col} for col in df.columns],
        df.to_dict("records"),
        f"Number of records: {len(df)}",
    )
