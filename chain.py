import os
import time
import json
import yaml
import requests
import re
import logging
import sys
from fastapi import FastAPI, HTTPException

from dotenv import load_dotenv

from langchain_core.messages import AIMessage
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain_core.output_parsers.base import BaseOutputParser
from langchain_community.llms import GigaChat
from langchain.prompts import PromptTemplate

load_dotenv()

logging.basicConfig(level=logging.ERROR, stream=sys.stderr, format='%(asctime)s %(levelname)s %(message)s')

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
        if text.endswith('<new_description>'):
            text = text[:-len('<new_description>')]
        lines = re.split('<new_description>', text.strip())
        texts = [
            line.replace('<new_description>', '').replace('</new_description>', '').replace('\n', '').strip() 
            for line in lines
        ]
        
        for item in texts:
            if ('new_description' in item) or (not item):
                raise ValueError("Invalid generation")
        
        descriptions_len = 4
        if len(texts) != descriptions_len:
            raise ValueError("Invalid generation")
        
        return texts

    def get_format_instructions(self) -> str:
        return "The answer should be in the form of a list, with each element separated by a line break."
    
def parse(ai_message: AIMessage) -> str:
    """Parse the AI message."""
    return ai_message.rstrip('.').lower()

def check_list(data):
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, str):
                raise ValueError("Invalid generation: list contains non-string elements")
            if len(item) > 900:
                raise ValueError("Invalid generation: string length exceeds 900 characters")
        return data
    else:
        raise ValueError("Invalid generation: input is not a list")

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
        try:
            response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
            data = response.json()
            return data[0]['id']
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=422, detail=f"Failed to get model: {e}")
        except Exception as e:
            logging.error(f"Failed to get model: {e}")

    def generate(self, prompt, model, images=1, width=960, height=640):
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
        try:
            response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
            data = response.json()
            return data['uuid']
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=422, detail=f"Failed to generate image: {e}")
        except Exception as e:
            logging.error(f"Failed to generate image: {e}")

    def check_generation(self, request_id, attempts=100, delay=20):
        try:
            while attempts > 0:
                response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
                data = response.json()
                if data['status'] == 'DONE':
                    return data['images']

                attempts -= 1
                time.sleep(delay)
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=422, detail=f"Failed to check generation status: {e}")
        except Exception as e:
            logging.error(f"Failed to check generation status: {e}")

def get_img(prompt):
    try:
        api = Text2ImageAPI('https://api-key.fusionbrain.ai/', KANDINSKY_API_KEY, KANDINSKY_SECRET_KEY)
        model_id = api.get_model()
        uuid = api.generate(prompt, model_id)
        images = api.check_generation(uuid)
        image_base64 = "data:image/jpg;base64," + images[0] 
        return image_base64
    except Exception as e:
        logging.error(f"System error: {e}")
        raise HTTPException(status_code=422, detail=f"System error: {e}")


model_lite = GigaChat(
    credentials=GIGACHAT_CREDENTIALS, 
    model="GigaChat",
    top_p=0.6,
    verify_ssl_certs=False
)

model_pro = GigaChat(
    credentials=GIGACHAT_CREDENTIALS, 
    model="GigaChat-Pro",
    top_p=0.9,
    verify_ssl_certs=False
)

tags_chain = TAGS_TEMPLATE | model_pro | parse | output_parser
description_chain = DESCRIPTION_TEMPLATE | model_pro | new_line_output_parser
food_chain = (
    FOOD_TEMPLATE 
    | model_lite 
    | parse 
    | output_parser
    | check_list
)
image_chain = IMAGE_TEMPLATE | model_lite | get_img
