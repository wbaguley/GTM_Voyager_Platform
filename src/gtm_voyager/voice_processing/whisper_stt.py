import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WhisperSTT:
    """
    OpenAI Whisper Speech-to-Text processor for GTM Voyager Platform.
    
    Handles audio file processing, validation, and transcription with
    comprehensive error handling and monitoring.
    """
    
    # Supported audio formats
    SUPPORTED_FORMATS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'}
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB limit for Whisper API
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize WhisperSTT processor.
        
        Args:
            api_key: OpenAI API key. If None, loads from environment.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.logger = self._setup_logger()
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'total_duration': 0,
            'total_cost': 0.0,
            'errors': 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for WhisperSTT operations."""
        logger = logging.getLogger('WhisperSTT')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate audio file for Whisper processing.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dict with validation results
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            return {'valid': False, 'error': f"File not found: {file_path}"}
        
        # Check file extension
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return {
                'valid': False, 
                'error': f"Unsupported format: {file_path.suffix}. Supported: {self.SUPPORTED_FORMATS}"
            }
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return {
                'valid': False,
                'error': f"File too large: {file_size / 1024 / 1024:.1f}MB. Max: 25MB"
            }
        
        return {
            'valid': True,
            'file_size': file_size,
            'format': file_path.suffix.lower(),
            'size_mb': file_size / 1024 / 1024
        }
    
    def transcribe_audio(self, 
                        file_path: str, 
                        language: Optional[str] = None,
                        prompt: Optional[str] = None,
                        temperature: float = 0.0) -> Dict[str, Any]:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        Args:
            file_path: Path to audio file
            language: Language code (e.g., 'en', 'es'). Auto-detect if None.
            prompt: Optional prompt to guide transcription
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Dict with transcription results
        """
        try:
            # Validate file
            validation = self.validate_audio_file(file_path)
            if not validation['valid']:
                self.stats['errors'] += 1
                return {
                    'success': False,
                    'error': validation['error'],
                    'file_path': file_path
                }
            
            self.logger.info(f"Processing audio file: {file_path} ({validation['size_mb']:.1f}MB)")
            
            # Prepare API call parameters
            params = {
                'model': 'whisper-1',
                'temperature': temperature
            }
            
            if language:
                params['language'] = language
            if prompt:
                params['prompt'] = prompt
            
            # Make API call
            with open(file_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **params
                )
            
            # Update statistics
            self.stats['files_processed'] += 1
            # Estimate cost (approximately $0.006 per minute)
            estimated_cost = validation['size_mb'] * 0.1  # Rough estimate
            self.stats['total_cost'] += estimated_cost
            
            result = {
                'success': True,
                'text': response.text,
                'file_path': file_path,
                'file_size_mb': validation['size_mb'],
                'estimated_cost': estimated_cost,
                'language': language,
                'model': 'whisper-1'
            }
            
            self.logger.info(f"Transcription successful: {len(response.text)} characters")
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            error_msg = f"Transcription failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'file_path': file_path
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            'files_processed': 0,
            'total_duration': 0,
            'total_cost': 0.0,
            'errors': 0
        }
