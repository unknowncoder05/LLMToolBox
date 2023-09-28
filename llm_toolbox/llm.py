from llm_toolbox import custom_logger

log = custom_logger.get_logger(__name__)

class LLMPetition:

    def __init__(self, model_name):
        self.model_name = model_name
        self.messages = list()
        return
    
    def _check_model(self, model_name):
        return True
    
    def on_message(self):
        pass
    
    def _raw_add_message(self, message):
        self.messages.append(message)
        self.on_message(message)

    def _add_message(self, role, content):
        self._raw_add_message(dict(role=role, content=content))
    
    def _execute(self, calls=0, limit_calls=-1):
        return ''

    def add_message(self, role, content):
        self._add_message(role, content)

    def execute(self, calls=0, limit_calls=-1):
        log.debug(f"calls: {calls}, limit_calls: {limit_calls}")
        if limit_calls != -1 and limit_calls > calls:
            return
        return self._execute(calls)