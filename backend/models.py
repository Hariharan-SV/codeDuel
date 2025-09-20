from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DuelStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELED = "canceled"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class User(BaseModel):
    id: str
    username: str
    rating: int = 1200
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Question(BaseModel):
    id: str
    prompt: str
    options: List[str]
    correct_index: int
    explanation: str
    topic: str
    difficulty: Difficulty

class Player(BaseModel):
    id: str
    score: int = 0

class Duel(BaseModel):
    id: str
    topic: str
    status: DuelStatus = DuelStatus.PENDING
    player1: Player
    player2: Player
    winner_id: Optional[str] = None
    current_question: Optional[int] = None
    questions: List[Question] = []
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Answer(BaseModel):
    question_index: int
    user_id: str
    selected_index: int
    correct: bool
    response_ms: int
    answered_at: datetime = Field(default_factory=datetime.utcnow)

class MatchmakingTicket(BaseModel):
    id: str
    user_id: str
    topic: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    socket_id: Optional[str] = None

class DuelResult(BaseModel):
    duel_id: str
    winner_id: Optional[str]
    player1_score: int
    player2_score: int
    questions_answered: int
    duration_seconds: int

class QuestionSet(BaseModel):
    topic: str
    questions: List[Question]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class GameEvent(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
