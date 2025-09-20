# CodeDuel

A real-time quiz duel application where two users compete by answering programming questions in 90 seconds.
[Medium](https://hariharan-sv.medium.com/codeduel-a-real-time-programming-quiz-duel-677ec976ef85)

## Architecture

- **Frontend**: React + Vite + TypeScript
- **Backend**: FastAPI (Python) with WebSocket support
- **Database**: Firestore
- **AI**: Google Gemini for question generation

## Project Structure

```
codeDuel/
├── frontend/          # React + Vite + TypeScript client
├── backend/           # FastAPI server
├── shared/            # Shared types and utilities
├── ARCHITECTURE.md    # Detailed architecture documentation
└── README.md         # This file
```

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create `.env` files in both frontend and backend directories:

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
FIRESTORE_CREDENTIALS=path_to_service_account.json
CORS_ORIGINS=http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Game Rules

- 10 questions per duel
- 9 seconds per question
- Multiple choice format
- Real-time synchronization
- Winner determined by highest score
