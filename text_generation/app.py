from fastapi import FastAPI
from langserve import add_routes
from chain import food_chain, description_chain


app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

add_routes(
    app, 
    food_chain, 
    path="/generate/food"
)

add_routes(
    app, 
    description_chain, 
    path="/generate/description"
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="10.128.0.27", port=8080)
