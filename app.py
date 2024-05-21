import asyncio
from fastapi import FastAPI
from chain import (
    tags_chain, 
    description_chain, 
    image_chain, 
    food_chain
)
from pydantic import BaseModel


class PredictionInput(BaseModel):
    title: str

app = FastAPI(title="Product Card Service App")


@app.post("/generate/descriptions")
async def get_descriptions(pinput: PredictionInput):
    title = pinput.title
    descriptions = description_chain.invoke({"title": title})
    cleaned_descriptions = []
    for description in descriptions[1:]: # skip first general message (non informative)
        if description == "": # skip empty generation
            continue
        new_description = description
        if description[:1].isdigit():
            new_description = description[3:]
        cleaned_descriptions.append(new_description)
    return {"descriptions": cleaned_descriptions + ["", "", "", ""]} # if no generations

@app.post("/generate/tags")
async def get_tags(pinput: PredictionInput):
    title = pinput.title
    tags = tags_chain.invoke({"title": title})

    return {"tags": tags}

@app.post("/generate/images")
async def get_images(pinput: PredictionInput):
    title = pinput.title
    images = []
    food_list = food_chain.invoke({"title": title})
    tasks = [image_chain.ainvoke({"title": food}) for food in food_list]    
    image_results = await asyncio.gather(*tasks)
    images.extend(image_results)

    return {"images": images}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
