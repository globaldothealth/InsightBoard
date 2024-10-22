from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

import InsightBoard.chatbot.callbacks  # noqa: F401
from InsightBoard.chatbot.datachat import dc, ChatbotState
from InsightBoard.config import ConfigManager

state = ChatbotState()


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


def set_table(project, table):
    dc.set_table(project, table)


def is_chatbot_enabled():
    config = ConfigManager()
    return config.get("chatbot.enabled", default=False)
