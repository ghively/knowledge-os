"""Authentication Middleware - FastAPI dependencies for protected routes"""
from __future__ import annotations
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth import auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict:
    """
    FastAPI dependency to get the current authenticated user.

    Use this in protected routes:

    ```python
    @router.get("/protected")
    async def protected_route(current_user: dict = Depends(get_current_user)):
        return {"message": f"Hello {current_user['username']}"}
    ```

    Raises:
        HTTPException 401: If token is missing or invalid
        HTTPException 404: If user is not found
    """
    token = credentials.credentials
    payload = auth_service.decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_optional_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] | None = None) -> dict | None:
    """
    FastAPI dependency to get the current user if authenticated, None otherwise.

    Use this for routes that work for both authenticated and anonymous users.

    ```python
    @router.get("/public")
    async def public_or_authenticated(current_user: dict | None = Depends(get_optional_user)):
        if current_user:
            return {"message": f"Hello {current_user['username']}"}
        return {"message": "Hello anonymous user"}
    ```
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
