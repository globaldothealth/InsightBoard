import json
import logging
import requests

from InsightBoard.config import ConfigManager
from InsightBoard.chatbot.dc_base import DataChat_Base

config = ConfigManager()


class DataChat_OpenAI_REST(DataChat_Base):
    SUPPORTED_MODELS = ["gpt-4o-mini"]

    def __init__(self, model=None, project=None, table=None):
        super().__init__(model, project, table)

    # override
    def base_url(self):
        return (
            "https://api.openai.com/v1/chat/completions"
        )

    # override
    def set_model(self, model):
        if model not in self.SUPPORTED_MODELS:
            self.model = None
            raise ValueError(f"Model {model} is not supported by OpenAI REST API")
        self.model = model

    # override
    def send_query(self, chat: [str]) -> str:
        if not isinstance(chat, list):
            chat = [chat]
        api_key = config.get("chatbot.api_key", default=None)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": c} for c in chat
            ],
            "temperature": 0.7,
        }
        logging.info(f"Sending request to chatbot: {payload}")
        response = requests.post(
            self.base_url(),
            headers=headers,
            data=json.dumps(payload),
        )
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: "
                f"{response.text}"
            )
        response_data = response.json()
        bot_response = response_data["choices"][0]["message"]["content"]
        logging.info(f"Bot response: {response_data}")
        return bot_response
