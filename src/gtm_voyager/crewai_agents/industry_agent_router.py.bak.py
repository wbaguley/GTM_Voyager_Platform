"""
GTM Voyager Platform - Multi-Industry Agent Router
Intelligent routing system for directing voice commands to appropriate industry agents.
"""

import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Import your agents
from .dental_agent import DentalAgent
from .prosthodontics_agent import ProsthodonticsAgent
# Future imports:
# from .hvac_agent import HVACAgent
# from .electrical_agent import ElectricalAgent
# from .plumbing_agent import PlumbingAgent


class IndustryType(Enum):
    """Supported industry types"""
    DENTAL_GENERAL = "dental_general"
    DENTAL_PROSTHODONTICS = "dental_prosthodontics"
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    AUTO_REPAIR = "auto_repair"
    GENERAL = "general"


@dataclass
class UserProfile:
    """User profile with industry preferences"""
    user_id: str
    name: str
    primary_industry: IndustryType
    secondary_industries: List[IndustryType]
    default_agent: str
    voice_preferences: Dict[str, Any]
    current_mode: Optional[IndustryType] = None


@dataclass
class RoutingResult:
    """Result of agent routing decision"""
    selected_agent: str
    industry_type: IndustryType
    confidence_score: float
    routing_reason: str
    context_detected: List[str]


