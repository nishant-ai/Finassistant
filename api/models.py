"""
Pydantic Models for Chat History
"""

from pydantic import BaseModel, Field, field_validator
from pydantic_core import core_schema
from typing import Optional, List, Literal, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic v2"""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ],
        serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    def __repr__(self):
        return f"PyObjectId({super().__repr__()})"


class MessageModel(BaseModel):
    """Model for individual chat messages"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None
    is_error: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is Apple's P/E ratio?",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": None,
                "is_error": False
            }
        }


class ChatSessionModel(BaseModel):
    """Model for chat sessions"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(default="New Chat")
    mode: Literal["chat", "think"]
    user_id: Optional[str] = Field(default="default_user")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = Field(default=0)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "title": "Apple Stock Analysis",
                "mode": "chat",
                "user_id": "default_user",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z",
                "message_count": 4
            }
        }


class ChatSessionWithMessages(ChatSessionModel):
    """Chat session with messages included"""
    messages: List[MessageModel] = []


class CreateSessionRequest(BaseModel):
    """Request model for creating a new session"""
    mode: Literal["chat", "think"]
    title: Optional[str] = None
    user_id: Optional[str] = "default_user"


class AddMessageRequest(BaseModel):
    """Request model for adding a message to a session"""
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: Optional[dict] = None
    is_error: bool = False


class UpdateSessionRequest(BaseModel):
    """Request model for updating session details"""
    title: Optional[str] = None
