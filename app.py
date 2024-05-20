from fastapi import FastAPI
from chain import tags_chain, description_chain, image_chain, food_chain

app = FastAPI(title="Product Card Service App")


@app.get("/generate/descriptions")
async def message(title: str):
    descriptions = description_chain.invoke({"title": title})

    return {"descriptions": descriptions}

@app.get("/generate/tags")
async def message(title: str):
    tags = tags_chain.invoke({"title": title})

    return {"tags": tags}

@app.get("/generate/images")
async def message(title: str):
    images=[]
    food_list = food_chain.invoke({"title": title})
    for food in food_list:
        images.append(image_chain.invoke({"title": food}))

    return {"images": images}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
