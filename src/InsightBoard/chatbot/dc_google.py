import json
import logging
import requests

from InsightBoard.config import ConfigManager
from InsightBoard.chatbot.dc_base import DataChat_Base

config = ConfigManager()


class DataChat_Google_REST(DataChat_Base):
    SUPPORTED_MODELS = ["gemini-1.5-flash"]

    def __init__(self, model=None, project=None, table=None):
        super().__init__(model, project, table)

    # override
    def base_url(self, model, api_key):
        model = model or self.model
        api_key = api_key or self.api_key
        return (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}-latest:generateContent?key={api_key}"
        )

    # override
    def set_model(self, model):
        if not model:
            self.model = None
            return
        if model not in self.SUPPORTED_MODELS:
            self.model = None
            raise ValueError(f"Model {model} is not supported")
        self.model = model

    # override
    def send_query(self, chat: [str]) -> str:
        if not isinstance(chat, list):
            chat = [chat]
        api_key = config.get("chatbot.api_key", default=None)
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": p} for p in chat]}]}
        logging.info(f"Sending request to chatbot: {payload}")
        response = requests.post(
            self.base_url(self.model, api_key),
            headers=headers,
            data=json.dumps(payload),
        )
        if response.status_code != 200:
            raise ValueError(
                f"Request failed with status code {response.status_code}: "
                f"{response.text}"
            )
        response_data = response.json()
        bot_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
        logging.info(f"Bot response: {response_data}")
        return bot_response
