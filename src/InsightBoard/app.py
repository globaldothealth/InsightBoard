import sys
import dash
import dash_bootstrap_components as dbc

from dash import html
from pathlib import Path

from InsightBoard.config import ConfigManager
from InsightBoard.utils import (
    get_projects_list,
    get_default_project,
    get_custom_assets_folder,
)


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

app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder=str(pages_path),
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
