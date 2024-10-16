import dash
import dash_bootstrap_components as dbc

from dash import html, dcc, callback, Input, Output, State

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

    dark_mode = config.get("theme.dark_mode", False)

    db_backend_list = [
        {"label": "Flat file (Parquet, unversioned)", "value": "parquet"},
        {"label": "Flat file (Parquet, versioned)", "value": "parquet_versioned"},
    ]
    db_backend = "parquet"

    db_backup_policy_list = [
        {"label": "None", "value": BackupPolicy.NONE.value},
        {"label": "Versioned", "value": BackupPolicy.VERSIONED.value},
        {"label": "Timestamp copies", "value": BackupPolicy.BACKUP.value},
    ]
    db_backup = BackupPolicy.NONE.value

    return html.Div(
        [
            # Store
            html.H1(
                "Settings",
                style={
                    "width": "67%",
                    "minWidth": "400px",
                    "maxWidth": "800px",
                    "border": "none",
                },
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
                        html.H5("Theme"),
                        dbc.Checklist(
                            id="dark-mode-toggle",
                            options=[
                                {"label": "Dark mode", "value": 1},
                            ],
                            value=[1] if dark_mode else [],
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
                                options=db_backend_list,
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
    [
        Output("project-info", "children"),
        Output("db-backend-dropdown", "value"),
        Output("db-backup-dropdown", "value"),
    ],
    [
        Input("project", "data"),
    ],
)
def update_project_info(project):
    projectObj = utils.get_project(project)
    db_backend = projectObj.get_db_backend()
    db_backup_policy = projectObj.get_db_backup_policy()
    return (
        html.Div(
            [
                "These settings apply to the current project: ",
                html.B(project),
            ]
        ),
        db_backend,
        db_backup_policy,
    )


@callback(
    Input("project-folder", "value"),
)
def update_project_folder(value):
    config = ConfigManager()
    config.set_project_folder(value)


@callback(
    Input("db-backend-dropdown", "value"),
    State("project", "data"),
)
def update_db_backend(db_backend, project):
    projectObj = utils.get_project(project)
    projectObj.set_db_backend(db_backend)


@callback(
    Input("db-backup-dropdown", "value"),
    State("project", "data"),
)
def update_db_backup(db_backup_policy, project):
    projectObj = utils.get_project(project)
    projectObj.set_db_backup_policy(db_backup_policy)


@callback(
    Output("dark-mode", "data"),
    Input("dark-mode-toggle", "value"),
)
def update_dark_mode(value):
    config = ConfigManager()
    dark_mode = 1 in value
    config.set("theme.dark_mode", dark_mode)
    config.save()
    return dark_mode
