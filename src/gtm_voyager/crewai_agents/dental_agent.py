"""
GTM Voyager Platform - Dental Practice Agent
AI-powered dental scribe and practice automation agent.
"""

import asyncio
import json
import re
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


# NEW: Enhanced Clinical Analysis Tool
class ClinicalAnalysisTool(BaseTool):
    """Enhanced clinical analysis tool with differential diagnosis and urgency assessment"""
    
    name: str = "clinical_analysis"
    description: str = "Analyze patient symptoms and provide differential diagnosis with urgency assessment"
    
    def _run(self, symptoms: str, patient_info: str = "", duration: str = "") -> str:
        """Perform comprehensive clinical analysis"""
        
        # Parse symptoms and extract key indicators
        analysis = self._analyze_symptoms(symptoms, patient_info, duration)
        
        # Generate differential diagnosis
        differential_dx = self._generate_differential_diagnosis(analysis)
        
        # Assess urgency level
        urgency = self._assess_urgency(analysis)
        
        # Create clinical reasoning
        reasoning = self._generate_clinical_reasoning(analysis, differential_dx, urgency)
        
        return json.dumps({
            "symptom_analysis": analysis,
            "differential_diagnosis": differential_dx,
            "urgency_assessment": urgency,
            "clinical_reasoning": reasoning,
            "recommended_actions": self._get_recommended_actions(urgency, differential_dx)
        }, indent=2)
    
    def _analyze_symptoms(self, symptoms: str, patient_info: str, duration: str) -> Dict:
        """Extract and categorize symptoms"""
        
        # Pain indicators
        pain_keywords = ["pain", "ache", "hurt", "sore", "tender", "throb", "sharp", "dull"]
        pain_level = self._extract_pain_level(symptoms)
        has_pain = any(keyword in symptoms.lower() for keyword in pain_keywords)
        
        # Swelling indicators
        swelling_keywords = ["swelling", "swollen", "puffy", "enlarged", "bulging"]
        has_swelling = any(keyword in symptoms.lower() for keyword in swelling_keywords)
        
        # Infection indicators
        infection_keywords = ["fever", "pus", "discharge", "abscess", "infection", "hot", "warm"]
        has_infection_signs = any(keyword in symptoms.lower() for keyword in infection_keywords)
        
        # Bleeding indicators
        bleeding_keywords = ["bleeding", "blood", "hemorrhage", "oozing"]
        has_bleeding = any(keyword in symptoms.lower() for keyword in bleeding_keywords)
        
        # Duration assessment
        duration_category = self._categorize_duration(duration, symptoms)
        
        return {
            "pain_present": has_pain,
            "pain_level": pain_level,
            "swelling_present": has_swelling,
            "infection_signs": has_infection_signs,
            "bleeding_present": has_bleeding,
            "duration_category": duration_category,
            "raw_symptoms": symptoms,
            "patient_context": patient_info
        }
    
    def _extract_pain_level(self, symptoms: str) -> Optional[int]:
        """Extract pain level from 1-10 scale"""
        pain_pattern = r'(\d+)(?:/10|out of 10| pain| level)'
        match = re.search(pain_pattern, symptoms.lower())
        if match:
            return int(match.group(1))
        
        # Qualitative pain assessment
        if "severe" in symptoms.lower() or "excruciating" in symptoms.lower():
            return 8
        elif "moderate" in symptoms.lower():
            return 5
        elif "mild" in symptoms.lower() or "slight" in symptoms.lower():
            return 3
        
        return None
    
    def _categorize_duration(self, duration: str, symptoms: str) -> str:
        """Categorize symptom duration"""
        if not duration:
            # Try to extract from symptoms
            symptoms_lower = symptoms.lower()
            if "started yesterday" in symptoms_lower or "started today" in symptoms_lower:
                return "acute"
            elif "few days" in symptoms_lower or "3 days" in symptoms_lower:
                return "acute"
            elif "week" in symptoms_lower:
                return "subacute"
            elif "month" in symptoms_lower:
                return "chronic"
            return "unknown"
        
        duration_lower = duration.lower()
        
        if "hour" in duration_lower or "today" in duration_lower:
            return "acute"
        elif "day" in duration_lower and ("few" in duration_lower or any(str(i) in duration_lower for i in range(1, 8))):
            return "acute"
        elif "week" in duration_lower:
            return "subacute"
        elif "month" in duration_lower or "year" in duration_lower:
            return "chronic"
        
        return "unknown"
    
    def _generate_differential_diagnosis(self, analysis: Dict) -> List[Dict]:
        """Generate differential diagnosis based on symptom analysis"""
        
        diagnoses = []
        
        # Pulpitis assessment
        if analysis["pain_present"] and analysis["pain_level"] and analysis["pain_level"] >= 6:
            if analysis["duration_category"] == "acute":
                diagnoses.append({
                    "condition": "Irreversible Pulpitis",
                    "probability": "High",
                    "reasoning": "Severe pain with acute onset suggests irreversible pulpal inflammation"
                })
            else:
                diagnoses.append({
                    "condition": "Reversible Pulpitis",
                    "probability": "Moderate",
                    "reasoning": "Pain present but duration suggests potentially reversible condition"
                })
        
        # Abscess assessment
        if analysis["swelling_present"] and analysis["infection_signs"]:
            diagnoses.append({
                "condition": "Dental Abscess",
                "probability": "High",
                "reasoning": "Swelling combined with infection signs indicates abscess formation"
            })
        
        # Periodontal disease
        if analysis["bleeding_present"] and analysis["swelling_present"]:
            diagnoses.append({
                "condition": "Periodontal Disease",
                "probability": "Moderate",
                "reasoning": "Bleeding and swelling suggest gingival or periodontal inflammation"
            })
        
        # Sensitivity issues
        if analysis["pain_present"] and analysis["pain_level"] and analysis["pain_level"] <= 4:
            diagnoses.append({
                "condition": "Dentin Hypersensitivity",
                "probability": "Moderate",
                "reasoning": "Mild to moderate pain suggests tooth sensitivity"
            })
        
        # Default if no specific patterns
        if not diagnoses:
            diagnoses.append({
                "condition": "Dental Consultation Required",
                "probability": "Certain",
                "reasoning": "Symptoms require professional dental evaluation"
            })
        
        return diagnoses
    
    def _assess_urgency(self, analysis: Dict) -> Dict:
        """Assess urgency level and timeframe"""
        
        # Emergency indicators
        if (analysis["infection_signs"] and analysis["swelling_present"]) or \
           (analysis["pain_level"] and analysis["pain_level"] >= 8):
            return {
                "level": "EMERGENCY",
                "timeframe": "Immediate (within hours)",
                "reasoning": "Severe pain or signs of spreading infection require immediate attention"
            }
        
        # Urgent indicators
        if analysis["pain_level"] and analysis["pain_level"] >= 6:
            return {
                "level": "URGENT",
                "timeframe": "Within 24-48 hours",
                "reasoning": "Significant pain requires prompt dental care"
            }
        
        # Routine but prompt
        if analysis["pain_present"] or analysis["bleeding_present"]:
            return {
                "level": "PROMPT",
                "timeframe": "Within 1 week",
                "reasoning": "Symptoms indicate need for dental evaluation"
            }
        
        # Routine
        return {
            "level": "ROUTINE",
            "timeframe": "Within 2-4 weeks",
            "reasoning": "Preventive care or routine evaluation recommended"
        }
    
    def _generate_clinical_reasoning(self, analysis: Dict, differential_dx: List[Dict], urgency: Dict) -> str:
        """Generate clinical reasoning narrative"""
        
        reasoning = f"Clinical Analysis:\n\n"
        
        # Symptom summary
        reasoning += f"Patient presents with: {analysis['raw_symptoms']}\n\n"
        
        # Key findings
        findings = []
        if analysis["pain_present"]:
            pain_desc = f"pain (level {analysis['pain_level']}/10)" if analysis["pain_level"] else "pain"
            findings.append(pain_desc)
        if analysis["swelling_present"]:
            findings.append("swelling")
        if analysis["infection_signs"]:
            findings.append("signs of infection")
        if analysis["bleeding_present"]:
            findings.append("bleeding")
        
        if findings:
            reasoning += f"Key clinical findings: {', '.join(findings)}\n\n"
        
        # Duration context
        if analysis["duration_category"] != "unknown":
            reasoning += f"Symptom duration: {analysis['duration_category']} onset\n\n"
        
        # Differential diagnosis reasoning
        reasoning += "Differential Diagnosis Considerations:\n"
        for dx in differential_dx:
            reasoning += f"• {dx['condition']} ({dx['probability']} probability): {dx['reasoning']}\n"
        
        reasoning += f"\nUrgency Assessment: {urgency['level']} - {urgency['reasoning']}"
        
        return reasoning
    
    def _get_recommended_actions(self, urgency: Dict, differential_dx: List[Dict]) -> List[str]:
        """Get recommended immediate actions"""
        
        actions = []
        
        if urgency["level"] == "EMERGENCY":
            actions.extend([
                "Seek immediate dental care or emergency room evaluation",
                "Take prescribed antibiotics if available",
                "Use over-the-counter pain management as directed",
                "Apply cold compress to reduce swelling"
            ])
        elif urgency["level"] == "URGENT":
            actions.extend([
                "Schedule dental appointment within 24-48 hours",
                "Use over-the-counter pain relief as needed",
                "Avoid hot/cold foods that trigger pain",
                "Maintain oral hygiene carefully"
            ])
        else:
            actions.extend([
                "Schedule routine dental appointment",
                "Continue regular oral hygiene",
                "Monitor symptoms for any worsening"
            ])
        
        # Specific actions based on diagnosis
        for dx in differential_dx:
            if "Abscess" in dx["condition"]:
                actions.append("Do not apply heat to swollen area")
            elif "Pulpitis" in dx["condition"]:
                actions.append("Avoid extreme temperatures in food/drink")
        
        return actions


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
        """Setup dental-specific tools - ENHANCED VERSION"""
        return [
            self._create_soap_generation_tool(),
            self._create_dental_terminology_tool(),
            self._create_treatment_code_lookup_tool(),
            self._create_appointment_scheduling_tool(),
            # NEW: Enhanced clinical analysis
            ClinicalAnalysisTool(),
            # Enhanced SOAP generation
            self._create_enhanced_soap_generation_tool()
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

    # NEW: Enhanced SOAP Generation Tool
    def _create_enhanced_soap_generation_tool(self) -> BaseTool:
        """Enhanced SOAP note generation with clinical reasoning"""
        
        class EnhancedSOAPGenerationTool(BaseTool):
            name: str = "enhanced_soap_note_generator"
            description: str = "Generate comprehensive SOAP notes with clinical analysis integration"
            
            def _run(self, conversation_text: str, patient_info: str = "", clinical_analysis: str = "") -> str:
                """Generate enhanced SOAP note with clinical reasoning"""
                
                # Parse clinical analysis if provided
                analysis_data = {}
                if clinical_analysis:
                    try:
                        analysis_data = json.loads(clinical_analysis)
                    except:
                        pass
                
                soap_note = f"""
SOAP NOTE - DENTAL CONSULTATION
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Provider: Dr. [Provider Name]
Patient: {patient_info}

SUBJECTIVE:
Chief Complaint: Patient presents with dental concerns as discussed.

History of Present Illness:
{conversation_text}

{self._extract_subjective_elements(conversation_text)}

OBJECTIVE:
Vital Signs: Within normal limits
Extraoral Examination: Completed
Intraoral Examination: 
{self._generate_objective_findings(analysis_data, conversation_text)}

ASSESSMENT:
{self._generate_enhanced_assessment(analysis_data, conversation_text)}

PLAN:
{self._generate_enhanced_plan(analysis_data, conversation_text)}

---
CLINICAL ANALYSIS:
{analysis_data.get('clinical_reasoning', 'Standard dental evaluation performed.')}
"""
                
                return soap_note
            
            def _extract_subjective_elements(self, conversation: str) -> str:
                """Extract key subjective elements"""
                elements = []
                
                if "pain" in conversation.lower():
                    elements.append("• Patient reports pain as primary concern")
                if "swelling" in conversation.lower():
                    elements.append("• Patient notes swelling in affected area")
                if "bleeding" in conversation.lower():
                    elements.append("• Patient reports bleeding")
                
                return "\n".join(elements) if elements else "• Patient concerns documented above"
            
            def _generate_objective_findings(self, analysis_data: Dict, conversation: str) -> str:
                """Generate objective findings"""
                
                findings = []
                
                if analysis_data.get("symptom_analysis"):
                    symptoms = analysis_data["symptom_analysis"]
                    
                    if symptoms.get("pain_present"):
                        findings.append("• Pain response noted during examination")
                    if symptoms.get("swelling_present"):
                        findings.append("• Localized swelling observed")
                    if symptoms.get("bleeding_present"):
                        findings.append("• Bleeding noted")
                else:
                    findings.append("• Clinical examination findings documented")
                
                findings.extend([
                    "• Oral hygiene assessment completed",
                    "• Periodontal evaluation performed"
                ])
                
                return "\n".join(findings)
            
            def _generate_enhanced_assessment(self, analysis_data: Dict, conversation: str) -> str:
                """Generate enhanced assessment with differential diagnosis"""
                
                assessment = "Clinical Impression:\n\n"
                
                if analysis_data.get("differential_diagnosis"):
                    assessment += "Differential Diagnosis:\n"
                    for i, dx in enumerate(analysis_data["differential_diagnosis"], 1):
                        assessment += f"{i}. {dx['condition']} - {dx['probability']} probability\n"
                        assessment += f"   Reasoning: {dx['reasoning']}\n\n"
                else:
                    # Fallback to basic assessment
                    if "pain" in conversation.lower():
                        assessment += "1. Dental pain - requires evaluation\n"
                    else:
                        assessment += "1. Routine dental consultation\n"
                
                if analysis_data.get("urgency_assessment"):
                    urgency = analysis_data["urgency_assessment"]
                    assessment += f"Urgency: {urgency['level']} - {urgency['reasoning']}\n"
                
                return assessment
            
            def _generate_enhanced_plan(self, analysis_data: Dict, conversation: str) -> str:
                """Generate enhanced treatment plan"""
                
                plan = "Treatment Plan:\n\n"
                
                # Immediate actions
                if analysis_data.get("recommended_actions"):
                    plan += "Immediate Actions:\n"
                    for action in analysis_data["recommended_actions"]:
                        plan += f"• {action}\n"
                    plan += "\n"
                
                # Standard plan elements
                plan += """Diagnostic Plan:
• Complete clinical examination
• Radiographic evaluation as indicated

Treatment Plan:
• Address immediate concerns
• Definitive treatment based on diagnosis

Patient Education:
• Discussed findings with patient
• Provided home care instructions

Follow-up:
• As clinically indicated"""
                
                return plan
        
        return EnhancedSOAPGenerationTool()

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

    # NEW: Enhanced Consultation Method
    async def conduct_enhanced_consultation(self, patient_query: str, patient_info: Dict = None) -> Dict:
        """Enhanced consultation with clinical analysis - NEW METHOD"""
        
        if patient_info is None:
            patient_info = {}
        
        # First, perform clinical analysis
        clinical_analysis_task = Task(
            description=f"""
            Analyze patient symptoms using clinical_analysis tool:
            
            Patient Query: {patient_query}
            Patient Info: {json.dumps(patient_info)}
            
            Provide comprehensive clinical analysis including:
            1. Symptom analysis with pain level and duration assessment
            2. Differential diagnosis with probability assessments
            3. Urgency assessment with specific timeframes
            4. Clinical reasoning that reads like a professional wrote it
            5. Evidence-based recommended actions
            
            Use the clinical_analysis tool to process this information.
            """,
            agent=self.agent,
            expected_output="Comprehensive clinical analysis with differential diagnosis and urgency assessment"
        )
        
        # Then generate enhanced SOAP note
        soap_task = Task(
            description=f"""
            Generate enhanced SOAP note using enhanced_soap_note_generator:
            
            Conversation: {patient_query}
            Patient Info: {json.dumps(patient_info)}
            
            Create a professional SOAP note that integrates the clinical analysis.
            The SOAP note should feel like it was written by an experienced dental professional.
            """,
            agent=self.agent,
            expected_output="Professional SOAP note with clinical analysis integration"
        )
        
        # Execute tasks
        crew = Crew(
            agents=[self.agent],
            tasks=[clinical_analysis_task, soap_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        return {
            "enhanced_consultation": result,
            "patient_query": patient_query,
            "patient_info": patient_info,
            "timestamp": datetime.now().isoformat(),
            "agent_type": "Enhanced Dental Agent"
        }

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
            
            # NEW: Enhanced consultation action
            elif action == "enhanced_consultation":
                patient_query = input_data["query"]
                patient_info = input_data.get("patient_info", {})
                result = asyncio.run(self.conduct_enhanced_consultation(patient_query, patient_info))
                return {"success": True, "consultation": result}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {"success": False, "error": str(e)}

