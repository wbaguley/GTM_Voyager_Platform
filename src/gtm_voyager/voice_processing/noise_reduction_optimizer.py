"""
Advanced Noise Reduction and Quality Optimization Module
Extends the Enhanced Audio Processor with sophisticated noise reduction and quality enhancement.
"""

import numpy as np
import librosa
import scipy.signal
from scipy.ndimage import median_filter
from typing import Optional, Tuple, Dict, Any
import logging

class NoiseReducer:
    """
    Advanced noise reduction using spectral subtraction and Wiener filtering.
    """
    
    def __init__(self, 
                 noise_reduction_strength: float = 0.5,
                 spectral_floor: float = 0.1,
                 smoothing_factor: float = 0.98):
        """
        Initialize noise reducer.
        
        Args:
            noise_reduction_strength: Strength of noise reduction (0.0-1.0)
            spectral_floor: Minimum spectral floor to prevent over-reduction
            smoothing_factor: Temporal smoothing factor for spectral estimates
        """
        self.noise_reduction_strength = noise_reduction_strength
        self.spectral_floor = spectral_floor
        self.smoothing_factor = smoothing_factor
        self.logger = logging.getLogger('NoiseReducer')
    
    def estimate_noise_spectrum(self, audio: np.ndarray, sample_rate: int, 
                               noise_duration: float = 0.5) -> np.ndarray:
        """
        Estimate noise spectrum from the beginning of the audio.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate
            noise_duration: Duration in seconds to use for noise estimation
            
        Returns:
            Estimated noise power spectrum
        """
        # Use first portion of audio for noise estimation
        noise_samples = int(noise_duration * sample_rate)
        noise_segment = audio[:min(noise_samples, len(audio) // 4)]
        
        # Compute STFT of noise segment
        stft_noise = librosa.stft(noise_segment, hop_length=512, n_fft=2048)
        noise_magnitude = np.abs(stft_noise)
        
        # Estimate noise power spectrum (average across time)
        noise_power = np.mean(noise_magnitude**2, axis=1, keepdims=True)
        
        return noise_power
    
    def spectral_subtraction(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply spectral subtraction noise reduction.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate
            
        Returns:
            Noise-reduced audio signal
        """
        # Compute STFT
        stft = librosa.stft(audio, hop_length=512, n_fft=2048)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise spectrum
        noise_power = self.estimate_noise_spectrum(audio, sample_rate)
        
        # Apply spectral subtraction
        signal_power = magnitude**2
        
        # Subtract noise estimate
        enhanced_power = signal_power - self.noise_reduction_strength * noise_power
        
        # Apply spectral floor to prevent over-subtraction
        enhanced_power = np.maximum(enhanced_power, 
                                   self.spectral_floor * signal_power)
        
        # Reconstruct magnitude
        enhanced_magnitude = np.sqrt(enhanced_power)
        
        # Reconstruct complex spectrum
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        
        # Convert back to time domain
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
        
        return enhanced_audio
    
    def wiener_filter(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply Wiener filtering for noise reduction.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate
            
        Returns:
            Filtered audio signal
        """
        # Compute STFT
        stft = librosa.stft(audio, hop_length=512, n_fft=2048)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise and signal power
        noise_power = self.estimate_noise_spectrum(audio, sample_rate)
        signal_power = magnitude**2
        
        # Compute Wiener filter
        wiener_gain = signal_power / (signal_power + noise_power)
        
        # Apply temporal smoothing
        if hasattr(self, '_prev_gain'):
            wiener_gain = (self.smoothing_factor * self._prev_gain + 
                          (1 - self.smoothing_factor) * wiener_gain)
        self._prev_gain = wiener_gain
        
        # Apply filter
        enhanced_magnitude = magnitude * wiener_gain
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        
        # Convert back to time domain
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
        
        return enhanced_audio

class AudioEnhancer:
    """
    Audio quality enhancement using various signal processing techniques.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('AudioEnhancer')
    
    def dynamic_range_compression(self, audio: np.ndarray, 
                                 threshold: float = -20.0,
                                 ratio: float = 4.0,
                                 attack_time: float = 0.003,
                                 release_time: float = 0.1,
                                 sample_rate: int = 16000) -> np.ndarray:
        """
        Apply dynamic range compression to improve speech intelligibility.
        
        Args:
            audio: Input audio signal
            threshold: Compression threshold in dB
            ratio: Compression ratio
            attack_time: Attack time in seconds
            release_time: Release time in seconds
            sample_rate: Sample rate
            
        Returns:
            Compressed audio signal
        """
        # Convert threshold to linear scale
        threshold_linear = 10**(threshold / 20)
        
        # Calculate attack and release coefficients
        attack_coeff = np.exp(-1 / (attack_time * sample_rate))
        release_coeff = np.exp(-1 / (release_time * sample_rate))
        
        # Initialize envelope follower
        envelope = 0.0
        compressed = np.zeros_like(audio)
        
        for i, sample in enumerate(audio):
            # Envelope detection
            input_level = abs(sample)
            if input_level > envelope:
                envelope = attack_coeff * envelope + (1 - attack_coeff) * input_level
            else:
                envelope = release_coeff * envelope + (1 - release_coeff) * input_level
            
            # Apply compression
            if envelope > threshold_linear:
                # Calculate gain reduction
                gain_reduction = threshold_linear + (envelope - threshold_linear) / ratio
                gain = gain_reduction / envelope if envelope > 0 else 1.0
            else:
                gain = 1.0
            
            compressed[i] = sample * gain
        
        return compressed
    
    def spectral_enhancement(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Enhance speech clarity using spectral shaping.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate
            
        Returns:
            Enhanced audio signal
        """
        # Compute STFT
        stft = librosa.stft(audio, hop_length=512, n_fft=2048)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Get frequency bins
        freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
        
        # Create enhancement filter for speech frequencies
        enhancement = np.ones_like(freqs)
        
        # Boost speech formant regions (300-3400 Hz)
        speech_mask = (freqs >= 300) & (freqs <= 3400)
        enhancement[speech_mask] *= 1.2
        
        # Boost presence region (2-5 kHz) for clarity
        presence_mask = (freqs >= 2000) & (freqs <= 5000)
        enhancement[presence_mask] *= 1.1
        
        # Reduce low-frequency noise
        low_freq_mask = freqs < 100
        enhancement[low_freq_mask] *= 0.7
        
        # Apply enhancement
        enhanced_magnitude = magnitude * enhancement[:, np.newaxis]
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        
        # Convert back to time domain
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=512)
        
        return enhanced_audio
    
    def adaptive_gain_control(self, audio: np.ndarray, 
                             target_level: float = -20.0,
                             max_gain: float = 20.0) -> np.ndarray:
        """
        Apply adaptive gain control to maintain consistent levels.
        
        Args:
            audio: Input audio signal
            target_level: Target RMS level in dB
            max_gain: Maximum gain in dB
            
        Returns:
            Gain-controlled audio signal
        """
        # Calculate RMS in overlapping windows
        window_size = 1024
        hop_size = 512
        
        enhanced = audio.copy()
        
        for i in range(0, len(audio) - window_size, hop_size):
            window = audio[i:i + window_size]
            rms = np.sqrt(np.mean(window**2))
            
            if rms > 0:
                # Calculate current level in dB
                current_level = 20 * np.log10(rms)
                
                # Calculate required gain
                gain_db = target_level - current_level
                gain_db = np.clip(gain_db, -max_gain, max_gain)
                gain_linear = 10**(gain_db / 20)
                
                # Apply gain with smooth transitions
                enhanced[i:i + window_size] *= gain_linear
        
        return enhanced
    
    def harmonic_enhancement(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Enhance harmonic content for better speech perception.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate
            
        Returns:
            Harmonically enhanced audio signal
        """
        # Detect pitch using autocorrelation
        autocorr = np.correlate(audio, audio, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        # Find fundamental frequency
        min_period = int(sample_rate / 800)  # 800 Hz max
        max_period = int(sample_rate / 80)   # 80 Hz min
        
        if max_period < len(autocorr):
            pitch_autocorr = autocorr[min_period:max_period]
            if len(pitch_autocorr) > 0:
                pitch_period = np.argmax(pitch_autocorr) + min_period
                fundamental_freq = sample_rate / pitch_period
                
                # Generate harmonic enhancement
                t = np.arange(len(audio)) / sample_rate
                harmonic_enhancement = 0.1 * np.sin(2 * np.pi * fundamental_freq * 2 * t)
                
                # Add subtle harmonic content
                enhanced = audio + harmonic_enhancement
                
                # Normalize to prevent clipping
                peak = np.max(np.abs(enhanced))
                if peak > 0.95:
                    enhanced = enhanced * (0.95 / peak)
                
                return enhanced
        
        return audio

class QualityOptimizer:
    """
    Comprehensive audio quality optimization combining multiple techniques.
    """
    
    def __init__(self, 
                 enable_noise_reduction: bool = True,
                 enable_compression: bool = True,
                 enable_spectral_enhancement: bool = True,
                 enable_harmonic_enhancement: bool = False):
        """
        Initialize quality optimizer.
        
        Args:
            enable_noise_reduction: Enable noise reduction
            enable_compression: Enable dynamic range compression
            enable_spectral_enhancement: Enable spectral enhancement
            enable_harmonic_enhancement: Enable harmonic enhancement
        """
        self.enable_noise_reduction = enable_noise_reduction
        self.enable_compression = enable_compression
        self.enable_spectral_enhancement = enable_spectral_enhancement
        self.enable_harmonic_enhancement = enable_harmonic_enhancement
        
        self.noise_reducer = NoiseReducer()
        self.enhancer = AudioEnhancer()
        self.logger = logging.getLogger('QualityOptimizer')
    
    def optimize_audio(self, audio: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply comprehensive quality optimization.
        
        Args:
            audio: Input audio signal
            sample_rate: Sample rate
            
        Returns:
            Tuple of (optimized_audio, optimization_info)
        """
        optimized = audio.copy()
        optimization_info = {
            'applied_techniques': [],
            'processing_order': [],
            'quality_improvements': {}
        }
        
        # Calculate initial quality metrics
        initial_rms = np.sqrt(np.mean(audio**2))
        initial_peak = np.max(np.abs(audio))
        
        # 1. Noise Reduction
        if self.enable_noise_reduction:
            self.logger.info("Applying noise reduction...")
            optimized = self.noise_reducer.spectral_subtraction(optimized, sample_rate)
            optimization_info['applied_techniques'].append('noise_reduction')
            optimization_info['processing_order'].append('spectral_subtraction')
        
        # 2. Spectral Enhancement
        if self.enable_spectral_enhancement:
            self.logger.info("Applying spectral enhancement...")
            optimized = self.enhancer.spectral_enhancement(optimized, sample_rate)
            optimization_info['applied_techniques'].append('spectral_enhancement')
            optimization_info['processing_order'].append('spectral_shaping')
        
        # 3. Dynamic Range Compression
        if self.enable_compression:
            self.logger.info("Applying dynamic range compression...")
            optimized = self.enhancer.dynamic_range_compression(optimized, sample_rate=sample_rate)
            optimization_info['applied_techniques'].append('compression')
            optimization_info['processing_order'].append('dynamic_compression')
        
        # 4. Adaptive Gain Control
        self.logger.info("Applying adaptive gain control...")
        optimized = self.enhancer.adaptive_gain_control(optimized)
        optimization_info['applied_techniques'].append('gain_control')
        optimization_info['processing_order'].append('adaptive_gain')
        
        # 5. Harmonic Enhancement (optional)
        if self.enable_harmonic_enhancement:
            self.logger.info("Applying harmonic enhancement...")
            optimized = self.enhancer.harmonic_enhancement(optimized, sample_rate)
            optimization_info['applied_techniques'].append('harmonic_enhancement')
            optimization_info['processing_order'].append('harmonic_boost')
        
        # Calculate final quality metrics
        final_rms = np.sqrt(np.mean(optimized**2))
        final_peak = np.max(np.abs(optimized))
        
        # Record improvements
        optimization_info['quality_improvements'] = {
            'rms_change': final_rms / initial_rms if initial_rms > 0 else 1.0,
            'peak_change': final_peak / initial_peak if initial_peak > 0 else 1.0,
            'dynamic_range_improvement': self._calculate_dynamic_range(optimized) - self._calculate_dynamic_range(audio)
        }
        
        self.logger.info(f"Quality optimization complete. Applied {len(optimization_info['applied_techniques'])} techniques.")
        
        return optimized, optimization_info
    
    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range of audio signal."""
        if len(audio) == 0:
            return 0.0
        
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio**2))
        
        if rms > 0:
            return 20 * np.log10(peak / rms)
        return 0.0

# Example usage
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = QualityOptimizer(
        enable_noise_reduction=True,
        enable_compression=True,
        enable_spectral_enhancement=True,
        enable_harmonic_enhancement=False
    )
    
    print("Noise Reduction Optimizer initialized successfully!")
    print("Available classes:")
    print("- NoiseReducer: Advanced noise reduction")
    print("- AudioEnhancer: Quality enhancement techniques")
    print("- QualityOptimizer: Comprehensive optimization pipeline")
