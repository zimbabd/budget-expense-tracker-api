from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth, categories, expenses, budgets

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(budgets.router)


@app.get("/")
def root():
    return {"message": "FastAPI project is running"}
