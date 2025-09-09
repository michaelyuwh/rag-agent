"""
Advanced session management for RAG Agent.
Handles multi-user sessions, session isolation, and user authentication.
"""

import uuid
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class User:
    """User information."""
    id: str
    username: str
    email: Optional[str]
    created_at: datetime
    last_active: datetime
    preferences: Dict[str, Any]
    is_active: bool = True

@dataclass
class UserSession:
    """Enhanced user session with isolation."""
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    data: Dict[str, Any]
    expires_at: datetime
    is_active: bool = True

class SessionManager:
    """Advanced session management with multi-user support."""
    
    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"
        
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.active_sessions: Dict[str, str] = {}  # session_id -> user_id
        
        self._load_data()
    
    def _load_data(self):
        """Load users and sessions from disk."""
        try:
            # Load users
            if self.users_file.exists():
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    self.users = {
                        uid: User(
                            id=data['id'],
                            username=data['username'],
                            email=data.get('email'),
                            created_at=datetime.fromisoformat(data['created_at']),
                            last_active=datetime.fromisoformat(data['last_active']),
                            preferences=data.get('preferences', {}),
                            is_active=data.get('is_active', True)
                        )
                        for uid, data in users_data.items()
                    }
            
            # Load sessions
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                    self.sessions = {
                        sid: UserSession(
                            session_id=data['session_id'],
                            user_id=data['user_id'],
                            created_at=datetime.fromisoformat(data['created_at']),
                            last_active=datetime.fromisoformat(data['last_active']),
                            ip_address=data.get('ip_address'),
                            user_agent=data.get('user_agent'),
                            data=data.get('data', {}),
                            expires_at=datetime.fromisoformat(data['expires_at']),
                            is_active=data.get('is_active', True)
                        )
                        for sid, data in sessions_data.items()
                    }
            
            # Update active sessions
            current_time = datetime.now()
            for session_id, session in self.sessions.items():
                if session.is_active and session.expires_at > current_time:
                    self.active_sessions[session_id] = session.user_id
            
            logger.info(f"Loaded {len(self.users)} users and {len(self.sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Error loading session data: {e}")
            self.users = {}
            self.sessions = {}
            self.active_sessions = {}
    
    def _save_data(self):
        """Save users and sessions to disk."""
        try:
            # Save users
            users_data = {
                uid: asdict(user) for uid, user in self.users.items()
            }
            # Convert datetime objects to ISO strings
            for uid, data in users_data.items():
                data['created_at'] = data['created_at'].isoformat() if isinstance(data['created_at'], datetime) else data['created_at']
                data['last_active'] = data['last_active'].isoformat() if isinstance(data['last_active'], datetime) else data['last_active']
            
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
            
            # Save sessions
            sessions_data = {
                sid: asdict(session) for sid, session in self.sessions.items()
            }
            # Convert datetime objects to ISO strings
            for sid, data in sessions_data.items():
                data['created_at'] = data['created_at'].isoformat() if isinstance(data['created_at'], datetime) else data['created_at']
                data['last_active'] = data['last_active'].isoformat() if isinstance(data['last_active'], datetime) else data['last_active']
                data['expires_at'] = data['expires_at'].isoformat() if isinstance(data['expires_at'], datetime) else data['expires_at']
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            
            logger.debug("Session data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
    
    def create_user(self, username: str, email: Optional[str] = None, preferences: Optional[Dict] = None) -> str:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            created_at=current_time,
            last_active=current_time,
            preferences=preferences or {},
            is_active=True
        )
        
        self.users[user_id] = user
        self._save_data()
        
        logger.info(f"Created user: {username} (ID: {user_id})")
        return user_id
    
    def get_or_create_anonymous_user(self) -> str:
        """Get or create an anonymous user for single-user mode."""
        anonymous_username = "anonymous"
        
        # Find existing anonymous user
        for user_id, user in self.users.items():
            if user.username == anonymous_username:
                return user_id
        
        # Create new anonymous user
        return self.create_user(anonymous_username, preferences={"theme": "light"})
    
    def create_session(self, user_id: str, duration_hours: int = 24, ip_address: str = None, user_agent: str = None) -> str:
        """Create a new session for a user."""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        session_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=current_time,
            last_active=current_time,
            ip_address=ip_address,
            user_agent=user_agent,
            data={},
            expires_at=current_time + timedelta(hours=duration_hours),
            is_active=True
        )
        
        self.sessions[session_id] = session
        self.active_sessions[session_id] = user_id
        
        # Update user last active
        self.users[user_id].last_active = current_time
        
        self._save_data()
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID if valid and active."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        current_time = datetime.now()
        
        # Check if session is expired
        if not session.is_active or session.expires_at <= current_time:
            self.end_session(session_id)
            return None
        
        return session
    
    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.expires_at = datetime.now() + timedelta(hours=hours)
        session.last_active = datetime.now()
        
        # Update user last active
        if session.user_id in self.users:
            self.users[session.user_id].last_active = datetime.now()
        
        self._save_data()
        return True
    
    def end_session(self, session_id: str) -> bool:
        """End a session."""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            self._save_data()
            logger.info(f"Ended session {session_id}")
            return True
        return False
    
    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user."""
        current_time = datetime.now()
        return [
            session for session in self.sessions.values()
            if session.user_id == user_id and session.is_active and session.expires_at > current_time
        ]
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.expires_at <= current_time or not session.is_active:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.end_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_session_data(self, session_id: str, key: str = None) -> Any:
        """Get data from session."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        if key:
            return session.data.get(key)
        return session.data
    
    def set_session_data(self, session_id: str, key: str, value: Any) -> bool:
        """Set data in session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.data[key] = value
        session.last_active = datetime.now()
        self._save_data()
        return True
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        current_time = datetime.now()
        active_sessions = len(self.active_sessions)
        total_sessions = len(self.sessions)
        total_users = len(self.users)
        active_users = len(set(self.active_sessions.values()))
        
        # Recent activity (last 24 hours)
        recent_cutoff = current_time - timedelta(hours=24)
        recent_sessions = sum(
            1 for session in self.sessions.values()
            if session.last_active > recent_cutoff
        )
        
        return {
            "active_sessions": active_sessions,
            "total_sessions": total_sessions,
            "total_users": total_users,
            "active_users": active_users,
            "recent_sessions_24h": recent_sessions,
            "last_cleanup": current_time.isoformat()
        }

class SessionIsolation:
    """Provides session isolation for data and operations."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.session_data_dirs: Dict[str, Path] = {}
    
    def get_session_data_dir(self, session_id: str) -> Optional[Path]:
        """Get isolated data directory for session."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        if session_id not in self.session_data_dirs:
            # Create session-specific data directory
            session_dir = Path(f"data/sessions/{session.user_id}/{session_id}")
            session_dir.mkdir(parents=True, exist_ok=True)
            self.session_data_dirs[session_id] = session_dir
        
        return self.session_data_dirs[session_id]
    
    def get_session_vector_store_path(self, session_id: str) -> Optional[str]:
        """Get isolated vector store path for session."""
        session_dir = self.get_session_data_dir(session_id)
        if not session_dir:
            return None
        
        return str(session_dir / "vector_store")
    
    def get_session_chat_history_path(self, session_id: str) -> Optional[str]:
        """Get isolated chat history path for session."""
        session_dir = self.get_session_data_dir(session_id)
        if not session_dir:
            return None
        
        return str(session_dir / "chat_history")
    
    def cleanup_session_data(self, session_id: str) -> bool:
        """Clean up session data when session ends."""
        try:
            if session_id in self.session_data_dirs:
                session_dir = self.session_data_dirs[session_id]
                if session_dir.exists():
                    import shutil
                    shutil.rmtree(session_dir)
                del self.session_data_dirs[session_id]
                logger.info(f"Cleaned up data for session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up session data: {e}")
        
        return False

# Global session manager instance
session_manager = SessionManager()
session_isolation = SessionIsolation(session_manager)
