"""
Agentcore Memory - Conversation persistence
Stores and retrieves conversation history across sessions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import boto3
from abc import ABC, abstractmethod


class MemoryBackend(ABC):
    """Abstract base class for memory storage backends"""
    
    @abstractmethod
    def save(self, key: str, data: Any):
        """Save data to storage"""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load data from storage"""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """Delete data from storage"""
        pass


class DynamoDBBackend(MemoryBackend):
    """DynamoDB storage backend for conversation memory"""
    
    def __init__(self, table_name: str, region: str = "us-east-1"):
        """
        Initialize DynamoDB backend
        
        Args:
            table_name: DynamoDB table name
            region: AWS region
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def save(self, key: str, data: Any):
        """Save data to DynamoDB"""
        self.table.put_item(
            Item={
                'session_id': key,
                'data': json.dumps(data),
                'updated_at': datetime.now().isoformat()
            }
        )
    
    def load(self, key: str) -> Optional[Any]:
        """Load data from DynamoDB"""
        try:
            response = self.table.get_item(Key={'session_id': key})
            if 'Item' in response:
                return json.loads(response['Item']['data'])
        except Exception:
            pass
        return None
    
    def delete(self, key: str):
        """Delete data from DynamoDB"""
        self.table.delete_item(Key={'session_id': key})


class LocalBackend(MemoryBackend):
    """In-memory storage backend (for development/testing)"""
    
    def __init__(self):
        """Initialize local backend"""
        self.storage: Dict[str, Any] = {}
    
    def save(self, key: str, data: Any):
        """Save data to memory"""
        self.storage[key] = data
    
    def load(self, key: str) -> Optional[Any]:
        """Load data from memory"""
        return self.storage.get(key)
    
    def delete(self, key: str):
        """Delete data from memory"""
        self.storage.pop(key, None)


class MemoryStore:
    """
    Memory Store manages conversation persistence
    
    Supports multiple backends:
    - DynamoDB (production)
    - Local (development/testing)
    - S3 (archival)
    """
    
    def __init__(self, backend: str = "local", **kwargs):
        """
        Initialize MemoryStore
        
        Args:
            backend: Storage backend type ("dynamodb", "local")
            **kwargs: Backend-specific configuration
        """
        if backend == "dynamodb":
            self.backend = DynamoDBBackend(
                table_name=kwargs.get('table_name', 'agent-memory'),
                region=kwargs.get('region', 'us-east-1')
            )
        else:
            self.backend = LocalBackend()
    
    def save(self, key: str, data: Any):
        """Save data to storage"""
        self.backend.save(key, data)
    
    def load(self, key: str) -> Optional[Any]:
        """Load data from storage"""
        return self.backend.load(key)
    
    def delete(self, key: str):
        """Delete data from storage"""
        self.backend.delete(key)


class ConversationMemory:
    """
    Conversation Memory manages chat history
    
    Responsibilities:
    - Store conversation messages
    - Retrieve conversation history
    - Support session-based isolation
    - Handle message metadata
    """
    
    def __init__(self, memory_store: MemoryStore):
        """
        Initialize ConversationMemory
        
        Args:
            memory_store: MemoryStore instance for persistence
        """
        self.memory_store = memory_store
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to conversation history
        
        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional message metadata (stored separately, not in Bedrock format)
        """
        history = self.get_history(session_id)
        
        # Store in Bedrock-compatible format (only role and content)
        message = {
            "role": role,
            "content": [{"text": content}]
        }
        
        history.append(message)
        self.memory_store.save(session_id, history)
        
        # Store metadata separately if needed (not sent to Bedrock)
        if metadata:
            metadata_key = f"{session_id}_metadata"
            all_metadata = self.memory_store.load(metadata_key) or []
            all_metadata.append({
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            })
            self.memory_store.save(metadata_key, all_metadata)
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation messages
        """
        history = self.memory_store.load(session_id)
        return history if history else []
    
    def clear_history(self, session_id: str):
        """
        Clear conversation history for a session
        
        Args:
            session_id: Session identifier
        """
        self.memory_store.delete(session_id)
    
    def export_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Export conversation history
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete conversation history with metadata
        """
        return self.get_history(session_id)
    
    def get_recent_messages(
        self,
        session_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from conversation
        
        Args:
            session_id: Session identifier
            count: Number of recent messages to retrieve
            
        Returns:
            List of recent messages
        """
        history = self.get_history(session_id)
        return history[-count:] if len(history) > count else history
