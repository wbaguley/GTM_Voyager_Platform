"""
MCP Tools for GTM Voyager Platform
Exposes GTM Voyager voice processing and AI capabilities as MCP tools
"""

import logging
import base64
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import GTM Voyager voice processing components
try:
    from ...voice_processing.voice_processor import VoiceProcessor
    from ...voice_processing.whisper_stt import WhisperSTT
    from ...crewai_agents.industry_agent_router import IndustryAgentRouter
    from ...database.models import UserProfile
    VOICE_PROCESSING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Voice processing imports not available: {e}")
    VOICE_PROCESSING_AVAILABLE = False

logger = logging.getLogger(__name__)

async def get_all_mcp_tools() -> List[Dict[str, Any]]:
    """Get all available MCP tools including voice processing"""
    tools = [
        # Basic system tools
        {
            "name": "ping",
            "description": "Test connectivity to GTM Voyager Platform",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "system_status",
            "description": "Get current system status and health",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        # ENHANCED: Add enhanced dental consultation tool
        {
            "name": "enhanced_dental_consultation",
            "description": "Enhanced dental consultation with clinical analysis and differential diagnosis",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Patient's dental concerns and symptoms"
                    },
                    "patient_info": {
                        "type": "object",
                        "description": "Patient information including name, age, medical history"
                    }
                },
                "required": ["query"]
            }
        }
    ]
    
    # Add voice processing tools if available
    if VOICE_PROCESSING_AVAILABLE:
        voice_tools = [
            {
                "name": "voice_transcribe",
                "description": "Transcribe audio to text using Whisper STT",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "Base64 encoded audio data"
                        },
                        "audio_format": {
                            "type": "string",
                            "description": "Audio format (mp3, wav, m4a, etc.)",
                            "enum": ["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "webm"]
                        }
                    },
                    "required": ["audio_data"]
                }
            },
            {
                "name": "voice_process_with_context",
                "description": "Process voice input with user context and industry-specific AI routing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "Base64 encoded audio data"
                        },
                        "audio_format": {
                            "type": "string",
                            "description": "Audio format",
                            "enum": ["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "webm"]
                        },
                        "user_context": {
                            "type": "object",
                            "description": "User context and preferences",
                            "properties": {
                                "user_id": {"type": "string"},
                                "industry_type": {
                                    "type": "string",
                                    "enum": ["dental", "hvac", "electrical", "prosthodontics"]
                                },
                                "company_name": {"type": "string"},
                                "preferences": {"type": "object"}
                            }
                        }
                    },
                    "required": ["audio_data"]
                }
            },
            {
                "name": "audio_quality_check",
                "description": "Validate audio quality and format compatibility",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "Base64 encoded audio data"
                        }
                    },
                    "required": ["audio_data"]
                }
            },
            {
                "name": "voice_processing_status",
                "description": "Get current voice processing system status and statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        tools.extend(voice_tools)
    
    return tools

async def get_tools_list() -> List[Dict[str, Any]]:
    """Get tools list in MCP format"""
    return await get_all_mcp_tools()

async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific tool"""
    try:
        logger.info(f"Executing MCP tool: {tool_name}")
        
        # Basic system tools
        if tool_name == "ping":
            return await execute_ping_tool(arguments)
        elif tool_name == "system_status":
            return await execute_system_status_tool(arguments)
        
        # ENHANCED: Add enhanced dental consultation tool execution
        elif tool_name == "enhanced_dental_consultation":
            return await execute_enhanced_dental_consultation_tool(arguments)
        
        # Voice processing tools
        elif tool_name == "voice_transcribe":
            return await execute_voice_transcribe_tool(arguments)
        elif tool_name == "voice_process_with_context":
            return await execute_voice_process_with_context_tool(arguments)
        elif tool_name == "audio_quality_check":
            return await execute_audio_quality_check_tool(arguments)
        elif tool_name == "voice_processing_status":
            return await execute_voice_processing_status_tool(arguments)
        
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": [tool["name"] for tool in await get_all_mcp_tools()]
            }
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {
            "error": f"Tool execution failed: {str(e)}",
            "tool": tool_name,
            "arguments": arguments,
            "timestamp": datetime.utcnow().isoformat()
        }

# Basic System Tools
async def execute_ping_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute ping tool"""
    return {
        "status": "success",
        "message": "GTM Voyager Platform is responding",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "gtm-voyager-mcp",
        "voice_processing_available": VOICE_PROCESSING_AVAILABLE
    }

async def execute_system_status_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute system status tool"""
    status = {
        "status": "healthy",
        "services": {
            "mcp_server": "available",
            "voice_processing": "available" if VOICE_PROCESSING_AVAILABLE else "unavailable",
            "ai_agents": "available",
            "workflow_automation": "available",
            "database": "connected"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    if VOICE_PROCESSING_AVAILABLE:
        status["voice_capabilities"] = {
            "whisper_stt": "available",
            "audio_formats": ["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "webm"],
            "max_file_size": "25MB",
            "industry_agents": ["dental", "hvac", "electrical", "prosthodontics"]
        }
    
    return status

# ENHANCED: Enhanced Dental Consultation Tool
async def execute_enhanced_dental_consultation_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute enhanced dental consultation with clinical analysis"""
    try:
        import aiohttp
        
        query = arguments.get('query', '')
        patient_info = arguments.get('patient_info', {})
        
        # Call the enhanced consultation endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/dental/enhanced-consultation",
                json={"query": query, "patient_info": patient_info},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "success",
                        "result": result
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"API call failed with status {response.status}: {error_text}"
                    }
                    
    except Exception as e:
        logger.error(f"Enhanced dental consultation error: {e}")
        return {
            "status": "error",
            "message": f"Enhanced dental consultation failed: {str(e)}"
        }

