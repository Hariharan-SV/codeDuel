# CodeDuel Setup Guide

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Google Cloud Project with Firestore enabled
- Google Gemini API key

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd codeDuel
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FIRESTORE_CREDENTIALS=path/to/service-account-key.json
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
cp .env.example .env
```

Edit `.env` file:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 4. Firebase/Firestore Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Enable Firestore Database
4. Go to Project Settings > Service Accounts
5. Generate new private key (downloads JSON file)
6. Place the JSON file in `backend/credentials/` directory
7. Update `FIRESTORE_CREDENTIALS` path in backend `.env`

### 5. Google Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add the key to `GEMINI_API_KEY` in backend `.env`

### 6. Run the Application

Terminal 1 (Backend):
```bash
cd backend
uvicorn main:socket_app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` to start playing!

## Docker Setup (Alternative)

```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit the .env files with your credentials

# Run with Docker Compose
docker-compose up --build
```

## Firestore Collections Structure

The application will automatically create these collections:

- `users` - User profiles and ratings
- `duels` - Duel records and game state
- `matchmaking` - Temporary matchmaking queue

## Troubleshooting

### Backend Issues

1. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
2. **Firestore connection**: Verify service account JSON path and permissions
3. **Gemini API**: Check API key validity and quota limits

### Frontend Issues

1. **Build errors**: Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. **Connection issues**: Verify backend is running on port 8000
3. **WebSocket errors**: Check CORS settings in backend

### Common Issues

1. **CORS errors**: Add your frontend URL to `CORS_ORIGINS` in backend `.env`
2. **Authentication failures**: Verify JWT_SECRET_KEY is set
3. **Question generation fails**: Check Gemini API key and internet connection

## Development Tips

- Use browser dev tools to monitor WebSocket connections
- Check backend logs for detailed error messages
- Firestore data can be viewed in Firebase Console
- Mock questions are used when Gemini API is unavailable

## Production Deployment

1. Set strong JWT_SECRET_KEY
2. Configure proper CORS origins
3. Use environment-specific Firestore projects
4. Enable Firestore security rules
5. Set up proper logging and monitoring
