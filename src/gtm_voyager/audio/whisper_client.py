"""
GTM Voyager Platform - OpenAI Whisper API Client
Robust Whisper API integration with error handling, rate limiting, and cost optimization.
"""

import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import json

# OpenAI and HTTP libraries
try:
    import openai
    import httpx
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError as e:
    logging.error(f"Required libraries not installed: {e}" )
    raise ImportError("Please install: openai, httpx, tenacity" )

# Import our audio processing module
from .audio_utils import AudioProcessor, AudioMetadata, optimize_audio_for_whisper


class WhisperModel(Enum):
    """Available Whisper models with cost and performance characteristics."""
    WHISPER_1 = "whisper-1"  # Standard model


@dataclass
class TranscriptionResult:
    """Container for Whisper transcription results."""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None
    word_count: Optional[int] = None
    cost_estimate: Optional[float] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None


@dataclass
class WhisperConfig:
    """Configuration for Whisper API client."""
    api_key: Optional[str] = None
    model: WhisperModel = WhisperModel.WHISPER_1
    language: Optional[str] = None  # Auto-detect if None
    temperature: float = 0.0  # Deterministic output
    max_retries: int = 3
    timeout: int = 300  # 5 minutes
    cost_per_minute: float = 0.006  # $0.006 per minute as of 2024
    max_file_size_mb: int = 25  # OpenAI limit
    enable_cost_tracking: bool = True


