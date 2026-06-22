from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

PriorityType = Literal["low", "medium", "high"]
StatusType = Literal["pending", "in-progress", "done"]


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=100)


class UserResponse(BaseModel):
    id: int
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
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