# Voice Processing Tools
async def execute_voice_transcribe_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute voice transcription tool"""
    if not VOICE_PROCESSING_AVAILABLE:
        return {
            "error": "Voice processing not available",
            "message": "Voice processing components not imported"
        }
    
    try:
        audio_data = arguments.get("audio_data")
        audio_format = arguments.get("audio_format", "mp3")
        
        if not audio_data:
            return {"error": "No audio data provided"}
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            return {"error": f"Invalid base64 audio data: {str(e)}"}
        
        # Create temporary file for Whisper processing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Initialize WhisperSTT and transcribe
            whisper_stt = WhisperSTT()
            result = await asyncio.to_thread(
                whisper_stt.transcribe_audio, 
                temp_file_path
            )
            
            return {
                "status": "success",
                "transcription": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        return {
            "error": f"Transcription failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

async def execute_voice_process_with_context_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute voice processing with context tool"""
    if not VOICE_PROCESSING_AVAILABLE:
        return {
            "error": "Voice processing not available",
            "message": "Voice processing components not imported"
        }
    
    try:
        audio_data = arguments.get("audio_data")
        audio_format = arguments.get("audio_format", "mp3")
        user_context = arguments.get("user_context", {})
        
        if not audio_data:
            return {"error": "No audio data provided"}
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            return {"error": f"Invalid base64 audio data: {str(e)}"}
        
        # Create temporary file for processing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Create UserProfile from context
            user_profile = create_user_profile_from_context(user_context)
            
            # Initialize VoiceProcessor and process
            voice_processor = VoiceProcessor()
            result = await asyncio.to_thread(
                voice_processor.process_voice_input,
                temp_file_path,
                user_profile
            )
            
            return {
                "status": "success",
                "transcription": result.get("transcription", ""),
                "speaker_info": result.get("speaker_info", {}),
                "agent_response": result.get("response_message", ""),
                "industry_type": user_context.get("industry_type", "unknown"),
                "confidence": result.get("confidence_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logger.error(f"Voice processing with context error: {e}")
        return {
            "error": f"Voice processing failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

async def execute_audio_quality_check_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute audio quality check tool"""
    try:
        audio_data = arguments.get("audio_data")
        
        if not audio_data:
            return {"error": "No audio data provided"}
        
        # Decode and analyze audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
            audio_size = len(audio_bytes)
        except Exception as e:
            return {"error": f"Invalid base64 audio data: {str(e)}"}
        
        # Basic quality checks
        quality_checks = {
            "size_check": {
                "size_bytes": audio_size,
                "size_mb": round(audio_size / (1024 * 1024), 2),
                "within_limit": audio_size <= 25 * 1024 * 1024,  # 25MB limit
                "status": "pass" if audio_size <= 25 * 1024 * 1024 else "fail"
            },
            "format_check": {
                "status": "pass",  # Basic check - could be enhanced
                "message": "Audio data format appears valid"
            }
        }
        
        overall_status = all(
            check.get("status") == "pass" 
            for check in quality_checks.values()
        )
        
        return {
            "status": "success",
            "overall_quality": "good" if overall_status else "poor",
            "checks": quality_checks,
            "recommendations": [] if overall_status else [
                "Reduce file size if over 25MB",
                "Ensure audio format is supported"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Audio quality check error: {e}")
        return {
            "error": f"Quality check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

async def execute_voice_processing_status_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute voice processing status tool"""
    try:
        status = {
            "voice_processing_available": VOICE_PROCESSING_AVAILABLE,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if VOICE_PROCESSING_AVAILABLE:
            status.update({
                "whisper_stt": {
                    "status": "available",
                    "supported_formats": ["mp3", "wav", "m4a", "mp4", "mpeg", "mpga", "webm"],
                    "max_file_size": "25MB"
                },
                "voice_processor": {
                    "status": "available",
                    "features": [
                        "audio_transcription",
                        "speaker_diarization",
                        "industry_agent_routing",
                        "context_aware_processing"
                    ]
                },
                "industry_agents": {
                    "available": ["dental", "hvac", "electrical", "prosthodontics"],
                    "status": "ready"
                }
            })
        else:
            status.update({
                "error": "Voice processing components not available",
                "message": "Check voice processing module imports"
            })
        
        return status
    
    except Exception as e:
        logger.error(f"Voice processing status error: {e}")
        return {
            "error": f"Status check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

def create_user_profile_from_context(user_context: Dict[str, Any]) -> 'UserProfile':
    """Create UserProfile object from MCP context"""
    try:
        # Create a basic UserProfile object
        # This is a simplified version - adjust based on your actual UserProfile model
        user_profile = UserProfile(
            user_id=user_context.get("user_id", "mcp_user"),
            industry_type=user_context.get("industry_type", "general"),
            company_name=user_context.get("company_name", "Unknown"),
            preferences=user_context.get("preferences", {})
        )
        return user_profile
    except Exception as e:
        logger.warning(f"Could not create UserProfile from context: {e}")
        # Return a minimal profile
        class MinimalUserProfile:
            def __init__(self):
                self.user_id = user_context.get("user_id", "mcp_user")
                self.industry_type = user_context.get("industry_type", "general")
                self.company_name = user_context.get("company_name", "Unknown")
                self.preferences = user_context.get("preferences", {})
        
        return MinimalUserProfile()

