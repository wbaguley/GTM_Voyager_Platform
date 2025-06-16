# GTM Voyager Platform - Main Package
"""
GTM Voyager Platform: Voice-First Business Automation Platform

A comprehensive AI-powered platform that transforms voice commands into 
intelligent business automation for trade businesses including dental 
practices, HVAC companies, and electrical contractors.

Key Features:
- Voice-to-action automation using OpenAI Whisper
- Intelligent agent orchestration with CrewAI
- Hybrid LLM architecture (OpenAI GPT-4 + Local Llama)
- Multi-tenant n8n workflow integration
- RTX 5080 optimized local AI processing
- HIPAA-compliant security architecture

Author: GTM Voyager Platform Team
Version: 1.0.0
License: Proprietary
"""

__version__ = "1.0.0"
__author__ = "GTM Voyager Platform Team"
__email__ = "dev@gtmvoyager.com"
__license__ = "Proprietary"

# Core module imports
from .voice_processing import VoiceProcessor, WhisperSTT
from .crewai_agents import AgentOrchestrator, DentalAgent, HVACAgent
from .n8n_integration import WorkflowTrigger, N8NClient
from .api import GTMVoyagerAPI
from .utils import ConfigManager, Logger, SecurityManager

# Package metadata
__all__ = [
    "VoiceProcessor",
    "WhisperSTT", 
    "AgentOrchestrator",
    "DentalAgent",
    "HVACAgent",
    "WorkflowTrigger",
    "N8NClient",
    "GTMVoyagerAPI",
    "ConfigManager",
    "Logger",
    "SecurityManager"
]

# Version information
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

def get_version():
    """Return the current version of GTM Voyager Platform."""
    return __version__

def get_version_info():
    """Return detailed version information."""
    return VERSION_INFO

