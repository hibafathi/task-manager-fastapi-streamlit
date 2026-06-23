# File: backend/schemas.py
from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Restricting allowed values here keeps validation consistent across all task schemas.
PriorityType = Literal["low", "medium", "high"]
StatusType = Literal["pending", "in-progress", "done"]


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    # bcrypt has a practical input limit, so validation should stop bad input early.
    password: str = Field(..., min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    # Keeping token_type explicit makes frontend auth handling more standard.
    token_type: str = "bearer"
    name: str
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    priority: PriorityType = "low"
    status: StatusType = "pending"
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    priority: PriorityType = "low"
    status: StatusType = "pending"
    due_date: date | None = None


class TaskStatusUpdate(BaseModel):
    status: StatusType


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: PriorityType
    status: StatusType
    due_date: date | None = None
    owner_email: EmailStr


class TaskSummary(BaseModel):
    total: int
    pending: int
    in_progress: int
    done: int
