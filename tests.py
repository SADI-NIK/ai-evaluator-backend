from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.models.database import get_db
from app.models.tables import Test, Question

router = APIRouter(prefix="/tests", tags=["tests"])

# ==========================================================================
# PYDANTIC VALIDATION SCHEMAS
# ==========================================================================
class TestCreate(BaseModel):
    title: str
    classroom_id: int
    duration: int = 30  # ⏱️ Expects incoming customized timer values

class TestResponse(BaseModel):
    id: int
    title: str
    classroom_id: int
    duration: int       # ⏱️ Returns validation timing maps to client interface

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    test_id: int
    question_text: str
    answer_key: str
    total_marks: float

class QuestionResponse(BaseModel):
    id: int
    test_id: int
    question_text: str
    answer_key: str
    total_marks: float

    class Config:
        from_attributes = True

# ==========================================================================
# API ENDPOINT ROUTERS
# ==========================================================================
@router.post("/", response_model=TestResponse)
def create_new_test(payload: TestCreate, db: Session = Depends(get_db)):
    db_test = Test(
        title=payload.title,
        classroom_id=payload.classroom_id,
        duration=payload.duration  # ⏱️ Commits customized time parameters to model
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test

@router.get("/{test_id}", response_model=TestResponse)
def get_single_test(test_id: int, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test profile not found")
    return test

@router.post("/questions", response_model=QuestionResponse)
def add_test_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    db_question = Question(
        test_id=payload.test_id,
        question_text=payload.question_text,
        answer_key=payload.answer_key,
        total_marks=payload.total_marks
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/{test_id}/questions", response_model=List[QuestionResponse])
def get_test_questions(test_id: int, db: Session = Depends(get_db)):
    return db.query(Question).filter(Question.test_id == test_id).all()

@router.delete("/questions/{question_id}")
def delete_test_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question entry not found")
    db.delete(question)
    db.commit()
    return {"detail": "Question successfully deleted"}