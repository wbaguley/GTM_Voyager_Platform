"""
Real-time Audio Validation and Monitoring System
Provides continuous quality assessment, adaptive optimization, and performance monitoring.
"""

import numpy as np
import threading
import time
import queue
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
import statistics

class ValidationLevel(Enum):
    """Audio validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ProcessingStatus(Enum):
    """Real-time processing status"""
    IDLE = "idle"
    PROCESSING = "processing"
    OPTIMIZING = "optimizing"
    VALIDATING = "validating"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class ValidationResult:
    """Result of audio validation check"""
    level: ValidationLevel
    message: str
    metric_name: str
    current_value: float
    expected_range: tuple
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ProcessingMetrics:
    """Real-time processing performance metrics"""
    processing_time: float
    quality_score: float
    snr_improvement: float
    noise_reduction_db: float
    dynamic_range_improvement: float
    file_size_reduction: float
    timestamp: datetime = field(default_factory=datetime.now)

class AudioValidator:
    """
    Real-time audio validation system with adaptive quality thresholds.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('AudioValidator')
        
        # Quality thresholds (adaptive based on historical data)
        self.thresholds = {
            'min_quality_score': 70.0,
            'min_snr': 10.0,
            'max_noise_level': 0.3,
            'min_dynamic_range': 5.0,
            'max_clipping_ratio': 0.01,
            'min_duration': 0.5,
            'max_duration': 300.0,
            'target_sample_rate': 16000
        }
        
        # Historical data for adaptive thresholds
        self.quality_history = []
        self.max_history_size = 1000
        
    def validate_audio_quality(self, metrics: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate audio quality against adaptive thresholds.
        
        Args:
            metrics: Audio metrics dictionary
            
        Returns:
            List of validation results
        """
        results = []
        
        # Update adaptive thresholds based on history
        self._update_adaptive_thresholds()
        
        # Quality Score Validation
        quality_score = metrics.get('quality_score', 0)
        if quality_score < self.thresholds['min_quality_score']:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING if quality_score > 50 else ValidationLevel.ERROR,
                message=f"Audio quality score ({quality_score:.1f}) below threshold",
                metric_name="quality_score",
                current_value=quality_score,
                expected_range=(self.thresholds['min_quality_score'], 100),
                recommendation="Consider applying noise reduction and audio enhancement"
            ))
        
        # SNR Validation
        snr = metrics.get('signal_to_noise_ratio', 0)
        if snr < self.thresholds['min_snr']:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING if snr > 5 else ValidationLevel.ERROR,
                message=f"Signal-to-noise ratio ({snr:.1f} dB) below threshold",
                metric_name="signal_to_noise_ratio",
                current_value=snr,
                expected_range=(self.thresholds['min_snr'], 50),
                recommendation="Apply noise reduction or record in quieter environment"
            ))
        
        # Dynamic Range Validation
        dynamic_range = metrics.get('dynamic_range', 0)
        if dynamic_range < self.thresholds['min_dynamic_range']:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Dynamic range ({dynamic_range:.1f} dB) below threshold",
                metric_name="dynamic_range",
                current_value=dynamic_range,
                expected_range=(self.thresholds['min_dynamic_range'], 40),
                recommendation="Apply dynamic range compression or adjust recording levels"
            ))
        
        # Clipping Detection
        has_clipping = metrics.get('has_clipping', False)
        if has_clipping:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                message="Audio clipping detected",
                metric_name="has_clipping",
                current_value=1.0,
                expected_range=(0, 0),
                recommendation="Reduce input gain or apply limiting before recording"
            ))
        
        # Duration Validation
        duration = metrics.get('duration', 0)
        if duration < self.thresholds['min_duration']:
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                message=f"Audio duration ({duration:.1f}s) very short",
                metric_name="duration",
                current_value=duration,
                expected_range=(self.thresholds['min_duration'], self.thresholds['max_duration']),
                recommendation="Ensure sufficient audio content for accurate transcription"
            ))
        elif duration > self.thresholds['max_duration']:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message=f"Audio duration ({duration:.1f}s) very long",
                metric_name="duration",
                current_value=duration,
                expected_range=(self.thresholds['min_duration'], self.thresholds['max_duration']),
                recommendation="Consider segmenting audio for better processing performance"
            ))
        
        # Sample Rate Validation
        sample_rate = metrics.get('sample_rate', 0)
        if sample_rate != self.thresholds['target_sample_rate']:
            results.append(ValidationResult(
                level=ValidationLevel.INFO,
                message=f"Sample rate ({sample_rate} Hz) not optimal",
                metric_name="sample_rate",
                current_value=sample_rate,
                expected_range=(self.thresholds['target_sample_rate'], self.thresholds['target_sample_rate']),
                recommendation=f"Resample to {self.thresholds['target_sample_rate']} Hz for optimal speech recognition"
            ))
        
        return results
    
    def _update_adaptive_thresholds(self):
        """Update thresholds based on historical performance data."""
        if len(self.quality_history) < 10:
            return
        
        # Calculate adaptive thresholds based on historical data
        recent_scores = [entry['quality_score'] for entry in self.quality_history[-100:]]
        
        if recent_scores:
            avg_score = statistics.mean(recent_scores)
            std_score = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0
            
            # Adjust minimum quality threshold based on recent performance
            self.thresholds['min_quality_score'] = max(50, avg_score - 2 * std_score)
    
    def add_quality_data(self, metrics: Dict[str, Any]):
        """Add quality data to historical tracking."""
        self.quality_history.append({
            'quality_score': metrics.get('quality_score', 0),
            'snr': metrics.get('signal_to_noise_ratio', 0),
            'timestamp': datetime.now()
        })
        
        # Limit history size
        if len(self.quality_history) > self.max_history_size:
            self.quality_history = self.quality_history[-self.max_history_size:]

class PerformanceMonitor:
    """
    Real-time performance monitoring and metrics collection.
    """
    
    def __init__(self, max_history_size: int = 1000):
        self.logger = logging.getLogger('PerformanceMonitor')
        self.max_history_size = max_history_size
        
        # Performance metrics storage
        self.processing_history = []
        self.quality_improvements = []
        self.error_log = []
        
        # Real-time statistics
        self.current_stats = {
            'total_files_processed': 0,
            'average_processing_time': 0.0,
            'average_quality_improvement': 0.0,
            'success_rate': 100.0,
            'last_update': datetime.now()
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'max_processing_time': 30.0,  # seconds
            'min_success_rate': 95.0,     # percentage
            'max_error_rate': 5.0         # percentage
        }
    
    def record_processing_metrics(self, metrics: ProcessingMetrics):
        """Record processing performance metrics."""
        self.processing_history.append(metrics)
        
        # Update current statistics
        self._update_current_stats()
        
        # Check for performance issues
        self._check_performance_thresholds(metrics)
        
        # Limit history size
        if len(self.processing_history) > self.max_history_size:
            self.processing_history = self.processing_history[-self.max_history_size:]
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Record processing errors for analysis."""
        error_entry = {
            'type': error_type,
            'message': error_message,
            'context': context or {},
            'timestamp': datetime.now()
        }
        
        self.error_log.append(error_entry)
        self.logger.error(f"Processing error: {error_type} - {error_message}")
        
        # Update statistics
        self._update_current_stats()
        
        # Limit error log size
        if len(self.error_log) > self.max_history_size:
            self.error_log = self.error_log[-self.max_history_size:]
    
    def get_performance_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get performance summary for specified time window.
        
        Args:
            time_window: Time window for analysis (default: last hour)
            
        Returns:
            Performance summary dictionary
        """
        if time_window is None:
            time_window = timedelta(hours=1)
        
        cutoff_time = datetime.now() - time_window
        
        # Filter recent data
        recent_processing = [m for m in self.processing_history if m.timestamp >= cutoff_time]
        recent_errors = [e for e in self.error_log if e['timestamp'] >= cutoff_time]
        
        if not recent_processing:
            return {
                'time_window': str(time_window),
                'files_processed': 0,
                'average_processing_time': 0.0,
                'average_quality_improvement': 0.0,
                'error_count': len(recent_errors),
                'success_rate': 0.0
            }
        
        # Calculate statistics
        processing_times = [m.processing_time for m in recent_processing]
        quality_improvements = [m.quality_score for m in recent_processing]
        
        total_operations = len(recent_processing) + len(recent_errors)
        success_rate = (len(recent_processing) / total_operations * 100) if total_operations > 0 else 0
        
        return {
            'time_window': str(time_window),
            'files_processed': len(recent_processing),
            'average_processing_time': statistics.mean(processing_times),
            'median_processing_time': statistics.median(processing_times),
            'average_quality_improvement': statistics.mean(quality_improvements),
            'error_count': len(recent_errors),
            'success_rate': success_rate,
            'performance_trend': self._calculate_performance_trend(recent_processing)
        }
    
    def _update_current_stats(self):
        """Update current performance statistics."""
        if not self.processing_history:
            return
        
        # Calculate overall statistics
        processing_times = [m.processing_time for m in self.processing_history]
        quality_scores = [m.quality_score for m in self.processing_history]
        
        total_operations = len(self.processing_history) + len(self.error_log)
        
        self.current_stats.update({
            'total_files_processed': len(self.processing_history),
            'average_processing_time': statistics.mean(processing_times),
            'average_quality_improvement': statistics.mean(quality_scores),
            'success_rate': (len(self.processing_history) / total_operations * 100) if total_operations > 0 else 100.0,
            'last_update': datetime.now()
        })
    
    def _check_performance_thresholds(self, metrics: ProcessingMetrics):
        """Check if performance metrics exceed thresholds."""
        # Check processing time
        if metrics.processing_time > self.performance_thresholds['max_processing_time']:
            self.logger.warning(f"Processing time ({metrics.processing_time:.1f}s) exceeds threshold")
        
        # Check success rate
        if self.current_stats['success_rate'] < self.performance_thresholds['min_success_rate']:
            self.logger.warning(f"Success rate ({self.current_stats['success_rate']:.1f}%) below threshold")
    
    def _calculate_performance_trend(self, recent_data: List[ProcessingMetrics]) -> str:
        """Calculate performance trend from recent data."""
        if len(recent_data) < 5:
            return "insufficient_data"
        
        # Split data into two halves and compare
        mid_point = len(recent_data) // 2
        first_half = recent_data[:mid_point]
        second_half = recent_data[mid_point:]
        
        first_avg = statistics.mean([m.processing_time for m in first_half])
        second_avg = statistics.mean([m.processing_time for m in second_half])
        
        if second_avg < first_avg * 0.9:
            return "improving"
        elif second_avg > first_avg * 1.1:
            return "degrading"
        else:
            return "stable"

class RealtimeAudioMonitor:
    """
    Comprehensive real-time audio monitoring system.
    """
    
    def __init__(self, 
                 validation_enabled: bool = True,
                 performance_monitoring_enabled: bool = True,
                 alert_callback: Optional[Callable] = None):
        """
        Initialize real-time audio monitor.
        
        Args:
            validation_enabled: Enable audio quality validation
            performance_monitoring_enabled: Enable performance monitoring
            alert_callback: Callback function for alerts
        """
        self.validation_enabled = validation_enabled
        self.performance_monitoring_enabled = performance_monitoring_enabled
        self.alert_callback = alert_callback
        
        self.logger = logging.getLogger('RealtimeAudioMonitor')
        
        # Initialize components
        self.validator = AudioValidator() if validation_enabled else None
        self.performance_monitor = PerformanceMonitor() if performance_monitoring_enabled else None
        
        # Monitoring state
        self.status = ProcessingStatus.IDLE
        self.current_file = None
        self.monitoring_active = False
        
        # Alert queue for non-blocking notifications
        self.alert_queue = queue.Queue()
        self.alert_thread = None
        
        self.logger.info("Real-time Audio Monitor initialized")
    
    def start_monitoring(self):
        """Start real-time monitoring."""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.status = ProcessingStatus.IDLE
        
        # Start alert processing thread
        if self.alert_callback:
            self.alert_thread = threading.Thread(target=self._process_alerts, daemon=True)
            self.alert_thread.start()
        
        self.logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        self.status = ProcessingStatus.IDLE
        
        # Stop alert processing
        if self.alert_thread and self.alert_thread.is_alive():
            self.alert_queue.put(None)  # Signal to stop
            self.alert_thread.join(timeout=1.0)
        
        self.logger.info("Real-time monitoring stopped")
    
    def validate_audio(self, metrics: Dict[str, Any], file_path: str = None) -> List[ValidationResult]:
        """
        Validate audio quality in real-time.
        
        Args:
            metrics: Audio quality metrics
            file_path: Optional file path for context
            
        Returns:
            List of validation results
        """
        if not self.validation_enabled or not self.validator:
            return []
        
        self.status = ProcessingStatus.VALIDATING
        self.current_file = file_path
        
        try:
            results = self.validator.validate_audio_quality(metrics)
            
            # Add quality data to historical tracking
            self.validator.add_quality_data(metrics)
            
            # Process alerts for critical issues
            for result in results:
                if result.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
                    self._queue_alert(result)
            
            self.status = ProcessingStatus.COMPLETE
            return results
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            self.status = ProcessingStatus.ERROR
            return []
    
    def record_processing_performance(self, 
                                    processing_time: float,
                                    quality_score: float,
                                    improvements: Dict[str, float]):
        """
        Record processing performance metrics.
        
        Args:
            processing_time: Time taken for processing
            quality_score: Final quality score
            improvements: Dictionary of quality improvements
        """
        if not self.performance_monitoring_enabled or not self.performance_monitor:
            return
        
        metrics = ProcessingMetrics(
            processing_time=processing_time,
            quality_score=quality_score,
            snr_improvement=improvements.get('snr', 0.0),
            noise_reduction_db=improvements.get('noise_reduction', 0.0),
            dynamic_range_improvement=improvements.get('dynamic_range', 0.0),
            file_size_reduction=improvements.get('file_size_reduction', 0.0)
        )
        
        self.performance_monitor.record_processing_metrics(metrics)
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Record processing error."""
        if self.performance_monitoring_enabled and self.performance_monitor:
            self.performance_monitor.record_error(error_type, error_message, context)
        
        self.status = ProcessingStatus.ERROR
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics."""
        status_info = {
            'monitoring_active': self.monitoring_active,
            'current_status': self.status.value,
            'current_file': self.current_file,
            'validation_enabled': self.validation_enabled,
            'performance_monitoring_enabled': self.performance_monitoring_enabled
        }
        
        # Add performance statistics if available
        if self.performance_monitoring_enabled and self.performance_monitor:
            status_info['performance_stats'] = self.performance_monitor.current_stats
            status_info['recent_performance'] = self.performance_monitor.get_performance_summary()
        
        return status_info
    
    def _queue_alert(self, validation_result: ValidationResult):
        """Queue alert for processing."""
        if self.alert_callback and self.monitoring_active:
            self.alert_queue.put(validation_result)
    
    def _process_alerts(self):
        """Process alerts in background thread."""
        while self.monitoring_active:
            try:
                alert = self.alert_queue.get(timeout=1.0)
                if alert is None:  # Stop signal
                    break
                
                if self.alert_callback:
                    self.alert_callback(alert)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Alert processing error: {str(e)}")

# Example usage and alert callback
def example_alert_callback(validation_result: ValidationResult):
    """Example alert callback function."""
    print(f"ALERT [{validation_result.level.value.upper()}]: {validation_result.message}")
    print(f"Recommendation: {validation_result.recommendation}")

if __name__ == "__main__":
    # Initialize monitor
    monitor = RealtimeAudioMonitor(
        validation_enabled=True,
        performance_monitoring_enabled=True,
        alert_callback=example_alert_callback
    )
    
    print("Real-time Audio Monitor initialized successfully!")
    print("Available features:")
    print("- Real-time audio quality validation")
    print("- Performance monitoring and metrics")
    print("- Adaptive quality thresholds")
    print("- Alert system for critical issues")
    print("- Historical data tracking")
