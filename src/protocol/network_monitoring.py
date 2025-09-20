"""
Network Monitoring and Anomaly Detection System.
Implements comprehensive monitoring to detect malicious relays and network attacks.
"""

import asyncio
import hashlib
import json
import os
import time
import statistics
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

from .encryption import EndToEndEncryption
from .mesh_network import MeshNetwork, RelayNode


class AnomalyType(Enum):
    """Types of detected anomalies."""
    
    TRAFFIC_SPIKE = "traffic_spike"
    UNUSUAL_PATTERNS = "unusual_patterns"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    NETWORK_ANOMALY = "network_anomaly"
    RELAY_MALFUNCTION = "relay_malfunction"
    ATTACK_DETECTED = "attack_detected"


class ThreatLevel(Enum):
    """Threat levels for detected anomalies."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NetworkMetric:
    """Network metric for monitoring."""
    
    metric_type: str
    value: float
    timestamp: int
    relay_id: Optional[bytes] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "timestamp": self.timestamp,
            "relay_id": self.relay_id.hex() if self.relay_id else None,
            "metadata": self.metadata or {}
        }


@dataclass
class AnomalyDetection:
    """Anomaly detection result."""
    
    anomaly_id: bytes
    anomaly_type: AnomalyType
    threat_level: ThreatLevel
    relay_id: bytes
    timestamp: int
    confidence: float
    evidence: Dict[str, Any]
    mitigation_applied: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "anomaly_id": self.anomaly_id.hex(),
            "anomaly_type": self.anomaly_type.value,
            "threat_level": self.threat_level.value,
            "relay_id": self.relay_id.hex(),
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "mitigation_applied": self.mitigation_applied
        }


class NetworkMonitoringSystem:
    """Comprehensive network monitoring and anomaly detection system."""
    
    def __init__(self, mesh_network: MeshNetwork):
        self.mesh_network = mesh_network
        self.encryption = EndToEndEncryption()
        
        # Monitoring data
        self.network_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.relay_metrics: Dict[bytes, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=100)))
        self.anomaly_detections: List[AnomalyDetection] = []
        self.suspicious_relays: Dict[bytes, float] = {}  # relay_id -> suspicion_score
        
        # Baseline data
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        self.normal_patterns: Dict[str, List[float]] = {}
        
        # Configuration
        self.monitoring_interval = 10  # 10 seconds
        self.anomaly_threshold = 2.0  # Standard deviations from mean
        self.suspicion_threshold = 0.7  # Suspicion score threshold
        self.baseline_period = 3600  # 1 hour baseline period
        self.metric_retention = 86400  # 24 hours retention
        
        # Statistics
        self.stats = {
            "metrics_collected": 0,
            "anomalies_detected": 0,
            "suspicious_relays": 0,
            "false_positives": 0,
            "true_positives": 0,
            "monitoring_uptime": 0
        }
        
        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.analysis_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Start time for uptime calculation
        self.start_time = int(time.time())
    
    async def start_monitoring_service(self) -> None:
        """Start the network monitoring service."""
        print("📊 Starting network monitoring service...")
        
        # Initialize baseline metrics
        await self._initialize_baseline_metrics()
        
        # Start background tasks
        self.monitoring_task = asyncio.create_task(self._continuous_monitoring())
        self.analysis_task = asyncio.create_task(self._continuous_analysis())
        self.cleanup_task = asyncio.create_task(self._cleanup_old_data())
        
        print("✅ Network monitoring service started")
    
    async def _initialize_baseline_metrics(self) -> None:
        """Initialize baseline metrics for anomaly detection."""
        # Set initial baselines
        self.baseline_metrics = {
            "message_frequency": {"mean": 10.0, "std": 2.0},
            "message_size": {"mean": 1024.0, "std": 512.0},
            "response_time": {"mean": 100.0, "std": 50.0},
            "connection_count": {"mean": 5.0, "std": 2.0},
            "error_rate": {"mean": 0.01, "std": 0.005}
        }
        
        # Initialize normal patterns
        self.normal_patterns = {
            "message_frequency": [10.0, 12.0, 8.0, 15.0, 9.0],
            "message_size": [1024.0, 2048.0, 512.0, 1536.0, 768.0],
            "response_time": [100.0, 120.0, 80.0, 150.0, 90.0]
        }
    
    async def _continuous_monitoring(self) -> None:
        """Continuous monitoring of network metrics."""
        while True:
            await asyncio.sleep(self.monitoring_interval)
            
            # Collect network metrics
            await self._collect_network_metrics()
            
            # Collect relay-specific metrics
            await self._collect_relay_metrics()
            
            # Update statistics
            self.stats["metrics_collected"] += 1
            self.stats["monitoring_uptime"] = int(time.time()) - self.start_time
    
    async def _collect_network_metrics(self) -> None:
        """Collect network-wide metrics."""
        current_time = int(time.time())
        
        # Message frequency
        message_count = await self._count_messages_in_period(60)  # Last minute
        self.network_metrics["message_frequency"].append(
            NetworkMetric("message_frequency", message_count, current_time)
        )
        
        # Average message size
        avg_message_size = await self._calculate_average_message_size()
        self.network_metrics["message_size"].append(
            NetworkMetric("message_size", avg_message_size, current_time)
        )
        
        # Network response time
        avg_response_time = await self._calculate_average_response_time()
        self.network_metrics["response_time"].append(
            NetworkMetric("response_time", avg_response_time, current_time)
        )
        
        # Active connections
        connection_count = len(self.mesh_network.known_nodes)
        self.network_metrics["connection_count"].append(
            NetworkMetric("connection_count", connection_count, current_time)
        )
        
        # Error rate
        error_rate = await self._calculate_error_rate()
        self.network_metrics["error_rate"].append(
            NetworkMetric("error_rate", error_rate, current_time)
        )
    
    async def _collect_relay_metrics(self) -> None:
        """Collect relay-specific metrics."""
        current_time = int(time.time())
        
        for relay_id in self.mesh_network.known_nodes:
            # Message frequency from this relay
            relay_message_count = await self._count_messages_from_relay(relay_id, 60)
            self.relay_metrics[relay_id]["message_frequency"].append(
                NetworkMetric("message_frequency", relay_message_count, current_time, relay_id)
            )
            
            # Response time to this relay
            response_time = await self._measure_relay_response_time(relay_id)
            self.relay_metrics[relay_id]["response_time"].append(
                NetworkMetric("response_time", response_time, current_time, relay_id)
            )
            
            # Error rate from this relay
            error_rate = await self._calculate_relay_error_rate(relay_id)
            self.relay_metrics[relay_id]["error_rate"].append(
                NetworkMetric("error_rate", error_rate, current_time, relay_id)
            )
    
    async def _continuous_analysis(self) -> None:
        """Continuous analysis for anomaly detection."""
        while True:
            await asyncio.sleep(30)  # Analyze every 30 seconds
            
            # Detect network-wide anomalies
            await self._detect_network_anomalies()
            
            # Detect relay-specific anomalies
            await self._detect_relay_anomalies()
            
            # Update baseline metrics
            await self._update_baseline_metrics()
    
    async def _detect_network_anomalies(self) -> None:
        """Detect network-wide anomalies."""
        for metric_type, metrics in self.network_metrics.items():
            if len(metrics) < 10:  # Need minimum data
                continue
            
            # Get recent values
            recent_values = [m.value for m in list(metrics)[-10:]]
            
            # Check for anomalies
            anomaly_score = await self._calculate_anomaly_score(metric_type, recent_values)
            
            if anomaly_score > self.anomaly_threshold:
                await self._handle_network_anomaly(metric_type, anomaly_score, recent_values)
    
    async def _detect_relay_anomalies(self) -> None:
        """Detect relay-specific anomalies."""
        for relay_id, metrics in self.relay_metrics.items():
            if relay_id in self.mesh_network.first_ring:
                continue  # Skip first ring members
            
            # Check each metric type
            for metric_type, metric_list in metrics.items():
                if len(metric_list) < 5:  # Need minimum data
                    continue
                
                # Get recent values
                recent_values = [m.value for m in list(metric_list)[-5:]]
                
                # Check for anomalies
                anomaly_score = await self._calculate_relay_anomaly_score(relay_id, metric_type, recent_values)
                
                if anomaly_score > self.anomaly_threshold:
                    await self._handle_relay_anomaly(relay_id, metric_type, anomaly_score, recent_values)
    
    async def _calculate_anomaly_score(self, metric_type: str, values: List[float]) -> float:
        """Calculate anomaly score for network metric."""
        try:
            if not values:
                return 0.0
            
            # Get baseline
            baseline = self.baseline_metrics.get(metric_type, {"mean": 0.0, "std": 1.0})
            baseline_mean = baseline["mean"]
            baseline_std = baseline["std"]
            
            if baseline_std == 0:
                return 0.0
            
            # Calculate current mean
            current_mean = statistics.mean(values)
            
            # Calculate z-score
            z_score = abs(current_mean - baseline_mean) / baseline_std
            
            return z_score
            
        except Exception as e:
            print(f"Error calculating anomaly score: {e}")
            return 0.0
    
    async def _calculate_relay_anomaly_score(self, relay_id: bytes, metric_type: str, values: List[float]) -> float:
        """Calculate anomaly score for relay metric."""
        try:
            if not values:
                return 0.0
            
            # Get network baseline
            network_baseline = self.baseline_metrics.get(metric_type, {"mean": 0.0, "std": 1.0})
            
            # Calculate relay-specific baseline
            relay_metrics = self.relay_metrics[relay_id][metric_type]
            if len(relay_metrics) < 10:
                # Use network baseline
                baseline_mean = network_baseline["mean"]
                baseline_std = network_baseline["std"]
            else:
                # Use relay-specific baseline
                relay_values = [m.value for m in list(relay_metrics)[-20:]]
                baseline_mean = statistics.mean(relay_values)
                baseline_std = statistics.stdev(relay_values) if len(relay_values) > 1 else network_baseline["std"]
            
            if baseline_std == 0:
                return 0.0
            
            # Calculate current mean
            current_mean = statistics.mean(values)
            
            # Calculate z-score
            z_score = abs(current_mean - baseline_mean) / baseline_std
            
            return z_score
            
        except Exception as e:
            print(f"Error calculating relay anomaly score: {e}")
            return 0.0
    
    async def _handle_network_anomaly(self, metric_type: str, anomaly_score: float, values: List[float]) -> None:
        """Handle detected network anomaly."""
        # Determine threat level
        if anomaly_score > 4.0:
            threat_level = ThreatLevel.CRITICAL
        elif anomaly_score > 3.0:
            threat_level = ThreatLevel.HIGH
        elif anomaly_score > 2.0:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        # Create anomaly detection
        anomaly = AnomalyDetection(
            anomaly_id=os.urandom(16),
            anomaly_type=AnomalyType.NETWORK_ANOMALY,
            threat_level=threat_level,
            relay_id=b"network",  # Network-wide anomaly
            timestamp=int(time.time()),
            confidence=min(anomaly_score / 5.0, 1.0),
            evidence={
                "metric_type": metric_type,
                "anomaly_score": anomaly_score,
                "values": values,
                "baseline": self.baseline_metrics.get(metric_type, {})
            },
            mitigation_applied=False
        )
        
        self.anomaly_detections.append(anomaly)
        self.stats["anomalies_detected"] += 1
        
        print(f"🚨 Network anomaly detected: {metric_type} (Score: {anomaly_score:.2f}, Level: {threat_level.value})")
        
        # Apply mitigation if critical
        if threat_level == ThreatLevel.CRITICAL:
            await self._apply_network_mitigation(metric_type, anomaly_score)
    
    async def _handle_relay_anomaly(self, relay_id: bytes, metric_type: str, anomaly_score: float, values: List[float]) -> None:
        """Handle detected relay anomaly."""
        # Determine threat level
        if anomaly_score > 4.0:
            threat_level = ThreatLevel.CRITICAL
        elif anomaly_score > 3.0:
            threat_level = ThreatLevel.HIGH
        elif anomaly_score > 2.0:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW
        
        # Create anomaly detection
        anomaly = AnomalyDetection(
            anomaly_id=os.urandom(16),
            anomaly_type=AnomalyType.SUSPICIOUS_BEHAVIOR,
            threat_level=threat_level,
            relay_id=relay_id,
            timestamp=int(time.time()),
            confidence=min(anomaly_score / 5.0, 1.0),
            evidence={
                "metric_type": metric_type,
                "anomaly_score": anomaly_score,
                "values": values,
                "relay_id": relay_id.hex()
            },
            mitigation_applied=False
        )
        
        self.anomaly_detections.append(anomaly)
        self.stats["anomalies_detected"] += 1
        
        # Update suspicion score
        if relay_id not in self.suspicious_relays:
            self.suspicious_relays[relay_id] = 0.0
        
        self.suspicious_relays[relay_id] += anomaly_score * 0.1
        
        print(f"🚨 Relay anomaly detected: {relay_id.hex()} - {metric_type} (Score: {anomaly_score:.2f}, Level: {threat_level.value})")
        
        # Check if relay should be blocked
        if self.suspicious_relays[relay_id] > self.suspicion_threshold:
            await self._block_suspicious_relay(relay_id, f"anomaly_{metric_type}")
        
        # Apply mitigation if critical
        if threat_level == ThreatLevel.CRITICAL:
            await self._apply_relay_mitigation(relay_id, metric_type, anomaly_score)
    
    async def _apply_network_mitigation(self, metric_type: str, anomaly_score: float) -> None:
        """Apply mitigation for network anomaly."""
        print(f"🛡️ Applying network mitigation for {metric_type}")
        
        # Adjust monitoring parameters
        if metric_type == "message_frequency" and anomaly_score > 3.0:
            # Reduce message processing rate
            await self._throttle_message_processing()
        
        elif metric_type == "error_rate" and anomaly_score > 3.0:
            # Increase error handling
            await self._enhance_error_handling()
        
        elif metric_type == "response_time" and anomaly_score > 3.0:
            # Optimize network routing
            await self._optimize_network_routing()
    
    async def _apply_relay_mitigation(self, relay_id: bytes, metric_type: str, anomaly_score: float) -> None:
        """Apply mitigation for relay anomaly."""
        print(f"🛡️ Applying relay mitigation for {relay_id.hex()}")
        
        # Block relay if critical
        if anomaly_score > 4.0:
            await self._block_suspicious_relay(relay_id, f"critical_anomaly_{metric_type}")
        
        # Throttle relay if high
        elif anomaly_score > 3.0:
            await self._throttle_relay(relay_id)
        
        # Monitor more closely if medium
        elif anomaly_score > 2.0:
            await self._increase_relay_monitoring(relay_id)
    
    async def _block_suspicious_relay(self, relay_id: bytes, reason: str) -> None:
        """Block a suspicious relay."""
        # Remove from known nodes
        if relay_id in self.mesh_network.known_nodes:
            del self.mesh_network.known_nodes[relay_id]
        
        # Remove from first ring if present
        self.mesh_network.first_ring.discard(relay_id)
        
        # Clear metrics
        if relay_id in self.relay_metrics:
            del self.relay_metrics[relay_id]
        
        # Clear suspicion score
        if relay_id in self.suspicious_relays:
            del self.suspicious_relays[relay_id]
        
        self.stats["suspicious_relays"] += 1
        
        print(f"🚫 Blocked suspicious relay {relay_id.hex()}: {reason}")
    
    async def _throttle_message_processing(self) -> None:
        """Throttle message processing to reduce load."""
        print("⏳ Throttling message processing")
        # Implementation would adjust message processing rate
    
    async def _enhance_error_handling(self) -> None:
        """Enhance error handling mechanisms."""
        print("🔧 Enhancing error handling")
        # Implementation would improve error handling
    
    async def _optimize_network_routing(self) -> None:
        """Optimize network routing for better performance."""
        print("🛣️ Optimizing network routing")
        # Implementation would optimize routing
    
    async def _throttle_relay(self, relay_id: bytes) -> None:
        """Throttle communication with a specific relay."""
        print(f"⏳ Throttling relay {relay_id.hex()}")
        # Implementation would throttle relay communication
    
    async def _increase_relay_monitoring(self, relay_id: bytes) -> None:
        """Increase monitoring for a specific relay."""
        print(f"👁️ Increasing monitoring for relay {relay_id.hex()}")
        # Implementation would increase monitoring frequency
    
    async def _update_baseline_metrics(self) -> None:
        """Update baseline metrics based on recent data."""
        current_time = int(time.time())
        
        for metric_type, metrics in self.network_metrics.items():
            if len(metrics) < 20:  # Need minimum data
                continue
            
            # Get recent values (last hour)
            recent_metrics = [m for m in metrics if current_time - m.timestamp < self.baseline_period]
            if len(recent_metrics) < 10:
                continue
            
            values = [m.value for m in recent_metrics]
            
            # Calculate new baseline
            new_mean = statistics.mean(values)
            new_std = statistics.stdev(values) if len(values) > 1 else 0.0
            
            # Update baseline
            self.baseline_metrics[metric_type] = {
                "mean": new_mean,
                "std": new_std
            }
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data."""
        while True:
            await asyncio.sleep(3600)  # Clean up every hour
            
            current_time = int(time.time())
            
            # Clean up old metrics
            for metric_type, metrics in self.network_metrics.items():
                # Remove metrics older than retention period
                while metrics and current_time - metrics[0].timestamp > self.metric_retention:
                    metrics.popleft()
            
            # Clean up old relay metrics
            for relay_id, relay_metric_dict in self.relay_metrics.items():
                for metric_type, metrics in relay_metric_dict.items():
                    while metrics and current_time - metrics[0].timestamp > self.metric_retention:
                        metrics.popleft()
            
            # Clean up old anomaly detections
            self.anomaly_detections = [
                anomaly for anomaly in self.anomaly_detections
                if current_time - anomaly.timestamp < self.metric_retention
            ]
            
            print("🧹 Cleaned up old monitoring data")
    
    # Helper methods for metric collection
    async def _count_messages_in_period(self, period_seconds: int) -> float:
        """Count messages in the last period."""
        # Simplified implementation
        return random.uniform(5, 20)
    
    async def _calculate_average_message_size(self) -> float:
        """Calculate average message size."""
        # Simplified implementation
        return random.uniform(512, 2048)
    
    async def _calculate_average_response_time(self) -> float:
        """Calculate average response time."""
        # Simplified implementation
        return random.uniform(50, 200)
    
    async def _calculate_error_rate(self) -> float:
        """Calculate network error rate."""
        # Simplified implementation
        return random.uniform(0.001, 0.05)
    
    async def _count_messages_from_relay(self, relay_id: bytes, period_seconds: int) -> float:
        """Count messages from specific relay."""
        # Simplified implementation
        return random.uniform(1, 10)
    
    async def _measure_relay_response_time(self, relay_id: bytes) -> float:
        """Measure response time to specific relay."""
        # Simplified implementation
        return random.uniform(50, 300)
    
    async def _calculate_relay_error_rate(self, relay_id: bytes) -> float:
        """Calculate error rate for specific relay."""
        # Simplified implementation
        return random.uniform(0.001, 0.1)
    
    def get_monitoring_status(self) -> Dict:
        """Get monitoring system status."""
        return {
            "active": True,
            "metrics_collected": self.stats["metrics_collected"],
            "anomalies_detected": self.stats["anomalies_detected"],
            "suspicious_relays": len(self.suspicious_relays),
            "monitoring_uptime": self.stats["monitoring_uptime"],
            "baseline_metrics": len(self.baseline_metrics),
            "relay_metrics": len(self.relay_metrics)
        }
    
    def get_anomaly_detections(self) -> List[Dict]:
        """Get recent anomaly detections."""
        return [anomaly.to_dict() for anomaly in self.anomaly_detections[-50:]]  # Last 50
    
    def get_suspicious_relays(self) -> Dict[str, float]:
        """Get suspicious relays with their scores."""
        return {
            relay_id.hex(): score 
            for relay_id, score in self.suspicious_relays.items()
        }
    
    def get_network_metrics(self, metric_type: str, limit: int = 100) -> List[Dict]:
        """Get network metrics for a specific type."""
        if metric_type not in self.network_metrics:
            return []
        
        metrics = list(self.network_metrics[metric_type])[-limit:]
        return [metric.to_dict() for metric in metrics]
    
    def get_relay_metrics(self, relay_id: bytes, metric_type: str, limit: int = 50) -> List[Dict]:
        """Get relay metrics for a specific relay and type."""
        if relay_id not in self.relay_metrics:
            return []
        
        if metric_type not in self.relay_metrics[relay_id]:
            return []
        
        metrics = list(self.relay_metrics[relay_id][metric_type])[-limit:]
        return [metric.to_dict() for metric in metrics]
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics."""
        return {
            **self.stats,
            "suspicious_relays_count": len(self.suspicious_relays),
            "anomaly_detections_count": len(self.anomaly_detections),
            "baseline_metrics_count": len(self.baseline_metrics),
            "relay_metrics_count": len(self.relay_metrics)
        }
    
    async def stop_monitoring_service(self) -> None:
        """Stop the network monitoring service."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        if self.analysis_task:
            self.analysis_task.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        print("🛑 Network monitoring service stopped")
