from pathlib import Path
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

from .config import ConfigManager
from .utils import get_projects_list, get_default_project, get_custom_assets_folder

projects = get_projects_list()
default_project = get_default_project()
if default_project not in projects:
    default_project = projects[0] if projects else None
custom_assets = get_custom_assets_folder()
assets_path = custom_assets if custom_assets else "/assets"
custom_css = (
    [
        str(Path(custom_assets).joinpath(css))
        for css in Path(custom_assets).rglob("*.css")
    ]
    if custom_assets
    else []
)
cogwheel = (html.I(className="fas fa-cog"),)

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        (
            "https://cdnjs.cloudflare.com/ajax/libs/"
            "font-awesome/6.0.0-beta3/css/all.min.css"
        ),
        *custom_css,
    ],
    suppress_callback_exceptions=True,
    assets_folder=assets_path,
)
app.scripts.config.serve_locally = True
server = app.server  # Expose the server


def logo():
    if (Path(assets_path) / "logo.png").exists():
        return [
            html.A(
                html.Img(
                    src="/assets/logo.png",
                    className="logo",
                    style={"maxHeight": "70px", "marginRight": "10px"},
                ),
                href="/",
            )
        ]
    else:
        return []


# Project Dropdown list
def ProjectDropDown():
    return html.Div(
        [
            *logo(),
            dcc.Dropdown(
                id="project-dropdown",
                options=[{"label": project, "value": project} for project in projects],
                value=default_project,
                clearable=False,
                style={"width": "200px", "color": "black"},
                placeholder="No project selected",
            ),
            # add settings cogwheel
            dbc.NavLink(
                cogwheel,
                href="/settings",
                style={"color": "var(--bs-navbar-hover-color)", "marginLeft": "10px"},
            ),
        ],
        style={"display": "flex", "alignItems": "center"},
    )


@app.callback(Output("project", "data"), Input("project-dropdown", "value"))
def store_selected_project(project):
    config = ConfigManager()
    config.set("project.default", project)
    config.save()
    return project


app.layout = dbc.Container(
    [
        dcc.Store(id="project", storage_type="memory", data=default_project),
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
        # Hearbeat interval and error reporting div
        html.Div(
            id="server-status",
            style={
                "font-size": "24px",
                "text-align": "center",
                "color": "red",
                "border": "5px solid red",
                "padding": "20px",
                "display": "none",  # Initially hidden
            },
        ),
        dcc.Interval(id="interval", interval=1000, n_intervals=0),
        # Page contents
        html.Div(dash.page_container, id="page-content"),
    ],
)

# Client-side callback to check server status every second
app.clientside_callback(
    """
    function(n_intervals) {
        // Perform a heartbeat check to the server
        return fetch(window.location.href)
            .then(function(response) {
                if (response.ok) {
                    // When connected, hide the message completely (display: none)
                    document.getElementById("server-status").style.display = "none";
                    document.getElementById("page-content").style.display = "block";
                    return "";
                } else {
                    // When disconnected, show the message with a red border
                    document.getElementById("server-status").style.display = "block";
                    document.getElementById("page-content").style.display = "none";
                    return "The InsightBoard application has been closed";
                }
            })
            .catch(function() {
                // Handle connection error (server down)
                document.getElementById("server-status").style.display = "block";
                document.getElementById("page-content").style.display = "none";
                return "The InsightBoard application has been closed";
            });
    }
    """,
    Output("server-status", "children"),
    Input("interval", "n_intervals"),
)
