"""
Test script for Multi-Industry Agent Router
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_industry_router():
    """Test the Multi-Industry Agent Router"""
    print("🚀 Testing GTM Voyager Multi-Industry Agent Router")
    print("=" * 60)
    
    try:
        # Import the router and required types
        from gtm_voyager.crewai_agents.industry_agent_router import (
            IndustryAgentRouter, 
            IndustryType,
            UserProfile
        )
        print("✅ Router module imported successfully!")
        
        # Initialize router
        print("\n🔍 Initializing router...")
        router = IndustryAgentRouter()
        print("✅ Router initialized")
        
        # Test agent access
        print("\n🔍 Testing agent access...")
        dental_agent = router.get_agent(IndustryType.DENTAL_GENERAL)
        prostho_agent = router.get_agent(IndustryType.DENTAL_PROSTHODONTICS)
        
        if dental_agent:
            print("✅ Dental agent accessed successfully")
        else:
            print("❌ Failed to access dental agent")
            
        if prostho_agent:
            print("✅ Prosthodontics agent accessed successfully")
        else:
            print("❌ Failed to access prosthodontics agent")
        
        # Test user profile creation
        print("\n🔍 Testing user profile management...")
        test_user = router.create_user_profile(
            user_id="test123",
            name="Test User",
            primary_industry=IndustryType.DENTAL_GENERAL
        )
        print(f"✅ Created user profile for {test_user.name}")
        
        # Test routing with different commands
        print("\n🔍 Testing voice command routing...")
        
        # Test dental command
        dental_command = "Schedule a cleaning appointment for patient John Smith"
        dental_result = router.route_voice_command(dental_command, test_user)
        print(f"Dental command routed to: {dental_result.selected_agent} (confidence: {dental_result.confidence_score:.2f})")
        print(f"Context detected: {dental_result.context_detected}")
        
        # Test prosthodontic command
        prostho_command = "Create a treatment plan for porcelain crown on tooth 14"
        prostho_result = router.route_voice_command(prostho_command, test_user)
        print(f"Prosthodontic command routed to: {prostho_result.selected_agent} (confidence: {prostho_result.confidence_score:.2f})")
        print(f"Context detected: {prostho_result.context_detected}")
        
        # Test explicit mode switch
        switch_command = "switch to prosthodontics mode"
        switch_result = router.route_voice_command(switch_command, test_user)
        print(f"Mode switch command routed to: {switch_result.selected_agent} (confidence: {switch_result.confidence_score:.2f})")
        print(f"Routing reason: {switch_result.routing_reason}")
        
        # Test full processing
        print("\n🔍 Testing full command processing...")
        process_result = router.process_voice_command("test123", "Check patient history for cavities")
        print(f"Processing result: {process_result['status']}")
        print(f"Selected agent: {process_result['selected_agent']}")
        
        # Test edge cases
        print("\n🔍 Testing edge cases...")
        
        # Test ambiguous command
        ambiguous_command = "I need to schedule something"
        ambiguous_result = router.route_voice_command(ambiguous_command, test_user)
        print(f"Ambiguous command routed to: {ambiguous_result.selected_agent} (confidence: {ambiguous_result.confidence_score:.2f})")
        print(f"Routing reason: {ambiguous_result.routing_reason}")
        
        # Test industry switching
        print("\n🔍 Testing industry switching...")
        test_user.current_mode = IndustryType.DENTAL_PROSTHODONTICS
        switch_back_command = "switch to dental mode"
        switch_back_result = router.route_voice_command(switch_back_command, test_user)
        print(f"Mode switched to: {switch_back_result.selected_agent}")
        print(f"Current user mode: {test_user.current_mode.value}")
        
        print("\n🎉 All tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_industry_router()
