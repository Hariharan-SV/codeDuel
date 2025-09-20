import uuid
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models import User
from database import FirestoreDB

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: FirestoreDB):
        self.db = db
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.security = HTTPBearer()
        
        # Warn if using default secret key
        if self.secret_key == "your-secret-key-change-in-production":
            logger.warning("Using default JWT secret key. Please set JWT_SECRET_KEY environment variable for production.")
    
    async def create_guest_user(self) -> User:
        """Create a new guest user"""
        user_id = str(uuid.uuid4())
        username = f"Guest_{user_id[:8]}"
        
        user = User(
            id=user_id,
            username=username,
            rating=1200
        )
        
        # Save to database
        user_data = user.dict()
        user_data["created_at"] = user.created_at.isoformat()
        user_data["updated_at"] = user.updated_at.isoformat()
        
        success = await self.db.create_document("users", user_id, user_data)
        if not success:
            raise Exception("Failed to create user in database")
        
        return user
    
    def create_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token for user"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
            
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token for user"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database"""
        user_data = await self.db.get_document("users", user_id)
        if not user_data:
            return None
        
        # Convert datetime strings back to datetime objects
        if "created_at" in user_data:
            user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
        if "updated_at" in user_data:
            user_data["updated_at"] = datetime.fromisoformat(user_data["updated_at"])
        
        return User(**user_data)
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Get current user from JWT token"""
        token = credentials.credentials
        user_id = self.verify_token(token)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
