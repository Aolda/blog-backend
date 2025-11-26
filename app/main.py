from fastapi import FastAPI

app = FastAPI(title="ABS (Aolda Blog Service) API")

@app.get("/")
def read_root():
    return {"message": "Welcome to ABS API"}