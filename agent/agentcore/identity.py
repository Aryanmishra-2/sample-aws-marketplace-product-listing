"""
Agentcore Identity - User and session management
Manages user identities and session lifecycle
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Session:
    """Represents a user session"""
    session_id: str
    user_id: str
    created_at: datetime
    last_accessed: datetime
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def update_access_time(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "attributes": self.attributes,
            "is_active": self.is_active
        }


class IdentityManager:
    """
    Agentcore Identity Manager
    
    Responsibilities:
    - Create and manage user sessions
    - Track session lifecycle
    - Store session metadata
    - Support multi-user scenarios
    """
    
    def __init__(self):
        """Initialize IdentityManager"""
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    def create_session(
        self,
        user_id: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session for a user
        
        Args:
            user_id: Unique user identifier
            attributes: Optional session metadata
            
        Returns:
            New Session object
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_accessed=now,
            attributes=attributes or {}
        )
        
        # Store session
        self.sessions[session_id] = session
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object or None
        """
        session = self.sessions.get(session_id)
        if session and session.is_active:
            session.update_access_time()
        return session
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was ended, False otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            return True
        return False
    
    def list_sessions(self, user_id: str, active_only: bool = True) -> List[Session]:
        """
        List all sessions for a user
        
        Args:
            user_id: User identifier
            active_only: Only return active sessions
            
        Returns:
            List of Session objects
        """
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for sid in session_ids:
            session = self.sessions.get(sid)
            if session:
                if not active_only or session.is_active:
                    sessions.append(session)
        
        return sessions
    
    def update_session_attributes(
        self,
        session_id: str,
        attributes: Dict[str, Any]
    ) -> bool:
        """
        Update session attributes
        
        Args:
            session_id: Session identifier
            attributes: Attributes to update
            
        Returns:
            True if updated, False otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            session.attributes.update(attributes)
            session.update_access_time()
            return True
        return False
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """
        Clean up old inactive sessions
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        now = datetime.now()
        to_remove = []
        
        for session_id, session in self.sessions.items():
            age_hours = (now - session.last_accessed).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            session = self.sessions.pop(session_id, None)
            if session:
                user_sessions = self.user_sessions.get(session.user_id, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