class IndustryAgentRouter:
    """
    Intelligent router for directing voice commands to appropriate industry agents.
    Uses combination of user profile, voice context detection, and explicit commands.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('IndustryAgentRouter')
        self._setup_logging()
        
        # Initialize available agents
        self.agents = {
            IndustryType.DENTAL_GENERAL: DentalAgent(),
            IndustryType.DENTAL_PROSTHODONTICS: ProsthodonticsAgent(),
            # Future agents will be added here
        }
        
        # User profiles cache
        self.user_profiles = {}
        
        # Routing history for analytics
        self.routing_history = []
        
        # Industry context keywords
        self.industry_keywords = {
            IndustryType.DENTAL_GENERAL: [
                "patient", "tooth", "teeth", "dental", "cleaning", "cavity", "filling",
                "exam", "checkup", "x-ray", "fluoride", "gums", "gingivitis", "extraction",
                "appointment", "dental office", "dentist", "hygienist"
            ],
            
            IndustryType.DENTAL_PROSTHODONTICS: [
                "crown", "bridge", "implant", "veneer", "denture", "prosthodontics",
                "restoration", "porcelain", "zirconia", "cosmetic", "esthetics",
                "reconstruction", "lab work", "impression", "temporary", "permanent"
            ],
            
            IndustryType.HVAC: [
                "furnace", "air conditioning", "hvac", "heating", "cooling", "thermostat",
                "ductwork", "filter", "maintenance", "repair", "installation", "unit",
                "temperature", "system", "condenser", "evaporator"
            ],
            
            IndustryType.ELECTRICAL: [
                "electrical", "wiring", "outlet", "switch", "breaker", "panel", "voltage",
                "circuit", "installation", "repair", "lighting", "electrical system",
                "power", "electricity", "electrician", "code", "safety"
            ],
            
            IndustryType.PLUMBING: [
                "plumbing", "pipe", "leak", "drain", "toilet", "sink", "faucet", "water",
                "sewer", "plumber", "installation", "repair", "fixture", "pressure",
                "flow", "blockage", "clog"
            ]
        }
        
        # Explicit mode switching commands
        self.mode_switch_patterns = {
            IndustryType.DENTAL_GENERAL: [
                r"switch to dental mode",
                r"dental mode",
                r"general dental",
                r"dental practice mode"
            ],
            
            IndustryType.DENTAL_PROSTHODONTICS: [
                r"switch to prosthodontics",
                r"prosthodontics mode", 
                r"prosthetic mode",
                r"cosmetic dental mode"
            ],
            
            IndustryType.HVAC: [
                r"switch to hvac",
                r"hvac mode",
                r"heating and cooling mode"
            ],
            
            IndustryType.ELECTRICAL: [
                r"switch to electrical",
                r"electrical mode",
                r"electrician mode"
            ],
            
            IndustryType.PLUMBING: [
                r"switch to plumbing",
                r"plumbing mode",
                r"plumber mode"
            ]
        }
    
    def _setup_logging(self):
        """Configure logging for the router"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format
        )
    
    def get_agent(self, industry_type: IndustryType) -> Optional[Any]:
        """
        Get agent instance for a specific industry type
        
        Args:
            industry_type: The industry type enum
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(industry_type)
    
    def route_voice_command(self, voice_command: str, user_profile: UserProfile) -> RoutingResult:
        """
        Main routing method - determines which agent should handle the voice command.
        Priority: Explicit switching > Voice context > User profile default
        """
        voice_command_lower = voice_command.lower()
        
        # 1. Check for explicit mode switching commands
        explicit_switch = self._check_explicit_mode_switch(voice_command_lower)
        if explicit_switch:
            user_profile.current_mode = explicit_switch
            return RoutingResult(
                selected_agent=explicit_switch.value,
                industry_type=explicit_switch,
                confidence_score=1.0,
                routing_reason="Explicit mode switch command",
                context_detected=[f"Mode switch to {explicit_switch.value}"]
            )
        
        # 2. Analyze voice context for industry keywords
        context_analysis = self._analyze_voice_context(voice_command_lower)
        if context_analysis and context_analysis.confidence_score > 0.7:
            return context_analysis
        
        # 3. Use current mode if set
        if user_profile.current_mode and user_profile.current_mode in self.agents:
            return RoutingResult(
                selected_agent=user_profile.current_mode.value,
                industry_type=user_profile.current_mode,
                confidence_score=0.6,
                routing_reason="Current user mode",
                context_detected=["Using current mode setting"]
            )
        
        # 4. Fall back to user profile default
        return RoutingResult(
            selected_agent=user_profile.default_agent,
            industry_type=user_profile.primary_industry,
            confidence_score=0.5,
            routing_reason="User profile default",
            context_detected=["No specific context detected"]
        )
    
    def _check_explicit_mode_switch(self, voice_command: str) -> Optional[IndustryType]:
        """Check if voice command contains explicit mode switching"""
        for industry_type, patterns in self.mode_switch_patterns.items():
            for pattern in patterns:
                if re.search(pattern, voice_command, re.IGNORECASE):
                    self.logger.info(f"Explicit mode switch detected: {industry_type.value}")
                    return industry_type
        return None
    
    def _analyze_voice_context(self, voice_command: str) -> Optional[RoutingResult]:
        """Analyze voice command for industry-specific context"""
        industry_scores = {}
        detected_keywords = {}
        
        # Score each industry based on keyword matches
        for industry_type, keywords in self.industry_keywords.items():
            score = 0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in voice_command:
                    score += 1
                    found_keywords.append(keyword)
            
            if score > 0:
                # Normalize score by number of keywords
                normalized_score = min(score / len(keywords) * 3, 1.0)  # Cap at 1.0
                industry_scores[industry_type] = normalized_score
                detected_keywords[industry_type] = found_keywords
        
        # Return highest scoring industry if above threshold
        if industry_scores:
            best_industry = max(industry_scores.items(), key=lambda x: x[1])
            industry_type, confidence = best_industry
            
            if confidence > 0.3:  # Minimum confidence threshold
                return RoutingResult(
                    selected_agent=industry_type.value,
                    industry_type=industry_type,
                    confidence_score=confidence,
                    routing_reason="Voice context analysis",
                    context_detected=detected_keywords[industry_type]
                )
        
        return None
    
    # ---- Additional Methods for Agent Management ----
    
    def register_agent(self, industry_type: IndustryType, agent_instance: Any) -> bool:
        """
        Register a new agent for a specific industry type
        
        Args:
            industry_type: The industry type enum
            agent_instance: Instance of the agent class
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        if industry_type in self.agents:
            self.logger.warning(f"Agent for {industry_type.value} already registered, overwriting")
        
        try:
            self.agents[industry_type] = agent_instance
            self.logger.info(f"Successfully registered agent for {industry_type.value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register agent for {industry_type.value}: {str(e)}")
            return False
    
    def list_available_agents(self) -> List[str]:
        """
        List all available agent types
        
        Returns:
            List of available agent industry types as strings
        """
        return [industry_type.value for industry_type in self.agents.keys()]
    
    # ---- User Profile Management ----
    
    def create_user_profile(self, 
                           user_id: str, 
                           name: str, 
                           primary_industry: IndustryType,
                           default_agent: str = None,
                           secondary_industries: List[IndustryType] = None,
                           voice_preferences: Dict[str, Any] = None) -> UserProfile:
        """
        Create a new user profile
        
        Args:
            user_id: Unique user identifier
            name: User's name
            primary_industry: User's primary industry
            default_agent: Default agent type (defaults to primary_industry value)
            secondary_industries: List of secondary industries
            voice_preferences: Voice settings preferences
            
        Returns:
            UserProfile: Created user profile
        """
        if default_agent is None:
            default_agent = primary_industry.value
            
        if secondary_industries is None:
            secondary_industries = []
            
        if voice_preferences is None:
            voice_preferences = {
                "voice_speed": 1.0,
                "voice_pitch": 1.0,
                "preferred_voice": "default"
            }
            
        profile = UserProfile(
            user_id=user_id,
            name=name,
            primary_industry=primary_industry,
            secondary_industries=secondary_industries,
            default_agent=default_agent,
            voice_preferences=voice_preferences
        )
        
        # Cache the profile
        self.user_profiles[user_id] = profile
        self.logger.info(f"Created user profile for {name} (ID: {user_id})")
        
        return profile
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserProfile or None if not found
        """
        profile = self.user_profiles.get(user_id)
        if not profile:
            self.logger.warning(f"User profile not found for ID: {user_id}")
        return profile
    
    def update_user_profile(self, user_id: str, **kwargs) -> Optional[UserProfile]:
        """
        Update user profile attributes
        
        Args:
            user_id: Unique user identifier
            **kwargs: Attributes to update
            
        Returns:
            Updated UserProfile or None if not found
        """
        profile = self.get_user_profile(user_id)
        if not profile:
            return None
            
        # Update provided attributes
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
                
        self.logger.info(f"Updated user profile for {profile.name} (ID: {user_id})")
        return profile
    
    def save_user_profiles(self, file_path: str) -> bool:
        """
        Save all user profiles to JSON file
        
        Args:
            file_path: Path to save JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert profiles to serializable format
            serializable_profiles = {}
            for user_id, profile in self.user_profiles.items():
                profile_dict = asdict(profile)
                # Convert enum values to strings
                profile_dict['primary_industry'] = profile.primary_industry.value
                profile_dict['secondary_industries'] = [ind.value for ind in profile.secondary_industries]
                if profile.current_mode:
                    profile_dict['current_mode'] = profile.current_mode.value
                serializable_profiles[user_id] = profile_dict
                
            with open(file_path, 'w') as f:
                json.dump(serializable_profiles, f, indent=2)
                
            self.logger.info(f"Saved {len(serializable_profiles)} user profiles to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save user profiles: {str(e)}")
            return False
    
    def load_user_profiles(self, file_path: str) -> bool:
        """
        Load user profiles from JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                serialized_profiles = json.load(f)
                
            # Convert serialized data back to UserProfile objects
            for user_id, profile_dict in serialized_profiles.items():
                # Convert string values back to enums
                primary_industry = IndustryType(profile_dict['primary_industry'])
                secondary_industries = [IndustryType(ind) for ind in profile_dict['secondary_industries']]
                current_mode = None
                if profile_dict.get('current_mode'):
                    current_mode = IndustryType(profile_dict['current_mode'])
                    
                profile = UserProfile(
                    user_id=profile_dict['user_id'],
                    name=profile_dict['name'],
                    primary_industry=primary_industry,
                    secondary_industries=secondary_industries,
                    default_agent=profile_dict['default_agent'],
                    voice_preferences=profile_dict['voice_preferences'],
                    current_mode=current_mode
                )
                self.user_profiles[user_id] = profile
                
            self.logger.info(f"Loaded {len(self.user_profiles)} user profiles from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load user profiles: {str(e)}")
            return False
    
    # ---- Routing Analytics ----
    
    def log_routing_decision(self, user_id: str, voice_command: str, result: RoutingResult) -> None:
        """
        Log routing decision for analytics
        
        Args:
            user_id: User ID
            voice_command: Original voice command
            result: Routing result
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "voice_command": voice_command,
            "selected_agent": result.selected_agent,
            "industry_type": result.industry_type.value,
            "confidence_score": result.confidence_score,
            "routing_reason": result.routing_reason,
            "context_detected": result.context_detected
        }
        
        self.routing_history.append(log_entry)
        self.logger.info(f"Logged routing decision: {result.selected_agent} ({result.confidence_score:.2f})")
    
    def get_routing_analytics(self, user_id: Optional[str] = None, 
                             time_period: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Get routing analytics for specified filters
        
        Args:
            user_id: Filter by user ID (optional)
            time_period: Filter by time period (start, end) (optional)
            
        Returns:
            Dict with analytics data
        """
        # Filter history based on parameters
        filtered_history = self.routing_history
        
        if user_id:
            filtered_history = [entry for entry in filtered_history if entry["user_id"] == user_id]
            
        if time_period:
            start, end = time_period
            filtered_history = [
                entry for entry in filtered_history 
                if start <= datetime.fromisoformat(entry["timestamp"]) <= end
            ]
            
        # Calculate analytics
        total_commands = len(filtered_history)
        if total_commands == 0:
            return {"error": "No routing data found for specified filters"}
            
        industry_distribution = {}
        confidence_scores = []
        routing_reasons = {}
        
        for entry in filtered_history:
            # Industry distribution
            industry = entry["industry_type"]
            industry_distribution[industry] = industry_distribution.get(industry, 0) + 1
            
            # Confidence scores
            confidence_scores.append(entry["confidence_score"])
            
            # Routing reasons
            reason = entry["routing_reason"]
            routing_reasons[reason] = routing_reasons.get(reason, 0) + 1
            
        # Calculate percentages
        for industry, count in industry_distribution.items():
            industry_distribution[industry] = {
                "count": count,
                "percentage": (count / total_commands) * 100
            }
            
        for reason, count in routing_reasons.items():
            routing_reasons[reason] = {
                "count": count,
                "percentage": (count / total_commands) * 100
            }
            
        # Average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
        return {
            "total_commands": total_commands,
            "industry_distribution": industry_distribution,
            "routing_reasons": routing_reasons,
            "average_confidence": avg_confidence,
            "time_period": {
                "start": time_period[0].isoformat() if time_period else None,
                "end": time_period[1].isoformat() if time_period else None
            }
        }
    
    # ---- Voice Command Processing ----
    
    def process_voice_command(self, user_id: str, voice_command: str) -> Dict[str, Any]:
        """
        Process voice command and route to appropriate agent
        
        Args:
            user_id: User ID
            voice_command: Voice command text
            
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        # Get user profile
        user_profile = self.get_user_profile(user_id)
        if not user_profile:
            return {
                "status": "error",
                "message": f"User profile not found for ID: {user_id}",
                "timestamp": datetime.now().isoformat()
            }
            
        # Route command
        routing_result = self.route_voice_command(voice_command, user_profile)
        
        # Log routing decision
        self.log_routing_decision(user_id, voice_command, routing_result)
        
        # Get appropriate agent
        agent = self.get_agent(routing_result.industry_type)
        if not agent:
            return {
                "status": "error",
                "message": f"Agent not found for industry: {routing_result.industry_type.value}",
                "timestamp": datetime.now().isoformat()
            }
            
        # Process with selected agent (implementation depends on agent interface)
        try:
            # This is a placeholder - actual implementation depends on agent interface
            # agent_response = agent.process_command(voice_command)
            agent_response = f"Agent would process: {voice_command}"
            
            processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "user_id": user_id,
                "voice_command": voice_command,
                "selected_agent": routing_result.selected_agent,
                "industry_type": routing_result.industry_type.value,
                "confidence_score": routing_result.confidence_score,
                "routing_reason": routing_result.routing_reason,
                "context_detected": routing_result.context_detected,
                "agent_response": agent_response,
                "processing_time_ms": round(processing_time * 1000, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error processing command with agent: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing command: {str(e)}",
                "selected_agent": routing_result.selected_agent,
                "timestamp": datetime.now().isoformat()
            }
    
    # ---- MCP Integration ----
    
    def register_with_mcp(self, mcp_server_url: str) -> bool:
        """
        Register router capabilities with MCP server
        
        Args:
            mcp_server_url: URL of MCP server
            
        Returns:
            bool: True if registration successful
        """
        # This is a placeholder for MCP integration
        # Actual implementation would register tools and capabilities with MCP server
        
        self.logger.info(f"Registered router capabilities with MCP server at {mcp_server_url}")
        return True
    
    def get_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get MCP-compatible tool definitions for this router
        
        Returns:
            List of tool definitions in MCP format
        """
        # This is a placeholder for MCP integration
        # Actual implementation would return tool definitions in MCP format
        
        return [
            {
                "name": "route_voice_command",
                "description": "Route voice command to appropriate industry agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "voice_command": {
                            "type": "string",
                            "description": "Voice command text"
                        }
                    },
                    "required": ["user_id", "voice_command"]
                }
            },
            {
                "name": "switch_industry_mode",
                "description": "Explicitly switch to a specific industry mode",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "industry_type": {
                            "type": "string",
                            "description": "Industry type to switch to",
                            "enum": [ind.value for ind in IndustryType]
                        }
                    },
                    "required": ["user_id", "industry_type"]
                }
            }
        ]
