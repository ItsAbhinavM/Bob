from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Enum as SQLEnum, Text
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

class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

# ==================== DATABASE MODELS ====================

class Task(Base):
    """Task/Todo model"""
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
    """Conversation history"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, index=True)
    user_message = Column(String)
    assistant_response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Contact(Base):
    """Contact aliases for email"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "john"
    email = Column(String(200), nullable=False)  # e.g., "john223@gmail.com"
    name = Column(String(100), nullable=True)  # Full name: "John Doe"
    notes = Column(Text, nullable=True)  # Optional notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLog(Base):
    """Log of sent emails"""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(200), nullable=False)
    to_alias = Column(String(50), nullable=True)  # If sent via alias
    subject = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), default=EmailStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Initialize database
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize on import
init_db()