
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import verify_token
from app.schemas.user import UserResponse  # ← Gunakan UserResponse dari database standalone

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple authentication - just verify token is valid"""
    token_data = verify_token(credentials.credentials)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Untuk cepat: return dummy user dari token data saja
    # Atau ambil dari database standalone
    
    from app.services.auth import auth
    email = token_data.get("email") or token_data.get("sub")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email"
        )
    
    # Get user from standalone database
    user = auth.get_user_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        full_name=user.get("full_name"),
        is_active=user["is_active"],
        is_superuser=user.get("is_superuser", False)
    )