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
