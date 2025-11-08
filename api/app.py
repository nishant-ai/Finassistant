"""
FastAPI Agent API for Financial Assistant

Provides REST endpoints for:
- /api/chat: Quick conversational responses
- /api/think: Comprehensive financial analysis
- /api/health: Health check endpoint
"""

from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import sys
import os
import asyncio

# Add parent directory to path to import agent module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.agent import run_agent

# Import MongoDB and chat history services
from api.database import connect_to_mongo, close_mongo_connection
from api.chat_history import chat_history_service
from api.models import (
    CreateSessionRequest,
    AddMessageRequest,
    UpdateSessionRequest,
    ChatSessionModel,
    ChatSessionWithMessages,
    MessageModel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Financial Assistant Agent API",
    description="API for financial analysis using AI agents with chat and report modes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Event handlers
@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("Application starting up")

    # Connect to MongoDB
    try:
        await connect_to_mongo()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Chat history will not be available.")


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    logger.info("Application shutting down")

    # Close MongoDB connection
    try:
        await close_mongo_connection()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.warning(f"Error closing MongoDB: {e}")


# Response Models
class QueryResponse(BaseModel):
    """Response model for agent queries"""
    success: bool = Field(description="Whether the query was processed successfully")
    query: str = Field(description="The original user query")
    query_type: str = Field(description="The type of query processed (chat or report)")
    result: str = Field(description="The agent's response")
    timestamp: str = Field(description="ISO timestamp of when the response was generated")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the execution"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "What is Apple's P/E ratio?",
                "query_type": "chat",
                "result": "Apple (AAPL) currently has a P/E ratio of 28.5...",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {
                    "execution_time_seconds": 3.2
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False)
    error: str = Field(description="Error message")
    error_type: str = Field(description="Type of error that occurred")
    timestamp: str = Field(description="ISO timestamp of when the error occurred")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid query parameter",
                "error_type": "ValidationError",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(description="API status")
    timestamp: str = Field(description="Current server timestamp")
    version: str = Field(description="API version")


# Helper function for processing queries
async def _process_agent_query(
    query: str,
    query_type: str,
    verbose: bool = False,
    session_id: Optional[str] = None,
    user_id: str = "default_user",
    save_to_history: bool = True
) -> QueryResponse:
    """
    Internal helper to process queries with the agent.

    Args:
        query: The user's financial question
        query_type: "chat" or "think"
        verbose: Include execution details
        session_id: Optional session ID to save conversation to
        user_id: User identifier
        save_to_history: Whether to save to MongoDB chat history

    Returns:
        QueryResponse with results
    """
    # Validate query
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Query cannot be empty",
                "error_type": "ValidationError",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        )

    query = query.strip()
    start_time = datetime.now(timezone.utc)

    # Create or get session if saving to history
    created_session_id = None
    if save_to_history:
        try:
            if not session_id:
                # Try to find a recent active session for this user
                recent_session = await chat_history_service.get_recent_active_session(
                    user_id=user_id,
                    mode=query_type,
                    max_age_minutes=30  # Continue sessions active within last 30 minutes
                )

                if recent_session:
                    # Use existing recent session
                    created_session_id = str(recent_session.id)
                    logger.info(f"Continuing recent session: {created_session_id}")
                else:
                    # Create a new session
                    session_request = CreateSessionRequest(
                        mode=query_type,
                        title=query[:50] + "..." if len(query) > 50 else query,
                        user_id=user_id
                    )
                    session = await chat_history_service.create_session(session_request)
                    created_session_id = str(session.id)
                    logger.info(f"Created new session: {created_session_id}")
            else:
                created_session_id = session_id
                logger.info(f"Using provided session: {created_session_id}")

            # Save user message
            user_message = AddMessageRequest(
                role="user",
                content=query,
                metadata={"query_type": query_type}
            )
            await chat_history_service.add_message(created_session_id, user_message)
            logger.info(f"Saved user message to session: {created_session_id}")
        except Exception as e:
            logger.warning(f"Failed to save user message to history: {e}")

    # Fetch conversation context for the agent (if session exists)
    conversation_context = []
    if save_to_history and created_session_id:
        try:
            # Fetch recent messages for context (excluding the current user message we just added)
            recent_messages = await chat_history_service.get_recent_messages(
                session_id=created_session_id,
                limit=10  # Last 10 messages (up to 5 exchanges)
            )

            # Format for agent - exclude the last message (current query)
            if len(recent_messages) > 1:
                conversation_context = [
                    {"role": msg.role, "content": msg.content}
                    for msg in recent_messages[:-1]  # Exclude the message we just added
                ]
                logger.info(f"Loaded {len(conversation_context)} messages for conversation context")
        except Exception as e:
            logger.warning(f"Failed to load conversation context: {e}")

    try:
        logger.info(f"Processing {query_type} query: {query[:100]}...")

        # Run the agent with conversation history in a thread pool to avoid blocking the event loop
        result = await asyncio.to_thread(
            run_agent,
            query=query,
            mode=query_type,
            verbose=verbose,
            conversation_history=conversation_context if conversation_context else None
        )

        end_time = datetime.now(timezone.utc)
        execution_time = (end_time - start_time).total_seconds()

        logger.info(f"Query processed successfully in {execution_time:.2f}s")

        # Save assistant response to history
        if save_to_history and created_session_id:
            try:
                assistant_message = AddMessageRequest(
                    role="assistant",
                    content=result,
                    metadata={
                        "execution_time_seconds": round(execution_time, 2),
                        "verbose": verbose
                    }
                )
                await chat_history_service.add_message(created_session_id, assistant_message)
                logger.info(f"Saved assistant response to session: {created_session_id}")
            except Exception as e:
                logger.warning(f"Failed to save assistant response to history: {e}")

        return QueryResponse(
            success=True,
            query=query,
            query_type=query_type,
            result=result,
            timestamp=end_time.isoformat().replace('+00:00', 'Z'),
            metadata={
                "execution_time_seconds": round(execution_time, 2),
                "verbose": verbose,
                "session_id": created_session_id
            }
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": str(e),
                "error_type": "ValidationError",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "An error occurred while processing your query. Please try again.",
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
        )


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Financial Assistant Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "chat": "/api/chat",
            "report": "/api/report"
        }
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        version="1.0.0"
    )


