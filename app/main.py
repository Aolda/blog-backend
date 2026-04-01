from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.api_router import api_router
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ABS (Aolda Blog Service) API",
    swagger_ui_parameters={"persistAuthorization": True} # 임시 (토큰 기억)
)

app.add_middleware(SessionMiddleware, secret_key="some_random_secret_string")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to ABS API"}
