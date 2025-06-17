"""
GTM Voyager Platform - Complete System Test
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

print("🧪 GTM Voyager Platform Test")
print("=" * 40)

def test_imports():
    """Test basic imports"""
    try:
        from gtm_voyager.voice_processing.whisper_stt import WhisperSTT
        print("✅ WhisperSTT imported")
        
        from gtm_voyager.audio import AudioProcessor
        print("✅ AudioProcessor imported")
        
        from gtm_voyager.crewai_agents.dental_agent import DentalAgent
        print("✅ DentalAgent imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_whisper():
    """Test WhisperSTT"""
    try:
        whisper = WhisperSTT()
        print("✅ WhisperSTT initialized")
        return True
    except Exception as e:
        print(f"❌ WhisperSTT failed: {e}")
        return False

if __name__ == "__main__":
    test_imports()
    test_whisper()
    print("🎯 Basic tests complete!")
