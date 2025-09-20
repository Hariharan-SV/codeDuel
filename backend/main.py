from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
import uvicorn
import os
from dotenv import load_dotenv
import asyncio
from typing import Dict, List, Optional
import json
import uuid
from datetime import datetime, timedelta
import logging

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
print(f"Loading .env from: {env_path}")
print(f"GEMINI_API_KEY loaded: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
print(f"JWT_SECRET_KEY loaded: {'Yes' if os.getenv('JWT_SECRET_KEY') else 'No'}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from models import User, Duel, Question, Answer, MatchmakingTicket
from services.auth_service import AuthService
from services.question_service import QuestionService
from services.matchmaking_service import MatchmakingService
from services.duel_service import DuelService

# Use mock database for development (comment out to use Firestore)
USE_MOCK_DB = True

if USE_MOCK_DB:
    print("Using mock database for development")
    from mock_database import MockFirestoreDB
    db = MockFirestoreDB()
else:
    # Try to initialize Firestore database
    try:
        from database import FirestoreDB
        db = FirestoreDB()
        print("Using Firestore database")
    except Exception as e:
        logger.warning(f"Failed to initialize Firestore: {e}. Falling back to mock database.")
        from mock_database import MockFirestoreDB
        db = MockFirestoreDB()

# Initialize FastAPI app
app = FastAPI(title="CodeDuel API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:3000"]
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Initialize services
auth_service = AuthService(db)
question_service = QuestionService()
matchmaking_service = MatchmakingService(db, sio)
duel_service = DuelService(db, sio)

# Store active connections
active_connections: Dict[str, WebSocket] = {}

@app.get("/")
async def root():
    return {"message": "CodeDuel API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Auth endpoints
@app.post("/api/auth/guest")
async def create_guest_user():
    """Create a guest user account"""
    try:
        user = await auth_service.create_guest_user()
        access_token = auth_service.create_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        return {
            "user": user.dict(), 
            "token": access_token,
            "refresh_token": refresh_token
        }
    except Exception as e:
        print(f"Error creating guest user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create guest user")

@app.post("/api/auth/refresh")
async def refresh_token(request: dict):
    """Refresh access token using refresh token"""
    try:
        refresh_token = request.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")
        
        user_id = auth_service.verify_token(refresh_token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        # Verify user still exists
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create new access token
        new_access_token = auth_service.create_token(user_id)
        return {"token": new_access_token}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

# Topics endpoints
@app.get("/api/topics")
async def get_topics():
    """Get available quiz topics"""
    topics = [
        "algorithms",
        "data-structures", 
        "javascript",
        "python",
        "react",
        "databases",
        "system-design",
        "web-development"
    ]
    return {"topics": topics}

# Duel endpoints
@app.post("/api/duel/match")
async def join_matchmaking(request: dict, user: User = Depends(auth_service.get_current_user)):
    """Join matchmaking queue for a topic"""
    try:
        topic = request.get("topic")
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        
        ticket = await matchmaking_service.join_queue(user.id, topic)
        return {"ticket": ticket.dict()}
    except Exception as e:
        print(f"Error joining matchmaking: {e}")
        raise HTTPException(status_code=500, detail="Failed to join matchmaking")

@app.post("/api/duel/cancel")
async def cancel_matchmaking(request: dict, user: User = Depends(auth_service.get_current_user)):
    """Cancel matchmaking"""
    try:
        ticket_id = request.get("ticketId")
        if not ticket_id:
            raise HTTPException(status_code=400, detail="Ticket ID is required")
        
        await matchmaking_service.cancel_queue(user.id, ticket_id)
        return {"success": True}
    except Exception as e:
        print(f"Error canceling matchmaking: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel matchmaking")

@app.get("/api/duel/{duel_id}")
async def get_duel(duel_id: str, user: dict = Depends(auth_service.get_current_user)):
    """Get duel information"""
    try:
        duel = await duel_service.get_duel(duel_id)
        if not duel:
            raise HTTPException(status_code=404, detail="Duel not found")
        
        # Check if user is part of this duel
        if user["id"] not in [duel.player1.id, duel.player2.id]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {"duel": duel.dict()}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting duel: {e}")
        raise HTTPException(status_code=500, detail="Failed to get duel")

@app.get("/api/user/active-duel")
async def get_user_active_duel(user: dict = Depends(auth_service.get_current_user)):
    """Get user's active duel for reconnection"""
    try:
        active_duel = await duel_service.get_user_active_duel(user["id"])
        if not active_duel:
            return {"activeDuel": None}
        
        # Get opponent info
        opponent_id = active_duel.player2.id if active_duel.player1.id == user["id"] else active_duel.player1.id
        
        return {
            "activeDuel": {
                "id": active_duel.id,
                "status": active_duel.status.value,
                "currentQuestion": active_duel.current_question,
                "opponent": {
                    "id": opponent_id,
                    "username": f"Player_{opponent_id[:8]}"
                },
                "topic": active_duel.topic,
                "scores": {
                    "player1": active_duel.player1.score,
                    "player2": active_duel.player2.score
                }
            }
        }
    except Exception as e:
        print(f"Error getting user active duel: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active duel")

# Socket.IO events
@sio.event
async def connect(sid, environ, auth=None):
    """Handle client connection - simplified for debugging"""
    try:
        print(f"Socket.IO connect event triggered for {sid}")
        logger.debug(f"Auth data: {auth}")
        logger.debug(f"Environ keys: {list(environ.keys()) if environ else 'None'}")
        
        user_id = None
        if auth and auth.get("userId"):
            user_id = auth.get("userId")
            print(f"👤 User {user_id} connecting with auth")
            
            # Check if user has an active duel
            active_duel = await duel_service.get_user_active_duel(user_id)
            if active_duel:
                print(f"🔄 User {user_id} reconnecting to active duel {active_duel.id}")
                
                # Join the duel room
                duel_room = f"duel_{active_duel.id}"
                await sio.enter_room(sid, duel_room)
                print(f"🏠 User {user_id} rejoined room {duel_room}")
                
                # Send current duel state
                await sio.emit("duel_reconnected", {
                    "duelId": active_duel.id,
                    "currentQuestion": active_duel.current_question,
                    "scores": {
                        "player1": active_duel.player1.score,
                        "player2": active_duel.player2.score
                    },
                    "status": active_duel.status.value
                }, room=sid)
                
                # If there's a current question, send it
                if active_duel.current_question is not None and active_duel.current_question < len(active_duel.questions):
                    current_q = active_duel.questions[active_duel.current_question]
                    question_data = {
                        "duelId": active_duel.id,
                        "questionIndex": active_duel.current_question,
                        "question": {
                            "prompt": current_q.prompt,
                            "options": current_q.options
                        },
                        "timeLimit": 9
                    }
                    await sio.emit("question_start", question_data, room=sid)
                    print(f"📡 Sent current question {active_duel.current_question} to reconnected user")
        
        # Store session
        await sio.save_session(sid, {"user_id": user_id or "temp_user", "authenticated": user_id is not None})
        print(f"Client {sid} connected successfully")
        
    except Exception as e:
        print(f"Error in connect handler: {e}")
        raise e

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client {sid} disconnected")
    await matchmaking_service.handle_disconnect(sid)

@sio.event
async def join_queue(sid, data):
    """Handle join matchmaking queue"""
    try:
        print(f"🎮 JOIN_QUEUE event received from {sid}")
        print(f"📊 Queue data: {data}")
        
        user_id = data.get("userId")
        topic = data.get("topic")
        
        if not user_id or not topic:
            logger.warning(f"❌ Invalid data from {sid}: userId={user_id}, topic={topic}")
            await sio.emit("error", {"code": "INVALID_DATA", "message": "User ID and topic are required"}, room=sid)
            return
        
        print(f"👤 User {user_id} joining queue for topic '{topic}' (socket: {sid})")
        
        # Store user session
        await sio.save_session(sid, {"user_id": user_id})
        
        # Join matchmaking queue
        ticket = await matchmaking_service.join_queue(user_id, topic, sid)
        print(f"🎫 Ticket created for {user_id}: {ticket.id}")
        
        # Send confirmation to user (convert datetime to string for JSON serialization)
        ticket_data = ticket.dict()
        ticket_data["created_at"] = ticket.created_at.isoformat()
        await sio.emit("queue_joined", {"ticket": ticket_data}, room=sid)
        print(f"✅ Queue joined confirmation sent to {user_id}")
        
    except Exception as e:
        print(f"💥 Error in join_queue for {sid}: {e}")
        await sio.emit("error", {"code": "JOIN_QUEUE_ERROR", "message": str(e)}, room=sid)

@sio.event
async def cancel_queue(sid, data):
    """Handle cancel matchmaking"""
    try:
        session = await sio.get_session(sid)
        user_id = session.get("user_id")
        ticket_id = data.get("ticketId")
        
        if not user_id or not ticket_id:
            await sio.emit("error", {"code": "INVALID_DATA", "message": "Invalid request"}, room=sid)
            return
        
        await matchmaking_service.cancel_queue(user_id, ticket_id)
        await sio.emit("queue_cancelled", {"success": True}, room=sid)
        
    except Exception as e:
        print(f"Error in cancel_queue: {e}")
        await sio.emit("error", {"code": "CANCEL_QUEUE_ERROR", "message": str(e)}, room=sid)

@sio.event
async def answer(sid, data):
    """Handle answer submission"""
    try:
        print(f"📝 ANSWER RECEIVED from socket {sid}")
        print(f"📊 Raw answer data: {data}")
        
        session = await sio.get_session(sid)
        user_id = session.get("user_id")
        
        duel_id = data.get("duelId")
        question_index = data.get("questionIndex")
        selected_index = data.get("selectedIndex")
        client_timestamp = data.get("clientTs")
        
        print(f"👤 User {user_id} answered:")
        print(f"   🎯 Duel: {duel_id}")
        print(f"   ❓ Question: {question_index}")
        print(f"   ✅ Selected option: {selected_index}")
        print(f"   ⏰ Client timestamp: {client_timestamp}")
        
        if not all([user_id, duel_id, question_index is not None, selected_index is not None]):
            print(f"❌ Invalid answer data from {sid}:")
            print(f"   user_id: {user_id}")
            print(f"   duel_id: {duel_id}")
            print(f"   question_index: {question_index}")
            print(f"   selected_index: {selected_index}")
            await sio.emit("error", {"code": "INVALID_DATA", "message": "Invalid answer data"}, room=sid)
            return
        
        print(f"🔄 Processing answer for user {user_id}...")
        result = await duel_service.submit_answer(
            duel_id, user_id, question_index, selected_index, client_timestamp
        )
        
        print(f"✅ Answer processed successfully for {user_id}:")
        print(f"   🎯 Result: {result}")
        await sio.emit("answer_submitted", {"result": result}, room=sid)
        print(f"📤 Answer result sent to {user_id}")
        
    except Exception as e:
        print(f"💥 Error processing answer from socket {sid}:")
        print(f"   🚨 Error: {str(e)}")
        print(f"   📊 Data: {data}")
        await sio.emit("error", {"code": "ANSWER_ERROR", "message": str(e)}, room=sid)

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    await matchmaking_service.start_background_tasks()
    print("Background tasks started")

if __name__ == "__main__":
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
