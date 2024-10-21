import json
import logging
import requests
import plotly.express as px
from typing import Tuple
from dash import dcc, html
from dash import dash_table
from pathlib import Path
from tempfile import NamedTemporaryFile

import InsightBoard.chatbot.prompts as prompts
import InsightBoard.utils as utils
from InsightBoard.config import ConfigManager


# Remove any existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("Logging started")


config = ConfigManager()
API_KEY = config.get("chatbot.api_key", None)


class DataChat:
    SUPPORTED_MODELS = ["gemini-1.5-flash"]

    def __init__(self, model=None, project=None, table=None):
        self.set_model(model)

        self.project = None
        self.table = None
        if project and table:
            self.set_table(project, table)

        self.chat_history = []
        self.prompt_sql_template = prompts.sql_template
        self.prompt_sql_viz = prompts.sql_viz

    def is_chatbot_ready(self):
        not_set = []
        if not self.model:
            not_set.append("model")
        if not self.project:
            not_set.append("project")
        if not self.table:
            not_set.append("table")
        return (
            not not_set,
            f"Chatbot is not ready, please set {', '.join(not_set)}",
        )

    def set_model(self, model):
        match model:
            case "gemini-1.5-flash":
                self.model = model
                self.url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-1.5-flash-latest:generateContent?key={API_KEY}"
                )
            case _:
                self.model = None

    def set_table(self, project=None, table=None):
        if not project or not table:
            raise ValueError("Project and table names must be provided.")
        self.project = project
        self.table = table
        projectObj = utils.get_project(self.project)
        self.json_schema = projectObj.get_schema(self.table)

    def prompt_sql(self) -> str:
        return self.prompt_sql_template.format(
            table=self.table,
            schema=json.dumps(self.json_schema),
        )

    def send_query(self, chat: [str]) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": p} for p in chat]}]}
        logging.info(f"Sending request to chatbot: {payload}")
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: {response.text}"
            )
        response_data = response.json()
        bot_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
        logging.info(f"Bot response: {response_data}")
        return bot_response

    def ask_sql(self, query: str) -> Tuple[str, bool, str]:
        """
        Ask the chatbot a question and return the response.

        Parameters
        ----------
        query : str
            The question to ask the chatbot.

        Returns
        -------
        sql: str
            The chatbot's response (SQL query).
        is_query : bool
            Whether the response is an SQL query or not.
        viz_suggestion : str
            The chatbot's visualization suggestion (see prompts.sql_viz for options).
        """
        ready, msg = self.is_chatbot_ready()
        if not ready:
            return msg, False, None

        # Ask the chatbot for an SQL query that answers the question
        try:
            sql_prompt = self.prompt_sql()
            bot_response = self.send_query(
                [
                    sql_prompt,
                    query,
                ]
            )
        except Exception as e:
            return (
                f"Error asking chatbot: {str(e)}",
                False,
                None,
            )

        # Ask the chatbot for a visualization suggestion
        viz_suggestion = None
        if bot_response.startswith("```sql\n"):
            bot_response = bot_response[7:-4]
            is_query = True
            # Add prompt for visualization
            try:
                viz_suggestion = self.send_query(
                    [
                        sql_prompt,
                        query,
                        bot_response,
                        self.prompt_sql_viz,
                    ]
                )
            except Exception:
                pass
        else:
            is_query = False
        return bot_response, is_query, viz_suggestion

    def parse_viz_suggestion(self, viz_suggestion: str) -> [str]:
        if not viz_suggestion:
            return None, None

        def dequote(s):
            if s[0] == s[-1] and s.startswith(("'", '"')):
                return s[1:-1]
            return s

        fcn_name = viz_suggestion.split("(")[0].strip() if "(" in viz_suggestion else "none"
        if fcn_name == "none":
            return [fcn_name]
        args = viz_suggestion.split("(")[1].split(")")[0].split(",")
        args = [dequote(arg.strip()) for arg in args]
        return [fcn_name, *args]

    def execute_query(self, query, viz):
        import pandas as pd
        import sqlite3

        # Read the Parquet file into a Pandas DataFrame and transfer to SQLite
        # (inefficient, but proof of concept)

        # ### Should not analyze versioned data - only clean data - read from database
        projectObj = utils.get_project(self.project)
        data = projectObj.database.read_table(self.table)
        with NamedTemporaryFile(suffix=".db", delete=False) as tempfile:
            try:
                Path(tempfile.name).unlink()  # Remove the file if it exists
                conn = sqlite3.connect(tempfile.name)  # Create or connect
                data.to_sql(self.table, conn, if_exists="replace", index=False)
                # Run a SQL query on the SQLite database and close the connection
                df = pd.read_sql_query(query, conn)
                conn.close()
            except Exception as e:
                return f"Error executing query: {str(e)}"
        Path(tempfile.name).unlink()

        # Visualize the data
        fig = None
        fcn_name, *args = self.parse_viz_suggestion(viz)
        match fcn_name:
            case "line":
                col1, col2 = args
                fig = px.line(df, x=col1, y=col2)
            case "histogram":
                col1 = args[0]
                fig = px.histogram(df, x=col1)
            case "scatter":
                col1, col2 = args
                fig = px.scatter(df, x=col1, y=col2)
            case "bar":
                col1, col2 = args
                fig = px.bar(df, x=col1, y=col2)
            case "pie":
                col1 = args[0]
                fig = px.pie(df, names=col1)
            case "bubble":
                col1, col2, col3 = args
                fig = px.scatter(df, x=col1, y=col2, size=col3)
            case "geo_iso3":
                location, color, size = args
                fig = px.scatter_geo(df, locations=location, color=color, size=size)
            case "none":
                pass

        # Return the query result as a Dash DataTable
        data_table = dash_table.DataTable(
            id="table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            page_size=10,
            style_table={"overflowX": "auto"},
        )

        if fig:
            return html.Div([data_table, dcc.Graph(figure=fig)])

        return html.Div([data_table])


class ChatbotState:
    _instance = None

    # Make ChatbotState a singleton instance
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChatbotState, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.display = "none"  # Initially hidden
        self.width = "50vw"
        self.height = "80vh"
        self.chat_history = []


dc = DataChat(
    config.get("chatbot.model", None),
    config.get("chatbot.project", None),
    config.get("chatbot.table", None),
)
