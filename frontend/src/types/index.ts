export interface User {
  id: string;
  username: string;
  rating: number;
  createdAt: string;
  updatedAt: string;
}

export interface Question {
  id: string;
  prompt: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface Player {
  id: string;
  score: number;
}

export interface Duel {
  id: string;
  topic: string;
  status: 'pending' | 'active' | 'completed' | 'canceled';
  player1: Player;
  player2: Player;
  winnerId?: string;
  currentQuestion?: number;
  questions: Question[];
  startedAt?: string;
  endedAt?: string;
  createdAt: string;
}

export interface Answer {
  questionIndex: number;
  userId: string;
  selectedIndex: number;
  correct: boolean;
  responseMs: number;
  answeredAt: string;
}

export interface MatchmakingTicket {
  id: string;
  userId: string;
  topic: string;
  createdAt: string;
  socketId?: string;
}

export interface GameEvent {
  type: string;
  data: any;
  timestamp: string;
}

export interface SocketEvents {
  // Client to Server
  join_queue: { userId: string; topic: string };
  cancel_queue: { ticketId: string };
  answer: {
    duelId: string;
    questionIndex: number;
    selectedIndex: number;
    clientTs: number;
  };

  // Server to Client
  queue_joined: { ticket: MatchmakingTicket };
  queue_cancelled: { success: boolean };
  matched: {
    duelId: string;
    opponent: { id: string; username: string };
    topic: string;
  };
  pregame_countdown: { duelId: string; startsAt: string };
  question_start: {
    duelId: string;
    questionIndex: number;
    question: { prompt: string; options: string[] };
    deadline: string;
    timeLimit: number;
  };
  question_end: {
    duelId: string;
    questionIndex: number;
    correctIndex: number;
    explanation: string;
    scores: { player1: number; player2: number };
  };
  duel_end: {
    duelId: string;
    winnerId?: string;
    finalScores: { player1: number; player2: number };
    duration: number;
  };
  answer_submitted: {
    result: {
      correct: boolean;
      points_earned: number;
      time_taken: number;
    };
  };
  duel_reconnected: {
    duelId: string;
    currentQuestion: number;
    scores: { player1: number; player2: number };
    status: string;
  };
  error: { code: string; message: string };
}
