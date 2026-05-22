from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.tables import Classroom, ClassroomMember, User
from app.core.auth import get_current_user, require_teacher
from pydantic import BaseModel

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])

class ClassroomCreate(BaseModel):
    name: str
    subject: str

class JoinClassroom(BaseModel):
    join_code: str

@router.post("/")
def create_classroom(data: ClassroomCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    classroom = Classroom(name=data.name, subject=data.subject, teacher_id=current_user.id)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom

@router.get("/")
def get_my_classrooms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "teacher":
        return db.query(Classroom).filter(Classroom.teacher_id == current_user.id).all()
    else:
        memberships = db.query(ClassroomMember).filter(ClassroomMember.user_id == current_user.id).all()
        classroom_ids = [m.classroom_id for m in memberships]
        return db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()

@router.get("/{classroom_id}")
def get_classroom(classroom_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom

@router.post("/join")
def join_classroom(data: JoinClassroom, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    classroom = db.query(Classroom).filter(Classroom.join_code == data.join_code.upper()).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Invalid join code")
    existing = db.query(ClassroomMember).filter(
        ClassroomMember.user_id == current_user.id,
        ClassroomMember.classroom_id == classroom.id
    ).first()
    if existing:
        return {"message": "Already a member", "classroom": classroom}
    member = ClassroomMember(user_id=current_user.id, classroom_id=classroom.id)
    db.add(member)
    db.commit()
    return {"message": "Joined successfully", "classroom": classroom}

@router.get("/{classroom_id}/members")
def get_members(classroom_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_teacher)):
    members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append({"id": user.id, "name": user.name, "email": user.email})
    return result