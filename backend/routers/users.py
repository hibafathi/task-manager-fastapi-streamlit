# File: backend/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import create_token, get_current_user, hash_password, verify_password
from backend.database import get_connection
from backend.schemas import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister) -> UserResponse:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (payload.email,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = hash_password(payload.password)
        cursor.execute(
            "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
            (payload.name.strip(), payload.email, hashed_password),
        )
        conn.commit()
        user_id = cursor.lastrowid

    return UserResponse(id=user_id, name=payload.name.strip(), email=payload.email)


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin) -> TokenResponse:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, hashed_password FROM users WHERE email = ?",
            (payload.email,),
        )
        user = cursor.fetchone()

    # A single generic error avoids revealing whether the email or password was wrong.
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_token(user["email"])
    return TokenResponse(
        access_token=token,
        name=user["name"],
        email=user["email"],
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: str = Depends(get_current_user)) -> UserResponse:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email FROM users WHERE email = ?",
            (current_user,),
        )
        user = cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
    )
