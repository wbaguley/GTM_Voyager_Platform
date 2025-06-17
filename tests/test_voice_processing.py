import asyncio
import os
from dotenv import load_dotenv
from gtm_voyager.crewai_agents.industry_agent_router import UserProfile, IndustryType
from gtm_voyager.voice_processing.voice_processor import VoiceProcessor

# Load environment variables from .env file
load_dotenv()

async def main():
    # --- Configuration ---
    # IMPORTANT: Replace with the actual path to your test audio file
    # Make sure this audio file exists and is accessible.
    # Example: a short .mp3 or .wav file of someone speaking.
    TEST_AUDIO_FILE = "C:/GTM_Planetary/Test Files/Prothodontists Test Audio.mp3" # Updated path


    # Create a dummy user profile for testing
    test_user_profile = UserProfile(
        user_id="test_user_123",
        name="Test User",
        primary_industry=IndustryType.DENTAL_GENERAL,
        secondary_industries=[],
        default_agent="dental_general",
        voice_preferences={}
    )

    # --- Initialize VoiceProcessor ---
    voice_processor = VoiceProcessor()

    # --- Process Voice Input ---
    print(f"\n--- Starting Voice Processing for {TEST_AUDIO_FILE} ---")
    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"Error: Test audio file not found at {TEST_AUDIO_FILE}")
        print("Please update TEST_AUDIO_FILE in test_voice_processing.py to a valid path.")
        return

    result = await voice_processor.process_voice_input(TEST_AUDIO_FILE, test_user_profile)

    print("\n--- Processing Result ---")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Transcription: {result['transcription']}")
    print(f"Speaker Info: {result['speaker_info']}")
    if 'routing_result' in result:
        print(f"Routing Result: Selected Agent={result['routing_result'].selected_agent}, "
              f"Confidence={result['routing_result'].confidence_score:.2f}, "
              f"Reason='{result['routing_result'].routing_reason}'")

if __name__ == "__main__":
    asyncio.run(main())
