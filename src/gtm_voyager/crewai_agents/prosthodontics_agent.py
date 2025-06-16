"""
GTM Voyager Platform - Prosthodontics Specialist Agent
AI-powered prosthodontic practice automation with specialized documentation.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool


class ProsthodonticProcedureType(Enum):
    """Types of prosthodontic procedures"""
    CROWN = "crown"
    BRIDGE = "bridge"
    IMPLANT = "implant"
    DENTURE_FULL = "denture_full"
    DENTURE_PARTIAL = "denture_partial"
    VENEER = "veneer"
    INLAY_ONLAY = "inlay_onlay"
    RECONSTRUCTION = "full_mouth_reconstruction"


@dataclass
class ProsthodonticCase:
    """Prosthodontic case information"""
    case_id: str
    patient_id: str
    procedure_type: ProsthodonticProcedureType
    teeth_involved: List[str]
    materials_planned: List[str]
    lab_work_required: bool
    estimated_appointments: int
    treatment_phases: List[str]
    cost_estimate: float
    insurance_coverage: Optional[float]


@dataclass
class ProsthodonticSOAP:
    """Specialized SOAP note for prosthodontics"""
    patient_id: str
    date: datetime
    provider: str
    procedure_type: ProsthodonticProcedureType
    
    # SOAP Components
    subjective: str
    objective: str
    assessment: str
    plan: str
    
    # Prosthodontic-specific fields
    teeth_involved: List[str]
    existing_restorations: List[str]
    occlusion_notes: str
    esthetics_concerns: str
    materials_discussed: List[str]
    lab_instructions: str
    follow_up_schedule: List[str]
    
    # Treatment planning
    treatment_phases: List[str]
    appointment_sequence: List[str]
    cost_breakdown: Dict[str, float]
    
    # Quality metrics
    confidence_score: float
    requires_review: bool
    generated_timestamp: datetime


class ProsthodonticsAgent:
    """
    Prosthodontics specialist agent for complex restorative cases.
    Handles specialized documentation, treatment planning, and case management.
    """
    
    def __init__(self):
        self.agent = self._create_prosthodontics_agent()
        self.conversation_buffer = []
        self.current_patient = None
        self.current_provider = None
        self.current_case = None
        self.is_recording = False
        
    def _create_prosthodontics_agent(self) -> Agent:
        """Create the specialized prosthodontics agent"""
        return Agent(
            role="AI Prosthodontics Specialist Assistant",
            goal="Automate prosthodontic practice workflows including complex case documentation, treatment planning, lab communication, and specialized SOAP note generation for restorative dentistry",
            backstory="""You are an expert prosthodontic practice assistant with extensive knowledge of restorative 
            dentistry, crown and bridge work, dental implants, dentures, cosmetic dentistry, and full mouth 
            rehabilitation. You understand complex treatment planning, occlusion, esthetics, dental materials, 
            laboratory procedures, and multi-phase treatment sequencing. You can document detailed conversations 
            between prosthodontists and patients, extract complex clinical information, organize it into specialized 
            SOAP notes, and assist with treatment planning and case management.""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_prosthodontic_soap_tool(),
                self._create_prosthodontic_terminology_tool(),
                self._create_prosthodontic_codes_tool(),
                self._create_treatment_planning_tool(),
                self._create_lab_communication_tool()
            ]
        )

    def _create_prosthodontic_soap_tool(self) -> BaseTool:
        """Tool for generating specialized prosthodontic SOAP notes"""
        class ProsthodonticSOAPTool(BaseTool):
            name: str = "prosthodontic_soap_generator"
            description: str = "Generate specialized SOAP notes for prosthodontic procedures and complex restorative cases"
            
            def _run(self, conversation_text: str, patient_info: str, provider_name: str, procedure_type: str) -> str:
                """Generate prosthodontic SOAP note from conversation"""
                prompt = f"""
                Convert the following prosthodontic consultation into a specialized SOAP note format:
                
                Patient Information: {patient_info}
                Provider: {provider_name}
                Procedure Type: {procedure_type}
                Conversation: {conversation_text}
                
                Generate a detailed prosthodontic SOAP note with:
                
                SUBJECTIVE:
                - Chief complaint and esthetic concerns
                - Functional problems (chewing, speaking)
                - Previous dental history and failed restorations
                - Patient expectations and preferences
                
                OBJECTIVE:
                - Clinical examination findings
                - Existing restorations and their condition
                - Occlusion analysis
                - Periodontal status
                - Radiographic findings
                - Impressions and models evaluation
                
                ASSESSMENT:
                - Diagnosis of prosthodontic needs
                - Prognosis for proposed treatment
                - Risk factors and complications
                - Esthetic and functional analysis
                
                PLAN:
                - Detailed treatment sequence
                - Materials and techniques planned
                - Laboratory requirements
                - Number of appointments needed
                - Cost estimates and insurance considerations
                - Alternative treatment options
                
                Include specific prosthodontic terminology, CDT codes, and material specifications.
                """
                
                return self._process_with_ai(prompt)
            
            def _process_with_ai(self, prompt: str) -> str:
                """Process with AI model - integrate with your OpenAI setup"""
                # TODO: Connect to your existing OpenAI integration
                return "Generated specialized prosthodontic SOAP note content"
        
        return ProsthodonticSOAPTool()

    def _create_prosthodontic_terminology_tool(self) -> BaseTool:
        """Tool for prosthodontic terminology and materials reference"""
        class ProsthodonticTerminologyTool(BaseTool):
            name: str = "prosthodontic_terminology"
            description: str = "Look up prosthodontic terminology, materials, and procedure definitions"
            
            def _run(self, term: str) -> str:
                """Look up prosthodontic terminology"""
                prosthodontic_terms = {
                    # Procedures
                    "crown": "Full coverage restoration covering entire clinical crown",
                    "bridge": "Fixed partial denture replacing missing teeth",
                    "implant": "Titanium fixture placed in bone to replace tooth root",
                    "veneer": "Thin shell covering facial surface of tooth",
                    "inlay": "Intracoronal restoration within tooth cusps",
                    "onlay": "Restoration covering one or more cusps",
                    "maryland bridge": "Resin-bonded bridge with minimal tooth preparation",
                    
                    # Materials
                    "zirconia": "High-strength ceramic material for crowns and bridges",
                    "lithium disilicate": "Glass-ceramic material for esthetic restorations",
                    "pfm": "Porcelain-fused-to-metal restoration",
                    "emax": "Lithium disilicate ceramic system",
                    "bruxzir": "Solid zirconia restoration material",
                    "lava": "3M zirconia crown system",
                    
                    # Techniques
                    "prep": "Tooth preparation for restoration",
                    "impression": "Negative reproduction of teeth and tissues",
                    "provisional": "Temporary restoration during treatment",
                    "cementation": "Final placement of restoration",
                    "occlusal adjustment": "Modification of biting surfaces",
                    
                    # Anatomy/Conditions
                    "occlusion": "Contact relationship between upper and lower teeth",
                    "centric relation": "Most retruded position of mandible",
                    "vertical dimension": "Height of face when teeth are in contact",
                    "freeway space": "Space between teeth at rest position",
                    "bruxism": "Grinding or clenching of teeth",
                    "attrition": "Wear from tooth-to-tooth contact",
                    "abrasion": "Wear from external substances",
                    
                    # Laboratory
                    "die": "Positive reproduction of prepared tooth",
                    "articulator": "Device simulating jaw movements",
                    "wax-up": "Wax pattern of proposed restoration",
                    "try-in": "Fitting appointment for restoration",
                    "shade matching": "Color selection for restoration"
                }
                return prosthodontic_terms.get(term.lower(), f"Prosthodontic term '{term}' not found in database")
        
        return ProsthodonticTerminologyTool()

    def _create_prosthodontic_codes_tool(self) -> BaseTool:
        """Tool for prosthodontic procedure codes and billing"""
        class ProsthodonticCodesTool(BaseTool):
            name: str = "prosthodontic_codes"
            description: str = "Look up CDT codes specific to prosthodontic procedures"
            
            def _run(self, procedure: str) -> str:
                """Look up prosthodontic procedure codes"""
                prosthodontic_codes = {
                    # Crowns
                    "porcelain crown": "D2740 - Crown - Porcelain/Ceramic",
                    "pfm crown": "D2750 - Crown - Porcelain Fused to Metal",
                    "gold crown": "D2790 - Crown - Full Cast Metal",
                    "zirconia crown": "D2740 - Crown - Porcelain/Ceramic",
                    "temporary crown": "D2799 - Provisional Crown",
                    
                    # Bridges
                    "porcelain bridge": "D6240 - Pontic - Porcelain/Ceramic",
                    "pfm bridge": "D6250 - Pontic - Porcelain Fused to Metal",
                    "maryland bridge": "D6545 - Retainer - Metal for Resin Bonded Fixed Prosthesis",
                    "bridge abutment": "D6740 - Retainer Crown - Porcelain/Ceramic",
                    
                    # Implants
                    "implant placement": "D6010 - Surgical Placement of Implant",
                    "implant crown": "D6058 - Abutment Supported Porcelain/Ceramic Crown",
                    "implant abutment": "D6056 - Prefabricated Abutment",
                    "custom abutment": "D6057 - Custom Abutment",
                    
                    # Veneers
                    "porcelain veneer": "D2962 - Labial Veneer - Porcelain Laminate",
                    "composite veneer": "D2961 - Labial Veneer - Resin Laminate",
                    
                    # Inlays/Onlays
                    "porcelain inlay": "D2510 - Inlay - Metallic, One Surface",
                    "porcelain onlay": "D2542 - Onlay - Metallic, Two Surfaces",
                    "gold inlay": "D2510 - Inlay - Metallic, One Surface",
                    "gold onlay": "D2542 - Onlay - Metallic, Two Surfaces",
                    
                    # Dentures
                    "complete denture": "D5110 - Complete Denture - Maxillary",
                    "partial denture": "D5213 - Maxillary Partial Denture - Cast Metal Framework",
                    "immediate denture": "D5130 - Immediate Denture - Maxillary",
                    "denture reline": "D5720 - Reline Complete Maxillary Denture",
                    "denture repair": "D5510 - Repair Broken Complete Denture Base",
                    
                    # Specialized Procedures
                    "full mouth reconstruction": "Multiple codes - comprehensive treatment",
                    "occlusal adjustment": "D9951 - Occlusal Adjustment - Limited",
                    "night guard": "D9944 - Occlusal Guard - Hard Appliance",
                    "tissue conditioning": "D5850 - Tissue Conditioning - Maxillary",
                    
                    # Laboratory Procedures
                    "lab reline": "D5751 - Reline Complete Maxillary Denture (Laboratory)",
                    "lab repair": "D5520 - Replace Missing or Broken Teeth (Laboratory)"
                }
                return prosthodontic_codes.get(procedure.lower(), f"Prosthodontic code for '{procedure}' not found")
        
        return ProsthodonticCodesTool()

    def _create_treatment_planning_tool(self) -> BaseTool:
        """Tool for complex prosthodontic treatment planning"""
        class TreatmentPlanningTool(BaseTool):
            name: str = "treatment_planning"
            description: str = "Create detailed treatment plans for complex prosthodontic cases"
            
            def _run(self, case_type: str, teeth_involved: str, patient_factors: str) -> str:
                """Generate treatment plan based on case complexity"""
                
                treatment_templates = {
                    "single_crown": {
                        "phases": ["Consultation", "Preparation", "Impression", "Temporary", "Delivery"],
                        "appointments": 3,
                        "timeline": "2-3 weeks",
                        "considerations": ["Occlusion", "Esthetics", "Material selection"]
                    },
                    
                    "bridge_3_unit": {
                        "phases": ["Consultation", "Preparation", "Impression", "Try-in", "Delivery"],
                        "appointments": 4,
                        "timeline": "3-4 weeks",
                        "considerations": ["Abutment health", "Pontic design", "Occlusion", "Hygiene access"]
                    },
                    
                    "implant_crown": {
                        "phases": ["Consultation", "Implant placement", "Healing", "Impression", "Crown delivery"],
                        "appointments": 5,
                        "timeline": "3-6 months",
                        "considerations": ["Bone quality", "Soft tissue", "Esthetics", "Emergence profile"]
                    },
                    
                    "full_mouth_reconstruction": {
                        "phases": ["Comprehensive exam", "Mounting", "Wax-up", "Provisional phase", "Final restorations"],
                        "appointments": 12-15,
                        "timeline": "6-12 months",
                        "considerations": ["VDO", "Centric relation", "Esthetics", "Function", "TMJ health"]
                    },
                    
                    "veneer_case": {
                        "phases": ["Consultation", "Preparation", "Impression", "Try-in", "Bonding"],
                        "appointments": 4,
                        "timeline": "2-3 weeks",
                        "considerations": ["Tooth reduction", "Shade matching", "Gingival health", "Occlusion"]
                    }
                }
                
                template = treatment_templates.get(case_type.lower(), {
                    "phases": ["Consultation", "Treatment", "Follow-up"],
                    "appointments": 3,
                    "timeline": "2-4 weeks",
                    "considerations": ["Patient factors", "Clinical complexity"]
                })
                
                return f"""
                Treatment Plan for {case_type}:
                
                Teeth Involved: {teeth_involved}
                Patient Factors: {patient_factors}
                
                Treatment Phases: {', '.join(template['phases'])}
                Estimated Appointments: {template['appointments']}
                Timeline: {template['timeline']}
                Key Considerations: {', '.join(template['considerations'])}
                
                Recommended next steps:
                1. Complete diagnostic records
                2. Treatment planning consultation
                3. Insurance pre-authorization if needed
                4. Schedule first treatment appointment
                """
        
        return TreatmentPlanningTool()

    def _create_lab_communication_tool(self) -> BaseTool:
        """Tool for dental laboratory communication and instructions"""
        class LabCommunicationTool(BaseTool):
            name: str = "lab_communication"
            description: str = "Generate detailed laboratory instructions and case communication"
            
            def _run(self, procedure_type: str, specifications: str, special_instructions: str) -> str:
                """Generate lab instructions based on procedure type"""
                
                lab_templates = {
                    "crown": {
                        "materials": ["Zirconia", "Lithium Disilicate", "PFM", "Gold"],
                        "instructions": [
                            "Margin location and finish line",
                            "Shade and characterization",
                            "Occlusal contacts and clearance",
                            "Emergence profile",
                            "Surface texture"
                        ]
                    },
                    
                    "bridge": {
                        "materials": ["Zirconia", "PFM", "Metal Framework"],
                        "instructions": [
                            "Abutment preparation margins",
                            "Pontic design and tissue contact",
                            "Connector size and location",
                            "Occlusal scheme",
                            "Embrasure form"
                        ]
                    },
                    
                    "veneer": {
                        "materials": ["Lithium Disilicate", "Feldspathic Porcelain"],
                        "instructions": [
                            "Preparation depth and design",
                            "Shade matching and translucency",
                            "Incisal edge design",
                            "Surface texture and characterization",
                            "Try-in paste compatibility"
                        ]
                    },
                    
                    "implant_crown": {
                        "materials": ["Zirconia", "Lithium Disilicate", "PFM"],
                        "instructions": [
                            "Abutment type and angulation",
                            "Emergence profile design",
                            "Screw vs cement retention",
                            "Tissue level considerations",
                            "Occlusal contacts"
                        ]
                    },
                    
                    "partial_denture": {
                        "materials": ["Cast Metal Framework", "Flexible Resin", "Acrylic"],
                        "instructions": [
                            "Framework design and clasping",
                            "Rest seat preparation",
                            "Tissue support areas",
                            "Retention and stability",
                            "Esthetic considerations"
                        ]
                    }
                }
                
                template = lab_templates.get(procedure_type.lower(), {
                    "materials": ["Standard materials"],
                    "instructions": ["Standard laboratory procedures"]
                })
                
                return f"""
                LABORATORY PRESCRIPTION
                
                Procedure: {procedure_type.upper()}
                Patient Specifications: {specifications}
                
                MATERIAL OPTIONS:
                {chr(10).join([f"• {material}" for material in template['materials']])}
                
                LABORATORY INSTRUCTIONS:
                {chr(10).join([f"• {instruction}" for instruction in template['instructions']])}
                
                SPECIAL INSTRUCTIONS:
                {special_instructions}
                
                DELIVERY REQUIREMENTS:
                • Quality control check
                • Shade verification
                • Fit and finish inspection
                • Delivery timeline coordination
                
                Please contact office with any questions regarding this case.
                """
        
        return LabCommunicationTool()

    def start_prosthodontic_consultation(self, patient_info: dict, provider_name: str, procedure_type: str):
        """Start recording prosthodontic consultation"""
        self.current_patient = patient_info
        self.current_provider = provider_name
        self.conversation_buffer = []
        self.is_recording = True
        
        # Create case record
        self.current_case = ProsthodonticCase(
            case_id=f"PROS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            patient_id=patient_info.get('patient_id', ''),
            procedure_type=ProsthodonticProcedureType(procedure_type.lower()),
            teeth_involved=[],
            materials_planned=[],
            lab_work_required=True,
            estimated_appointments=3,
            treatment_phases=[],
            cost_estimate=0.0,
            insurance_coverage=None
        )
        
        return f"Started prosthodontic consultation for {patient_info.get('name')} - {procedure_type} case"
    
    def stop_consultation(self):
        """Stop recording consultation"""
        self.is_recording = False
        return "Prosthodontic consultation recording stopped"
    
    def add_conversation_text(self, text: str):
        """Add conversation text to buffer"""
        if self.is_recording:
            timestamp = datetime.now()
            self.conversation_buffer.append({
                "timestamp": timestamp,
                "text": text
            })
    
    def generate_prosthodontic_soap(self) -> ProsthodonticSOAP:
        """Generate specialized prosthodontic SOAP note"""
        if not self.conversation_buffer:
            raise ValueError("No consultation recorded")
        
        conversation_text = " ".join([item["text"] for item in self.conversation_buffer])
        
        # Use the prosthodontic SOAP generation tool
        soap_content = self.agent.tools[0]._run(
            conversation_text=conversation_text,
            patient_info=f"{self.current_patient.get('name')}, Age: {self.current_patient.get('age')}",
            provider_name=self.current_provider,
            procedure_type=self.current_case.procedure_type.value
        )
        
        # Create specialized prosthodontic SOAP note
        prosthodontic_soap = ProsthodonticSOAP(
            patient_id=self.current_patient.get('patient_id', ''),
            date=datetime.now(),
            provider=self.current_provider,
            procedure_type=self.current_case.procedure_type,
            subjective="Patient chief complaint and esthetic concerns",
            objective="Clinical examination and diagnostic findings",
            assessment="Prosthodontic diagnosis and treatment recommendations",
            plan="Detailed treatment plan and material selection",
            teeth_involved=self.current_case.teeth_involved,
            existing_restorations=[],
            occlusion_notes="Occlusal analysis findings",
            esthetics_concerns="Patient esthetic requirements",
            materials_discussed=self.current_case.materials_planned,
            lab_instructions="Laboratory communication requirements",
            follow_up_schedule=[],
            treatment_phases=self.current_case.treatment_phases,
            appointment_sequence=[],
            cost_breakdown={},
            confidence_score=0.90,
            requires_review=True,
            generated_timestamp=datetime.now()
        )
        
        return prosthodontic_soap
    
    def generate_lab_prescription(self, procedure_type: str, specifications: str, special_instructions: str = ""):
        """Generate laboratory prescription and instructions"""
        return self.agent.tools[4]._run(
            procedure_type=procedure_type,
            specifications=specifications,
            special_instructions=special_instructions
        )
    
    def create_treatment_plan(self, case_type: str, teeth_involved: str, patient_factors: str):
        """Create detailed prosthodontic treatment plan"""
        return self.agent.tools[3]._run(
            case_type=case_type,
            teeth_involved=teeth_involved,
            patient_factors=patient_factors
        )

