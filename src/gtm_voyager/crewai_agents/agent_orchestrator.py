"""
GTM Voyager Platform - Agent Orchestrator
Coordinates and manages multiple CrewAI agents for different industries.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import json

from crewai import Agent, Task, Crew, Process
from .dental_agent import DentalAgent, PatientInfo, SOAPNote, ConversationType
from .base_agent import BaseBusinessAgent


class AgentType(Enum):
    """Available agent types"""
    DENTAL = "dental"
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    GENERAL = "general"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Task structure for agent execution"""
    task_id: str
    agent_type: AgentType
    task_type: str
    input_data: Dict[str, Any]
    priority: int = 1
    created_at: datetime = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AgentSession:
    """Session management for agent interactions"""
    session_id: str
    agent_type: AgentType
    user_id: str
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    context: Dict[str, Any] = None
    is_active: bool = True
    created_at: datetime = None
    last_activity: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.context is None:
            self.context = {}


class AgentOrchestrator:
    """
    CrewAI agent orchestrator for GTM Voyager Platform.
    Manages multiple specialized agents and coordinates their interactions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[AgentType, BaseBusinessAgent] = {}
        self.active_sessions: Dict[str, AgentSession] = {}
        self.task_queue: List[AgentTask] = []
        self.crews: Dict[str, Crew] = {}
        
        # Initialize agents
        self._initialize_agents()
        
        self.logger.info("AgentOrchestrator initialized with agents: %s", 
                        list(self.agents.keys()))
    
    def _initialize_agents(self):
        """Initialize all available agents"""
        try:
            # Initialize dental agent
            self.agents[AgentType.DENTAL] = DentalAgent()
            self.logger.info("Dental agent initialized successfully")
            
            # TODO: Initialize other agents when implemented
            # self.agents[AgentType.HVAC] = HVACAgent()
            # self.agents[AgentType.ELECTRICAL] = ElectricalAgent()
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            raise
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        return [agent_type.value for agent_type in self.agents.keys()]
    
    def create_session(self, agent_type: str, user_id: str, 
                      patient_id: Optional[str] = None,
                      provider_id: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new agent session"""
        try:
            agent_enum = AgentType(agent_type.lower())
            if agent_enum not in self.agents:
                raise ValueError(f"Agent type '{agent_type}' not available")
            
            session_id = f"{agent_type}_{user_id}_{datetime.now().timestamp()}"
            
            session = AgentSession(
                session_id=session_id,
                agent_type=agent_enum,
                user_id=user_id,
                patient_id=patient_id,
                provider_id=provider_id,
                context=context or {}
            )
            
            self.active_sessions[session_id] = session
            
            self.logger.info(f"Created session {session_id} for agent {agent_type}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close an agent session"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].is_active = False
                del self.active_sessions[session_id]
                self.logger.info(f"Closed session {session_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error closing session {session_id}: {e}")
            return False
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a task with the appropriate agent"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            start_time = datetime.now()
            
            agent = self.agents.get(task.agent_type)
            if not agent:
                raise ValueError(f"Agent {task.agent_type} not available")
            
            # Route task to appropriate handler based on agent type and task type
            if task.agent_type == AgentType.DENTAL:
                result = await self._execute_dental_task(agent, task)
            else:
                raise ValueError(f"Task execution not implemented for {task.agent_type}")
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.execution_time = execution_time
            
            self.logger.info(f"Task {task.task_id} completed in {execution_time:.2f}s")
            
            return {
                "success": True,
                "task_id": task.task_id,
                "result": result,
                "execution_time": execution_time
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            
            self.logger.error(f"Task {task.task_id} failed: {e}")
            
            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e)
            }
    
    async def _execute_dental_task(self, agent: DentalAgent, task: AgentTask) -> Dict[str, Any]:
        """Execute dental-specific tasks"""
        task_type = task.task_type
        input_data = task.input_data
        
        if task_type == "start_recording":
            # Start recording conversation
            patient_info = PatientInfo(**input_data["patient_info"])
            provider_name = input_data["provider_name"]
            
            result = agent.start_recording(patient_info, provider_name)
            return {"message": result, "recording_started": True}
        
        elif task_type == "stop_recording":
            # Stop recording conversation
            result = agent.stop_recording()
            return {"message": result, "recording_stopped": True}
        
        elif task_type == "add_conversation":
            # Add conversation text
            text = input_data["text"]
            agent.add_conversation_text(text)
            return {"message": "Conversation text added", "text_length": len(text)}
        
        elif task_type == "generate_soap":
            # Generate SOAP note
            soap_note = agent.generate_soap_note()
            return {
                "soap_note": {
                    "patient_id": soap_note.patient_id,
                    "date": soap_note.date.isoformat(),
                    "provider": soap_note.provider,
                    "conversation_type": soap_note.conversation_type.value,
                    "subjective": soap_note.subjective,
                    "objective": soap_note.objective,
                    "assessment": soap_note.assessment,
                    "plan": soap_note.plan,
                    "confidence_score": soap_note.confidence_score,
                    "requires_review": soap_note.requires_review
                }
            }
        
        elif task_type == "lookup_terminology":
            # Look up dental terminology
            term = input_data["term"]
            result = agent.agent.tools[1]._run(term)
            return {"term": term, "definition": result}
        
        elif task_type == "lookup_treatment_code":
            # Look up treatment code
            procedure = input_data["procedure"]
            result = agent.agent.tools[2]._run(procedure)
            return {"procedure": procedure, "code": result}
        
        elif task_type == "schedule_appointment":
            # Schedule appointment
            action = input_data["action"]
            details = input_data["details"]
            result = agent.agent.tools[3]._run(action, details)
            return {"action": action, "result": result}
        
        else:
            raise ValueError(f"Unknown dental task type: {task_type}")
    
    async def create_crew_for_complex_task(self, task_description: str, 
                                         agent_types: List[str]) -> str:
        """Create a crew for complex multi-agent tasks"""
        try:
            crew_id = f"crew_{datetime.now().timestamp()}"
            
            # Get agents for the crew
            crew_agents = []
            for agent_type in agent_types:
                agent_enum = AgentType(agent_type.lower())
                if agent_enum in self.agents:
                    crew_agents.append(self.agents[agent_enum].agent)
            
            if not crew_agents:
                raise ValueError("No valid agents found for crew")
            
            # Create the task
            crew_task = Task(
                description=task_description,
                agent=crew_agents[0],  # Primary agent
                expected_output="Comprehensive analysis and recommendations"
            )
            
            # Create the crew
            crew = Crew(
                agents=crew_agents,
                tasks=[crew_task],
                process=Process.sequential,
                verbose=True
            )
            
            self.crews[crew_id] = crew
            
            self.logger.info(f"Created crew {crew_id} with {len(crew_agents)} agents")
            return crew_id
            
        except Exception as e:
            self.logger.error(f"Error creating crew: {e}")
            raise
    
    async def execute_crew(self, crew_id: str) -> Dict[str, Any]:
        """Execute a crew task"""
        try:
            if crew_id not in self.crews:
                raise ValueError(f"Crew {crew_id} not found")
            
            crew = self.crews[crew_id]
            start_time = datetime.now()
            
            # Execute the crew
            result = crew.kickoff()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Crew {crew_id} completed in {execution_time:.2f}s")
            
            return {
                "success": True,
                "crew_id": crew_id,
                "result": str(result),
                "execution_time": execution_time
            }
            
        except Exception as e:
            self.logger.error(f"Error executing crew {crew_id}: {e}")
            return {
                "success": False,
                "crew_id": crew_id,
                "error": str(e)
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session.session_id,
            "agent_type": session.agent_type.value,
            "user_id": session.user_id,
            "patient_id": session.patient_id,
            "provider_id": session.provider_id,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "context": session.context
        }
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get overall orchestrator status"""
        return {
            "available_agents": self.get_available_agents(),
            "active_sessions": len(self.active_sessions),
            "pending_tasks": len([t for t in self.task_queue if t.status == TaskStatus.PENDING]),
            "active_crews": len(self.crews),
            "uptime": datetime.now().isoformat()
        }


# Global orchestrator instance
orchestrator = AgentOrchestrator()

