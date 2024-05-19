from langchain.prompts import PromptTemplate
from langchain_community.llms import YandexGPT
from langchain_community.llms import GigaChat
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.output_parsers.base import BaseOutputParser
import re
import os
import json
import yaml
import time
import requests
from dotenv import load_dotenv

from uuid import uuid4

load_dotenv()

unique_id = uuid4().hex[0:8]

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "fitcha"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

API_KEY = os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
KANDINSKY_API_KEY = os.getenv('KANDINSKY_API_KEY')
KANDINSKY_SECRET_KEY = os.getenv('KANDINSKY_SECRET_KEY')

script_dir = os.path.dirname(__file__)
prompts_path = os.path.join(script_dir, 'prompts.yaml')

with open(prompts_path, "r", encoding='utf-8') as f:
    prompts = yaml.safe_load(f)


TAGS_TEMPLATE = PromptTemplate.from_template(prompts['tags'])
DESCRIPTION_TEMPLATE = PromptTemplate.from_template(prompts['description'])
FOOD_TEMPLATE = PromptTemplate.from_template(prompts['food'])
IMAGE_TEMPLATE = PromptTemplate.from_template(prompts['image'])


class NewlineOutputParser(BaseOutputParser):
    def parse(self, text: str) -> list:
        return re.split(r'\n', text.strip())

    def get_format_instructions(self) -> str:
        return "The answer should be in the form of a list, with each element separated by a line break."

def parse(ai_message: AIMessage) -> str:
    """Parse the AI message."""
    return ai_message.rstrip('.').lower()

new_line_output_parser = NewlineOutputParser()
output_parser = CommaSeparatedListOutputParser()


class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}",
                "title": "Detailed photo"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)


def get_img(prompt):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', KANDINSKY_API_KEY, KANDINSKY_SECRET_KEY)
    model_id = api.get_model()
    uuid = api.generate(prompt, model_id)
    images = api.check_generation(uuid)
    image_base64 = images[0] 

    return image_base64


model_lite = GigaChat(
    credentials=GIGACHAT_CREDENTIALS, 
    model="GigaChat",
    temperature=0.2,
    verify_ssl_certs=False
)

model_pro = GigaChat(
    credentials=GIGACHAT_CREDENTIALS, 
    model="GigaChat-Pro",
    temperature=0.5,
    verify_ssl_certs=False
)

tags_chain = TAGS_TEMPLATE | model_lite | parse
description_chain = DESCRIPTION_TEMPLATE | model_lite | new_line_output_parser
food_chain = FOOD_TEMPLATE | model_lite | parse | output_parser
image_chain = IMAGE_TEMPLATE | model_lite | get_img
