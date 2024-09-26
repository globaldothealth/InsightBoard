import dash
from dash import dcc, html, dash_table
from dash import Input, Output, State, callback
import pandas as pd
import os
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
            html.Div(
                id="datatable-container"
            ),  # Container for dynamically generated DataTable
        ]
    )


# Callback to load the available database tables and populate the dropdown
@callback(Output("table-dropdown", "options"), Input("project", "data"))
def update_parquet_file_list(selected_project):
    if not selected_project:
        return []

    # Get the data folder for the selected project
    global projectObj
    projectObj = utils.get_project(selected_project)
    data_folder = projectObj.get_data_folder()

    # List all .parquet files in the data folder
    try:
        parquet_files = [f for f in os.listdir(data_folder) if f.endswith(".parquet")]
        if not parquet_files:
            return [{"label": "No tables files found", "value": ""}]
        return [{"label": f.split(".")[:-1], "value": f} for f in parquet_files]
    except FileNotFoundError:
        return [
            {
                "label": f"Error: Data folder for {selected_project} not found",
                "value": "",
            }
        ]
    except Exception as e:
        return [{"label": f"Error: {str(e)}", "value": ""}]


# Callback to load the selected table and display it as a DataTable
@callback(
    Output("datatable-container", "children"),
    Input("table-dropdown", "value"),
    State("project", "data"),
)
def load_selected_parquet_file(selected_file, selected_project):
    if not selected_file or not selected_project:
        return "Please select a table."

    # Get the data folder for the selected project
    data_folder = projectObj.get_data_folder()

    # Define the path to the selected table
    parquet_file_path = os.path.join(data_folder, selected_file)

    # Load the table into a Pandas DataFrame
    try:
        df = pd.read_parquet(parquet_file_path)
    except FileNotFoundError:
        return html.Div(f"Error: File not found at {parquet_file_path}.")
    except Exception as e:
        return html.Div(f"Error loading table: {str(e)}")

    # Dynamically create the DataTable
    return dash_table.DataTable(
        id="editable-table",  # The dynamically generated table's ID
        columns=[
            {"name": col, "id": col} for col in df.columns
        ],  # Define columns based on DataFrame
        data=df.to_dict("records"),  # Convert DataFrame rows to dictionary format
        page_size=10,
        style_table={"height": "400px", "overflowY": "auto"},
        style_cell={"textAlign": "left"},
        style_header={"backgroundColor": "lightgray", "fontWeight": "bold"},
        style_data={"backgroundColor": "white"},
    )
