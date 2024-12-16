try:
    import adtl.autoparser as autoparser
except ImportError:
    autoparser = None


class AutoParser:
    def __init__(self, model=None, api_key=None, schema=None):
        self.model = model
        self.api_key = api_key

        # find appropriate way to get the config file & schema
        self.schema = schema
        self.config = None

        # created attributes
        self.data_dict = None
        self.mapping_file = None
        # don't need to save the parser, it'll get written out

    @property
    def is_autoparser_ready(self):
        not_set = []
        if not self.model:
            not_set.append("model")
        if not self.api_key:
            not_set.append("api key")
        if not self.schema:
            not_set.append("schema")

        return (
            not not_set,
            f"AutoParser is not ready, please set {', '.join(not_set)}",
        )

    def create_dict(self, data, language, llm_descriptions):
        ready, msg = self.is_autoparser_ready
        if not ready:
            return msg, None

        # currently config doesn't make any difference
        self.data_dict = autoparser.create_dict(data, config=self.config)

        # this config won't be right
        if llm_descriptions:
            self.data_dict = autoparser.generate_descriptions(
                self.data_dict,
                language,
                key=self.api_key,
                llm=self.model,
                config=self.config,
            )

        return self.data_dict

    def create_mapping(self):
        if not self.data_dict:
            return "No data dictionary provided", None

        self.mapping = autoparser.create_mapping(
            self.data_dict,
            self.schema,
            self.api_key,
            llm=self.model,
            config=self.config,
        )

        return "Sucess", self.mapping

    def create_parser(self):
        if not self.mapping:
            return "No mapping file", None

        autoparser.create_parser(
            self.mapping, self.schema, "file path for parser", config=self.config
        )

        return "Parser saved to <file path>", True
