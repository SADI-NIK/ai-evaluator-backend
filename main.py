from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.database import engine
from app.models import tables
from app.routers import classrooms, tests, submissions, auth

tables.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Evaluator", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(classrooms.router)
app.include_router(tests.router)
app.include_router(submissions.router)

@app.get("/")
def root():
    return {"message": "AI Evaluator v2.0 is running!"}