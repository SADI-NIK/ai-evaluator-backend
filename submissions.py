from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.tables import Submission, User, Test, Question
from app.core.auth import get_current_user, require_teacher
from app.core.evaluator import evaluate_question
from pydantic import BaseModel
import json

router = APIRouter(prefix="/submissions", tags=["Submissions"])

class AnswerSubmit(BaseModel):
    test_id: int
    answers: list[dict]

@router.post("/")
def submit_answers(data: AnswerSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if already submitted
    existing = db.query(Submission).filter(
        Submission.student_id == current_user.id,
        Submission.test_id == data.test_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="ALREADY_SUBMITTED")

    test = db.query(Test).filter(Test.id == data.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    questions = db.query(Question).filter(Question.test_id == data.test_id).all()

    total_marks = 0
    detailed_results = []

    for question in questions:
        student_answer = next((a for a in data.answers if a["question_id"] == question.id), None)
        student_blanks = student_answer["answers"] if student_answer else []
        answer_key = [a.strip() for a in question.answer_key.split(",")]
        result = evaluate_question(student_blanks, answer_key, question.total_marks)
        total_marks += result["marks_obtained"]
        detailed_results.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "marks_obtained": result["marks_obtained"],
            "total_marks": result["total_marks"],
            "results": result["results"]
        })

    submission = Submission(
        student_id=current_user.id,
        test_id=data.test_id,
        answers=json.dumps(detailed_results),
        marks_obtained=round(total_marks, 2)
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "submission_id": submission.id,
        "student_name": current_user.name,
        "total_marks_obtained": round(total_marks, 2),
        "total_marks_possible": test.total_marks,
        "percentage": round((total_marks / test.total_marks * 100), 2) if test.total_marks > 0 else 0,
        "detailed_results": detailed_results
    }

@router.get("/my/{test_id}")
def get_my_submission(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    submission = db.query(Submission).filter(
        Submission.student_id == current_user.id,
        Submission.test_id == test_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="No submission found")
    return {
        "submission_id": submission.id,
        "marks_obtained": submission.marks_obtained,
        "detailed_results": json.loads(submission.answers)
    }

@router.get("/test/{test_id}/results")
def get_test_results(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    submissions = db.query(Submission).filter(Submission.test_id == test_id).all()
    test = db.query(Test).filter(Test.id == test_id).first()
    results = []
    for sub in submissions:
        student = db.query(User).filter(User.id == sub.student_id).first()
        results.append({
            "submission_id": sub.id,
            "student_name": student.name,
            "email": student.email,
            "marks_obtained": sub.marks_obtained,
            "total_marks": test.total_marks,
            "percentage": round((sub.marks_obtained / test.total_marks * 100), 2) if test.total_marks > 0 else 0,
            "submitted_at": sub.submitted_at
        })
    results.sort(key=lambda x: x["marks_obtained"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results

@router.get("/{submission_id}")
def get_submission(submission_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if current_user.role != "teacher" and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "submission_id": submission.id,
        "student_id": submission.student_id,
        "marks_obtained": submission.marks_obtained,
        "detailed_results": json.loads(submission.answers)
    }

@router.delete("/reset/{student_id}/{test_id}")
def reset_attempt(student_id: int, test_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    submission = db.query(Submission).filter(
        Submission.student_id == student_id,
        Submission.test_id == test_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="No submission found")
    db.delete(submission)
    db.commit()
    return {"message": "Attempt reset successfully"}