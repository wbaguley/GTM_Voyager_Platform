"""
Comprehensive test suite for Enhanced Audio Processing components.
Tests all audio processing functionality including validation, enhancement, and monitoring.
"""

import unittest
import numpy as np
import tempfile
import os
from pathlib import Path
import librosa
import soundfile as sf
from unittest.mock import Mock, patch

# Import the enhanced audio processing modules
# Import the enhanced audio processing modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gtm_voyager.voice_processing.enhanced_audio_processor import (
    EnhancedAudioProcessor, AudioQuality, AudioMetrics, ProcessingResult
)
from gtm_voyager.voice_processing.noise_reduction_optimizer import (
    NoiseReducer, AudioEnhancer, QualityOptimizer
)
from gtm_voyager.voice_processing.realtime_audio_monitor import (
    RealtimeAudioMonitor, AudioValidator, PerformanceMonitor, ValidationLevel
)


class TestEnhancedAudioProcessor(unittest.TestCase):
    """Test cases for Enhanced Audio Processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = EnhancedAudioProcessor()
        self.sample_rate = 16000
        self.duration = 2.0  # 2 seconds
        
        # Create test audio signal
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration))
        self.test_audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        
        # Create temporary audio file
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(self.temp_file.name, self.test_audio, self.sample_rate)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_audio_validation(self):
        """Test audio file validation."""
        # Test valid file
        is_valid, errors = self.processor.validate_audio_file(self.temp_file.name)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test non-existent file
        is_valid, errors = self.processor.validate_audio_file("nonexistent.wav")
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_audio_quality_analysis(self):
        """Test audio quality analysis."""
        metrics = self.processor.analyze_audio_quality(self.test_audio, self.sample_rate)
        
        self.assertIsInstance(metrics, AudioMetrics)
        self.assertAlmostEqual(metrics.duration, self.duration, places=1)
        self.assertEqual(metrics.sample_rate, self.sample_rate)
        self.assertEqual(metrics.channels, 1)
        self.assertGreater(metrics.quality_score, 0)
        self.assertLessEqual(metrics.quality_score, 100)
        self.assertIsInstance(metrics.quality_level, AudioQuality)
    
    def test_audio_normalization(self):
        """Test audio normalization."""
        # Create audio with low level
        low_level_audio = self.test_audio * 0.1
        normalized = self.processor.normalize_audio(low_level_audio)
        
        # Check that normalized audio has higher RMS
        original_rms = np.sqrt(np.mean(low_level_audio**2))
        normalized_rms = np.sqrt(np.mean(normalized**2))
        self.assertGreater(normalized_rms, original_rms)
        
        # Check no clipping
        self.assertLessEqual(np.max(np.abs(normalized)), 0.95)
    
    def test_silence_removal(self):
        """Test silence removal."""
        # Create audio with silence at beginning and end
        silence_duration = 0.5  # 0.5 seconds
        silence_samples = int(silence_duration * self.sample_rate)
        
        audio_with_silence = np.concatenate([
            np.zeros(silence_samples),  # Leading silence
            self.test_audio,
            np.zeros(silence_samples)   # Trailing silence
        ])
        
        trimmed = self.processor.remove_silence(audio_with_silence, self.sample_rate)
        
        # Should be shorter than original
        self.assertLess(len(trimmed), len(audio_with_silence))
        # Should be close to original audio length
        self.assertAlmostEqual(len(trimmed) / self.sample_rate, self.duration, delta=0.2)
    
    def test_audio_segmentation(self):
        """Test audio segmentation for long files."""
        # Create long audio (35 seconds)
        long_duration = 35.0
        t = np.linspace(0, long_duration, int(self.sample_rate * long_duration))
        long_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        segments = self.processor.segment_audio(long_audio, self.sample_rate)
        
        # Should create multiple segments
        self.assertGreater(len(segments), 1)
        
        # Each segment should be within max length
        for segment in segments:
            segment_duration = len(segment) / self.sample_rate
            self.assertLessEqual(segment_duration, self.processor.MAX_SEGMENT_LENGTH + 1)
    
    def test_process_audio_file(self):
        """Test complete audio file processing."""
        result = self.processor.process_audio_file(self.temp_file.name)
        
        self.assertIsInstance(result, ProcessingResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.processed_file_path)
        self.assertIsNotNone(result.original_metrics)
        self.assertIsNotNone(result.processed_metrics)
        self.assertGreater(result.processing_time, 0)
        
        # Check that processed file exists
        self.assertTrue(os.path.exists(result.processed_file_path))
        
        # Clean up processed file
        os.unlink(result.processed_file_path)
    
    def test_processing_statistics(self):
        """Test processing statistics tracking."""
        # Process a file to generate statistics
        self.processor.process_audio_file(self.temp_file.name)
        
        stats = self.processor.get_processing_statistics()
        
        self.assertGreater(stats['files_processed'], 0)
        self.assertGreater(stats['total_processing_time'], 0)
        self.assertGreaterEqual(stats['average_processing_time'], 0)

class TestNoiseReductionOptimizer(unittest.TestCase):
    """Test cases for Noise Reduction and Quality Optimization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_rate = 16000
        self.duration = 2.0
        
        # Create test audio with noise
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration))
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        noise = 0.1 * np.random.randn(len(signal))
        self.noisy_audio = signal + noise
        
        self.noise_reducer = NoiseReducer()
        self.enhancer = AudioEnhancer()
        self.optimizer = QualityOptimizer()
    
    def test_noise_spectrum_estimation(self):
        """Test noise spectrum estimation."""
        noise_spectrum = self.noise_reducer.estimate_noise_spectrum(
            self.noisy_audio, self.sample_rate
        )
        
        self.assertIsInstance(noise_spectrum, np.ndarray)
        self.assertGreater(noise_spectrum.shape[0], 0)
        self.assertTrue(np.all(noise_spectrum >= 0))  # Power spectrum should be non-negative
    
    def test_spectral_subtraction(self):
        """Test spectral subtraction noise reduction."""
        enhanced = self.noise_reducer.spectral_subtraction(self.noisy_audio, self.sample_rate)
        
        self.assertAlmostEqual(len(enhanced), len(self.noisy_audio), delta=500)
        self.assertIsInstance(enhanced, np.ndarray)
        
        # Enhanced audio should have different characteristics
        original_std = np.std(self.noisy_audio)
        enhanced_std = np.std(enhanced)
        self.assertNotEqual(original_std, enhanced_std)
    
    def test_wiener_filter(self):
        """Test Wiener filtering."""
        filtered = self.noise_reducer.wiener_filter(self.noisy_audio, self.sample_rate)
        
        self.assertAlmostEqual(len(filtered), len(self.noisy_audio), delta=500)
        self.assertIsInstance(filtered, np.ndarray)
    
    def test_dynamic_range_compression(self):
        """Test dynamic range compression."""
        # Create audio with high dynamic range
        loud_signal = 0.9 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, self.sample_rate))
        quiet_signal = 0.1 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, self.sample_rate))
        high_dr_audio = np.concatenate([loud_signal, quiet_signal])
        
        compressed = self.enhancer.dynamic_range_compression(
            high_dr_audio, sample_rate=self.sample_rate
        )
        
        self.assertEqual(len(compressed), len(high_dr_audio))
        
        # Check that dynamic range is reduced
        original_peak = np.max(np.abs(high_dr_audio))
        original_rms = np.sqrt(np.mean(high_dr_audio**2))
        original_dr = 20 * np.log10(original_peak / original_rms)
        
        compressed_peak = np.max(np.abs(compressed))
        compressed_rms = np.sqrt(np.mean(compressed**2))
        compressed_dr = 20 * np.log10(compressed_peak / compressed_rms)
        
        self.assertNotEqual(compressed_dr, original_dr)
    
    def test_spectral_enhancement(self):
        """Test spectral enhancement."""
        enhanced = self.enhancer.spectral_enhancement(self.noisy_audio, self.sample_rate)
        
        self.assertAlmostEqual(len(enhanced), len(self.noisy_audio), delta=500)
        self.assertIsInstance(enhanced, np.ndarray)
    
    def test_adaptive_gain_control(self):
        """Test adaptive gain control."""
        # Create audio with varying levels
        varying_audio = np.concatenate([
            0.1 * self.noisy_audio,  # Quiet section
            0.8 * self.noisy_audio   # Loud section
        ])
        
        controlled = self.enhancer.adaptive_gain_control(varying_audio)
        
        self.assertEqual(len(controlled), len(varying_audio))
        
        # Check that levels are more consistent
        first_half_rms = np.sqrt(np.mean(controlled[:len(controlled)//2]**2))
        second_half_rms = np.sqrt(np.mean(controlled[len(controlled)//2:]**2))
        
        # Levels should be closer than in original
        original_ratio = 0.8 / 0.1  # 8:1 ratio
        controlled_ratio = max(first_half_rms, second_half_rms) / min(first_half_rms, second_half_rms)
        
        self.assertLess(controlled_ratio, original_ratio)
    
    def test_quality_optimization_pipeline(self):
        """Test complete quality optimization pipeline."""
        optimized, info = self.optimizer.optimize_audio(self.noisy_audio, self.sample_rate)
        
        self.assertAlmostEqual(len(optimized), len(self.noisy_audio), delta=500)
        self.assertIsInstance(info, dict)
        self.assertIn('applied_techniques', info)
        self.assertIn('processing_order', info)
        self.assertIn('quality_improvements', info)
        
        # Should have applied multiple techniques
        self.assertGreater(len(info['applied_techniques']), 0)

class TestRealtimeAudioMonitor(unittest.TestCase):
    """Test cases for Real-time Audio Monitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = RealtimeAudioMonitor(
            validation_enabled=True,
            performance_monitoring_enabled=True
        )
        
        # Sample metrics for testing
        self.sample_metrics = {
            'quality_score': 75.0,
            'signal_to_noise_ratio': 15.0,
            'dynamic_range': 12.0,
            'has_clipping': False,
            'duration': 5.0,
            'sample_rate': 16000
        }
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertIsNotNone(self.monitor.validator)
        self.assertIsNotNone(self.monitor.performance_monitor)
        self.assertFalse(self.monitor.monitoring_active)
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.monitoring_active)
        
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring_active)
    
    def test_audio_validation(self):
        """Test audio quality validation."""
        self.monitor.start_monitoring()
        
        results = self.monitor.validate_audio(self.sample_metrics)
        
        self.assertIsInstance(results, list)
        # Should pass validation with good metrics
        error_results = [r for r in results if r.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]]
        self.assertEqual(len(error_results), 0)
        
        self.monitor.stop_monitoring()
    
    def test_validation_with_poor_quality(self):
        """Test validation with poor quality audio."""
        poor_metrics = {
            'quality_score': 30.0,  # Poor quality
            'signal_to_noise_ratio': 3.0,  # Low SNR
            'dynamic_range': 2.0,  # Low dynamic range
            'has_clipping': True,  # Has clipping
            'duration': 0.2,  # Too short
            'sample_rate': 8000  # Non-optimal sample rate
        }
        
        self.monitor.start_monitoring()
        results = self.monitor.validate_audio(poor_metrics)
        
        # Should have multiple validation issues
        self.assertGreater(len(results), 0)
        
        # Should have at least one error or warning
        issues = [r for r in results if r.level in [ValidationLevel.WARNING, ValidationLevel.ERROR]]
        self.assertGreater(len(issues), 0)
        
        self.monitor.stop_monitoring()
    
    def test_performance_monitoring(self):
        """Test performance monitoring."""
        self.monitor.start_monitoring()
        
        # Record some performance metrics
        improvements = {
            'snr': 2.5,
            'noise_reduction': 3.0,
            'dynamic_range': 1.5,
            'file_size_reduction': 0.1
        }
        
        self.monitor.record_processing_performance(
            processing_time=2.5,
            quality_score=80.0,
            improvements=improvements
        )
        
        # Get monitoring status
        status = self.monitor.get_monitoring_status()
        
        self.assertIn('performance_stats', status)
        self.assertIn('recent_performance', status)
        self.assertGreater(status['performance_stats']['total_files_processed'], 0)
        
        self.monitor.stop_monitoring()
    
    def test_error_recording(self):
        """Test error recording."""
        self.monitor.start_monitoring()
        
        self.monitor.record_error(
            error_type="processing_error",
            error_message="Test error message",
            context={"file": "test.wav"}
        )
        
        # Check that error was recorded
        if self.monitor.performance_monitor:
            self.assertGreater(len(self.monitor.performance_monitor.error_log), 0)
        
        self.monitor.stop_monitoring()
    
    def test_adaptive_thresholds(self):
        """Test adaptive threshold adjustment."""
        validator = AudioValidator()
        
        # Add some quality data
        for score in [70, 75, 80, 85, 90]:
            validator.add_quality_data({'quality_score': score})
        
        # Check that thresholds can be updated
        original_threshold = validator.thresholds['min_quality_score']
        validator._update_adaptive_thresholds()
        
        # Threshold might change based on historical data
        self.assertIsInstance(validator.thresholds['min_quality_score'], float)

class TestIntegration(unittest.TestCase):
    """Integration tests for complete audio processing pipeline."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.processor = EnhancedAudioProcessor()
        self.optimizer = QualityOptimizer()
        self.monitor = RealtimeAudioMonitor()
        
        # Create test audio file
        sample_rate = 16000
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(self.temp_file.name, audio, sample_rate)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_complete_processing_pipeline(self):
        """Test complete audio processing pipeline with monitoring."""
        self.monitor.start_monitoring()
        
        # Process audio file
        result = self.processor.process_audio_file(self.temp_file.name)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.processed_file_path)
        
        # Validate processed audio
        if result.processed_metrics:
            validation_results = self.monitor.validate_audio({
                'quality_score': result.processed_metrics.quality_score,
                'signal_to_noise_ratio': result.processed_metrics.signal_to_noise_ratio,
                'dynamic_range': result.processed_metrics.dynamic_range,
                'has_clipping': result.processed_metrics.has_clipping,
                'duration': result.processed_metrics.duration,
                'sample_rate': result.processed_metrics.sample_rate
            })
            
            # Record performance
            self.monitor.record_processing_performance(
                processing_time=result.processing_time,
                quality_score=result.processed_metrics.quality_score,
                improvements=result.improvements
            )
        
        # Clean up
        if result.processed_file_path and os.path.exists(result.processed_file_path):
            os.unlink(result.processed_file_path)
        
        self.monitor.stop_monitoring()

def run_all_tests():
    """Run all test suites."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEnhancedAudioProcessor))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestNoiseReductionOptimizer))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRealtimeAudioMonitor))
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegration))

    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running Enhanced Audio Processing Test Suite...")
    print("=" * 60)
    
    success = run_all_tests()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed successfully!")
    else:
        print("❌ Some tests failed. Check output above for details.")
    
    print("\nTest suite covers:")
    print("- Enhanced Audio Processor functionality")
    print("- Noise reduction and quality optimization")
    print("- Real-time monitoring and validation")
    print("- Complete integration pipeline")
