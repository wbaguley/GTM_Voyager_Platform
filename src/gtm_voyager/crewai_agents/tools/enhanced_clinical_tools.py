"""
Enhanced Clinical Analysis Tools for GTM Voyager Dental Agent
"""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from crewai_tools import BaseTool

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
        duration_category = self._categorize_duration(duration)
        
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
    
    def _categorize_duration(self, duration: str) -> str:
        """Categorize symptom duration"""
        if not duration:
            # Try to extract from symptoms
            symptoms_lower = self.raw_symptoms.lower() if hasattr(self, 'raw_symptoms') else ""
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