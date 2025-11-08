"""
Chat History Service - Handles chat session and message storage
"""

from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from .database import get_collection
from .models import (
    ChatSessionModel,
    ChatSessionWithMessages,
    MessageModel,
    CreateSessionRequest,
    AddMessageRequest,
    UpdateSessionRequest
)
import logging

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Service for managing chat history"""

    def __init__(self):
        self._sessions_collection = None
        self._messages_collection = None

    @property
    def sessions_collection(self):
        """Lazy-load sessions collection"""
        if self._sessions_collection is None:
            self._sessions_collection = get_collection("chat_sessions")
        return self._sessions_collection

    @property
    def messages_collection(self):
        """Lazy-load messages collection"""
        if self._messages_collection is None:
            self._messages_collection = get_collection("messages")
        return self._messages_collection

    async def create_session(self, request: CreateSessionRequest) -> ChatSessionModel:
        """Create a new chat session"""
        session_data = {
            "title": request.title or f"New {request.mode.capitalize()} Session",
            "mode": request.mode,
            "user_id": request.user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0
        }

        result = await self.sessions_collection.insert_one(session_data)
        session_data["_id"] = result.inserted_id

        logger.info(f"Created new session: {result.inserted_id}")
        return ChatSessionModel(**session_data)

    async def get_session(self, session_id: str) -> Optional[ChatSessionModel]:
        """Get a session by ID"""
        try:
            session = await self.sessions_collection.find_one({"_id": ObjectId(session_id)})
            if session:
                return ChatSessionModel(**session)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    async def get_session_with_messages(self, session_id: str) -> Optional[ChatSessionWithMessages]:
        """Get a session with all its messages"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return None

            messages_cursor = self.messages_collection.find(
                {"session_id": session_id}
            ).sort("timestamp", 1)

            messages = []
            async for msg in messages_cursor:
                messages.append(MessageModel(**msg))

            return ChatSessionWithMessages(
                **session.model_dump(),
                messages=messages
            )
        except Exception as e:
            logger.error(f"Error getting session with messages {session_id}: {e}")
            return None

    async def list_sessions(
        self,
        user_id: str = "default_user",
        limit: int = 50,
        skip: int = 0,
        mode: Optional[str] = None
    ) -> List[ChatSessionModel]:
        """List all sessions for a user, optionally filtered by mode"""
        try:
            # Build query
            query = {"user_id": user_id}
            if mode:
                query["mode"] = mode

            cursor = self.sessions_collection.find(
                query
            ).sort("updated_at", -1).skip(skip).limit(limit)

            sessions = []
            async for session in cursor:
                sessions.append(ChatSessionModel(**session))

            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    async def get_recent_active_session(
        self,
        user_id: str,
        mode: str,
        max_age_minutes: int = 30
    ) -> Optional[ChatSessionModel]:
        """
        Get the most recent active session for a user within a time window.

        Args:
            user_id: User identifier
            mode: Session mode (chat or report)
            max_age_minutes: Maximum age of session in minutes (default: 30)

        Returns:
            Most recent session or None if no recent session found
        """
        try:
            from datetime import timedelta

            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

            # Find most recent session within time window
            session = await self.sessions_collection.find_one(
                {
                    "user_id": user_id,
                    "mode": mode,
                    "updated_at": {"$gte": cutoff_time}
                },
                sort=[("updated_at", -1)]
            )

            if session:
                logger.info(f"Found recent active session: {session['_id']} (updated: {session['updated_at']})")
                return ChatSessionModel(**session)

            return None
        except Exception as e:
            logger.error(f"Error getting recent active session: {e}")
            return None

    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[MessageModel]:
        """
        Get the most recent messages from a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return (default: 10)

        Returns:
            List of recent messages, ordered oldest to newest
        """
        try:
            messages_cursor = self.messages_collection.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(limit)  # Get most recent, newest first

            messages = []
            async for msg in messages_cursor:
                messages.append(MessageModel(**msg))

            # Reverse to get chronological order (oldest to newest)
            messages.reverse()

            logger.info(f"Retrieved {len(messages)} recent messages for session {session_id}")
            return messages
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []

    async def add_message(
        self,
        session_id: str,
        message: AddMessageRequest
    ) -> Optional[MessageModel]:
        """Add a message to a session"""
        try:
            # Check for duplicate message within last 2 seconds to prevent double-saving
            recent_cutoff = datetime.utcnow()
            from datetime import timedelta
            recent_cutoff = recent_cutoff - timedelta(seconds=2)

            existing_message = await self.messages_collection.find_one({
                "session_id": session_id,
                "role": message.role,
                "content": message.content,
                "timestamp": {"$gte": recent_cutoff}
            })

            if existing_message:
                logger.warning(f"Duplicate message detected and skipped for session {session_id}")
                return MessageModel(**existing_message)

            message_data = {
                "session_id": session_id,
                "role": message.role,
                "content": message.content,
                "timestamp": datetime.utcnow(),
                "metadata": message.metadata,
                "is_error": message.is_error
            }

            result = await self.messages_collection.insert_one(message_data)
            message_data["_id"] = result.inserted_id

            # Update session's updated_at and message_count
            await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {"message_count": 1}
                }
            )

            # Auto-generate title from first user message
            session = await self.get_session(session_id)
            if session and session.message_count == 1 and message.role == "user":
                await self.update_session_title(
                    session_id,
                    self._generate_title(message.content)
                )

            logger.info(f"Added message to session {session_id}")
            return MessageModel(**message_data)

        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        updates: UpdateSessionRequest
    ) -> bool:
        """Update session details"""
        try:
            update_data = {
                "updated_at": datetime.utcnow()
            }

            if updates.title:
                update_data["title"] = updates.title

            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": update_data}
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False

    async def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        return await self.update_session(
            session_id,
            UpdateSessionRequest(title=title)
        )

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            # Delete all messages
            await self.messages_collection.delete_many({"session_id": session_id})

            # Delete session
            result = await self.sessions_collection.delete_one({"_id": ObjectId(session_id)})

            logger.info(f"Deleted session {session_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def clear_session_messages(self, session_id: str) -> bool:
        """Clear all messages from a session"""
        try:
            await self.messages_collection.delete_many({"session_id": session_id})

            # Reset message count
            await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "message_count": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info(f"Cleared messages from session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing messages from session {session_id}: {e}")
            return False

    @staticmethod
    def _generate_title(content: str, max_length: int = 50) -> str:
        """Generate a title from the first message"""
        content = content.strip()
        if len(content) <= max_length:
            return content
        return content[:max_length].rsplit(' ', 1)[0] + "..."


# Global service instance
chat_history_service = ChatHistoryService()
