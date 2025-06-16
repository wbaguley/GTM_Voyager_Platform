"""
GTM Voyager Platform - Voice Integration Tool
Connects audio processing and Whisper API with CrewAI agents for voice-activated automation.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Import our audio processing system
from ...audio import transcribe_audio_file, WhisperClient, WhisperConfig

# Import CrewAI components
try:
    from crewai import Agent, Task, Crew
except ImportError:
    logging.error("CrewAI not installed. Please install with: pip install crewai")
    raise


class VoiceCommandType(Enum):
    """Types of voice commands supported."""
    DENTAL = "dental"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    GENERAL = "general"
    UNKNOWN = "unknown"


@dataclass
class VoiceCommand:
    """Container for processed voice commands."""
    original_text: str
    command_type: VoiceCommandType
    intent: str
    entities: Dict[str, Any]
    confidence: float
    agent_target: Optional[str] = None


class VoiceCommandParser:
    """Parses voice commands and extracts intent and entities."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        # Command patterns for different agent types
        self.command_patterns = {
            VoiceCommandType.DENTAL: [
                r"schedule.*appointment",
                r"book.*dental",
                r"patient.*appointment",
                r"dental.*cleaning",
                r"check.*schedule",
                r"cancel.*appointment"
            ],
            VoiceCommandType.ELECTRICAL: [
                r"electrical.*inspection",
                r"wire.*installation",
                r"electrical.*safety",
                r"circuit.*breaker",
                r"electrical.*maintenance",
                r"power.*system"
            ],
            VoiceCommandType.HVAC: [
                r"hvac.*maintenance",
                r"air.*conditioning",
                r"heating.*system",
                r"temperature.*control",
                r"hvac.*inspection",
                r"ventilation.*system"
            ]
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for voice command parsing."""
        logger = logging.getLogger('GTMVoyager.VoiceCommandParser')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def parse_command(self, text: str) -> VoiceCommand:
        """
        Parse voice command text and extract intent and entities.
        
        Args:
            text: Transcribed voice command text
            
        Returns:
            VoiceCommand object with parsed information
        """
        text_lower = text.lower()
        
        # Determine command type
        command_type = self._classify_command(text_lower)
        
        # Extract intent and entities
        intent = self._extract_intent(text_lower, command_type)
        entities = self._extract_entities(text_lower, command_type)
        
        # Calculate confidence based on pattern matching
        confidence = self._calculate_confidence(text_lower, command_type)
        
        # Determine target agent
        agent_target = self._get_target_agent(command_type)
        
        command = VoiceCommand(
            original_text=text,
            command_type=command_type,
            intent=intent,
            entities=entities,
            confidence=confidence,
            agent_target=agent_target
        )
        
        self.logger.info(f"Parsed command: {intent} -> {agent_target} (confidence: {confidence:.2f})")
        return command
    
    def _classify_command(self, text: str) -> VoiceCommandType:
        """Classify the command type based on keywords."""
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return command_type
        
        return VoiceCommandType.UNKNOWN
    
    def _extract_intent(self, text: str, command_type: VoiceCommandType) -> str:
        """Extract the main intent from the command."""
        # Common intent patterns
        if re.search(r"schedule|book|create", text):
            return "schedule"
        elif re.search(r"cancel|delete|remove", text):
            return "cancel"
        elif re.search(r"check|view|show|list", text):
            return "query"
        elif re.search(r"update|modify|change", text):
            return "update"
        elif re.search(r"generate|create|make", text):
            return "generate"
        else:
            return "general"
    
    def _extract_entities(self, text: str, command_type: VoiceCommandType) -> Dict[str, Any]:
        """Extract entities like names, dates, times from the command."""
        entities = {}
        
        # Extract time patterns
        time_pattern = r"(\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm)|\d{1,2}\s*o'clock)"
        time_match = re.search(time_pattern, text)
        if time_match:
            entities["time"] = time_match.group(1)
        
        # Extract date patterns
        date_pattern = r"(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}/\d{1,2})"
        date_match = re.search(date_pattern, text)
        if date_match:
            entities["date"] = date_match.group(1)
        
        # Extract names (simple pattern)
        name_pattern = r"for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
        name_match = re.search(name_pattern, text)
        if name_match:
            entities["name"] = name_match.group(1)
        
        return entities
    
    def _calculate_confidence(self, text: str, command_type: VoiceCommandType) -> float:
        """Calculate confidence score based on pattern matching."""
        if command_type == VoiceCommandType.UNKNOWN:
            return 0.1
        
        # Count matching patterns
        patterns = self.command_patterns.get(command_type, [])
        matches = sum(1 for pattern in patterns if re.search(pattern, text))
        
        # Base confidence + pattern matches
        confidence = 0.5 + (matches * 0.2)
        return min(confidence, 1.0)
    
    def _get_target_agent(self, command_type: VoiceCommandType) -> Optional[str]:
        """Get the target agent name for the command type."""
        agent_mapping = {
            VoiceCommandType.DENTAL: "dental_agent",
            VoiceCommandType.ELECTRICAL: "electrical_agent", 
            VoiceCommandType.HVAC: "hvac_agent",
            VoiceCommandType.GENERAL: "agent_orchestrator"
        }
        return agent_mapping.get(command_type)


class VoiceAgentIntegration:
    """Main class for integrating voice processing with CrewAI agents."""
    
    def __init__(self, whisper_config: Optional[WhisperConfig] = None):
        """Initialize voice-agent integration."""
        self.whisper_config = whisper_config or WhisperConfig()
        self.whisper_client = WhisperClient(self.whisper_config)
        self.command_parser = VoiceCommandParser()
        self.logger = self._setup_logger()
        
        # Agent registry (to be populated with actual agents)
        self.agents: Dict[str, Agent] = {}
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for voice-agent integration."""
        logger = logging.getLogger('GTMVoyager.VoiceAgentIntegration')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def register_agent(self, name: str, agent: Agent):
        """Register an agent for voice activation."""
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")
    
    async def process_voice_command(self, audio_path: str) -> Dict[str, Any]:
        """
        Process a voice command from audio file to agent execution.
        
        Args:
            audio_path: Path to audio file containing voice command
            
        Returns:
            Result from agent execution
        """
        try:
            # Step 1: Transcribe audio to text
            self.logger.info(f"Transcribing audio: {audio_path}")
            transcription_result = await transcribe_audio_file(
                audio_path, 
                api_key=self.whisper_config.api_key
            )
            
            if not transcription_result.text:
                return {"error": "No speech detected in audio"}
            
            # Step 2: Parse voice command
            self.logger.info(f"Parsing command: {transcription_result.text}")
            voice_command = self.command_parser.parse_command(transcription_result.text)
            
            # Step 3: Route to appropriate agent
            if voice_command.agent_target and voice_command.agent_target in self.agents:
                result = await self._execute_agent_task(voice_command)
                
                return {
                    "success": True,
                    "transcription": transcription_result.text,
                    "command": voice_command,
                    "result": result
                }
            else:
                return {
                    "error": f"No agent available for command type: {voice_command.command_type}",
                    "transcription": transcription_result.text,
                    "command": voice_command
                }
                
        except Exception as e:
            self.logger.error(f"Error processing voice command: {e}")
            return {"error": str(e)}
    
    async def _execute_agent_task(self, voice_command: VoiceCommand) -> Any:
        """Execute the voice command using the appropriate agent."""
        agent = self.agents[voice_command.agent_target]
        
        # Create a task based on the voice command
        task_description = self._create_task_description(voice_command)
        
        # For now, return a placeholder - this would integrate with your actual agent execution
        self.logger.info(f"Executing task with {voice_command.agent_target}: {task_description}")
        
        return {
            "agent": voice_command.agent_target,
            "task": task_description,
            "status": "completed",
            "message": f"Task executed by {voice_command.agent_target}"
        }
    
    def _create_task_description(self, voice_command: VoiceCommand) -> str:
        """Create a task description for the agent based on the voice command."""
        base_description = voice_command.original_text
        
        # Add context based on extracted entities
        if voice_command.entities:
            context_parts = []
            for key, value in voice_command.entities.items():
                context_parts.append(f"{key}: {value}")
            
            if context_parts:
                base_description += f" (Context: {', '.join(context_parts)})"
        
        return base_description


# Utility functions for easy integration
async def process_voice_file(audio_path: str, 
                           whisper_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Quick voice processing function."""
    config = WhisperConfig(api_key=whisper_api_key)
    integration = VoiceAgentIntegration(config)
    return await integration.process_voice_command(audio_path)


def create_voice_integration(whisper_api_key: Optional[str] = None) -> VoiceAgentIntegration:
    """Create a voice integration instance."""
    config = WhisperConfig(api_key=whisper_api_key)
    return VoiceAgentIntegration(config)
