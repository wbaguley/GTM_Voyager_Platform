"""
GTM Voyager Platform - Audio Processing Module
Audio preprocessing and utilities for voice processing pipeline.
"""

from .audio_utils import (
    AudioProcessor,
    AudioFormat,
    AudioMetadata,
    AudioProcessingConfig,
    validate_audio,
    optimize_audio_for_whisper,
    get_audio_metadata
)

from .whisper_client import (
    WhisperClient,
    WhisperConfig,
    WhisperModel,
    TranscriptionResult,
    transcribe_audio_file,
    transcribe_large_audio_file
)

__all__ = [
    # Audio processing
    'AudioProcessor',
    'AudioFormat', 
    'AudioMetadata',
    'AudioProcessingConfig',
    'validate_audio',
    'optimize_audio_for_whisper',
    'get_audio_metadata',
    
    # Whisper API
    'WhisperClient',
    'WhisperConfig',
    'WhisperModel',
    'TranscriptionResult',
    'transcribe_audio_file',
    'transcribe_large_audio_file'
]
