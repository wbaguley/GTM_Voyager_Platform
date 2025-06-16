"""
GTM Voyager Platform - Agent Configuration
Configuration for CrewAI agents with voice integration capabilities.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass

# Import CrewAI components
try:
    from crewai import Agent, Task, Crew
    from crewai.tools import BaseTool
except ImportError:
    print("CrewAI not installed. Please install with: pip install crewai")
    raise


@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    name: str
    role: str
    goal: str
    backstory: str
    voice_keywords: List[str]
    tools: List[str] = None
    verbose: bool = True
    allow_delegation: bool = False


class GTMVoyagerAgentConfigs:
    """Centralized configuration for all GTM Voyager agents."""
    
    @staticmethod
    def get_dental_agent_config() -> AgentConfig:
        """Configuration for dental practice agent."""
        return AgentConfig(
            name="dental_agent",
            role="Dental Practice Automation Specialist",
            goal="Manage dental practice operations including appointment scheduling, patient communication, and treatment planning through voice commands",
            backstory="""You are an expert dental practice management specialist with years of experience 
            in patient care coordination, appointment scheduling, and dental workflow optimization. 
            You understand dental terminology, treatment procedures, and practice management best practices. 
            You can process voice commands to schedule appointments, manage patient records, and coordinate 
            dental treatments efficiently.""",
            voice_keywords=[
                "dental", "appointment", "patient", "cleaning", "checkup", "dentist", 
                "tooth", "teeth", "oral", "hygiene", "schedule", "book", "cancel"
            ],
            tools=["calendar_tool", "patient_database", "voice_integration"],
            verbose=True,
            allow_delegation=True
        )
    
    @staticmethod
    def get_electrical_agent_config() -> AgentConfig:
        """Configuration for electrical services agent."""
        return AgentConfig(
            name="electrical_agent", 
            role="Electrical Services Automation Specialist",
            goal="Manage electrical service operations including inspections, installations, maintenance scheduling, and safety compliance through voice commands",
            backstory="""You are a certified electrical services specialist with extensive experience 
            in electrical systems, safety protocols, and service management. You understand electrical 
            codes, installation procedures, and maintenance requirements. You can process voice commands 
            to schedule electrical work, create inspection checklists, and manage electrical service 
            workflows efficiently.""",
            voice_keywords=[
                "electrical", "wire", "circuit", "breaker", "power", "voltage", 
                "installation", "inspection", "safety", "maintenance", "electrical work"
            ],
            tools=["scheduling_tool", "inspection_checklist", "voice_integration"],
            verbose=True,
            allow_delegation=True
        )
    
    @staticmethod
    def get_hvac_agent_config() -> AgentConfig:
        """Configuration for HVAC services agent."""
        return AgentConfig(
            name="hvac_agent",
            role="HVAC Services Automation Specialist", 
            goal="Manage HVAC service operations including maintenance scheduling, system diagnostics, and climate control optimization through voice commands",
            backstory="""You are an experienced HVAC technician and service coordinator with deep knowledge 
            of heating, ventilation, and air conditioning systems. You understand HVAC maintenance schedules, 
            system diagnostics, and energy efficiency optimization. You can process voice commands to schedule 
            maintenance, create service reports, and manage HVAC service workflows efficiently.""",
            voice_keywords=[
                "hvac", "heating", "cooling", "air conditioning", "ventilation", "temperature", 
                "maintenance", "filter", "thermostat", "system", "climate"
            ],
            tools=["maintenance_scheduler", "diagnostic_tool", "voice_integration"],
            verbose=True,
            allow_delegation=True
        )
    
    @staticmethod
    def get_orchestrator_config() -> AgentConfig:
        """Configuration for agent orchestrator."""
        return AgentConfig(
            name="agent_orchestrator",
            role="Multi-Agent Workflow Coordinator",
            goal="Coordinate multiple agents and manage complex workflows that span across different business domains through voice commands",
            backstory="""You are a master workflow coordinator with expertise in managing complex 
            multi-step business processes. You understand how different business domains (dental, 
            electrical, HVAC) interconnect and can orchestrate workflows that involve multiple 
            specialized agents. You excel at breaking down complex voice commands into actionable 
            tasks for the appropriate agents.""",
            voice_keywords=[
                "coordinate", "workflow", "multi", "complex", "orchestrate", "manage", 
                "overall", "general", "help", "assist"
            ],
            tools=["workflow_manager", "agent_coordinator", "voice_integration"],
            verbose=True,
            allow_delegation=True
        )
    
    @staticmethod
    def get_all_agent_configs() -> Dict[str, AgentConfig]:
        """Get all agent configurations."""
        return {
            "dental_agent": GTMVoyagerAgentConfigs.get_dental_agent_config(),
            "electrical_agent": GTMVoyagerAgentConfigs.get_electrical_agent_config(), 
            "hvac_agent": GTMVoyagerAgentConfigs.get_hvac_agent_config(),
            "agent_orchestrator": GTMVoyagerAgentConfigs.get_orchestrator_config()
        }


class VoiceIntegrationConfig:
    """Configuration for voice integration with agents."""
    
    # OpenAI API configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Voice processing settings
    VOICE_CONFIDENCE_THRESHOLD = 0.7
    MAX_AUDIO_DURATION = 300  # 5 minutes
    SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "m4a", "flac"]
    
    # Agent routing settings
    DEFAULT_AGENT = "agent_orchestrator"
    ENABLE_MULTI_AGENT_WORKFLOWS = True
    
    # Logging configuration
    LOG_VOICE_COMMANDS = True
    LOG_AGENT_RESPONSES = True
    
    @staticmethod
    def get_whisper_config() -> Dict[str, Any]:
        """Get Whisper API configuration."""
        return {
            "api_key": VoiceIntegrationConfig.OPENAI_API_KEY,
            "model": "whisper-1",
            "language": None,  # Auto-detect
            "temperature": 0.0,
            "max_retries": 3,
            "timeout": 300
        }
