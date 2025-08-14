"""Enhanced monitoring and metrics for Jira-GitHub integration."""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WebhookMetrics:
    """Metrics for webhook processing."""
    total_webhooks_received: int = 0
    successful_jira_creations: int = 0
    duplicate_detections: int = 0
    errors: int = 0
    processing_times: list = field(default_factory=list)
    last_activity: Optional[datetime] = None


class MonitoringService:
    """Service for monitoring webhook performance and statistics."""
    
    def __init__(self):
        self.metrics = WebhookMetrics()
        self.start_time = datetime.now()
    
    def record_webhook_received(self):
        """Record that a webhook was received."""
        self.metrics.total_webhooks_received += 1
        self.metrics.last_activity = datetime.now()
    
    def record_jira_creation(self, processing_time: float):
        """Record successful Jira issue creation."""
        self.metrics.successful_jira_creations += 1
        self.metrics.processing_times.append(processing_time)
    
    def record_duplicate_detection(self):
        """Record duplicate issue detection."""
        self.metrics.duplicate_detections += 1
    
    def record_error(self):
        """Record an error occurred."""
        self.metrics.errors += 1
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        uptime = datetime.now() - self.start_time
        avg_processing_time = (
            sum(self.metrics.processing_times) / len(self.metrics.processing_times)
            if self.metrics.processing_times else 0
        )
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_webhooks": self.metrics.total_webhooks_received,
            "successful_creations": self.metrics.successful_jira_creations,
            "duplicates_prevented": self.metrics.duplicate_detections,
            "errors": self.metrics.errors,
            "average_processing_time": avg_processing_time,
            "last_activity": self.metrics.last_activity.isoformat() if self.metrics.last_activity else None,
            "success_rate": (
                self.metrics.successful_jira_creations / max(1, self.metrics.total_webhooks_received) * 100
            )
        }


# Global monitoring instance
monitoring = MonitoringService()
