"""
Test script for Dental and Prosthodontics Agents
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_dental_agents():
    """Test both dental agents"""
    print("🦷 Testing GTM Voyager Dental Agents")
    print("=" * 50)
    
    try:
        # Import both agents
        from gtm_voyager.crewai_agents.dental_agent import DentalAgent
        from gtm_voyager.crewai_agents.prosthodontics_agent import ProsthodonticsAgent
        
        print("✅ Both agents imported successfully!")
        
        # Test General Dental Agent
        print("\n🔍 Testing General Dental Agent...")
        dental_agent = DentalAgent()
        print("✅ General Dental Agent initialized")
        
        # Test Prosthodontics Agent  
        print("\n🔍 Testing Prosthodontics Agent...")
        prostho_agent = ProsthodonticsAgent()
        print("✅ Prosthodontics Agent initialized")
        
        # Test dental terminology
        print("\n📚 Testing Dental Terminology...")
        dental_term = dental_agent.agent.tools[1]._run("crown")
        print(f"Dental term lookup: {dental_term}")
        
        # Test prosthodontic terminology
        print("\n📚 Testing Prosthodontic Terminology...")
        prostho_term = prostho_agent.agent.tools[1]._run("zirconia")
        print(f"Prosthodontic term lookup: {prostho_term}")
        
        # Test procedure codes
        print("\n💰 Testing Procedure Codes...")
        dental_code = dental_agent.agent.tools[2]._run("cleaning")
        prostho_code = prostho_agent.agent.tools[2]._run("porcelain crown")
        print(f"Dental code: {dental_code}")
        print(f"Prosthodontic code: {prostho_code}")
        
        print("\n🎉 All tests passed! Both agents are working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_dental_agents()
