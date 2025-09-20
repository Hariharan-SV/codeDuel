# CodeDuel Project Structure

```
codeDuel/
├── backend/                    # Backend server code
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication and user management
│   │   ├── duel_service.py    # Duel management and game logic
│   │   ├── matchmaking.py     # Matchmaking service for pairing players
│   │   └── question_service.py# Question generation and management
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── models.py             # Data models and schemas
│   ├── database.py           # Database connection and operations
│   ├── config.py             # Configuration settings
│   └── requirements.txt      # Python dependencies
│
├── frontend/                  # Frontend React application
│   ├── public/               # Static files
│   └── src/
│       ├── components/       # Reusable UI components
│       │   ├── DuelScreen.tsx  # Main game screen
│       │   ├── Lobby.tsx     # Lobby component
│       │   ├── Matchmaking.tsx # Matchmaking component
│       │   ├── Results.tsx   # Results screen
│       │   └── TopicSelect.tsx # Topic selection component
│       │
│       ├── contexts/         # React contexts
│       │   ├── AuthContext.tsx  # Authentication context
│       │   └── SocketContext.tsx # WebSocket context
│       │
│       ├── types/            # TypeScript type definitions
│       │   └── index.ts      # Shared type definitions
│       │
│       ├── utils/            # Utility functions
│       ├── App.tsx           # Main application component
│       ├── main.tsx          # Application entry point
│       └── vite-env.d.ts     # Vite type definitions
│
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Backend Dockerfile
├── Dockerfile.frontend       # Frontend Dockerfile
└── README.md                 # Project documentation
```

## Key Files and Their Purposes

### Backend
- `main.py`: FastAPI application setup, routes, and WebSocket handlers
- `services/duel_service.py`: Manages duels, game state, and player interactions
- `services/matchmaking.py`: Handles player matching and queue management
- `services/question_service.py`: Generates and serves questions
- `services/auth_service.py`: Handles user authentication and JWT tokens
- `models.py`: Defines data models and Pydantic schemas
- `database.py`: Database connection and CRUD operations

### Frontend
- `components/DuelScreen.tsx`: Main game interface for the duel
- `components/Matchmaking.tsx`: Handles the matchmaking process
- `components/Results.tsx`: Displays duel results and statistics
- `contexts/AuthContext.tsx`: Manages user authentication state
- `contexts/SocketContext.tsx`: Handles WebSocket connections and events
- `types/index.ts`: Shared TypeScript type definitions

### Configuration
- `docker-compose.yml`: Defines services for development/production
- `Dockerfile`: Backend container configuration
- `Dockerfile.frontend`: Frontend container configuration
- `.env`: Environment variables (not in version control)

### Development
- `requirements.txt`: Python dependencies
- `package.json`: Frontend dependencies and scripts
- `vite.config.ts`: Vite build configuration
