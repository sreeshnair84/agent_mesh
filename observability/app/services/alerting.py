"""
Alerting and notification service
"""

import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import httpx
import aioredis
from enum import Enum

from ..core.config import get_settings
from .metrics import MetricsCollector, MetricsQuery

logger = structlog.get_logger(__name__)
settings = get_settings()


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    duration: str
    severity: AlertSeverity
    description: str
    metric_name: str
    threshold: float
    operator: str  # >, <, >=, <=, ==, !=
    enabled: bool = True
    actions: List[Dict[str, Any]] = None
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.labels is None:
            self.labels = {}


@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    agent_id: Optional[str] = None
    metric_name: Optional[str] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class AlertingService:
    """Alerting and notification service"""
    
    def __init__(self):
        self.redis_client = None
        self.metrics_collector = MetricsCollector()
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.running = False
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Initialize default alert rules
        self._init_default_rules()
        
        # Initialize notification handlers
        self._init_notification_handlers()
    
    async def initialize(self):
        """Initialize the alerting service"""
        try:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            await self.metrics_collector.initialize()
            logger.info("Alerting service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize alerting service: {e}")
    
    def _init_default_rules(self):
        """Initialize default alert rules"""
        self.alert_rules = {
            "high_cpu_usage": AlertRule(
                name="high_cpu_usage",
                condition="cpu_usage > 80",
                duration="5m",
                severity=AlertSeverity.HIGH,
                description="CPU usage is above 80%",
                metric_name="cpu_usage_percent",
                threshold=80.0,
                operator=">",
                actions=[
                    {"type": "webhook", "url": "http://alertmanager:9093/api/v1/alerts"},
                    {"type": "email", "recipients": ["admin@company.com"]}
                ]
            ),
            "high_memory_usage": AlertRule(
                name="high_memory_usage",
                condition="memory_usage > 85",
                duration="5m",
                severity=AlertSeverity.HIGH,
                description="Memory usage is above 85%",
                metric_name="memory_usage_percent",
                threshold=85.0,
                operator=">",
                actions=[
                    {"type": "webhook", "url": "http://alertmanager:9093/api/v1/alerts"},
                    {"type": "email", "recipients": ["admin@company.com"]}
                ]
            ),
            "low_success_rate": AlertRule(
                name="low_success_rate",
                condition="success_rate < 95",
                duration="10m",
                severity=AlertSeverity.CRITICAL,
                description="Success rate is below 95%",
                metric_name="success_rate",
                threshold=95.0,
                operator="<",
                actions=[
                    {"type": "webhook", "url": "http://alertmanager:9093/api/v1/alerts"},
                    {"type": "email", "recipients": ["admin@company.com", "oncall@company.com"]},
                    {"type": "slack", "webhook_url": "https://hooks.slack.com/services/..."}
                ]
            ),
            "agent_failure": AlertRule(
                name="agent_failure",
                condition="agent_status == 'failed'",
                duration="1m",
                severity=AlertSeverity.CRITICAL,
                description="Agent has failed",
                metric_name="agent_status",
                threshold=0.0,
                operator="==",
                actions=[
                    {"type": "webhook", "url": "http://alertmanager:9093/api/v1/alerts"},
                    {"type": "email", "recipients": ["admin@company.com", "oncall@company.com"]}
                ]
            ),
            "slow_response_time": AlertRule(
                name="slow_response_time",
                condition="response_time > 2.0",
                duration="5m",
                severity=AlertSeverity.MEDIUM,
                description="Response time is above 2 seconds",
                metric_name="response_time_seconds",
                threshold=2.0,
                operator=">",
                actions=[
                    {"type": "webhook", "url": "http://alertmanager:9093/api/v1/alerts"}
                ]
            )
        }
    
    def _init_notification_handlers(self):
        """Initialize notification handlers"""
        self.notification_handlers = {
            "email": self._send_email_notification,
            "webhook": self._send_webhook_notification,
            "slack": self._send_slack_notification
        }
    
    async def start_monitoring(self):
        """Start alert monitoring"""
        self.running = True
        logger.info("Starting alert monitoring")
        
        # Start monitoring tasks
        await asyncio.gather(
            self._monitor_alert_rules(),
            self._process_alert_actions(),
            self._cleanup_resolved_alerts()
        )
    
    async def stop_monitoring(self):
        """Stop alert monitoring"""
        self.running = False
        logger.info("Stopping alert monitoring")
    
    async def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules[rule.name] = rule
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.setex(
                f"alert_rule:{rule.name}",
                86400,  # 24 hours TTL
                json.dumps({
                    "name": rule.name,
                    "condition": rule.condition,
                    "duration": rule.duration,
                    "severity": rule.severity.value,
                    "description": rule.description,
                    "metric_name": rule.metric_name,
                    "threshold": rule.threshold,
                    "operator": rule.operator,
                    "enabled": rule.enabled,
                    "actions": rule.actions,
                    "labels": rule.labels
                })
            )
        
        logger.info(f"Added alert rule: {rule.name}")
    
    async def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            
            # Remove from Redis
            if self.redis_client:
                await self.redis_client.delete(f"alert_rule:{rule_name}")
            
            logger.info(f"Removed alert rule: {rule_name}")
    
    async def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return list(self.alert_rules.values())
    
    async def get_alerts(self, status: Optional[AlertStatus] = None) -> List[Alert]:
        """Get alerts, optionally filtered by status"""
        alerts = list(self.active_alerts.values())
        
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        
        return alerts
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            # Update in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert:{alert_id}",
                    86400,  # 24 hours TTL
                    json.dumps({
                        "id": alert.id,
                        "rule_name": alert.rule_name,
                        "severity": alert.severity.value,
                        "status": alert.status.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                        "agent_id": alert.agent_id,
                        "metric_name": alert.metric_name,
                        "threshold": alert.threshold,
                        "current_value": alert.current_value,
                        "labels": alert.labels
                    })
                )
            
            logger.info(f"Resolved alert: {alert_id}")
    
    async def silence_alert(self, alert_id: str, duration: timedelta):
        """Silence an alert for a specific duration"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.SILENCED
            
            # Set silence expiry
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert_silence:{alert_id}",
                    int(duration.total_seconds()),
                    "silenced"
                )
            
            logger.info(f"Silenced alert: {alert_id} for {duration}")
    
    async def _monitor_alert_rules(self):
        """Monitor alert rules"""
        while self.running:
            try:
                for rule_name, rule in self.alert_rules.items():
                    if not rule.enabled:
                        continue
                    
                    # Check if alert should be triggered
                    should_trigger = await self._evaluate_alert_rule(rule)
                    
                    if should_trigger:
                        await self._trigger_alert(rule)
                    else:
                        # Check if alert should be resolved
                        await self._check_alert_resolution(rule)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring alert rules: {e}")
                await asyncio.sleep(10)
    
    async def _evaluate_alert_rule(self, rule: AlertRule) -> bool:
        """Evaluate if an alert rule should be triggered"""
        try:
            # Get recent metrics
            query = MetricsQuery(
                metric_names=[rule.metric_name],
                start_time=datetime.utcnow() - timedelta(minutes=10),
                end_time=datetime.utcnow()
            )
            
            result = await self.metrics_collector.get_metrics(query)
            
            if not result.metrics:
                return False
            
            # Get the latest metric value
            latest_metric = max(result.metrics, key=lambda m: m.timestamp)
            current_value = latest_metric.value
            
            # Evaluate condition
            if rule.operator == ">":
                return current_value > rule.threshold
            elif rule.operator == "<":
                return current_value < rule.threshold
            elif rule.operator == ">=":
                return current_value >= rule.threshold
            elif rule.operator == "<=":
                return current_value <= rule.threshold
            elif rule.operator == "==":
                return current_value == rule.threshold
            elif rule.operator == "!=":
                return current_value != rule.threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert rule {rule.name}: {e}")
            return False
    
    async def _trigger_alert(self, rule: AlertRule):
        """Trigger an alert"""
        try:
            # Check if alert is already active
            existing_alert = None
            for alert in self.active_alerts.values():
                if alert.rule_name == rule.name and alert.status == AlertStatus.ACTIVE:
                    existing_alert = alert
                    break
            
            if existing_alert:
                return  # Alert already active
            
            # Get current metric value
            query = MetricsQuery(
                metric_names=[rule.metric_name],
                start_time=datetime.utcnow() - timedelta(minutes=1),
                end_time=datetime.utcnow()
            )
            
            result = await self.metrics_collector.get_metrics(query)
            current_value = None
            
            if result.metrics:
                latest_metric = max(result.metrics, key=lambda m: m.timestamp)
                current_value = latest_metric.value
            
            # Create alert
            alert_id = f"alert-{rule.name}-{datetime.utcnow().timestamp()}"
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                message=rule.description,
                timestamp=datetime.utcnow(),
                metric_name=rule.metric_name,
                threshold=rule.threshold,
                current_value=current_value,
                labels=rule.labels
            )
            
            self.active_alerts[alert_id] = alert
            
            # Store in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert:{alert_id}",
                    86400,  # 24 hours TTL
                    json.dumps({
                        "id": alert.id,
                        "rule_name": alert.rule_name,
                        "severity": alert.severity.value,
                        "status": alert.status.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metric_name": alert.metric_name,
                        "threshold": alert.threshold,
                        "current_value": alert.current_value,
                        "labels": alert.labels
                    })
                )
            
            # Queue alert actions
            for action in rule.actions:
                await self._queue_alert_action(alert, action)
            
            logger.warning(f"Alert triggered: {rule.name} - {rule.description}")
            
        except Exception as e:
            logger.error(f"Error triggering alert {rule.name}: {e}")
    
    async def _send_email_notification(self, alert: Alert, action: Dict[str, Any]):
        """Send email notification"""
        try:
            recipients = action.get("recipients", [])
            if not recipients:
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"Alert: {alert.rule_name}"
            
            body = f"""
            Alert: {alert.rule_name}
            Severity: {alert.severity.value}
            Message: {alert.message}
            Time: {alert.timestamp.isoformat()}
            
            Current Value: {alert.current_value}
            Threshold: {alert.threshold}
            
            Labels: {alert.labels}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_webhook_notification(self, alert: Alert, action: Dict[str, Any]):
        """Send webhook notification"""
        try:
            webhook_url = action.get("url")
            if not webhook_url:
                return
            
            payload = {
                "id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metric_name": alert.metric_name,
                "threshold": alert.threshold,
                "current_value": alert.current_value,
                "labels": alert.labels
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook notification sent for alert: {alert.id}")
                else:
                    logger.error(f"Webhook notification failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert, action: Dict[str, Any]):
        """Send Slack notification"""
        try:
            webhook_url = action.get("webhook_url")
            if not webhook_url:
                return
            
            # Create Slack message
            color = {
                AlertSeverity.LOW: "good",
                AlertSeverity.MEDIUM: "warning",
                AlertSeverity.HIGH: "danger",
                AlertSeverity.CRITICAL: "danger"
            }.get(alert.severity, "warning")
            
            payload = {
                "text": f"Alert: {alert.rule_name}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value,
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.current_value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert.threshold),
                                "short": True
                            }
                        ],
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack notification sent for alert: {alert.id}")
                else:
                    logger.error(f"Slack notification failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            
    # Additional methods for alert processing...
    async def _check_alert_resolution(self, rule: AlertRule):
        """Check if alert should be resolved"""
        # Implementation continues...
        pass
    
    async def _queue_alert_action(self, alert: Alert, action: Dict[str, Any]):
        """Queue an alert action for processing"""
        # Implementation continues...
        pass
    
    async def _process_alert_actions(self):
        """Process queued alert actions"""
        # Implementation continues...
        pass
    
    async def _cleanup_resolved_alerts(self):
        """Clean up resolved alerts"""
        # Implementation continues...
        pass
        
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
