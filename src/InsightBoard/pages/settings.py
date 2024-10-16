import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

import InsightBoard.utils as utils
from InsightBoard.config import ConfigManager
from InsightBoard.database import BackupPolicy

# Register the page
dash.register_page(__name__, path="/settings")


# Layout for the Data Page
def layout():
    # Load the configuration
    config = ConfigManager()
    project_folder = config.get_project_folder()

    db_backend = "parquet"

    db_backup_policy_list = [
        {"label": "None", "value": str(BackupPolicy.NONE)},
        {"label": "Versioned", "value": str(BackupPolicy.VERSIONED)},
        {"label": "Timestamp copies", "value": str(BackupPolicy.BACKUP)},
    ]
    db_backup = str(BackupPolicy.NONE)

    return html.Div(
        [
            # Store
            html.H1(
                "Settings",
                style={"width": "67%", "minWidth": "400px", "maxWidth": "800px", "border": "none"},
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("Global settings"),
                        html.P("These settings apply to all projects."),
                        html.H5("Project folder"),
                        dcc.Input(
                            id="project-folder",
                            value=project_folder,
                            style={"width": "100%"},
                        ),
                        html.H5("Dark mode"),
                        dbc.Checklist(
                            id="dark-mode-toggle",
                            options=[
                                {"label": "Dark mode", "value": 1},
                            ],
                            value=[],  # list of 'value's that are 'on' by default
                            inline=True,
                            switch=True,
                        ),
                    ]
                ),
                style={"width": "67%", "minWidth": "400px", "maxWidth": "800px"},
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("Project settings"),
                        html.P(
                            "These settings apply to the current project: {project}",
                            id="project-info",
                        ),
                        html.H5("Database"),
                        html.H6("Backend"),
                        dbc.Col(
                            dcc.Dropdown(
                                id="db-backend-dropdown",
                                options=[
                                    {
                                        "label": "Flat file (parquet)",
                                        "value": "parquet",
                                    },
                                ],
                                value=db_backend,
                                clearable=False,
                                style={"width": "100%"},
                            ),
                            width=12,
                        ),
                        html.H6("Backup policy"),
                        dbc.Col(
                            dcc.Dropdown(
                                id="db-backup-dropdown",
                                options=db_backup_policy_list,
                                clearable=False,
                                value=db_backup,
                                style={"width": "100%"},
                            ),
                            width=12,
                        ),
                        html.Br(),
                        dbc.Button("Set as defaults", color="primary"),
                    ]
                ),
                style={"width": "67%", "minWidth": "400px", "maxWidth": "800px"},
            ),
        ],
        style={
            "display": "flex",
            "width": "100%",
            "justify-content": "center",
            "align-items": "center",
            "flex-direction": "column",
            "gap": "20px",
        },
    )


@callback(
    Output("project-info", "children"),
    Input("project", "data"),
)
def update_project_info(project):
    return html.Div(
        [
            "These settings apply to the current project: ",
            html.B(project),
        ]
    )


@callback(
    Input("project-folder", "value"),
)
def update_project_folder(value):
    config = ConfigManager()
    config.set_project_folder(value)


@callback(
    Input("dark-mode", "data"),
)
def update_dark_mode(value):
    print("Dark mode:", value)


def register_callbacks(app):
    @callback(
        Output("dark-mode", "data"),
        Input("dark-mode-toggle", "value"),
    )
    def set_dark_mode(value):
        return 1 in value


@callback(
    Input("db-backup-dropdown", "value"),
    State("project", "data"),
)
def update_db_backup(db_backup_policy, project):
    projectObj = utils.get_project(project)
    projectObj.set_db_backup_policy(db_backup_policy)
