import sys
import dash
import dash_bootstrap_templates as dbt
import dash_bootstrap_components as dbc

from dash import dcc, html, callback, Input, Output
from pathlib import Path

from InsightBoard.app import app
from InsightBoard.config import ConfigManager
from InsightBoard.utils import (
    get_projects_list,
    get_default_project,
    get_custom_assets_folder,
)
from InsightBoard.chatbot import initialize_chatbot

# If running from PyInstaller, get the path to the temporary directory
if hasattr(sys, "_MEIPASS"):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

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
pages_path = base_path / "pages"
config = ConfigManager()
dark_mode = config.get("theme.dark_mode", False)


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


@callback(Output("project", "data"), Input("project-dropdown", "value"))
def store_selected_project(project):
    config = ConfigManager()
    if project:
        config.set("project.default", project)
        config.save()
    return project


app.layout = dbc.Container(
    [
        dcc.Store(id="project", data=default_project),
        dcc.Store(id="dark-mode", data=dark_mode),
        html.Div(
            [
                dbt.ThemeSwitchAIO(
                    aio_id="theme",
                    themes=[
                        dbc.themes.BOOTSTRAP,
                        dbc.themes.DARKLY,
                    ],
                ),
            ],
            style={"display": "none"},
        ),
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

# Add chatbox clientside callbacks
initialize_chatbot()


@callback(
    Output(dbt.ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input("project", "data"),
    Input("dark-mode", "data"),
)
def set_theme(project, dark_mode):
    config = ConfigManager()
    dark_mode = config.get("theme.dark_mode", False)
    return not dark_mode
