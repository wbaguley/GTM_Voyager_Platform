"""
GTM Voyager Platform - Audio Utilities Module
Handles audio preprocessing, format conversion, and quality optimization for Whisper API integration.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import asyncio
from dataclasses import dataclass
from enum import Enum

# Audio processing libraries
try:
    import librosa
    import soundfile as sf
    import numpy as np
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
except ImportError as e:
    logging.error(f"Audio processing libraries not installed: {e}")
    raise ImportError("Please install audio processing dependencies: librosa, soundfile, pydub")


class AudioFormat(Enum):
    """Supported audio formats for processing."""
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"


@dataclass
class AudioMetadata:
    """Audio file metadata container."""
    duration: float
    sample_rate: int
    channels: int
    format: str
    file_size: int
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None


@dataclass
class AudioProcessingConfig:
    """Configuration for audio preprocessing."""
    target_sample_rate: int = 16000  # Optimal for Whisper
    target_channels: int = 1  # Mono for Whisper
    normalize_audio: bool = True
    noise_reduction: bool = True
    dynamic_range_compression: bool = True
    max_duration: int = 600  # 10 minutes max
    min_duration: float = 0.1  # 100ms minimum
class AudioProcessor:
    """
    Comprehensive audio preprocessing for GTM Voyager Platform.
    Optimizes audio for OpenAI Whisper API integration.
    """
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize audio processor with configuration."""
        self.config = config or AudioProcessingConfig()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for audio processing."""
        logger = logging.getLogger('GTMVoyager.AudioProcessor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def extract_metadata(self, file_path: Union[str, Path]) -> AudioMetadata:
        """
        Extract comprehensive metadata from audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            AudioMetadata object with file information
        """
        try:
            file_path = Path(file_path)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Load audio for analysis
            audio_data, sample_rate = librosa.load(str(file_path), sr=None)
            duration = len(audio_data) / sample_rate
            
            # Get additional metadata using pydub
            audio_segment = AudioSegment.from_file(str(file_path))
            channels = audio_segment.channels
            
            metadata = AudioMetadata(
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                format=file_path.suffix.lower().lstrip('.'),
                file_size=file_size,
                bitrate=getattr(audio_segment, 'bitrate', None)
            )
            
            self.logger.info(f"Extracted metadata for {file_path.name}: {duration:.2f}s, {sample_rate}Hz, {channels}ch")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
            raise

    async def validate_audio_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate audio file for processing compatibility.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Validation result with status and details
        """
        try:
            metadata = await self.extract_metadata(file_path)
            
            validation_result = {
                "valid": True,
                "metadata": metadata,
                "warnings": [],
                "errors": []
            }
            
            # Check duration limits
            if metadata.duration > self.config.max_duration:
                validation_result["errors"].append(
                    f"Audio duration ({metadata.duration:.1f}s) exceeds maximum ({self.config.max_duration}s)"
                )
                validation_result["valid"] = False
            
            if metadata.duration < self.config.min_duration:
                validation_result["errors"].append(
                    f"Audio duration ({metadata.duration:.1f}s) below minimum ({self.config.min_duration}s)"
                )
                validation_result["valid"] = False
            
            # Check file size (25MB limit for OpenAI)
            max_size_mb = 25
            file_size_mb = metadata.file_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                validation_result["errors"].append(
                    f"File size ({file_size_mb:.1f}MB) exceeds OpenAI limit ({max_size_mb}MB)"
                )
                validation_result["valid"] = False
            
            # Check format compatibility
            supported_formats = [fmt.value for fmt in AudioFormat]
            if metadata.format not in supported_formats:
                validation_result["errors"].append(
                    f"Unsupported format: {metadata.format}. Supported: {supported_formats}"
                )
                validation_result["valid"] = False
            
            # Warnings for suboptimal settings
            if metadata.sample_rate != self.config.target_sample_rate:
                validation_result["warnings"].append(
                    f"Sample rate ({metadata.sample_rate}Hz) will be converted to {self.config.target_sample_rate}Hz"
                )
            
            if metadata.channels != self.config.target_channels:
                validation_result["warnings"].append(
                    f"Audio channels ({metadata.channels}) will be converted to mono"
                )
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "metadata": None,
                "warnings": [],
                "errors": [f"Validation failed: {str(e)}"]
            }
    
    async def convert_format(self, 
                           input_path: Union[str, Path], 
                           output_path: Union[str, Path],
                           target_format: AudioFormat = AudioFormat.WAV) -> bool:
        """
        Convert audio file to target format.
        
        Args:
            input_path: Source audio file
            output_path: Destination file path
            target_format: Target audio format
            
        Returns:
            Success status
        """
        try:
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # Load audio with pydub for format conversion
            audio = AudioSegment.from_file(str(input_path))
            
            # Export in target format
            audio.export(str(output_path), format=target_format.value)
            
            self.logger.info(f"Converted {input_path.name} to {target_format.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Format conversion failed: {e}")
            return False

    async def optimize_for_whisper(self, 
                                 input_path: Union[str, Path],
                                 output_path: Optional[Union[str, Path]] = None) -> str:
        """
        Optimize audio file for OpenAI Whisper API processing.
        
        Args:
            input_path: Source audio file
            output_path: Optional output path (creates temp file if None)
            
        Returns:
            Path to optimized audio file
        """
        try:
            input_path = Path(input_path)
            
            # Create output path if not provided
            if output_path is None:
                temp_dir = tempfile.mkdtemp()
                output_path = Path(temp_dir) / f"optimized_{input_path.stem}.wav"
            else:
                output_path = Path(output_path)
            
            # Load audio with librosa for advanced processing
            audio_data, original_sr = librosa.load(str(input_path), sr=None)
            
            # Resample to target sample rate
            if original_sr != self.config.target_sample_rate:
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=original_sr, 
                    target_sr=self.config.target_sample_rate
                )
            
            # Apply noise reduction if enabled
            if self.config.noise_reduction:
                audio_data = self._apply_noise_reduction(audio_data)
            
            # Normalize audio if enabled
            if self.config.normalize_audio:
                audio_data = librosa.util.normalize(audio_data)
            
            # Save optimized audio
            sf.write(
                str(output_path),
                audio_data,
                self.config.target_sample_rate,
                format='WAV',
                subtype='PCM_16'
            )
            
            self.logger.info(f"Optimized audio saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Audio optimization failed: {e}")
            raise
    
    def _apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply basic noise reduction to audio data.
        
        Args:
            audio_data: Audio signal as numpy array
            
        Returns:
            Noise-reduced audio data
        """
        try:
            # Simple spectral gating for noise reduction
            # This is a basic implementation - can be enhanced with more sophisticated algorithms
            
            # Compute spectral centroid to identify noise characteristics
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data)[0]
            
            # Apply gentle high-pass filter to reduce low-frequency noise
            audio_data = librosa.effects.preemphasis(audio_data, coef=0.97)
            
            return audio_data
            
        except Exception as e:
            self.logger.warning(f"Noise reduction failed, returning original audio: {e}")
            return audio_data

    async def chunk_audio(self, 
                         input_path: Union[str, Path],
                         chunk_duration: int = 300,  # 5 minutes
                         overlap: float = 1.0) -> list[str]:
        """
        Split audio file into chunks for processing large files.
        
        Args:
            input_path: Source audio file
            chunk_duration: Duration of each chunk in seconds
            overlap: Overlap between chunks in seconds
            
        Returns:
            List of chunk file paths
        """
        try:
            input_path = Path(input_path)
            
            # Load audio
            audio = AudioSegment.from_file(str(input_path))
            duration_ms = len(audio)
            chunk_duration_ms = chunk_duration * 1000
            overlap_ms = overlap * 1000
            
            chunks = []
            temp_dir = tempfile.mkdtemp()
            
            start_ms = 0
            chunk_index = 0
            
            while start_ms < duration_ms:
                end_ms = min(start_ms + chunk_duration_ms, duration_ms)
                
                # Extract chunk
                chunk = audio[start_ms:end_ms]
                
                # Save chunk
                chunk_path = Path(temp_dir) / f"{input_path.stem}_chunk_{chunk_index:03d}.wav"
                chunk.export(str(chunk_path), format="wav")
                chunks.append(str(chunk_path))
                
                # Move to next chunk with overlap
                start_ms += chunk_duration_ms - overlap_ms
                chunk_index += 1
            
            self.logger.info(f"Split {input_path.name} into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Audio chunking failed: {e}")
            raise


# Utility functions for easy integration
async def validate_audio(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Quick audio validation function."""
    processor = AudioProcessor()
    return await processor.validate_audio_file(file_path)


async def optimize_audio_for_whisper(input_path: Union[str, Path], 
                                   output_path: Optional[Union[str, Path]] = None) -> str:
    """Quick audio optimization function."""
    processor = AudioProcessor()
    return await processor.optimize_for_whisper(input_path, output_path)


async def get_audio_metadata(file_path: Union[str, Path]) -> AudioMetadata:
    """Quick metadata extraction function."""
    processor = AudioProcessor()
    return await processor.extract_metadata(file_path)
