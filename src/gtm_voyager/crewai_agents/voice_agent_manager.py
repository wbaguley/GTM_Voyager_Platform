"""
GTM Voyager Platform - Voice-Agent Manager
Main orchestrator for voice-activated CrewAI agent workflows.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import our components
from .tools.voice_integration import VoiceAgentIntegration, VoiceCommandType
from .configs.agent_config import GTMVoyagerAgentConfigs, VoiceIntegrationConfig
from ...audio import WhisperConfig

# Import CrewAI components
try:
    from crewai import Agent, Task, Crew
    from crewai.tools import BaseTool
except ImportError:
    logging.error("CrewAI not installed. Please install with: pip install crewai")
    raise


class VoiceAgentManager:
    """
    Main manager for voice-activated CrewAI agent workflows.
    Integrates voice processing with specialized business agents.
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize the voice-agent manager.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenant support
        """
        self.tenant_id = tenant_id or "default"
        self.logger = self._setup_logger()
        
        # Initialize voice integration
        whisper_config = WhisperConfig(**VoiceIntegrationConfig.get_whisper_config())
        self.voice_integration = VoiceAgentIntegration(whisper_config)
        
        # Agent storage
        self.agents: Dict[str, Agent] = {}
        self.crews: Dict[str, Crew] = {}
        
        # Initialize agents
        self._initialize_agents()
        
        self.logger.info(f"VoiceAgentManager initialized for tenant: {self.tenant_id}")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the voice-agent manager."""
        logger = logging.getLogger(f'GTMVoyager.VoiceAgentManager.{self.tenant_id}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_agents(self):
        """Initialize all CrewAI agents with voice integration."""
        agent_configs = GTMVoyagerAgentConfigs.get_all_agent_configs()
        
        for agent_name, config in agent_configs.items():
            try:
                # Create CrewAI agent
                agent = Agent(
                    role=config.role,
                    goal=config.goal,
                    backstory=config.backstory,
                    verbose=config.verbose,
                    allow_delegation=config.allow_delegation,
                    tools=self._get_agent_tools(config.tools or [])
                )
                
                # Store agent
                self.agents[agent_name] = agent
                
                # Register agent with voice integration
                self.voice_integration.register_agent(agent_name, agent)
                
                self.logger.info(f"Initialized agent: {agent_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_name}: {e}")
    
    def _get_agent_tools(self, tool_names: List[str]) -> List[BaseTool]:
        """Get tools for agents (placeholder for now)."""
        # This would return actual CrewAI tools based on tool names
        # For now, return empty list - tools can be added later
        return []
    
    async def process_voice_command(self, audio_path: str) -> Dict[str, Any]:
        """
        Process a voice command through the complete workflow.
        
        Args:
            audio_path: Path to audio file containing voice command
            
        Returns:
            Complete workflow result
        """
        try:
            self.logger.info(f"Processing voice command from: {audio_path}")
            
            # Process through voice integration
            result = await self.voice_integration.process_voice_command(audio_path)
            
            if result.get("success"):
                # Add tenant context
                result["tenant_id"] = self.tenant_id
                result["timestamp"] = asyncio.get_event_loop().time()
                
                self.logger.info(f"Voice command processed successfully: {result.get('transcription')}")
            else:
                self.logger.warning(f"Voice command processing failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in voice command processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": self.tenant_id
            }
    
    async def process_text_command(self, text: str) -> Dict[str, Any]:
        """
        Process a text command directly (bypass voice processing).
        
        Args:
            text: Text command to process
            
        Returns:
            Command processing result
        """
        try:
            self.logger.info(f"Processing text command: {text}")
            
            # Parse command using voice integration parser
            voice_command = self.voice_integration.command_parser.parse_command(text)
            
            # Execute if agent is available
            if voice_command.agent_target and voice_command.agent_target in self.agents:
                result = await self.voice_integration._execute_agent_task(voice_command)
                
                return {
                    "success": True,
                    "command": voice_command,
                    "result": result,
                    "tenant_id": self.tenant_id
                }
            else:
                return {
                    "success": False,
                    "error": f"No agent available for command type: {voice_command.command_type}",
                    "command": voice_command,
                    "tenant_id": self.tenant_id
                }
                
        except Exception as e:
            self.logger.error(f"Error processing text command: {e}")
            return {
                "success": False,
                "error": str(e),
                "tenant_id": self.tenant_id
            }
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
        return list(self.agents.keys())
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent."""
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        config = GTMVoyagerAgentConfigs.get_all_agent_configs().get(agent_name)
        
        return {
            "name": agent_name,
            "role": agent.role,
            "goal": agent.goal,
            "voice_keywords": config.voice_keywords if config else [],
            "tools": config.tools if config else [],
            "tenant_id": self.tenant_id
        }
    
    async def create_custom_workflow(self, 
                                   agents: List[str], 
                                   tasks: List[str],
                                   voice_trigger: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a custom multi-agent workflow.
        
        Args:
            agents: List of agent names to include
            tasks: List of task descriptions
            voice_trigger: Optional voice command that triggers this workflow
            
        Returns:
            Workflow creation result
        """
        try:
            # Validate agents exist
            missing_agents = [name for name in agents if name not in self.agents]
            if missing_agents:
                return {
                    "success": False,
                    "error": f"Missing agents: {missing_agents}"
                }
            
            # Create workflow (placeholder implementation)
            workflow_id = f"workflow_{len(self.crews)}"
            
            self.logger.info(f"Created custom workflow: {workflow_id}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "agents": agents,
                "tasks": tasks,
                "voice_trigger": voice_trigger,
                "tenant_id": self.tenant_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creating custom workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class MultiTenantVoiceAgentManager:
    """Manager for multiple tenant voice-agent systems."""
    
    def __init__(self):
        """Initialize multi-tenant manager."""
        self.tenant_managers: Dict[str, VoiceAgentManager] = {}
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for multi-tenant manager."""
        logger = logging.getLogger('GTMVoyager.MultiTenantVoiceAgentManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_tenant_manager(self, tenant_id: str) -> VoiceAgentManager:
        """Get or create a voice-agent manager for a tenant."""
        if tenant_id not in self.tenant_managers:
            self.tenant_managers[tenant_id] = VoiceAgentManager(tenant_id)
            self.logger.info(f"Created voice-agent manager for tenant: {tenant_id}")
        
        return self.tenant_managers[tenant_id]
    
    async def process_tenant_voice_command(self, 
                                         tenant_id: str, 
                                         audio_path: str) -> Dict[str, Any]:
        """Process voice command for a specific tenant."""
        manager = self.get_tenant_manager(tenant_id)
        return await manager.process_voice_command(audio_path)
    
    def get_tenant_stats(self) -> Dict[str, Any]:
        """Get statistics about all tenants."""
        return {
            "total_tenants": len(self.tenant_managers),
            "active_tenants": list(self.tenant_managers.keys()),
            "total_agents": sum(len(manager.agents) for manager in self.tenant_managers.values())
        }


# Utility functions for easy integration
def create_voice_agent_manager(tenant_id: Optional[str] = None) -> VoiceAgentManager:
    """Create a voice-agent manager instance."""
    return VoiceAgentManager(tenant_id)


def create_multi_tenant_manager() -> MultiTenantVoiceAgentManager:
    """Create a multi-tenant voice-agent manager."""
    return MultiTenantVoiceAgentManager()


# Global multi-tenant manager instance
_global_manager = None

def get_global_manager() -> MultiTenantVoiceAgentManager:
    """Get the global multi-tenant manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = MultiTenantVoiceAgentManager()
    return _global_manager
