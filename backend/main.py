from fastapi import FastAPI
from routes import cake

app = FastAPI()

app.include_router(cake.router, prefix="/cake")

@app.get("/")

def root():
    return {"message": "cakebridge service is live!"}