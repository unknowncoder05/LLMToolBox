import openai
import json
from llm_toolbox.exceptions import ModelResponseError
from llm_toolbox.llm import LLMPetition
from llm_toolbox import custom_logger

log = custom_logger.get_logger(__name__)

def check_model(model_name):
    allowed = ['gpt-3.5-turbo-0613']
    return model_name in allowed

class ChatGptPetition(LLMPetition):
    functions: dict = {}

    def __init__(self, model_name='gpt-3.5-turbo-0613'):
        self.model_name = model_name
        self.messages = list()
        return
    
    def _check_model(self, model_name):
        return check_model(model_name)
    
    def _add_message(self, role, content):
        self.messages.append(dict(role=role, content=content))
    
    def _execute(self):
        return ''

    def add_function(self, function, name, description, parameters):
        self.functions[name] = dict(
            definition=dict(
                name=name,
                description=description,
                parameters={
                    "type": "object",
                    "properties": parameters,
                    "required": ["role"],
                }
            ),
            function=function
        )

    def system(self, content):
        self._add_message('system', content)
    
    def user(self, content):
        self._add_message('user', content)
    
    def assistant(self, content):
        self._add_message('assistant', content)

    def _execute(self, calls=0, limit_calls=-1):
        petition_kwargs = {}
        if self.functions:
            petition_kwargs['functions']=[f['definition'] for f in self.functions.values()]
            petition_kwargs['function_call']="auto"

        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=self.messages,
            **petition_kwargs
        )

        message = response["choices"][0]["message"]

        # Step 2, check if the model wants to call a function
        log.info(f"message: {message}")
        if message.get("function_call"):
            function_name = message["function_call"]["name"]

            if function_name not in self.functions:
                raise ModelResponseError(
                    f'"{function_name}" function not registered')
            
            # Args
            function_call_arguments = message["function_call"]["arguments"]
            try:
                function_args = json.loads(function_call_arguments)
            except json.decoder.JSONDecodeError:
                log.error(f"function_call arguments: {function_call_arguments}")
                raise ModelResponseError(
                    'model response arguments not in json')

            function = self.functions[function_name]['function']

            # Function call
            try:
                function_response = function(**function_args)
                function_response = json.dumps(function_response)
            except TypeError as e:
                log.error(e)
                raise ModelResponseError('model response arguments invalid')

            self.messages.extend([
                message,
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            ])

            # Step 4, send model the info on the function call and function response
            second_response = self.execute(calls+1, limit_calls)
            return second_response
        return message