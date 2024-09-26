import dash
from dash import dcc, Input, Output
import dash_bootstrap_components as dbc
from .utils import get_projects_list

projects = get_projects_list()

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.MINTY],
    suppress_callback_exceptions=True,
)
server = app.server  # Expose the server


# Project Dropdown list
def ProjectDropDown():
    return dcc.Dropdown(
        id="project-dropdown",
        options=[{"label": project, "value": project} for project in projects],
        value=projects[0],  # Default
        clearable=False,
        style={"width": "200px", "color": "black"},
    )


@app.callback(Output("project", "data"), Input("project-dropdown", "value"))
def store_selected_project(project):
    return project


app.layout = dbc.Container(
    [
        dcc.Store(id="project", storage_type="memory"),
        dbc.NavbarSimple(
            children=[
                dbc.NavLink("Home", href="/"),
                dbc.NavLink("Upload", href="/upload"),
                dbc.NavLink("Data", href="/data"),
                dbc.NavLink("Reports", href="/reports"),
            ],
            brand=ProjectDropDown(),
            color="primary",
            dark=True,
        ),
        dash.page_container,
    ]
)
