from fastapi import FastAPI
from diwanic.api.routes.search_routes import router as search_router

app = FastAPI(title="Diwanic", version="0.2.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "diwanic"}


app.include_router(search_router)