class WhisperClient:
    """
    Comprehensive OpenAI Whisper API client for GTM Voyager Platform.
    Handles transcription with error handling, cost optimization, and quality validation.
    """
    
    def __init__(self, config: Optional[WhisperConfig] = None):
        """Initialize Whisper client with configuration."""
        self.config = config or WhisperConfig()
        self.audio_processor = AudioProcessor()
        self.logger = self._setup_logger()
        self.total_cost = 0.0
        self.total_minutes_processed = 0.0
        
        # Initialize OpenAI client
        self._setup_openai_client()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for Whisper client."""
        logger = logging.getLogger('GTMVoyager.WhisperClient')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_openai_client(self):
        """Initialize OpenAI client with API key."""
        api_key = self.config.api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass in config.")
        
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        self.logger.info("OpenAI Whisper client initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError))
    )
    async def transcribe_audio(self, 
                             audio_path: Union[str, Path],
                             optimize_audio: bool = True,
                             language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        Args:
            audio_path: Path to audio file
            optimize_audio: Whether to optimize audio for Whisper
            language: Language code (ISO-639-1) or None for auto-detection
            
        Returns:
            TranscriptionResult with transcription and metadata
        """
        start_time = time.time()
        
        try:
            audio_path = Path(audio_path)
            
            # Validate audio file
            validation = await self.audio_processor.validate_audio_file(audio_path)
            if not validation["valid"]:
                raise ValueError(f"Audio validation failed: {validation['errors']}")
            
            metadata = validation["metadata"]
            self.logger.info(f"Processing audio: {audio_path.name} ({metadata.duration:.1f}s)")
            
            # Optimize audio for Whisper if requested
            if optimize_audio:
                optimized_path = await optimize_audio_for_whisper(audio_path)
                processing_path = optimized_path
                self.logger.info("Audio optimized for Whisper processing")
            else:
                processing_path = str(audio_path)
            
            # Prepare transcription parameters
            transcription_params = {
                "model": self.config.model.value,
                "temperature": self.config.temperature,
                "response_format": "json"
            }
            
            # Add language if specified
            if language or self.config.language:
                transcription_params["language"] = language or self.config.language
            
            # Perform transcription
            with open(processing_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **transcription_params
                )
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            cost_estimate = self._calculate_cost(metadata.duration)
            
            # Update tracking
            if self.config.enable_cost_tracking:
                self.total_cost += cost_estimate
                self.total_minutes_processed += metadata.duration / 60
            
            # Create result
            result = TranscriptionResult(
                text=response.text,
                language=getattr(response, 'language', None),
                duration=metadata.duration,
                word_count=len(response.text.split()) if response.text else 0,
                cost_estimate=cost_estimate,
                processing_time=processing_time,
                model_used=self.config.model.value
            )
            
            self.logger.info(
                f"Transcription completed: {result.word_count} words, "
                f"${cost_estimate:.4f} cost, {processing_time:.1f}s processing"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription failed for {audio_path}: {e}")
            raise
    
    async def transcribe_large_audio(self, 
                                   audio_path: Union[str, Path],
                                   chunk_duration: int = 300) -> List[TranscriptionResult]:
        """
        Transcribe large audio file by chunking it into smaller segments.
        
        Args:
            audio_path: Path to large audio file
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            List of TranscriptionResult objects for each chunk
        """
        try:
            audio_path = Path(audio_path)
            
            # Validate audio file
            validation = await self.audio_processor.validate_audio_file(audio_path)
            if not validation["valid"]:
                raise ValueError(f"Audio validation failed: {validation['errors']}")
            
            metadata = validation["metadata"]
            
            # Check if chunking is needed
            if metadata.duration <= chunk_duration:
                self.logger.info("Audio file is small enough, processing without chunking")
                result = await self.transcribe_audio(audio_path)
                return [result]
            
            # Chunk the audio
            self.logger.info(f"Chunking large audio file: {metadata.duration:.1f}s")
            chunks = await self.audio_processor.chunk_audio(audio_path, chunk_duration)
            
            # Transcribe each chunk
            results = []
            for i, chunk_path in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                try:
                    result = await self.transcribe_audio(chunk_path, optimize_audio=True)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to process chunk {i+1}: {e}")
                    # Continue with other chunks
                    continue
            
            self.logger.info(f"Large audio transcription completed: {len(results)} chunks processed")
            return results
            
        except Exception as e:
            self.logger.error(f"Large audio transcription failed: {e}")
            raise
    
    def combine_chunk_results(self, chunk_results: List[TranscriptionResult]) -> TranscriptionResult:
        """
        Combine multiple chunk transcription results into a single result.
        
        Args:
            chunk_results: List of TranscriptionResult objects
            
        Returns:
            Combined TranscriptionResult
        """
        if not chunk_results:
            raise ValueError("No chunk results to combine")
        
        # Combine text
        combined_text = " ".join(result.text for result in chunk_results if result.text)
        
        # Calculate combined metrics
        total_duration = sum(result.duration or 0 for result in chunk_results)
        total_cost = sum(result.cost_estimate or 0 for result in chunk_results)
        total_processing_time = sum(result.processing_time or 0 for result in chunk_results)
        total_words = sum(result.word_count or 0 for result in chunk_results)
        
        # Use language from first chunk (assuming consistent)
        language = chunk_results[0].language if chunk_results else None
        model_used = chunk_results[0].model_used if chunk_results else None
        
        return TranscriptionResult(
            text=combined_text,
            language=language,
            duration=total_duration,
            word_count=total_words,
            cost_estimate=total_cost,
            processing_time=total_processing_time,
            model_used=model_used
        )
    
    def _calculate_cost(self, duration_seconds: float) -> float:
        """Calculate estimated cost for transcription."""
        duration_minutes = duration_seconds / 60
        return duration_minutes * self.config.cost_per_minute
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for cost tracking."""
        return {
            "total_cost": self.total_cost,
            "total_minutes_processed": self.total_minutes_processed,
            "average_cost_per_minute": self.config.cost_per_minute,
            "total_files_processed": getattr(self, '_files_processed', 0)
        }
    
    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key by making a test request."""
        try:
            # Make a simple API call to validate the key
            models = self.client.models.list()
            self.logger.info("API key validation successful")
            return True
        except Exception as e:
            self.logger.error(f"API key validation failed: {e}")
            return False


# Utility functions for easy integration
async def transcribe_audio_file(audio_path: Union[str, Path], 
                              api_key: Optional[str] = None,
                              language: Optional[str] = None) -> TranscriptionResult:
    """Quick transcription function."""
    config = WhisperConfig(api_key=api_key, language=language)
    client = WhisperClient(config)
    return await client.transcribe_audio(audio_path)


async def transcribe_large_audio_file(audio_path: Union[str, Path],
                                    api_key: Optional[str] = None,
                                    chunk_duration: int = 300) -> TranscriptionResult:
    """Quick large file transcription function."""
    config = WhisperConfig(api_key=api_key)
    client = WhisperClient(config)
    chunk_results = await client.transcribe_large_audio(audio_path, chunk_duration)
    return client.combine_chunk_results(chunk_results)
