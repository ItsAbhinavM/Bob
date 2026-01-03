from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import enum

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bob_assistant.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Enums
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Database Models
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default=TaskStatus.PENDING.value)
    priority = Column(String, default=TaskPriority.MEDIUM.value)
    due_date = Column(DateTime, nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, index=True)
    user_message = Column(String)
    assistant_response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()