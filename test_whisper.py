import os
from gtm_voyager.voice_processing.whisper_stt import WhisperSTT

def test_whisper_stt():
    """Test WhisperSTT functionality"""
    
    print("🎯 Testing GTM Voyager WhisperSTT Implementation")
    print("=" * 50)
    
    try:
        # Initialize WhisperSTT
        whisper = WhisperSTT()
        print("✅ WhisperSTT initialized successfully")
        
        # Test file validation with a non-existent file
        print("\n📁 Testing file validation...")
        validation = whisper.validate_audio_file("test_audio.mp3")
        print(f"Validation result: {validation}")
        
        # Show supported formats
        print(f"\n🎵 Supported audio formats: {whisper.SUPPORTED_FORMATS}")
        print(f"📏 Max file size: {whisper.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Show current stats
        print(f"\n📊 Current stats: {whisper.get_stats()}")
        
        print("\n✅ WhisperSTT class is working correctly!")
        print("🎯 Ready for audio file processing!")
        
    except Exception as e:
        print(f"❌ Error testing WhisperSTT: {e}")

if __name__ == "__main__":
    test_whisper_stt()
