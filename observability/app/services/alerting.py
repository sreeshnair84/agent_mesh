"""
Alerting and notification service
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from ..core.config import get_settings
from ..core.database import get_db

logger = structlog.get_logger(__name__)

settings = get_settings()


class AlertingService:
    """Service for alerting and notifications"""
    
    def __init__(self):
        self.running = False
        self.alert_rules = []
        self.notification_channels = []
        self._init_alert_rules()
        self._init_notification_channels()
    
    def _init_alert_rules(self):
        """Initialize default alert rules"""
        self.alert_rules = [
            {
                "name": "High Error Rate",
                "condition": "error_rate > 0.05",
                "threshold": 0.05,
                "severity": "critical",
                "description": "Error rate is above 5%",
                "metric": "error_rate",
                "evaluation_window": 300,  # 5 minutes
                "cooldown": 900  # 15 minutes
            },
            {
                "name": "High Response Time",
                "condition": "avg_response_time > 1000",
                "threshold": 1000,
                "severity": "warning",
                "description": "Average response time is above 1 second",
                "metric": "avg_response_time",
                "evaluation_window": 300,
                "cooldown": 600
            },
            {
                "name": "Low Agent Availability",
                "condition": "active_agents < 1",
                "threshold": 1,
                "severity": "critical",
                "description": "Less than 1 agent is active",
                "metric": "active_agents",
                "evaluation_window": 60,
                "cooldown": 300
            },
            {
                "name": "High Memory Usage",
                "condition": "memory_usage > 0.8",
                "threshold": 0.8,
                "severity": "warning",
                "description": "Memory usage is above 80%",
                "metric": "memory_usage",
                "evaluation_window": 300,
                "cooldown": 600
            },
            {
                "name": "Database Connection Issues",
                "condition": "db_connection_errors > 5",
                "threshold": 5,
                "severity": "critical",
                "description": "Database connection errors detected",
                "metric": "db_connection_errors",
                "evaluation_window": 300,
                "cooldown": 900
            }
        ]
    
    def _init_notification_channels(self):
        """Initialize notification channels"""
        self.notification_channels = []
        
        # Slack webhook
        if settings.SLACK_WEBHOOK_URL:
            self.notification_channels.append({
                "type": "slack",
                "name": "Slack",
                "config": {
                    "webhook_url": settings.SLACK_WEBHOOK_URL
                }
            })
        
        # Email SMTP
        if settings.EMAIL_SMTP_HOST:
            self.notification_channels.append({
                "type": "email",
                "name": "Email",
                "config": {
                    "smtp_host": settings.EMAIL_SMTP_HOST,
                    "smtp_port": settings.EMAIL_SMTP_PORT,
                    "username": settings.EMAIL_USERNAME,
                    "password": settings.EMAIL_PASSWORD
                }
            })
    
    async def start_monitoring(self):
        """Start alert monitoring"""
        if not settings.ALERTING_ENABLED:
            logger.info("Alerting is disabled")
            return
        
        self.running = True
        logger.info("Starting alert monitoring")
        
        while self.running:
            try:
                await self._check_alerts()
                await asyncio.sleep(settings.ALERT_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(10)
    
    async def stop_monitoring(self):
        """Stop alert monitoring"""
        self.running = False
        logger.info("Stopping alert monitoring")
    
    async def _check_alerts(self):
        """Check all alert rules"""
        try:
            # Get current metrics
            metrics = await self._get_current_metrics()
            
            for rule in self.alert_rules:
                await self._evaluate_rule(rule, metrics)
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _get_current_metrics(self) -> Dict[str, float]:
        """Get current metrics for alert evaluation"""
        try:
            metrics = {}
            
            # Get metrics from backend
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.BACKEND_URL}/api/v1/metrics")
                if response.status_code == 200:
                    backend_metrics = response.json()
                    
                    # Extract key metrics
                    metrics.update({
                        "error_rate": backend_metrics.get("error_rate", 0.0),
                        "avg_response_time": backend_metrics.get("avg_response_time", 0.0),
                        "active_agents": backend_metrics.get("active_agents", 0),
                        "memory_usage": backend_metrics.get("memory_usage", 0.0),
                        "db_connection_errors": backend_metrics.get("db_connection_errors", 0)
                    })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {}
    
    async def _evaluate_rule(self, rule: Dict[str, Any], metrics: Dict[str, float]):
        """Evaluate a single alert rule"""
        try:
            metric_name = rule["metric"]
            threshold = rule["threshold"]
            current_value = metrics.get(metric_name, 0)
            
            # Check if alert condition is met
            if self._check_condition(rule["condition"], current_value, threshold):
                # Check if alert is not in cooldown
                if not await self._is_in_cooldown(rule["name"]):
                    await self._trigger_alert(rule, current_value)
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule['name']}: {e}")
    
    def _check_condition(self, condition: str, current_value: float, threshold: float) -> bool:
        """Check if alert condition is met"""
        try:
            if ">" in condition:
                return current_value > threshold
            elif "<" in condition:
                return current_value < threshold
            elif ">=" in condition:
                return current_value >= threshold
            elif "<=" in condition:
                return current_value <= threshold
            elif "==" in condition:
                return current_value == threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking condition {condition}: {e}")
            return False
    
    async def _is_in_cooldown(self, alert_name: str) -> bool:
        """Check if alert is in cooldown period"""
        # This would typically check a database or cache
        # For now, return False (no cooldown)
        return False
    
    async def _trigger_alert(self, rule: Dict[str, Any], current_value: float):
        """Trigger an alert"""
        try:
            alert_data = {
                "name": rule["name"],
                "severity": rule["severity"],
                "description": rule["description"],
                "current_value": current_value,
                "threshold": rule["threshold"],
                "timestamp": datetime.utcnow().isoformat(),
                "service": "agent-mesh"
            }
            
            logger.warning(f"Alert triggered: {alert_data}")
            
            # Send notifications
            await self._send_notifications(alert_data)
            
            # Record alert in database
            await self._record_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    async def _send_notifications(self, alert_data: Dict[str, Any]):
        """Send notifications to all configured channels"""
        for channel in self.notification_channels:
            try:
                if channel["type"] == "slack":
                    await self._send_slack_notification(channel, alert_data)
                elif channel["type"] == "email":
                    await self._send_email_notification(channel, alert_data)
                    
            except Exception as e:
                logger.error(f"Error sending notification to {channel['name']}: {e}")
    
    async def _send_slack_notification(self, channel: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send Slack notification"""
        try:
            webhook_url = channel["config"]["webhook_url"]
            
            # Format message
            color = "danger" if alert_data["severity"] == "critical" else "warning"
            message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 {alert_data['name']}",
                        "text": alert_data["description"],
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert_data["severity"].upper(),
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert_data["current_value"]),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert_data["threshold"]),
                                "short": True
                            },
                            {
                                "title": "Service",
                                "value": alert_data["service"],
                                "short": True
                            }
                        ],
                        "footer": "Agent Mesh Observability",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=message)
                if response.status_code != 200:
                    logger.error(f"Failed to send Slack notification: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    async def _send_email_notification(self, channel: Dict[str, Any], alert_data: Dict[str, Any]):
        """Send email notification"""
        try:
            config = channel["config"]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config["username"]
            msg['To'] = "admin@example.com"  # This should be configurable
            msg['Subject'] = f"🚨 Alert: {alert_data['name']}"
            
            # Create HTML body
            html_body = f"""
            <html>
                <body>
                    <h2 style="color: {'red' if alert_data['severity'] == 'critical' else 'orange'};">
                        🚨 {alert_data['name']}
                    </h2>
                    <p><strong>Description:</strong> {alert_data['description']}</p>
                    <p><strong>Severity:</strong> {alert_data['severity'].upper()}</p>
                    <p><strong>Current Value:</strong> {alert_data['current_value']}</p>
                    <p><strong>Threshold:</strong> {alert_data['threshold']}</p>
                    <p><strong>Service:</strong> {alert_data['service']}</p>
                    <p><strong>Timestamp:</strong> {alert_data['timestamp']}</p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])
            server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _record_alert(self, alert_data: Dict[str, Any]):
        """Record alert in database"""
        try:
            # This would typically save to database
            # For now, just log
            logger.info(f"Alert recorded: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Error recording alert: {e}")
    
    async def create_alert_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert rule"""
        try:
            # Validate rule data
            required_fields = ["name", "condition", "threshold", "severity", "metric"]
            for field in required_fields:
                if field not in rule_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add default values
            rule_data.setdefault("evaluation_window", 300)
            rule_data.setdefault("cooldown", 600)
            rule_data.setdefault("description", rule_data["name"])
            
            # Add to rules list
            self.alert_rules.append(rule_data)
            
            logger.info(f"Created alert rule: {rule_data['name']}")
            return rule_data
            
        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            raise
    
    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get all alert rules"""
        return self.alert_rules.copy()
    
    async def get_alert_history(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get alert history for a time range"""
        # This would typically query a database
        # For now, return mock data
        return [
            {
                "id": "alert-123",
                "name": "High Error Rate",
                "severity": "critical",
                "status": "resolved",
                "triggered_at": start_time.isoformat(),
                "resolved_at": end_time.isoformat(),
                "current_value": 0.08,
                "threshold": 0.05
            }
        ]
