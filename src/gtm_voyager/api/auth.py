from typing import Optional, Dict, Any
import secrets

class AuthManager:
    """Authentication manager for GTM Voyager Platform."""
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.active_sessions = {}
        self.api_keys = {}
    
    def create_session(self, user_id: str) -> str:
        """Create a new user session."""
        session_token = secrets.token_urlsafe(32)
        self.active_sessions[session_token] = {
            'user_id': user_id,
            'created_at': 'now'
        }
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate a session token."""
        return self.active_sessions.get(session_token)
    
    def create_api_key(self, user_id: str) -> str:
        """Create a new API key for a user."""
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            'user_id': user_id,
            'created_at': 'now'
        }
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key."""
        return self.api_keys.get(api_key)
    
    def revoke_session(self, session_token: str) -> bool:
        """Revoke a session token."""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            return True
        return False
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            return True
        return False
