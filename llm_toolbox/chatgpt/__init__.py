import os
import openai
from .chatgpt import *

# OpenAi
OPEN_AI_API_KEY = os.environ.get('OPEN_AI_API_KEY')
openai.api_key = OPEN_AI_API_KEY