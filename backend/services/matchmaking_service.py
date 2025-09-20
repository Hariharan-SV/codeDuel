import uuid
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import socketio

from models import MatchmakingTicket, User, Duel, Player, DuelStatus
from database import FirestoreDB
from services.question_service import QuestionService
from services.duel_service import DuelService

logger = logging.getLogger(__name__)

class MatchmakingService:
    def __init__(self, db: FirestoreDB, sio: socketio.AsyncServer):
        self.db = db
        self.sio = sio
        self.question_service = QuestionService()
        
        # In-memory queues for fast matching (topic -> list of tickets)
        self.queues: Dict[str, List[MatchmakingTicket]] = {}
        self.user_tickets: Dict[str, MatchmakingTicket] = {}  # user_id -> ticket
        self.socket_users: Dict[str, str] = {}  # socket_id -> user_id
        
        # Background task reference
        self._cleanup_task = None
    
    async def start_background_tasks(self):
        """Start background tasks - call this after event loop is running"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_stale_tickets())
    
    async def join_queue(self, user_id: str, topic: str, socket_id: str = None) -> MatchmakingTicket:
        """Add user to matchmaking queue"""
        
        # Cancel any existing ticket for this user
        if user_id in self.user_tickets:
            await self.cancel_queue(user_id, self.user_tickets[user_id].id)
        
        # Create new ticket
        ticket = MatchmakingTicket(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            socket_id=socket_id
        )
        
        # Add to queues
        if topic not in self.queues:
            self.queues[topic] = []
        
        self.queues[topic].append(ticket)
        self.user_tickets[user_id] = ticket
        
        if socket_id:
            self.socket_users[socket_id] = user_id
        
        print(f"🎪 User {user_id} added to '{topic}' queue (total: {len(self.queues[topic])} players)")
        
        # Try to find a match immediately
        print(f"🔄 Attempting to match players in '{topic}' queue...")
        await self._try_match(topic)
        
        return ticket
    
    async def cancel_queue(self, user_id: str, ticket_id: str):
        """Remove user from matchmaking queue"""
        
        if user_id not in self.user_tickets:
            return
        
        ticket = self.user_tickets[user_id]
        if ticket.id != ticket_id:
            return
        
        # Remove from topic queue
        topic = ticket.topic
        if topic in self.queues:
            self.queues[topic] = [t for t in self.queues[topic] if t.id != ticket_id]
        
        # Remove from user tracking
        del self.user_tickets[user_id]
        
        # Remove socket tracking
        if ticket.socket_id and ticket.socket_id in self.socket_users:
            del self.socket_users[ticket.socket_id]
        
        print(f"User {user_id} cancelled matchmaking for topic {topic}")
    
    async def handle_disconnect(self, socket_id: str):
        """Handle user disconnection"""
        if socket_id in self.socket_users:
            user_id = self.socket_users[socket_id]
            if user_id in self.user_tickets:
                ticket = self.user_tickets[user_id]
                await self.cancel_queue(user_id, ticket.id)
    
    async def _try_match(self, topic: str):
        """Try to match two users in the same topic"""
        print(f"🔍 Checking for matches in topic '{topic}'")
        print(f"📊 Queue status: {len(self.queues.get(topic, []))} players waiting")
        
        if topic not in self.queues or len(self.queues[topic]) < 2:
            print(f"⏳ Not enough players for match in '{topic}' (need 2, have {len(self.queues.get(topic, []))})")
            return
        
        # Get two users from the queue
        ticket1 = self.queues[topic].pop(0)
        ticket2 = self.queues[topic].pop(0)
        
        print(f"🎯 MATCH FOUND! {ticket1.user_id} vs {ticket2.user_id} in '{topic}'")
        
        # Remove from user tracking
        if ticket1.user_id in self.user_tickets:
            del self.user_tickets[ticket1.user_id]
        if ticket2.user_id in self.user_tickets:
            del self.user_tickets[ticket2.user_id]
        
        try:
            # Create duel
            print(f"🏟️ Creating duel for {ticket1.user_id} vs {ticket2.user_id}")
            duel = await self._create_duel(ticket1.user_id, ticket2.user_id, topic)
            print(f"✅ Duel created with ID: {duel.id}")
            
            # Notify both players
            match_data = {
                "duelId": duel.id,
                "opponent": {
                    "id": ticket2.user_id,
                    "username": f"Player_{ticket2.user_id[:8]}"
                },
                "topic": topic
            }
            
            # Join both players to the duel room for real-time communication
            duel_room = f"duel_{duel.id}"
            if ticket1.socket_id:
                await self.sio.enter_room(ticket1.socket_id, duel_room)
                print(f"🏠 {ticket1.user_id} joined room {duel_room}")
            if ticket2.socket_id:
                await self.sio.enter_room(ticket2.socket_id, duel_room)
                print(f"🏠 {ticket2.user_id} joined room {duel_room}")
            
            print(f"📤 Sending match notification to {ticket1.user_id} (socket: {ticket1.socket_id})")
            if ticket1.socket_id:
                await self.sio.emit("matched", match_data, room=ticket1.socket_id)
            
            match_data["opponent"] = {
                "id": ticket1.user_id,
                "username": f"Player_{ticket1.user_id[:8]}"
            }
            
            print(f"📤 Sending match notification to {ticket2.user_id} (socket: {ticket2.socket_id})")
            if ticket2.socket_id:
                await self.sio.emit("matched", match_data, room=ticket2.socket_id)
            
            print(f"Matched users {ticket1.user_id} and {ticket2.user_id} for topic {topic}")
            
            # Start duel after a short delay
            asyncio.create_task(self._start_duel_countdown(duel.id, [ticket1.socket_id, ticket2.socket_id]))
            
        except Exception as e:
            print(f"Error creating match: {e}")
            # Put users back in queue
            self.queues[topic].insert(0, ticket1)
            self.queues[topic].insert(0, ticket2)
            self.user_tickets[ticket1.user_id] = ticket1
            self.user_tickets[ticket2.user_id] = ticket2
    
    async def _create_duel(self, user1_id: str, user2_id: str, topic: str) -> Duel:
        """Create a new duel between two users"""
        
        # Generate questions for the duel
        questions = await self.question_service.generate_questions(topic, 10)
        
        duel = Duel(
            id=str(uuid.uuid4()),
            topic=topic,
            status=DuelStatus.PENDING,
            player1=Player(id=user1_id),
            player2=Player(id=user2_id),
            questions=questions
        )
        
        # Save to database
        duel_data = duel.dict()
        duel_data["created_at"] = duel.created_at.isoformat()
        if duel.started_at:
            duel_data["started_at"] = duel.started_at.isoformat()
        if duel.ended_at:
            duel_data["ended_at"] = duel.ended_at.isoformat()
        
        # Convert questions to dict format
        duel_data["questions"] = [q.dict() for q in questions]
        
        success = await self.db.create_document("duels", duel.id, duel_data)
        if not success:
            raise Exception("Failed to create duel in database")
        
        return duel
    
    async def _start_duel_countdown(self, duel_id: str, socket_ids: List[str]):
        """Start countdown before duel begins"""
        
        print(f"⏰ COUNTDOWN STARTED for duel {duel_id}")
        print(f"⏰ COUNTDOWN STARTED for duel {duel_id}")
        
        # Wait 3 seconds for pregame
        await asyncio.sleep(3)
        
        # Notify clients that duel is starting
        countdown_data = {
            "duelId": duel_id,
            "startsAt": (datetime.utcnow() + timedelta(seconds=3)).isoformat()
        }
        
        duel_room = f"duel_{duel_id}"
        print(f"📢 Sending pregame_countdown to room {duel_room}")
        print(f"📢 Sending pregame_countdown to room {duel_room}")
        
        # Send to duel room instead of individual sockets
        await self.sio.emit("pregame_countdown", countdown_data, room=duel_room)
        
        # Also send to individual sockets as backup
        for socket_id in socket_ids:
            if socket_id:
                print(f"📢 Sending pregame_countdown to socket {socket_id}")
                await self.sio.emit("pregame_countdown", countdown_data, room=socket_id)
        
        print(f"⏳ Waiting 3 seconds for countdown...")
        # Wait for countdown
        await asyncio.sleep(3)
        
        print(f"🚀 Starting actual duel {duel_id}")
        print(f"🚀 Starting actual duel {duel_id}")
        
        # Start the actual duel
        from services.duel_service import DuelService
        duel_service = DuelService(self.db, self.sio)
        await duel_service.start_duel(duel_id)
    
    async def _cleanup_stale_tickets(self):
        """Background task to clean up stale matchmaking tickets"""
        while True:
            try:
                cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                
                for topic in list(self.queues.keys()):
                    original_count = len(self.queues[topic])
                    self.queues[topic] = [
                        ticket for ticket in self.queues[topic]
                        if ticket.created_at > cutoff_time
                    ]
                    
                    removed_count = original_count - len(self.queues[topic])
                    if removed_count > 0:
                        print(f"Cleaned up {removed_count} stale tickets for topic {topic}")
                
                # Clean up user_tickets mapping
                stale_users = [
                    user_id for user_id, ticket in self.user_tickets.items()
                    if ticket.created_at <= cutoff_time
                ]
                
                for user_id in stale_users:
                    del self.user_tickets[user_id]
                
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except Exception as e:
                print(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
