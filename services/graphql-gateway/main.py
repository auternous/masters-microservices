from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from schema import schema

app = FastAPI(title="GraphQL Gateway", version="1.0.0")

graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {"message": "GraphQL Gateway", "playground": "/graphql"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "graphql-gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
