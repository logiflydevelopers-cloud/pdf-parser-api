from fastapi import FastAPI
from app.config import APP_NAME, API_PREFIX
from app.routes import router

app = FastAPI(
    title=APP_NAME,
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
def health():
    return {"status": "ok"}

