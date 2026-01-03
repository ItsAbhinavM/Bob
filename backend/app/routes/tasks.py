from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskStatus
from app.services.database import get_db, Task

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = Task(
        title=task.title,
        description=task.description,
        status=TaskStatus.PENDING.value,
        priority=task.priority.value,
        due_date=task.due_date,
        tags=task.tags or []
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(status: str = None, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tasks"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(task, field):
            if field in ['status', 'priority'] and value:
                setattr(task, field, value.value)
            else:
                setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    db.delete(task)
    db.commit()