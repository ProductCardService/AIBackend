from langchain.prompts import PromptTemplate
from langchain_community.llms import YandexGPT
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain_core.messages import AIMessage
import os
import yaml
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")

script_dir = os.path.dirname(__file__)
prompts_path = os.path.join(script_dir, 'prompts.yaml')

with open(prompts_path, "r") as f:
    prompts = yaml.safe_load(f)

FOOD_TEMPLATE = PromptTemplate.from_template(prompts['food'])
DESCRIPTION_TEMPLATE = PromptTemplate.from_template(prompts['description'])

output_parser = CommaSeparatedListOutputParser()

def parse(ai_message: AIMessage) -> str:
    """Parse the AI message."""
    return ai_message.rstrip('.').lower()

model = YandexGPT(
    api_key=API_KEY, 
    folder_id=FOLDER_ID, 
    temperature=0, 
    model_name='yandexgpt'
)

food_chain = FOOD_TEMPLATE | model | parse | output_parser
description_chain = DESCRIPTION_TEMPLATE | model
