import dash
import dash_bootstrap_components as dbc

from dash import html, dcc, callback, Input, Output, State

import InsightBoard.utils as utils
from InsightBoard.config import ConfigManager
from InsightBoard.chatbot import is_chatbot_enabled
from InsightBoard.database import DatabaseBackend, BackupPolicy
from InsightBoard.chatbot import chatbot_model_providers as chatbot_provider

# Register the page
dash.register_page(__name__, path="/settings")


# Layout for the Data Page
def layout():
    config = ConfigManager()

    tab_chatbot = []
    if is_chatbot_enabled():
        tab_chatbot = [
            dcc.Tab(
                label="Chatbot",
                children=[dbc.Card(dbc.CardBody(chatbot_settings(config)))],
            ),
        ]

    return html.Div(
        [
            html.Div(
                [
                    dcc.Store(id="project"),
                    html.H1("Settings"),
                    dcc.Tabs(
                        [
                            dcc.Tab(
                                label="General",
                                children=[
                                    dbc.Card(dbc.CardBody(general_settings(config)))
                                ],
                            ),
                            *tab_chatbot,
                            dcc.Tab(
                                label="Project",
                                children=[
                                    dbc.Card(dbc.CardBody(project_settings(config)))
                                ],
                            ),
                        ],
                    ),
                ],
                style={
                    "width": "67%",
                    "minWidth": "400px",
                    "maxWidth": "800px",
                    "alignItems": "center",
                },
            )
        ],
        style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "height": "100%",
        },
    )


def general_settings(config):
    project_folder = config.get_project_folder()
    dark_mode = config.get("theme.dark_mode", False)
    return [
        html.H6("Project folder"),
        dcc.Input(
            id="project-folder",
            value=project_folder,
            style={"width": "100%"},
        ),
        html.H6("Theme"),
        dbc.Checklist(
            id="dark-mode-toggle",
            options=[
                {
                    "label": "Dark mode",
                    "value": 1,
                },
            ],
            value=[1] if dark_mode else [],
            inline=True,
            switch=True,
        ),
    ]


def chatbot_settings(config):
    chatbot_model_list = [{"label": k, "value": k} for k in sorted(chatbot_provider)]
    chatbot_model = config.get("chatbot.model", None)
    chatbot_api_key = config.get("chatbot.api_key", "")
    return [
        dbc.Alert(
            "You must restart the InsightBoard server for model changes to take effect",
            id="chatbot-restart-alert",
            color="warning",
        ),
        html.H6("Model"),
        dbc.Col(
            dcc.Dropdown(
                id="chatbot-model",
                options=chatbot_model_list,
                value=chatbot_model,
                style={"width": "100%"},
            ),
            width=12,
        ),
        html.P(
            "This settings is read first from the InsightBoard configuration, "
            "then environment variable CHATBOT_MODEL",
            style={"font-weight": "lighter", "opacity": "0.7", "fontSize": "0.8em"},
        ),
        html.H6("API key"),
        dbc.Input(
            id="chatbot-api-key",
            type="password",
            value=chatbot_api_key,
            style={"width": "100%"},
        ),
        html.P(
            "This settings is read first from the InsightBoard configuration, "
            "then environment variable CHATBOT_API_KEY",
            style={"font-weight": "lighter", "opacity": "0.7", "fontSize": "0.8em"},
        ),
        dbc.Button("Show API key", id="show-api-key", color="primary"),
    ]


def project_settings(config):
    db_backend_list = [
        {
            "label": "Flat file (Parquet, unversioned)",
            "value": DatabaseBackend.PARQUET.name,
        },
        {
            "label": "Flat file (Parquet, versioned)",
            "value": DatabaseBackend.PARQUET_VERSIONED.name,
        },
        {
            "label": "SQL (SQLite)",
            "value": DatabaseBackend.SQLITE.name,
        },
    ]
    if utils.check_module("duckdb"):
        db_backend_list.append(
            {
                "label": "SQL (DuckDB)",
                "value": DatabaseBackend.DUCKDB.name,
            }
        )
    db_backend = DatabaseBackend.PARQUET.name
    db_backup_policy_list = [
        {"label": "None", "value": BackupPolicy.NONE.name},
        {"label": "Timestamp copies", "value": BackupPolicy.TIMESTAMPED_COPIES.name},
    ]
    db_backup = BackupPolicy.NONE.name
    return [
        dbc.Alert(
            "These settings apply to the current project: {project}",
            id="project-info",
            color="info",
        ),
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
        dbc.Button(
            "Set as defaults",
            id="set-project-defaults",
            color="primary",
            disabled=True,
        ),
    ]


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
        db_backend.name,
        db_backup_policy.name,
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
    projectObj.set_db_backend(DatabaseBackend[db_backend])


@callback(
    Input("db-backup-dropdown", "value"),
    State("project", "data"),
)
def update_db_backup(db_backup_policy, project):
    projectObj = utils.get_project(project)
    projectObj.set_db_backup_policy(BackupPolicy[db_backup_policy])


@callback(
    Output("dark-mode", "data"),
    Input("dark-mode-toggle", "value"),
)
def update_dark_mode(value):
    config = ConfigManager()
    dark_mode = 1 in value
    config.set("theme.dark_mode", dark_mode)
    return dark_mode


@callback(
    Input("chatbot-model", "value"),
    State("project", "data"),
)
def update_chatbot_model(model, project):
    if model not in chatbot_provider:
        raise ValueError(f"Unable to determine model provider for model: {model}")
    config = ConfigManager()
    config.set("chatbot.model", model)
    config.set("chatbot.provider", chatbot_provider[model])


@callback(
    Input("chatbot-api-key", "value"),
    State("project", "data"),
)
def update_chatbot_api_key(api_key, project):
    config = ConfigManager()
    config.set("chatbot.api_key", api_key)


@callback(
    Output("chatbot-api-key", "type"),
    Output("show-api-key", "value"),
    Input("show-api-key", "n_clicks"),
    State("chatbot-api-key", "type"),
)
def show_api_key(n_clicks, input_type):
    if n_clicks:
        return (
            ("text", "Hide API key")
            if input_type == "password"
            else ("password", "Show API key")
        )
    raise dash.exceptions.PreventUpdate
