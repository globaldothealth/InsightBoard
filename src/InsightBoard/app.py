import dash
from dash import dcc, Input, Output, html
import dash_bootstrap_components as dbc

from .utils import get_projects_list

projects = get_projects_list()
cogwheel = (html.I(className="fas fa-cog"),)

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.MINTY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
)
server = app.server  # Expose the server


# Project Dropdown list
def ProjectDropDown():
    return html.Div(
        [
            dcc.Dropdown(
                id="project-dropdown",
                options=[{"label": project, "value": project} for project in projects],
                value=projects[0] if projects else [],  # Default
                clearable=False,
                style={"width": "200px", "color": "black"},
                placeholder="No project selected",
            ),
            # add settings cogwheel
            dbc.NavLink(
                cogwheel,
                href="/settings",
                style={"color": "#c2e3da", "marginLeft": "10px"},
            ),
        ],
        style={"display": "flex", "alignItems": "center"},
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
