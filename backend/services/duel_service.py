import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import socketio

from models import Duel, DuelStatus, Answer, DuelResult
from database import FirestoreDB

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DuelService:
    # Static class variables for shared state
    active_duels: Dict[str, Duel] = {}
    duel_timers: Dict[str, asyncio.Task] = {}
    
    def __init__(self, db: FirestoreDB, sio: socketio.AsyncServer):
        self.db = db
        self.sio = sio
        
    async def get_duel(self, duel_id: str) -> Optional[Duel]:
        """Get a duel by ID"""
        
        # Check active duels first
        if duel_id in DuelService.active_duels:
            return DuelService.active_duels[duel_id]
        
        # Get from database
        duel_data = await self.db.get_document("duels", duel_id)
        if not duel_data:
            print(f"❌ Duel {duel_id} not found in database")
            return None
        
        # Convert datetime strings back to datetime objects
        if "created_at" in duel_data and duel_data["created_at"]:
            duel_data["created_at"] = datetime.fromisoformat(duel_data["created_at"])
        if "started_at" in duel_data and duel_data["started_at"]:
            duel_data["started_at"] = datetime.fromisoformat(duel_data["started_at"])
        if "ended_at" in duel_data and duel_data["ended_at"]:
            duel_data["ended_at"] = datetime.fromisoformat(duel_data["ended_at"])
        
        DuelService.active_duels[duel_id] = Duel(**duel_data)

        return Duel(**duel_data)
    
    async def get_user_active_duel(self, user_id: str) -> Optional[Duel]:
        """Find user's active duel for reconnection"""
        try:
            print(f"🔍 Looking for active duel for user {user_id}")
            
            # Check active duels first
            for duel_id, duel in DuelService.active_duels.items():
                if (duel.player1.id == user_id or duel.player2.id == user_id) and duel.status == DuelStatus.ACTIVE:
                    print(f"✅ Found active duel {duel_id} for user {user_id}")
                    return duel
            
            # Query database for active duels involving this user
            all_duels = await self.db.query_collection("duels", [("status", "==", "active")])
            for duel_data in all_duels:
                if (duel_data.get("player1", {}).get("id") == user_id or 
                    duel_data.get("player2", {}).get("id") == user_id):
                    
                    print(f"✅ Found active duel in DB for user {user_id}")
                    # Load the duel into active duels
                    duel = await self.get_duel(duel_data["id"])
                    if duel:
                        DuelService.active_duels[duel.id] = duel
                        return duel
            
            print(f"❌ No active duel found for user {user_id}")
            return None
            
        except Exception as e:
            print(f"💥 Error finding active duel for user {user_id}: {e}")
            return None
    
    async def start_duel(self, duel_id: str):
        """Start a duel and begin question sequence"""
        
        print(f"🚀 START_DUEL CALLED for duel {duel_id}")
        print(f"🚀 START_DUEL CALLED for duel {duel_id}")
        
        duel = await self.get_duel(duel_id)
        if not duel:
            print(f"❌ Duel {duel_id} not found")
            print(f"❌ Duel {duel_id} not found")
            return
        
        print(f"📋 Duel {duel_id} status: {duel.status}")
        print(f"📋 Duel {duel_id} status: {duel.status}")
        
        if duel.status != DuelStatus.PENDING:
            print(f"⚠️ Duel {duel_id} is not in pending status: {duel.status}")
            logger.warning(f"⚠️ Duel {duel_id} is not in pending status: {duel.status}")
            return
        
        # Update duel status
        duel.status = DuelStatus.ACTIVE
        duel.started_at = datetime.utcnow()
        duel.current_question = 0
        
        # Add to active duels
        DuelService.active_duels[duel_id] = duel
        print(f"✅ Added duel {duel_id} to active duels")
        print(f"   Total active duels: {len(DuelService.active_duels), DuelService.active_duels}")
        
        print(f"💾 Updating duel {duel_id} in database")
        
        # Save to database
        await self._update_duel_in_db(duel)
        
        print(f"✅ Duel {duel_id} started successfully")
        print(f"✅ Duel {duel_id} started successfully")
        
        # Start question sequence
        print(f"🎯 Starting question sequence for duel {duel_id}")
        print(f"🎯 Starting question sequence for duel {duel_id, DuelService.active_duels}")
        self.duel_timers[duel_id] = asyncio.create_task(self._run_question_sequence(duel))
    
    async def submit_answer(self, duel_id: str, user_id: str, question_index: int, selected_index: int, client_timestamp: Optional[int] = None) -> Dict:
        """Submit an answer for a question"""
        print(f"\n📝 ANSWER SUBMISSION RECEIVED")
        print(f"   🎯 Duel ID: {duel_id}")
        print(f"   👤 User ID: {user_id}")
        print(f"   ❓ Question Index: {question_index}")
        print(f"   ✅ Selected Index: {selected_index}")
        print(f"   ⏰ Client Timestamp: {client_timestamp}")
        print(f"   🔍 Active Duels: {list(DuelService.active_duels.keys())}")

                
        duel = DuelService.active_duels.get(duel_id)
        if not duel:
            raise Exception("Duel not found or not active")
        
        if duel.current_question == 1:
            return

        # if int(duel.current_question) != int(question_index):
        #     raise Exception("Invalid question index", duel.current_question, question_index)
        
        if user_id not in [duel.player1.id, duel.player2.id]:
            raise Exception("User not in this duel")
        
        # For now, allow answers during the duel (we'll handle timing on frontend)
        # TODO: Implement proper question timing tracking
        current_time = datetime.utcnow()
        time_elapsed = 5.0  # Default time for scoring calculation
        
        # Check if user already answered this question
        existing_answers = await self.db.get_subcollection("duels", duel_id, "answers")
        for answer_data in existing_answers:
            if (answer_data.get("user_id") == user_id and 
                answer_data.get("question_index") == question_index):
                raise Exception("Already answered this question")
        
        # Get the question
        question = duel.questions[question_index]
        is_correct = selected_index == question.correct_index
        
        # Create answer record
        answer = Answer(
            question_index=question_index,
            user_id=user_id,
            selected_index=selected_index,
            correct=is_correct,
            response_ms=int(time_elapsed * 1000)
        )
        
        # Save answer to database
        answer_data = answer.dict()
        answer_data["answered_at"] = answer.answered_at.isoformat()
        
        await self.db.add_to_subcollection("duels", duel_id, "answers", answer_data)
        
        # Update player score
        total_points = 0
        if is_correct:
            points = 10  # Base points for correct answer
            time_bonus = max(0, 9 - int(time_elapsed))  # Bonus points for speed
            total_points = points + time_bonus
            
            print(f"💯 Correct answer! Base: {points}, Time bonus: {time_bonus}, Total: {total_points}")
            
            if user_id == duel.player1.id:
                duel.player1.score += total_points
                print(f"🎯 Player1 ({user_id}) score updated: {duel.player1.score}")
            else:
                duel.player2.score += total_points
                print(f"🎯 Player2 ({user_id}) score updated: {duel.player2.score}")
            
            # Update duel in database
            await self._update_duel_in_db(duel)
        else:
            print(f"❌ Incorrect answer - no points awarded")
        
        print(f"User {user_id} answered question {question_index} in duel {duel_id}: {'correct' if is_correct else 'incorrect'}")
        
        return {
            "correct": is_correct,
            "points_earned": total_points if is_correct else 0,
            "time_taken": time_elapsed
        }
    
    async def _run_question_sequence(self, duel: Duel):
        """Run the sequence of questions for a duel"""
        print(f"\n🎯 QUESTION SEQUENCE STARTED for duel {duel.id}")
        print(f"   Total questions: {len(duel.questions)}")
        print(f"   Current active duels: {list(DuelService.active_duels.keys()), DuelService.active_duels}")
        
        try:
            # Ensure duel is in active_duels
            if duel.id not in DuelService.active_duels:
                print(f"⚠️  Duel {duel.id} not in active_duels at start of question sequence")
                DuelService.active_duels[duel.id] = duel
                print(f"✅ Added duel {duel.id} back to active_duels")
            
            duel.status = DuelStatus.ACTIVE
            await self._update_duel_in_db(duel)
            
            for question_index in range(min(10, len(duel.questions))):  # Ensure we don't exceed available questions
                print(f"\n📝 Preparing question {question_index} for duel {duel.id}")
                
                # Double-check duel is still active
                if duel.id not in DuelService.active_duels:
                    print(f"⚠️  Duel {duel.id} was removed from active_duels during question sequence")
                    DuelService.active_duels[duel.id] = duel
                    print(f"✅ Added duel {duel.id} back to active_duels")
                
                duel.current_question = question_index
                await self._update_duel_in_db(duel)
                
                # Send question to both players
                question = duel.questions[question_index]
                question_data = {
                    "duelId": duel.id,
                    "questionIndex": question_index,
                    "question": {
                        "prompt": question.prompt,
                        "options": question.options
                    },
                    "deadline": (datetime.utcnow() + timedelta(seconds=9)).isoformat(),
                    "timeLimit": 9
                }
                
                # Emit to both players
                room_name = f"duel_{duel.id}"
                print(f"📡 Sending question {question_index} to room {room_name}")
                print(f"📡 Sending question {question_index} to room {room_name}")
                
                await self.sio.emit("question_start", question_data, room=room_name)
                
                print(f"✅ Sent question {question_index} for duel {duel.id} {DuelService.active_duels}")
                
                # Wait for 9 seconds (question time limit)
                wait_time = 9
                print(f"⏰ Waiting {wait_time} seconds for question {question_index}")
                
                # Split the wait into smaller chunks to be more responsive
                chunk_size = 1.0  # Check every second
                for _ in range(wait_time):
                    await asyncio.sleep(chunk_size)
                    # Double-check the duel is still active
                    if duel.id not in DuelService.active_duels:
                        print(f"⚠️  Duel {duel.id} was removed from active_duels during question {question_index}")
                        DuelService.active_duels[duel.id] = duel
                        print(f"✅ Added duel {duel.id} back to active_duels")
                
                # Send question end with correct answer
                question_end_data = {
                    "duelId": duel.id,
                    "questionIndex": question_index,
                    "correctIndex": question.correct_index,
                    "explanation": question.explanation,
                    "scores": {
                        "player1": duel.player1.score,
                        "player2": duel.player2.score
                    }
                }
                
                await self.sio.emit("question_end", question_end_data, room=f"duel_{duel.id}")
                
                # Short break between questions
                await asyncio.sleep(2)
            
            # Duel completed successfully
            print(f"🏁 All questions completed for duel {duel.id}")
            print(f"   Final scores - Player1: {duel.player1.score}, Player2: {duel.player2.score}")
            await self._end_duel(duel)
            
        except asyncio.CancelledError:
            print(f"ℹ️  Question sequence for duel {duel.id} was cancelled")
            raise
            
        except Exception as e:
            print(f"🔥 ERROR in question sequence for duel {duel.id}: {str(e)}")
            import traceback
            traceback.print_exc()
            try:
                await self._end_duel(duel, error=True)
            except Exception as end_error:
                print(f"🔥 Failed to end duel after error: {end_error}")
        finally:
            # Clean up the timer when the question sequence is done
            if duel.id in self.duel_timers:
                self.duel_timers[duel.id].cancel()
                del self.duel_timers[duel.id]
    
    async def _end_duel(self, duel: Duel, error: bool = False):
        """End a duel and determine winner"""
        print(f"\n🏁 Ending duel {duel.id}")
        
        # Set end time
        duel.ended_at = datetime.utcnow()
        duel.status = DuelStatus.COMPLETED if not error else DuelStatus.ERROR
        
        # Only determine winner if not an error
        if not error:
            # Determine winner based on score
            if duel.player1.score > duel.player2.score:
                duel.winner_id = duel.player1.id
            elif duel.player2.score > duel.player1.score:
                duel.winner_id = duel.player2.id
            # In case of tie, winner_id remains None
        
        # Update database
        await self._update_duel_in_db(duel)
        
        # Prepare result data
        result_data = {
            "duelId": duel.id,
            "winnerId": duel.winner_id,
            "finalScores": {
                "player1": duel.player1.score,
                "player2": duel.player2.score
            },
            "ended_at": duel.ended_at.isoformat() if duel.ended_at else None,
            "duration": (duel.ended_at - duel.started_at).total_seconds() if duel.started_at else 0
        }
        
        # Notify players
        room_name = f"duel_{duel.id}"
        await self.sio.emit("duel_ended", result_data, room=room_name)
        
        # Give some time for the end message to be sent
        await asyncio.sleep(2)
        
        # Clean up
        if duel.id in DuelService.active_duels:
            print(f"🧹 Removing duel {duel.id} from active duels")
            del DuelService.active_duels[duel.id]
        
        print(f"🏁 Duel {duel.id} ended. Winner: {duel.winner_id or 'Tie'}")
    
    async def _update_duel_in_db(self, duel: Duel):
        """Update duel in database"""
        
        duel_data = duel.dict()
        duel_data["created_at"] = duel.created_at.isoformat()
        if duel.started_at:
            duel_data["started_at"] = duel.started_at.isoformat()
        if duel.ended_at:
            duel_data["ended_at"] = duel.ended_at.isoformat()
        
        # Convert questions to dict format
        duel_data["questions"] = [q.dict() for q in duel.questions]
        
        await self.db.update_document("duels", duel.id, duel_data)