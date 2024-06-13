import sys
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from chain import (
    tags_chain, 
    description_chain, 
    image_chain, 
    food_chain
)
from pydantic import BaseModel


logging.basicConfig(level=logging.ERROR, stream=sys.stderr, format='%(asctime)s %(levelname)s %(message)s')

class PredictionInput(BaseModel):
    title: str

app = FastAPI(title="Product Card Service App")

def retry(chain, body, num_attempts=5):
    for _ in range(num_attempts):
        try:
            output = chain.invoke(body)
            return output
        except Exception as e:
            pass
    else:
        raise Exception("All attempts failed to execute the code")


@app.post("/generate/descriptions")
async def get_descriptions(pinput: PredictionInput):
    try:
        title = pinput.title
        descriptions = retry(
            chain=description_chain, 
            body={"title": title}
        )
        return {"descriptions": descriptions}
    except ValueError as e:
        return JSONResponse(status_code=422, content={"message": f"Validation error: {e}"})
    except Exception as e:
        logging.error(f"System error: {e}")
        return JSONResponse(status_code=422, content={"message": f"System error: {e}"})

@app.post("/generate/tags")
async def get_tags(pinput: PredictionInput):
    try:
        title = pinput.title
        tags = tags_chain.invoke({"title": title})
        return {"tags": tags}
    except ValueError as e:
        return JSONResponse(status_code=422, content={"message": f"Validation error: {e}"})
    except Exception as e:
        logging.error(f"System error: {e}")
        return JSONResponse(status_code=422, content={"message": f"System error: {e}"})

@app.post("/generate/images")
async def get_images(pinput: PredictionInput):
    try:
        title = pinput.title
        images = []
        food_list = retry(
            chain=food_chain, 
            body={"title": title}
        )
        tasks = [image_chain.ainvoke({"title": food}) for food in food_list]    
        image_results = await asyncio.gather(*tasks)
        images.extend(image_results)
        return {"images": images}
    except ValueError as e:
        return JSONResponse(status_code=422, content={"message": f"Validation error: {e}"})
    except Exception as e:
        logging.error(f"System error: {e}")
        return JSONResponse(status_code=422, content={"message": f"System error: {e}"})

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
