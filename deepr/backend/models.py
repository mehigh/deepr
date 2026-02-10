from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Text, DateTime, Float, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class NodeType(enum.Enum):
    ROOT = "root"
    PLAN = "plan"
    RESEARCH = "research"
    CRITIQUE = "critique"
    SYNTHESIS = "synthesis"
    PROPOSAL = "proposal"
    TEST_CASES = "test_cases"
    REFINEMENT = "refinement"
    VERDICT = "verdict"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    settings = relationship("UserSettings", back_populates="user", uselist=False)
    conversations = relationship("Conversation", back_populates="user")

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    encrypted_api_key = Column(String, nullable=True)

    user = relationship("User", back_populates="settings")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    method = Column(String, default="dag") # dag or ensemble
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="conversations")
    nodes = relationship("Node", back_populates="conversation", cascade="all, delete-orphan")

class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    type = Column(String) # Storing enum as string for simplicity with SQLite
    content = Column(Text)
    model_name = Column(String, nullable=True) # Metadata about which model generated this
    attachment_filenames = Column(Text, nullable=True)  # Comma-separated list of attachment filenames
    prompt_sent = Column(Text, nullable=True)  # Full prompt sent to the model
    estimated_cost = Column(Float, nullable=True)  # Estimated cost before API call
    actual_cost = Column(Float, nullable=True)  # Actual cost from OpenRouter response
    warnings = Column(Text, nullable=True)  # JSON array of warning messages
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="nodes")
    children = relationship("Node", backref="parent", remote_side=[id])
    attachments = relationship("Attachment", back_populates="node", cascade="all, delete-orphan")

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'image', 'pdf', 'audio', 'video'
    mime_type = Column(String(100), nullable=False)  # 'image/jpeg', 'application/pdf', etc.
    file_data = Column(LargeBinary, nullable=False)  # Binary file data
    file_size = Column(Integer, nullable=False)  # Size in bytes
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    node = relationship("Node", back_populates="attachments")

