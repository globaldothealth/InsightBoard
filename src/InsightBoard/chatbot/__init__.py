import os
import plotly.express as px
from typing import Tuple
from dash import dcc, html, Input, Output, State, callback_context, callback
import dash_bootstrap_components as dbc
from dash import dash_table

API_KEY = os.getenv("CHATBOT_API_KEY")


import requests
import json


prompt_text = """
You are a research assistant for an epidemiological laboratory.
Data is stored in SQLite within the '{table}' table.
You must respond to questions with a valid SQL query.
Do not return any natural language explanation, only the SQL query.

The dataset has the following json schema:
{schema}
"""


class DataChat:
    def __init__(self):
        self.chat_history = []
        self.url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash-latest:generateContent?key={API_KEY}"
        )
        self.table = "linelist"
        self.prompt_text = prompt_text
        with open(
            "linelist.schema.json"
        ) as f:
            self.json_schema = json.load(f)

    def prompt(self):
        return self.prompt_text.format(
            table=self.table,
            schema=json.dumps(self.json_schema),
        )

    def ask(self, query) -> Tuple[str, bool]:
        """
        Ask the chatbot a question and return the response.

        Parameters
        ----------
        query : str
            The question to ask the chatbot.

        Returns
        -------
        str
            The chatbot's response.
        is_query : bool
            Whether the response is an SQL query or not.
        """
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": self.prompt()}, {"text": query}]}]}
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            response_data = response.json()
            bot_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
            if bot_response.startswith("```sql\n"):
                bot_response = bot_response[7:-4]
                is_query = True
            else:
                is_query = False
            return bot_response, is_query
        else:
            return (
                f"Request failed with status code {response.status_code}: "
                "{response.text}"
            ), False

    def execute_query(self, query):
        import pandas as pd
        import sqlite3

        # Read the Parquet file into a Pandas DataFrame and transfer to SQLite
        # ### Should not analyze versioned data - only clean data - read from database
        filename = "linelist.parquet"
        data = pd.read_parquet(filename)
        conn = sqlite3.connect("linelist.db")  # Create or connect to the database
        data.to_sql(
            "linelist", conn, if_exists="replace", index=False
        )
        # Run a SQL query on the SQLite database and close the connection
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Line chart of col 1 vs col 2
        fig = px.line(df, x=df.columns[0], y=df.columns[1])

        if False:
            # Simple graph to demonstrate functionality - only works on limited queries
            return html.Div(
                [
                    html.H4("Query Result"),
                    dcc.Graph(figure=fig),
                ],
                style={"margin": "10px 0"},
            )

        # Return the query result as a Dash DataTable
        return html.Div(
            [
                dash_table.DataTable(
                    id="table",
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict("records"),
                    page_size=10,
                    style_table={"overflowX": "auto"},
                )
            ]
        )


dc = DataChat()


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


state = ChatbotState()


# Chatbot popup overlay layout with native resize (bottom-right corner)
chatbot_overlay = html.Div(
    id="chatbot-overlay",
    style={
        "position": "fixed",
        "bottom": "80px",  # Position the overlay just above the button
        "right": "20px",
        "width": state.width,
        "height": state.height,
        "background-color": "white",
        "box-shadow": "0px 4px 12px rgba(0, 0, 0, 0.1)",
        "border-radius": "10px",
        "padding": "15px",
        "display": state.display,
        "z-index": "1000",  # Make sure it's on top
        "overflow-y": "auto",  # Allows scrolling if content overflows
        "resize": "both",  # Allow resizing from the bottom-right corner
        "min-width": "200px",  # Set minimum width
        "min-height": "200px",  # Set minimum height
        "max-height": "90%",  # Limit height to screen size
        "max-width": "90%",  # Limit width to screen size
    },
    children=[
        html.Div(
            "Chat with Bot",
            style={"font-weight": "bold", "margin-bottom": "10px"},
        ),
        dcc.Loading(
            type="default",
            children=[
                html.Div(
                    id="chat-container",
                    style={"overflow-y": "auto"},
                ),
            ],
        ),
        html.Br(),
        dbc.Input(id="user-input", placeholder="Type your message...", type="text"),
        dbc.Button(
            "Send",
            id="send-button",
            n_clicks=0,
            color="primary",
            style={"margin-top": "10px"},
        ),
    ],
)

