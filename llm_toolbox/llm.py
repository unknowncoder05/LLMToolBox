import openai
import json
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ModelResponseError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class GPTPetition:
    functions: dict = {}

    def __init__(self, model_name="gpt-3.5-turbo-0613"):
        self.model_name = model_name
        self.messages = list()
        return

    def add_function(
        self, function, name, description, parameters=None, parameters_schema=None
    ):
        # TODO: validate one of parameters_schema or parameters
        self.functions[name] = dict(
            definition=dict(
                name=name,
                description=description,
                parameters=parameters_schema
                if parameters_schema
                else {
                    "type": "object",
                    "properties": parameters,
                },
            ),
            function=function,
        )
        logger.debug(f"GPT: Added function {name}")

    def _add_message(self, role, content, name=None):
        data = dict(role=role, content=content)
        if name:
            data["name"] = name
        self.messages.append(data)

    def system(self, content):
        self._add_message("system", content)

    def user(self, content):
        self._add_message("user", content)

    def assistant(self, content):
        self._add_message("assistant", content)

    def function(self, content, function_name):
        self._add_message("function", content, function_name)

    def execute(self, calls=0, limit_calls=-1, function_call="auto"):
        logger.debug(f"GPT: api call {self.messages}")
        print("MESSAGES")
        for message in self.messages:
            print(message["role"], ":", message["content"])

        if self.functions.values():
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=self.messages,
                functions=[f["definition"] for f in self.functions.values()],
                function_call=function_call,
            )
        else:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=self.messages,
            )

        message = response["choices"][0]["message"]
        messages = [message]
        print("GPTR:", message)

        # Step 2, check if the model wants to call a function
        if message.get("function_call"):
            logger.debug(f"GPT: function_call {message}")
            function_name = message["function_call"]["name"]

            # Args
            try:
                function_args = json.loads(message["function_call"]["arguments"])
            except json.decoder.JSONDecodeError:
                raise ModelResponseError("model response arguments not in json")

            if function_name not in self.functions:
                raise ModelResponseError(f'"{function_name}" function not registered')

            function = self.functions[function_name]["function"]

            # Function call
            try:
                function_response = function(**function_args)
            except TypeError as e:
                logger.error(f"GPT: {e} {function_args}")
                raise ModelResponseError("model function call error")

            try:
                verbose_function_response = dict(name=function_name)
                verbose_function_response['content'] = json.dumps(function_response)
            except TypeError as e:
                logger.error(f"GPT: {e} {function_args}")
                raise Exception("function response is not JSON serializable")

            self.messages.extend(
                [
                    #message,
                    {
                        "role": "function",
                        "name": function_name,
                        "content": verbose_function_response['content'],
                    },
                ]
            )

            # Step 4, send model the info on the function call and function response
            if ((not isinstance(function_response, dict) or not function_response.get('success'))
                    and limit_calls != -1 and calls == 0):
                # The function failed so we call again for GPT to add instructions to the user in a second message.
                inner_messages, _ = self.execute(calls + 1)
                return inner_messages, verbose_function_response
            elif limit_calls != -1 and calls + 1 >= limit_calls:
                return messages, verbose_function_response
            else:
                inner_messages, _ = self.execute(calls + 1)
                return messages + inner_messages, verbose_function_response
        return messages, None


if __name__ == "__main__":
    import os
    import openai

    openai.api_key = os.getenv("OPEN_AI_API_KEY")
    from api.jobai.services.gpt import GPTPetition

    petition = GPTPetition()
    petition.system(
        """you are a job seeking assistant that:
    1. gets the missing user information and saves it, you want to follow this route
        a. collect name "To start, could you pleas tell me your full name?"
        b. collect contact info "Could you please provide your phone number, email address ..."
        c. collect objective/summary "Do you have a short professional summary or career objective you'd like to add at the top of your resume? if you are unsure, I can help guide you"
    2. if the user asks you to make an action that is not in this list, say "am sorry but that is out of my current capabilities"
    """
    )
    petition.user("take me to the moon")

    def get_jobs_by_rol(role):
        return ["gugle", "facebuk"]

    petition.add_function(
        get_jobs_by_rol,
        "get_jobs_by_rol",
        "gets the best job matches for an specific role",
        {
            "role": {
                "type": "string",
                "description": "name of the professional role",
            }
        },
    )

    print(petition.execute())
