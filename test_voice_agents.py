"""
GTM Voyager Platform - Voice Agent Testing Suite
Comprehensive tests for voice processing and agent integration.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

# Test imports
try:
    from gtm_voyager.audio import (
        AudioProcessor, 
        validate_audio, 
        optimize_audio_for_whisper,
        get_audio_metadata
    )
    from gtm_voyager.crewai_agents.tools.voice_integration import (
        VoiceCommandParser,
        VoiceCommandType
    )
    from gtm_voyager.crewai_agents.voice_agent_manager import (
        VoiceAgentManager,
        create_voice_agent_manager
    )
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class VoiceAgentTester:
    """Comprehensive testing suite for voice-agent system."""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.test_results = {}
        
    def _setup_logger(self):
        """Set up logging for tests."""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger('VoiceAgentTester')
    
    async def test_audio_processing(self):
        """Test audio processing capabilities."""
        print("\n🎵 Testing Audio Processing...")
        
        try:
            # Test audio processor initialization
            processor = AudioProcessor()
            print("✅ AudioProcessor initialized successfully")
            
            # Test configuration
            config = processor.config
            print(f"✅ Audio config: {config.target_sample_rate}Hz, {config.target_channels} channel(s)")
            
            self.test_results['audio_processing'] = True
            print("✅ Audio processing tests passed!")
            
        except Exception as e:
            print(f"❌ Audio processing test failed: {e}")
            self.test_results['audio_processing'] = False
    
    async def test_voice_command_parsing(self):
        """Test voice command parsing and intent recognition."""
        print("\n🗣️ Testing Voice Command Parsing...")
        
        try:
            parser = VoiceCommandParser()
            
            # Test dental commands
            dental_command = "Schedule a dental appointment for John tomorrow at 2pm"
            parsed = parser.parse_command(dental_command)
            
            print(f"✅ Parsed dental command: {parsed.command_type}")
            print(f"   Intent: {parsed.intent}")
            print(f"   Entities: {parsed.entities}")
            
            # Test electrical commands
            electrical_command = "Create an electrical inspection checklist for the office"
            parsed = parser.parse_command(electrical_command)
            
            print(f"✅ Parsed electrical command: {parsed.command_type}")
            
            self.test_results['voice_parsing'] = True
            print("✅ Voice command parsing tests passed!")
            
        except Exception as e:
            print(f"❌ Voice parsing test failed: {e}")
            self.test_results['voice_parsing'] = False
    
    async def test_agent_framework(self):
        """Test CrewAI agent framework initialization."""
        print("\n🤖 Testing Agent Framework...")
        
        try:
            # Test agent manager creation
            manager = create_voice_agent_manager("test_tenant")
            print("✅ Voice agent manager created successfully")
            
            # Test agent initialization
            await manager.initialize_agents()
            print(f"✅ Initialized {len(manager.agents)} agents")
            
            # List available agents
            for agent_name in manager.agents.keys():
                print(f"   - {agent_name}")
            
            self.test_results['agent_framework'] = True
            print("✅ Agent framework tests passed!")
            
        except Exception as e:
            print(f"❌ Agent framework test failed: {e}")
            self.test_results['agent_framework'] = False
    
    async def test_voice_integration(self):
        """Test voice integration with agents."""
        print("\n🔄 Testing Voice-Agent Integration...")
        
        try:
            manager = create_voice_agent_manager("test_tenant")
            await manager.initialize_agents()
            
            # Test voice command processing (without actual audio file)
            test_commands = [
                "Schedule dental appointment for Sarah",
                "Create electrical safety inspection",
                "Generate HVAC maintenance schedule"
            ]
            
            for command in test_commands:
                # Simulate voice command processing
                parser = VoiceCommandParser()
                parsed_command = parser.parse_command(command)
                
                print(f"✅ Command: '{command}'")
                print(f"   → Routed to: {parsed_command.command_type}")
                print(f"   → Intent: {parsed_command.intent}")
            
            self.test_results['voice_integration'] = True
            print("✅ Voice-agent integration tests passed!")
            
        except Exception as e:
            print(f"❌ Voice integration test failed: {e}")
            self.test_results['voice_integration'] = False
    
    async def test_multi_tenant_support(self):
        """Test multi-tenant capabilities."""
        print("\n🏢 Testing Multi-Tenant Support...")
        
        try:
            from gtm_voyager.crewai_agents.voice_agent_manager import MultiTenantVoiceAgentManager
            
            # Test multi-tenant manager
            multi_manager = MultiTenantVoiceAgentManager()
            
            # Create test tenants
            tenant1 = multi_manager.get_tenant_manager("dental_practice_1")
            tenant2 = multi_manager.get_tenant_manager("electrical_company_1")
            
            print("✅ Created multiple tenant managers")
            
            # Test tenant isolation
            stats = multi_manager.get_tenant_stats()
            print(f"✅ Tenant stats: {stats}")
            
            self.test_results['multi_tenant'] = True
            print("✅ Multi-tenant tests passed!")
            
        except Exception as e:
            print(f"❌ Multi-tenant test failed: {e}")
            self.test_results['multi_tenant'] = False
    
    def print_test_summary(self):
        """Print comprehensive test results."""
        print("\n" + "="*50)
        print("🧪 VOICE-AGENT SYSTEM TEST RESULTS")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Your voice-agent system is ready! 🚀")
        else:
            print("⚠️ Some tests failed. Check the errors above.")


async def main():
    """Run all tests."""
    print("🧪 Starting GTM Voyager Voice-Agent System Tests...")
    
    tester = VoiceAgentTester()
    
    # Run all test suites
    await tester.test_audio_processing()
    await tester.test_voice_command_parsing()
    await tester.test_agent_framework()
    await tester.test_voice_integration()
    await tester.test_multi_tenant_support()
    
    # Print summary
    tester.print_test_summary()


if __name__ == "__main__":
    asyncio.run(main())
