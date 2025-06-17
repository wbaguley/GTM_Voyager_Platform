"""
GTM Voyager Platform - Base Business Agent
Base class for all specialized business agents in the platform.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from crewai import Agent


class AgentCapability(Enum):
    """Agent capabilities"""
    VOICE_PROCESSING = "voice_processing"
    TEXT_ANALYSIS = "text_analysis"
    APPOINTMENT_SCHEDULING = "appointment_scheduling"
    DOCUMENTATION = "documentation"
    COMPLIANCE = "compliance"
    BILLING = "billing"
    REPORTING = "reporting"


class BaseBusinessAgent(ABC):
    """
    Base class for all business agents in the GTM Voyager Platform.
    Provides common functionality and interface for specialized agents.
    """
    
    def __init__(self, agent_type: str, capabilities: List[AgentCapability]):
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.logger = logging.getLogger(f"{__name__}.{agent_type}")
        self.agent: Optional[Agent] = None
        self.tools: List = []
        self.is_initialized = False
        
        # Initialize the agent
        self._initialize_agent()
        
        self.logger.info(f"{agent_type} agent initialized with capabilities: {[c.value for c in capabilities]}")
    
    @abstractmethod
    def _initialize_agent(self):
        """Initialize the CrewAI agent with specific configuration"""
        pass
    
    @abstractmethod
    def _setup_tools(self) -> List:
        """Setup agent-specific tools"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities"""
        return [capability.value for capability in self.capabilities]
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has specific capability"""
        return capability in self.capabilities
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_type": self.agent_type,
            "capabilities": self.get_capabilities(),
            "is_initialized": self.is_initialized,
            "tools_count": len(self.tools),
            "role": self.agent.role if self.agent else None,
            "goal": self.agent.goal if self.agent else None
        }
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate input data has required fields"""
        try:
            for field in required_fields:
                if field not in input_data:
                    raise ValueError(f"Missing required field: {field}")
                if input_data[field] is None or input_data[field] == "":
                    raise ValueError(f"Field '{field}' cannot be empty")
            return True
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            raise
    
    def log_activity(self, activity: str, details: Optional[Dict[str, Any]] = None):
        """Log agent activity"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": self.agent_type,
            "activity": activity,
            "details": details or {}
        }
        self.logger.info(f"Activity: {activity}", extra=log_entry)
    
    @abstractmethod
    def process_voice_input(self, audio_data: bytes, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process voice input and return structured response"""
        pass
    
    @abstractmethod
    def process_text_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process text input and return structured response"""
        pass
    
    @abstractmethod
    def generate_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response based on input data"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_type": self.agent_type,
            "is_initialized": self.is_initialized,
            "capabilities": self.get_capabilities(),
            "last_activity": datetime.now().isoformat(),
            "status": "active" if self.is_initialized else "inactive"
        }

