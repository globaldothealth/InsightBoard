from dash import html, Input, Output, State, callback_context, callback

from InsightBoard.chatbot.datachat import dc, ChatbotState

state = ChatbotState()

# Chat history


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
        response, is_query, viz = dc.ask_sql(user_input)

        # If the response is an SQL query, execute it
        if is_query:

            def sql_response(response):
                return html.Div(response, style={"fontSize": "0.8em"})

            bot_response = {"role": "bot", "message": sql_response(response)}
            chat_history.append(bot_response)
            query_response = dc.execute_query(response, viz)
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