# Floating button layout
floating_chat_button = html.Div(
    dbc.Button(
        "💬",
        id="open-chatbot",
        color="primary",
        style={"border-radius": "50%", "font-size": "24px"},
    ),
    style={
        "position": "fixed",
        "bottom": "20px",
        "right": "20px",
        "z-index": "999",
    },
)


# Layout for the page
def layout():
    return html.Div(
        [
            dcc.Store(
                id="store-chat-history", data=[]
            ),  # Store chat history to keep across pages
            dcc.Store(id="chatbot-state-display", data=state.display),
            dcc.Store(id="chatbot-state-width", data=state.width),
            dcc.Store(id="chatbot-state-height", data=state.height),
            floating_chat_button,  # The floating button
            chatbot_overlay,  # The chatbot overlay
            dcc.Interval(
                id="scroll-interval", interval=500, n_intervals=0, max_intervals=1
            ),  # For auto-scrolling
        ],
    )


# Helper function to add chat bubbles for text and images
def format_chat_bubble(role, message=None, image_url=None):
    if role == "user":
        # User's message (aligned right)
        return html.Div(
            message,
            style={
                "text-align": "right",
                "background-color": "#dcf8c6",
                "border-radius": "10px",
                "padding": "8px",
                "margin": "5px 0",
            },
        )
    elif role == "bot":
        # Bot's text message (aligned left)
        if message:
            return html.Div(
                message,
                style={
                    "text-align": "left",
                    "background-color": "#f1f0f0",
                    "border-radius": "10px",
                    "padding": "8px",
                    "margin": "5px 0",
                },
            )
        # Bot's image response
        elif image_url:
            return html.Div(
                html.Img(
                    src=image_url,
                    style={
                        "max-width": "100%",
                        "border-radius": "10px",
                        "margin": "5px 0",
                    },
                ),
                style={"text-align": "left", "padding": "8px", "margin": "5px 0"},
            )


# Add Chatbot client-side callbacks
def initialize_chatbot():
    # auto-scroll when new elements are added to the chat container
    from InsightBoard import app

    app.clientside_callback(
        """
        function(children) {
            const chatContainer = document.getElementById('chat-container');
            if (chatContainer) {
                // Auto-scroll to the bottom of the container
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            return null;
        }
        """,
        Output("scroll-interval", "n_intervals"),
        [Input("chat-container", "children")],
    )


# Chat history


@callback(
    Output("store-chat-history", "data"),
    Input("send-button", "n_clicks"),
    State("user-input", "value"),
    State("store-chat-history", "data"),
)
def chat_history_state(n_clicks, user_input, chat_history):
    # Track callback context
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0]

    if not n_clicks:
        chat_history = state.chat_history

    if n_clicks > 0 and triggered == "send-button":
        # Append user input to the chat history
        chat_history.append({"role": "user", "message": user_input})

        # Make bot request
        response, is_query = dc.ask(user_input)

        # If the response is an SQL query, execute it
        if is_query:
            def sql_response(response):
                return html.Div(response, style={'fontSize': '0.8em'})
            bot_response = {"role": "bot", "message": sql_response(response)}
            chat_history.append(bot_response)
            query_response = dc.execute_query(response)
            chat_history.append({"role": "bot", "message": query_response})
        else:
            bot_response = {"role": "bot", "message": response}
            chat_history.append(bot_response)

    state.chat_history = chat_history

    return chat_history


@callback(
    Output("chat-container", "children"),
    Input("store-chat-history", "data"),
)
def chat_history_ui(chat_history):
    # Rebuild conversation after bot response
    conversation = []
    for entry in chat_history:
        if entry["role"] == "user":
            conversation.append(
                format_chat_bubble(role="user", message=entry["message"])
            )
        elif entry["role"] == "bot":
            if "message" in entry:
                conversation.append(
                    format_chat_bubble(role="bot", message=entry["message"])
                )
            elif "image_url" in entry:
                conversation.append(
                    format_chat_bubble(role="bot", image_url=entry["image_url"])
                )

    return conversation


# Display on/off


@callback(
    Output("chatbot-state-display", "data"),
    Input("open-chatbot", "n_clicks"),
)
def display_state(n_clicks):
    if n_clicks:
        if state.display == "none":
            state.display = "block"
        else:
            state.display = "none"
    return state.display


@callback(
    Output("chatbot-overlay", "style"),
    Input("chatbot-state-display", "data"),
    State("chatbot-overlay", "style"),
)
def display_ui(display, style):
    style["display"] = display
    return style
