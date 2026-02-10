from typing import List
from fastapi import Depends, HTTPException, Request, status
from appdatainternal.settings import rbac_roles

USERNAME_HEADER = "X-SSO-REMOTE-USER"
def get_current_user(request: Request):
    # Placeholder for user authentication logic
    # In a real application, implement proper authentication here
    username = request.headers.get(USERNAME_HEADER)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Unauthorized: No user information found.")
    norm_username = username.strip().lower()
    return norm_username

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: str = Depends(get_current_user)):
        user_roles = [role for role, users in rbac_roles.items() if user in users]
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=403,
                detail="Operation not permitted"
            )
        return user
