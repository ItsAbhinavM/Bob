from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None

class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    """Schema for chat messages"""
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Schema for chat responses"""
    response: str
    conversation_id: str
    action_taken: Optional[str] = None
    data: Optional[dict] = None

class WeatherResponse(BaseModel):
    """Schema for weather response"""
    location: str
    temperature: float
    condition: str
    description: str
    humidity: int
    wind_speed: float
    suggestion: str