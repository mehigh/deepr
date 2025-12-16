from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Text, DateTime
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="nodes")
    children = relationship("Node", backref="parent", remote_side=[id])
