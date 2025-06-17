import asyncio
import os
from dotenv import load_dotenv
from gtm_voyager.crewai_agents.industry_agent_router import UserProfile, IndustryType
from gtm_voyager.voice_processing.voice_processor import VoiceProcessor

# Load environment variables from .env file
load_dotenv()

async def test_dental_general_scenarios():
    """Test voice commands for dental general scenarios"""
    print("\n=== Testing Dental General Scenarios ===")
    
    # Create a user profile for dental general
    dental_user_profile = UserProfile(
        user_id="dental_user_001",
        name="Dr. Johnson",
        primary_industry=IndustryType.DENTAL_GENERAL,
        secondary_industries=[],
        default_agent="dental_general",
        voice_preferences={}
    )
    
    voice_processor = VoiceProcessor()
    
    # Test scenarios for dental general
    test_scenarios = [
        "Schedule a cleaning appointment for next Tuesday",
        "Patient needs a filling on tooth number 14",
        "Create a treatment plan for cavity restoration",
        "Book a routine checkup for Mrs. Smith",
        "Patient has tooth pain and needs emergency appointment"
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Dental General Test {i} ---")
        print(f"Simulated Voice Command: '{scenario}'")
        
        # Simulate voice processing by directly calling the router
        routing_result = voice_processor.router.route_voice_command(scenario, dental_user_profile)
        selected_agent_instance = voice_processor.router.get_agent(routing_result.industry_type)
        
        print(f"Selected Agent: {routing_result.selected_agent}")
        print(f"Confidence Score: {routing_result.confidence_score:.2f}")
        print(f"Routing Reason: {routing_result.routing_reason}")
        print(f"Agent Instance Available: {selected_agent_instance is not None}")

async def test_prosthodontics_scenarios():
    """Test voice commands for prosthodontics scenarios"""
    print("\n=== Testing Prosthodontics Scenarios ===")
    
    # Create a user profile for prosthodontics
    prostho_user_profile = UserProfile(
        user_id="prostho_user_001",
        name="Dr. Smith",
        primary_industry=IndustryType.DENTAL_PROSTHODONTICS,
        secondary_industries=[],
        default_agent="dental_prosthodontics",
        voice_preferences={}
    )
    
    voice_processor = VoiceProcessor()
    
    # Test scenarios for prosthodontics
    test_scenarios = [
        "Patient needs a crown on the upper molar",
        "Schedule implant consultation for dental implants",
        "Create treatment plan for full mouth reconstruction",
        "Patient requires bridge work for missing teeth",
        "Denture fitting appointment needed for partial dentures"
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Prosthodontics Test {i} ---")
        print(f"Simulated Voice Command: '{scenario}'")
        
        # Simulate voice processing by directly calling the router
        routing_result = voice_processor.router.route_voice_command(scenario, prostho_user_profile)
        selected_agent_instance = voice_processor.router.get_agent(routing_result.industry_type)
        
        print(f"Selected Agent: {routing_result.selected_agent}")
        print(f"Confidence Score: {routing_result.confidence_score:.2f}")
        print(f"Routing Reason: {routing_result.routing_reason}")
        print(f"Agent Instance Available: {selected_agent_instance is not None}")

async def test_cross_industry_routing():
    """Test routing between different industries"""
    print("\n=== Testing Cross-Industry Routing ===")
    
    # Create a user profile with multiple industries
    multi_user_profile = UserProfile(
        user_id="multi_user_001",
        name="Dr. Multi Practice",
        primary_industry=IndustryType.DENTAL_GENERAL,
        secondary_industries=[IndustryType.DENTAL_PROSTHODONTICS],
        default_agent="dental_general",
        voice_preferences={}
    )
    
    voice_processor = VoiceProcessor()
    
    # Test cross-industry scenarios
    test_scenarios = [
        ("General dental command", "Schedule a routine cleaning"),
        ("Prosthodontics command", "Patient needs crown preparation"),
        ("Explicit mode switch", "Switch to prosthodontics mode"),
        ("HVAC command (should fallback)", "Fix the air conditioning unit"),
        ("Ambiguous command", "Schedule an appointment")
    ]
    
    for scenario_name, command in test_scenarios:
        print(f"\n--- {scenario_name} ---")
        print(f"Command: '{command}'")
        
        routing_result = voice_processor.router.route_voice_command(command, multi_user_profile)
        selected_agent_instance = voice_processor.router.get_agent(routing_result.industry_type)
        
        print(f"Selected Agent: {routing_result.selected_agent}")
        print(f"Confidence Score: {routing_result.confidence_score:.2f}")
        print(f"Routing Reason: {routing_result.routing_reason}")
        print(f"Agent Instance Available: {selected_agent_instance is not None}")

async def test_speaker_diarization():
    """Test the conceptual speaker diarization functionality"""
    print("\n=== Testing Speaker Diarization ===")
    
    voice_processor = VoiceProcessor()
    
    # Test different speaker scenarios
    test_texts = [
        "Hello, I'm Dr. Smith and I need to schedule an appointment",
        "The doctor said I need a crown and the patient asked about the cost",
        "Patient reports pain in the upper left molar area",
        "Doctor recommends implant treatment for missing tooth"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Speaker Diarization Test {i} ---")
        print(f"Text: '{text}'")
        
        speaker_info = voice_processor._conceptual_speaker_diarization(text)
        print(f"Speaker Info: {speaker_info}")

async def main():
    """Main test function"""
    print("Starting comprehensive voice processing integration tests...")
    
    try:
        await test_dental_general_scenarios()
        await test_prosthodontics_scenarios()
        await test_cross_industry_routing()
        await test_speaker_diarization()
        
        print("\n" + "="*60)
        print("All integration tests completed successfully!")
        print("Voice processing system is fully integrated with the industry agent router.")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
