from typing import List
from fastapi import Depends, HTTPException, status
from app.database.models import User
from app.security.auth import get_current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role or current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}. Your role: {current_user.role.name if current_user.role else 'None'}"
            )
        return current_user

# Predefined role dependencies
require_admin = RoleChecker(["admin"])
require_faculty = RoleChecker(["faculty"])
require_student = RoleChecker(["student"])
require_hod = RoleChecker(["hod"])

# Combined role dependencies
require_admin_or_hod = RoleChecker(["admin", "hod"])
require_faculty_or_admin = RoleChecker(["faculty", "admin"])
require_all_authenticated = RoleChecker(["admin", "faculty", "student", "hod"])
