import os
import dash
import InsightBoard.utils as utils

from dash import dcc, html, Input, Output, State, callback

# Register the page
dash.register_page(__name__, path="/reports")
projectObj = None


# Entry point for the page
def layout():
    return html.Div(
        [
            html.H3("Select a Report"),
            dcc.Store(id="project", storage_type="memory"),  # Store the project name
            dcc.Dropdown(id="report-dropdown", placeholder="Select a report"),
            dcc.Loading(
                type="default",
                children=[
                    html.Div(
                        id="report-content", style={"width": "100%", "height": "100%"}
                    ),
                ],
                style={
                    "position": "absolute",
                    "top": 0,
                    "z-index": 9999,
                },
                color="var(--bs-primary)",
            ),
        ],
        style={"width": "100%", "height": "100%"},
    )


# Callback to update the list of available reports based on the selected project
@callback(Output("report-dropdown", "options"), Input("project", "data"))
def update_report_list(project):
    if project:
        global projectObj
        projectObj = utils.get_project(project)
        return projectObj.get_reports_list()
    return []


# Callback to display the selected report content
@callback(
    Output("report-content", "children"),
    Input("report-dropdown", "value"),
    State("project", "data"),
    _allow_dynamic_callbacks=True,  # python report modules are loaded dynamically
)
def display_selected_report(selected_report, project):
    if not selected_report:
        return "Please select a report."

    try:
        # Dynamically load the selected report
        reports_folder = projectObj.get_reports_folder()
        report_path = os.path.join(reports_folder, f"{selected_report}.py")
        report_module = utils.load_module(selected_report[:-3], report_path)

        # Each report should have a DATASETS attribute that lists the datasets it needs
        if not getattr(report_module, "DATASETS", None):
            return html.Div("No datasets requested by this report.")

        # Call the generate_report function from the report module
        return report_module.generate_report(
            *projectObj.get_datasets(report_module.DATASETS)
        )
    except Exception as e:
        return html.Div(
            [
                html.Div("Error loading report:", style={"color": "orange"}),
                *[html.Div(t, style={"color": "orange"}) for t in str(e).split("\n")],
            ]
        )
