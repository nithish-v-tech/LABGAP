from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, Role
from app.security.auth import verify_password, create_access_token, get_current_user
from app.schemas.schemas import Token, LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name if user.role else "student"}
    )

    user_info = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name if user.role else "student",
        "department_id": user.department_id,
        "is_active": user.is_active
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_info
    }

@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role_name = current_user.role.name if current_user.role else "student"
    profile = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": role_name,
        "department_id": current_user.department_id,
        "department_name": current_user.department.name if current_user.department else None,
        "institution_name": current_user.department.institution.name if (current_user.department and current_user.department.institution) else "National Institute of Engineering",
        "is_active": current_user.is_active
    }

    if role_name == "faculty" and current_user.faculty_profile:
        profile["faculty_id"] = current_user.faculty_profile.id
        profile["faculty_code"] = current_user.faculty_profile.faculty_code
        profile["assigned_laboratory_id"] = current_user.faculty_profile.assigned_laboratory_id

    elif role_name == "student" and current_user.student_profile:
        profile["student_id"] = current_user.student_profile.id
        profile["student_id_number"] = current_user.student_profile.student_id_number
        profile["batch_id"] = current_user.student_profile.batch_id
        profile["batch_code"] = current_user.student_profile.batch.batch_code if current_user.student_profile.batch else None

    return profile