@app.post("/api/chat", response_model=QueryResponse, responses={
    400: {"model": ErrorResponse, "description": "Bad Request"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"}
})
async def chat_query(
    query: str,
    session_id: Optional[str] = None,
    user_id: str = "default_user",
    save_history: bool = True
):
    """
    Chat endpoint for quick conversational financial queries.

    - **query**: The financial question (e.g., "What is Apple's P/E ratio?")
    - **session_id**: Optional session ID to continue an existing conversation
    - **user_id**: User identifier (defaults to "default_user")
    - **save_history**: Whether to save this conversation to MongoDB (default: true)

    Returns a quick, conversational response optimized for speed.
    Uses single-agent workflow for efficient processing.
    Automatically saves conversation to MongoDB if connected.

    Example:
        POST /api/chat?query=What%20is%20Apple's%20current%20stock%20price?
        POST /api/chat?query=Tell%20me%20more&session_id=<session_id>
    """
    return await _process_agent_query(
        query=query,
        query_type="chat",
        verbose=False,
        session_id=session_id,
        user_id=user_id,
        save_to_history=save_history
    )


@app.post("/api/think", response_model=QueryResponse, responses={
    400: {"model": ErrorResponse, "description": "Bad Request"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"}
})
async def think_query(
    query: str,
    verbose: bool = False,
    session_id: Optional[str] = None,
    user_id: str = "default_user",
    save_history: bool = True
):
    """
    Think endpoint for comprehensive financial analysis.

    - **query**: The financial question (e.g., "Analyze Tesla's financial health")
    - **verbose**: Include detailed execution information (optional, default: false)
    - **session_id**: Optional session ID to continue an existing conversation
    - **user_id**: User identifier (defaults to "default_user")
    - **save_history**: Whether to save this conversation to MongoDB (default: true)

    Returns a detailed, structured financial analysis with comprehensive research.
    Uses multi-agent workflow (Planner → Financial → Publisher) for thorough analysis.
    Automatically saves conversation to MongoDB if connected.

    Example:
        POST /api/think?query=Analyze%20Tesla%27s%20financial%20performance&verbose=true
        POST /api/think?query=Compare%20with%20Ford&session_id=<session_id>
    """
    return await _process_agent_query(
        query=query,
        query_type="think",
        verbose=verbose,
        session_id=session_id,
        user_id=user_id,
        save_to_history=save_history
    )


# ============================================================================
# CHAT HISTORY ENDPOINTS
# ============================================================================

@app.post("/api/sessions", response_model=ChatSessionModel, status_code=status.HTTP_201_CREATED)
async def create_chat_session(request: CreateSessionRequest):
    """
    Create a new chat session.

    - **mode**: "chat" or "think"
    - **title**: Optional session title
    - **user_id**: User identifier (defaults to "default_user")
    """
    try:
        session = await chat_history_service.create_session(request)
        return session
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@app.get("/api/sessions", response_model=List[ChatSessionModel])
async def list_chat_sessions(
    user_id: str = "default_user",
    limit: int = 50,
    skip: int = 0,
    mode: Optional[str] = None
):
    """
    List all chat sessions for a user, optionally filtered by mode.

    - **user_id**: User identifier
    - **limit**: Maximum number of sessions to return
    - **skip**: Number of sessions to skip (for pagination)
    - **mode**: Optional filter by mode ("chat" or "think")
    """
    try:
        sessions = await chat_history_service.list_sessions(user_id, limit, skip, mode)
        return sessions
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@app.get("/api/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(session_id: str):
    """
    Get a specific session with all its messages.

    - **session_id**: The session ID
    """
    try:
        session = await chat_history_service.get_session_with_messages(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@app.post("/api/sessions/{session_id}/messages", response_model=MessageModel, status_code=status.HTTP_201_CREATED)
async def add_message_to_session(session_id: str, message: AddMessageRequest):
    """
    Add a message to a session.

    - **session_id**: The session ID
    - **message**: Message object with role, content, metadata
    """
    try:
        added_message = await chat_history_service.add_message(session_id, message)
        if not added_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message"
            )
        return added_message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@app.patch("/api/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def update_chat_session(session_id: str, updates: UpdateSessionRequest):
    """
    Update session details.

    - **session_id**: The session ID
    - **updates**: Object with fields to update (currently supports: title)
    """
    try:
        success = await chat_history_service.update_session(session_id, updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found or no changes made"
            )
        return {"success": True, "message": "Session updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@app.delete("/api/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def delete_chat_session(session_id: str):
    """
    Delete a session and all its messages.

    - **session_id**: The session ID
    """
    try:
        success = await chat_history_service.delete_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        return {"success": True, "message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@app.delete("/api/sessions/{session_id}/messages", status_code=status.HTTP_200_OK)
async def clear_session_messages(session_id: str):
    """
    Clear all messages from a session.

    - **session_id**: The session ID
    """
    try:
        success = await chat_history_service.clear_session_messages(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear messages"
            )
        return {"success": True, "message": "Messages cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear messages: {str(e)}"
        )


# ============================================================================
# WEBSOCKET ENDPOINT FOR REAL-TIME STREAMING
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    user_id: str = "default_user"
):
    """
    WebSocket endpoint for real-time streaming chat responses.

    The client should:
    1. Connect to ws://localhost:8000/ws/chat?user_id=xxx
    2. Send JSON: {"query": "...", "mode": "chat|think", "session_id": "...", "save_history": true}
    3. Receive real-time events as the agent processes the query

    Event types:
    - agent_start: Agent begins processing
    - agent_step: Progress update (e.g., "Loading session...", "Analyzing query...")
    - tool_call: Tool is being executed
    - tool_result: Tool execution completed
    - llm_start: LLM is generating response
    - llm_token: Individual token from LLM (for streaming text effect)
    - llm_end: LLM finished generating
    - agent_complete: Final result ready
    - error: An error occurred
    """
    from api.websocket_handler import StreamCallback

    await websocket.accept()
    logger.info(f"WebSocket connection accepted for user: {user_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            query = data.get("query")
            mode = data.get("mode", "chat")
            session_id = data.get("session_id")
            save_history = data.get("save_history", True)

            if not query:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "error": "Query is required",
                        "error_type": "ValidationError"
                    }
                })
                continue

            # Create callback for streaming
            callback = StreamCallback(websocket)

            # Send start event
            await callback.on_agent_start(mode, query)

            # Process in background to allow streaming
            try:
                # Send step updates
                await callback.on_agent_step("Initializing", f"Preparing {mode} mode analysis...")

                if save_history:
                    await callback.on_agent_step(
                        "Session",
                        "Loading conversation history..." if session_id else "Creating new session..."
                    )

                await callback.on_agent_step(
                    "Processing",
                    "Analyzing your query..."
                )

                # Run agent with streaming
                result = await _process_agent_query(
                    query=query,
                    query_type=mode,
                    verbose=False,
                    session_id=session_id,
                    user_id=user_id,
                    save_to_history=save_history
                )

                # Stream the response text token by token
                await callback.on_llm_start([])

                response_text = result.result
                words = response_text.split()

                for i, word in enumerate(words):
                    if not callback.is_connected:
                        break

                    # Send word with space (except last word)
                    token = word if i == len(words) - 1 else word + " "
                    await callback.on_llm_token(token)

                    # Small delay for smooth streaming
                    await asyncio.sleep(0.02)

                await callback.on_llm_end(response_text)

                # Send completion
                await callback.on_agent_complete(
                    result=response_text,
                    metadata={
                        "session_id": result.metadata.get("session_id"),
                        "execution_time": result.metadata.get("execution_time_seconds"),
                        "mode": mode
                    }
                )

            except Exception as e:
                logger.error(f"Error processing WebSocket query: {e}", exc_info=True)
                await callback.on_error(
                    error=str(e),
                    error_type=type(e).__name__
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass


# Error handlers
@app.exception_handler(404)
async def not_found_handler(_request, _exc):
    """Custom 404 handler"""
    return {
        "success": False,
        "error": "Endpoint not found",
        "error_type": "NotFoundError",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "available_endpoints": [
            "/api/chat",
            "/api/report",
            "/api/health",
            "/api/sessions"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("🚀 Starting Financial Assistant Agent API")
    print("=" * 70)
    print("API Docs: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/health")
    print("Chat: POST http://localhost:8000/api/chat?query=YOUR_QUERY")
    print("Report: POST http://localhost:8000/api/report?query=YOUR_QUERY")
    print("=" * 70)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
