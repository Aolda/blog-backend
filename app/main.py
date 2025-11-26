from fastapi import FastAPI
from app.api.v1.api_router import api_router

app = FastAPI(title="ABS (Aolda Blog Service) API")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to ABS API"}