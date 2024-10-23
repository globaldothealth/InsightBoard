from InsightBoard.chatbot.layout import (  # noqa: F401
    layout,
    initialize_chatbot,
    set_table,
    is_chatbot_enabled,
)
from InsightBoard.chatbot.dc_base import (  # noqa: F401
    DataChat_Providers,
)

chatbot_model_providers = {
    # Google (REST API)
    "gemini-1.5-flash": "google_rest",
    "gemini-1.5-flash-8b": "google_rest",
    "gemini-1.5-pro": "google_rest",
    "gemini-1.0-pro": "google_rest",
    # OpenAI (REST API)
    "gpt-4o": "openai_rest",
    "o1-preview": "openai_rest",
    "o1-mini": "openai_rest",
    "gpt-4-turbo": "openai_rest",
    "gpt-4": "openai_rest",
    "gpt-3.5-turbo": "openai_rest",
}
