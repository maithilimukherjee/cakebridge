from fastapi import FastAPI
from routes import cake, user, baker, order, auth

app = FastAPI()

app.include_router(auth.router, prefix="/auth")
app.include_router(cake.router, prefix="/cake")
app.include_router(user.router, prefix="/user")
app.include_router(baker.router, prefix="/baker")
app.include_router(order.router, prefix="/order")

@app.get("/")

def root():
    return {"message": "cakebridge service is live!"}