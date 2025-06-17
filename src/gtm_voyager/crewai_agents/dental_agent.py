"""
GTM Voyager Platform - Dental Practice Agent
AI-powered dental scribe and practice automation agent.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from .base_agent import BaseBusinessAgent, AgentCapability


class ConversationType(Enum):
    """Types of dental conversations"""
    CONSULTATION = "consultation"
    EXAMINATION = "examination"
    TREATMENT_PLANNING = "treatment_planning"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"


@dataclass
class PatientInfo:
    """Patient information structure"""
    patient_id: str
    name: str
    age: int
    medical_history: List[str]
    dental_history: List[str]
    current_medications: List[str]
    allergies: List[str]


@dataclass
class SOAPNote:
    """SOAP Note structure for dental practices"""
    patient_id: str
    date: datetime
    provider: str
    conversation_type: ConversationType
    
    # SOAP Components
    subjective: str  # Patient complaints, symptoms, concerns
    objective: str   # Clinical findings, measurements, observations
    assessment: str  # Diagnosis, clinical impressions
    plan: str       # Treatment plan, next steps, prescriptions
    
    # Additional dental-specific fields
    teeth_examined: List[str]
    procedures_discussed: List[str]
    treatment_codes: List[str]
    next_appointment: Optional[str]
    
    # Metadata
    confidence_score: float
    requires_review: bool
    generated_timestamp: datetime


class DentalAgent(BaseBusinessAgent):
    """
    Dental industry specialized agent with AI scribe functionality.
    Handles conversation processing and SOAP note generation.
    """
    
    def __init__(self):
        # Define dental agent capabilities
        capabilities = [
            AgentCapability.VOICE_PROCESSING,
            AgentCapability.TEXT_ANALYSIS,
            AgentCapability.APPOINTMENT_SCHEDULING,
            AgentCapability.DOCUMENTATION,
            AgentCapability.COMPLIANCE
        ]
        
        # Initialize base agent
        super().__init__("dental", capabilities)
        
        # Dental-specific attributes
        self.conversation_buffer = []
        self.current_patient = None
        self.current_provider = None
        self.is_recording = False
        
    def _initialize_agent(self):
        """Initialize the dental CrewAI agent"""
        self.tools = self._setup_tools()
        
        self.agent = Agent(
            role="AI Dental Practice Assistant",
            goal="Automate dental practice workflows including real-time conversation transcription, SOAP note generation, and practice management tasks",
            backstory="""You are an expert dental practice assistant with extensive knowledge of dental terminology, 
            procedures, documentation standards, and practice management. You can listen to conversations between 
            dentists and patients, extract relevant clinical information, organize it into proper SOAP note format,
            and assist with various dental practice automation tasks. You understand dental anatomy, common procedures, 
            insurance codes, treatment planning, and regulatory compliance.""",
            verbose=True,
            allow_delegation=False,
            tools=self.tools
        )
        
        self.is_initialized = True
        
    def _setup_tools(self) -> List[BaseTool]:
        """Setup dental-specific tools"""
        return [
            self._create_soap_generation_tool(),
            self._create_dental_terminology_tool(),
            self._create_treatment_code_lookup_tool(),
            self._create_appointment_scheduling_tool()
        ]
    
    def _create_soap_generation_tool(self) -> BaseTool:
        """Tool for generating SOAP notes from conversation text"""
        class SOAPGenerationTool(BaseTool):
            name: str = "soap_note_generator"
            description: str = "Generate professional SOAP notes from dental conversation transcripts"
            
            def _run(self, conversation_text: str, patient_info: str, provider_name: str) -> str:
                """Generate SOAP note from conversation"""
                prompt = f"""
                Convert the following dental conversation into a professional SOAP note format:
                
                Patient Information: {patient_info}
                Provider: {provider_name}
                Conversation: {conversation_text}
                
                Generate a structured SOAP note with:
                - Subjective: Patient complaints, symptoms, concerns
                - Objective: Clinical findings, measurements, observations  
                - Assessment: Diagnosis, clinical impressions
                - Plan: Treatment recommendations, next steps
                
                Include relevant dental terminology and procedure codes where applicable.
                """
                
                # This would integrate with your OpenAI API
                return self._process_with_ai(prompt)
            
            def _process_with_ai(self, prompt: str) -> str:
                """Process with AI model - integrate with your OpenAI setup"""
                # TODO: Connect to your existing OpenAI integration
                return "Generated SOAP note content"
        
        return SOAPGenerationTool()
    def _create_dental_terminology_tool(self) -> BaseTool:
        """Tool for dental terminology and anatomy reference"""
        class DentalTerminologyTool(BaseTool):
            name: str = "dental_terminology"
            description: str = "Look up dental terminology, anatomy, and procedure definitions"
            
            def _run(self, term: str) -> str:
                """Look up dental terminology"""
                dental_terms = {
                    "caries": "Tooth decay or cavities",
                    "gingivitis": "Inflammation of the gums",
                    "periodontitis": "Advanced gum disease affecting supporting structures",
                    "crown": "Dental restoration covering entire tooth surface",
                    "root canal": "Endodontic treatment removing infected pulp",
                    "extraction": "Surgical removal of tooth",
                    "filling": "Restoration material placed in cavity",
                    "bridge": "Fixed prosthetic replacing missing teeth",
                    "implant": "Titanium post replacing tooth root",
                    "prophylaxis": "Professional dental cleaning",
                    "scaling": "Removal of plaque and tartar",
                    "endodontics": "Treatment of tooth pulp and root",
                    "periodontics": "Treatment of gum disease",
                    "orthodontics": "Correction of teeth alignment"
                }
                return dental_terms.get(term.lower(), f"Term '{term}' not found in database")
        
        return DentalTerminologyTool()
    def _create_treatment_code_lookup_tool(self) -> BaseTool:
        """Tool for looking up dental procedure codes"""
        class TreatmentCodeTool(BaseTool):
            name: str = "treatment_code_lookup"
            description: str = "Look up CDT (Current Dental Terminology) codes for procedures"
            
            def _run(self, procedure: str) -> str:
                """Look up treatment codes"""
                cdt_codes = {
                    "cleaning": "D1110 - Adult Prophylaxis",
                    "deep cleaning": "D4341 - Periodontal Scaling and Root Planing",
                    "filling": "D2140 - Amalgam Restoration (1 surface)",
                    "composite filling": "D2330 - Resin-based Composite (1 surface)",
                    "crown": "D2740 - Crown - Porcelain/Ceramic",
                    "root canal": "D3310 - Endodontic Treatment (Anterior)",
                    "extraction": "D7140 - Simple Extraction",
                    "surgical extraction": "D7210 - Surgical Removal of Erupted Tooth",
                    "x-ray": "D0220 - Intraoral Periapical Radiograph",
                    "bitewing x-ray": "D0272 - Bitewings - Two Radiographs",
                    "panoramic x-ray": "D0330 - Panoramic Radiograph",
                    "exam": "D0150 - Comprehensive Oral Evaluation",
                    "limited exam": "D0140 - Limited Oral Evaluation",
                    "emergency exam": "D0140 - Limited Oral Evaluation (Problem Focused)",
                    "fluoride": "D1208 - Topical Application of Fluoride",
                    "sealant": "D1351 - Sealant - Per Tooth"
                }
                return cdt_codes.get(procedure.lower(), f"Code for '{procedure}' not found")
        
        return TreatmentCodeTool()

    def _create_appointment_scheduling_tool(self) -> BaseTool:
        """Tool for appointment scheduling assistance"""
        class AppointmentSchedulingTool(BaseTool):
            name: str = "appointment_scheduler"
            description: str = "Help schedule and manage dental appointments"
            
            def _run(self, action: str, details: str) -> str:
                """Handle appointment scheduling actions"""
                if "schedule" in action.lower():
                    return f"Scheduling appointment: {details}"
                elif "reschedule" in action.lower():
                    return f"Rescheduling appointment: {details}"
                elif "cancel" in action.lower():
                    return f"Canceling appointment: {details}"
                elif "reminder" in action.lower():
                    return f"Setting reminder for: {details}"
                else:
                    return f"Appointment action '{action}' processed: {details}"
        
        return AppointmentSchedulingTool()

    def start_recording(self, patient_info: PatientInfo, provider_name: str):
        """Start recording conversation for a patient"""
        self.current_patient = patient_info
        self.current_provider = provider_name
        self.conversation_buffer = []
        self.is_recording = True
        return f"Started recording for patient {patient_info.name} with Dr. {provider_name}"
    
    def stop_recording(self):
        """Stop recording conversation"""
        self.is_recording = False
        return "Recording stopped"
    
    def add_conversation_text(self, text: str):
        """Add conversation text to buffer"""
        if self.is_recording:
            timestamp = datetime.now()
            self.conversation_buffer.append({
                "timestamp": timestamp,
                "text": text
            })
    
    def generate_soap_note(self) -> SOAPNote:
        """Generate SOAP note from recorded conversation"""
        if not self.conversation_buffer:
            raise ValueError("No conversation recorded")
        
        conversation_text = " ".join([item["text"] for item in self.conversation_buffer])
        
        # Use the SOAP generation tool
        soap_content = self.agent.tools[0]._run(
            conversation_text=conversation_text,
            patient_info=f"{self.current_patient.name}, Age: {self.current_patient.age}",
            provider_name=self.current_provider
        )
        
        # Create structured SOAP note
        soap_note = SOAPNote(
            patient_id=self.current_patient.patient_id,
            date=datetime.now(),
            provider=self.current_provider,
            conversation_type=ConversationType.CONSULTATION,
            subjective="Patient complaints extracted from conversation",
            objective="Clinical findings from examination",
            assessment="Diagnosis and clinical impressions",
            plan="Treatment recommendations and next steps",
            teeth_examined=[],
            procedures_discussed=[],
            treatment_codes=[],
            next_appointment=None,
            confidence_score=0.85,
            requires_review=True,
            generated_timestamp=datetime.now()
        )
        
        return soap_note

    
    # Implement abstract methods from BaseBusinessAgent
    def process_voice_input(self, audio_data: bytes, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process voice input and return structured response"""
        try:
            # TODO: Implement actual voice processing with Whisper
            # For now, return placeholder
            self.log_activity("voice_input_processed", {"audio_size": len(audio_data)})
            
            return {
                "success": True,
                "transcribed_text": "Voice processing placeholder",
                "confidence": 0.95,
                "processing_time": 1.2
            }
        except Exception as e:
            self.logger.error(f"Error processing voice input: {e}")
            return {"success": False, "error": str(e)}
    
    def process_text_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process text input and return structured response"""
        try:
            self.validate_input({"text": text}, ["text"])
            
            # Add text to conversation buffer if recording
            if self.is_recording:
                self.add_conversation_text(text)
            
            self.log_activity("text_input_processed", {"text_length": len(text)})
            
            return {
                "success": True,
                "processed_text": text,
                "added_to_conversation": self.is_recording,
                "conversation_length": len(self.conversation_buffer)
            }
        except Exception as e:
            self.logger.error(f"Error processing text input: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response based on input data"""
        try:
            action = input_data.get("action", "")
            
            if action == "start_recording":
                patient_info = PatientInfo(**input_data["patient_info"])
                provider_name = input_data["provider_name"]
                result = self.start_recording(patient_info, provider_name)
                return {"success": True, "message": result}
            
            elif action == "stop_recording":
                result = self.stop_recording()
                return {"success": True, "message": result}
            
            elif action == "generate_soap":
                soap_note = self.generate_soap_note()
                return {"success": True, "soap_note": soap_note}
            
            elif action == "lookup_term":
                term = input_data["term"]
                result = self.tools[1]._run(term)
                return {"success": True, "definition": result}
            
            elif action == "lookup_code":
                procedure = input_data["procedure"]
                result = self.tools[2]._run(procedure)
                return {"success": True, "code": result}
            
            elif action == "schedule_appointment":
                action_type = input_data["action_type"]
                details = input_data["details"]
                result = self.tools[3]._run(action_type, details)
                return {"success": True, "result": result}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {"success": False, "error": str(e)}

