"""
GTM Voyager Platform - Enhanced API Endpoints
Updated endpoints that connect to the AgentOrchestrator and dental agents.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Dict, Any, Optional
import uuid
import asyncio

from ..api.dependencies import get_current_user
from ..crewai_agents.agent_orchestrator import orchestrator, AgentTask, AgentType, TaskStatus


# Voice processing router
voice_router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@voice_router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Transcribe audio file to text using Whisper."""
    try:
        # Read audio data
        audio_data = await file.read()
        
        # Create session if needed
        session_id = orchestrator.create_session(
            agent_type="dental",
            user_id=current_user["user_id"]
        )
        
        # Process voice input through dental agent
        dental_agent = orchestrator.agents[AgentType.DENTAL]
        result = dental_agent.process_voice_input(audio_data)
        
        return {
            "success": True,
            "session_id": session_id,
            "transcribed_text": result.get("transcribed_text", ""),
            "confidence": result.get("confidence", 0.0),
            "filename": file.filename,
            "size": file.size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@voice_router.post("/process")
async def process_voice_command(
    audio_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Process voice command through the complete pipeline."""
    try:
        # Create task for voice processing
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="process_voice",
            input_data=audio_data,
            priority=1
        )
        
        # Execute task
        result = await orchestrator.execute_task(task)
        
        return {
            "success": result["success"],
            "task_id": result["task_id"],
            "result": result.get("result", {}),
            "execution_time": result.get("execution_time", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent management router
agent_router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@agent_router.get("/")
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List all available agents."""
    try:
        available_agents = orchestrator.get_available_agents()
        
        agent_details = []
        for agent_type in available_agents:
            agent_enum = AgentType(agent_type)
            agent = orchestrator.agents.get(agent_enum)
            if agent:
                agent_details.append(agent.get_agent_info())
        
        return {
            "agents": agent_details,
            "count": len(agent_details),
            "orchestrator_status": orchestrator.get_orchestrator_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/{agent_type}/execute")
async def execute_agent(
    agent_type: str, 
    task_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Execute a specific agent with task data."""
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")
        
        # Create task
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=agent_enum,
            task_type=task_data.get("task_type", "general"),
            input_data=task_data.get("input_data", {}),
            priority=task_data.get("priority", 1)
        )
        
        # Execute task
        result = await orchestrator.execute_task(task)
        
        return {
            "success": result["success"],
            "agent_type": agent_type,
            "task_id": result["task_id"],
            "task_result": result.get("result", {}),
            "execution_time": result.get("execution_time", 0),
            "error": result.get("error")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/{agent_type}/session")
async def create_agent_session(
    agent_type: str,
    session_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create a new agent session."""
    try:
        session_id = orchestrator.create_session(
            agent_type=agent_type,
            user_id=current_user["user_id"],
            patient_id=session_data.get("patient_id"),
            provider_id=session_data.get("provider_id"),
            context=session_data.get("context", {})
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_type": agent_type,
            "user_id": current_user["user_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.get("/session/{session_id}")
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of an agent session."""
    try:
        status = orchestrator.get_session_status(session_id)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.delete("/session/{session_id}")
async def close_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Close an agent session."""
    try:
        success = orchestrator.close_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "message": f"Session {session_id} closed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dental-specific endpoints
dental_router = APIRouter(prefix="/api/v1/dental", tags=["dental"])

@dental_router.post("/recording/start")
async def start_recording(
    recording_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Start recording a dental conversation."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="start_recording",
            input_data=recording_data
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dental_router.post("/recording/stop")
async def stop_recording(
    session_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Stop recording a dental conversation."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="stop_recording",
            input_data=session_data
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dental_router.post("/conversation/add")
async def add_conversation_text(
    conversation_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Add conversation text to the current recording."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="add_conversation",
            input_data=conversation_data
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dental_router.post("/soap/generate")
async def generate_soap_note(
    soap_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Generate SOAP note from recorded conversation."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="generate_soap",
            input_data=soap_data
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dental_router.get("/terminology/{term}")
async def lookup_dental_terminology(
    term: str,
    current_user: dict = Depends(get_current_user)
):
    """Look up dental terminology."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="lookup_terminology",
            input_data={"term": term}
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dental_router.get("/treatment-code/{procedure}")
async def lookup_treatment_code(
    procedure: str,
    current_user: dict = Depends(get_current_user)
):
    """Look up dental treatment code."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="lookup_treatment_code",
            input_data={"procedure": procedure}
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dental_router.post("/appointment/schedule")
async def schedule_appointment(
    appointment_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Schedule a dental appointment."""
    try:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_type=AgentType.DENTAL,
            task_type="schedule_appointment",
            input_data=appointment_data
        )
        
        result = await orchestrator.execute_task(task)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Workflow management router
workflow_router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

@workflow_router.get("/")
async def list_workflows(current_user: dict = Depends(get_current_user)):
    """List all available workflows."""
    try:
        # TODO: Implement workflow management
        return {
            "workflows": [
                {
                    "id": "dental_consultation",
                    "name": "Dental Consultation Workflow",
                    "description": "Complete dental consultation with SOAP note generation",
                    "steps": ["start_recording", "conversation_capture", "soap_generation", "review"]
                },
                {
                    "id": "appointment_scheduling",
                    "name": "Appointment Scheduling Workflow", 
                    "description": "Schedule and manage dental appointments",
                    "steps": ["patient_lookup", "availability_check", "schedule_confirmation"]
                }
            ],
            "count": 2
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@workflow_router.post("/execute")
async def execute_workflow(
    workflow_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Execute a workflow."""
    try:
        workflow_id = workflow_data.get("workflow_id")
        
        if workflow_id == "dental_consultation":
            # Create crew for dental consultation
            crew_id = await orchestrator.create_crew_for_complex_task(
                task_description="Complete dental consultation workflow with SOAP note generation",
                agent_types=["dental"]
            )
            
            # Execute the crew
            result = await orchestrator.execute_crew(crew_id)
            
            return {
                "success": result["success"],
                "workflow_id": workflow_id,
                "crew_id": crew_id,
                "execution_id": result.get("crew_id"),
                "status": "completed" if result["success"] else "failed",
                "result": result.get("result"),
                "execution_time": result.get("execution_time")
            }
        else:
            return {
                "success": False,
                "error": f"Workflow '{workflow_id}' not implemented"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Status and monitoring endpoints
status_router = APIRouter(prefix="/api/v1/status", tags=["status"])

@status_router.get("/orchestrator")
async def get_orchestrator_status(current_user: dict = Depends(get_current_user)):
    """Get orchestrator status."""
    try:
        return orchestrator.get_orchestrator_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@status_router.get("/agents")
async def get_agents_status(current_user: dict = Depends(get_current_user)):
    """Get status of all agents."""
    try:
        agents_status = {}
        for agent_type, agent in orchestrator.agents.items():
            agents_status[agent_type.value] = agent.get_status()
        
        return {
            "agents": agents_status,
            "total_agents": len(agents_status)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

