from InsightBoard.config import ConfigManager
from InsightBoard.chatbot.dc_base import (  # noqa: F401
    DataChat_Base,
    DataChat_Providers,
    DEFAULT_DATACHAT_PROVIDER,
)
from InsightBoard.chatbot.dc_google import DataChat_Google_REST
from InsightBoard.chatbot.dc_openai import DataChat_OpenAI_REST


class DataChat:
    def __new__(
        self,
        provider: DataChat_Providers = DEFAULT_DATACHAT_PROVIDER,
    ):
        config = ConfigManager()
        model = config.get("chatbot.model", default=None)
        project = config.get("chatbot.project", default=None)
        table = config.get("chatbot.table", default=None)
        match provider:
            case DataChat_Providers.GOOGLE_REST:
                return DataChat_Google_REST(model=model, project=project, table=table)
            case DataChat_Providers.OPENAI_REST:
                return DataChat_OpenAI_REST(model=model, project=project, table=table)
            case _:
                raise ValueError(f"Provider '{provider}' not supported.")


dc = DataChat(
    DataChat_Providers[
        ConfigManager().get("chatbot.provider", default="google_rest").upper()
    ]
)
