# Observability Service Deployment

## Overview
This document describes the deployment and configuration of the comprehensive observability service that provides monitoring, alerting, and metrics collection for the Agent Mesh system.

## Architecture

### Core Components
- **MetricsCollector**: Collects and stores system metrics with Redis caching
- **MonitoringService**: Provides real-time system monitoring and network topology
- **AlertingService**: Handles alert rules, notifications, and lifecycle management
- **Integration Layer**: Interfaces with Team A (Core Framework) and Team B (Agent Management)

### Technology Stack
- **FastAPI**: REST API framework with WebSocket support
- **Redis**: Real-time caching and pub/sub messaging
- **PostgreSQL**: Primary database for metrics, logs, and alerts
- **Prometheus**: Metrics collection and exposition
- **WebSockets**: Real-time data streaming
- **SMTP/Slack/Webhook**: Multi-channel notification system

## API Endpoints

### Monitoring Endpoints
- `GET /api/v1/monitoring/overview` - System overview metrics
- `GET /api/v1/monitoring/agents` - Agent status and metrics
- `GET /api/v1/monitoring/topology` - Network topology visualization
- `GET /api/v1/monitoring/performance/trends` - Performance trend data
- `WS /api/v1/monitoring/ws/metrics` - Real-time metrics stream

### Metrics Endpoints
- `GET /api/v1/metrics` - Query metrics with filters
- `POST /api/v1/metrics/batch` - Batch metric ingestion
- `GET /api/v1/metrics/prometheus` - Prometheus metrics exposition

### Alert Endpoints
- `GET /api/v1/monitoring/alerts` - List active alerts
- `POST /api/v1/monitoring/alerts/{id}/resolve` - Resolve alert
- `POST /api/v1/monitoring/alerts/{id}/silence` - Silence alert
- `GET /api/v1/monitoring/alert-rules` - List alert rules
- `POST /api/v1/monitoring/alert-rules` - Create alert rule
- `PUT /api/v1/monitoring/alert-rules/{id}` - Update alert rule
- `DELETE /api/v1/monitoring/alert-rules/{id}` - Delete alert rule

### Notification Channels
- `GET /api/v1/monitoring/notification-channels` - List channels
- `POST /api/v1/monitoring/notification-channels` - Create channel
- `PUT /api/v1/monitoring/notification-channels/{id}` - Update channel
- `DELETE /api/v1/monitoring/notification-channels/{id}` - Delete channel

## Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/observability

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=observability@yourdomain.com
SMTP_TO=alerts@yourdomain.com
SMTP_TLS=true

# Webhook Configuration
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Performance Settings
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
METRICS_RETENTION_DAYS=30
LOGS_RETENTION_DAYS=7
ALERTS_RETENTION_DAYS=90
```

### Alert Rule Configuration
```json
{
  "name": "High CPU Usage",
  "description": "Alert when CPU usage exceeds 80%",
  "metric_name": "cpu_usage",
  "operator": "gt",
  "threshold": 80,
  "severity": "high",
  "enabled": true,
  "notification_channels": ["email", "slack"],
  "labels": {
    "team": "infrastructure",
    "environment": "production"
  }
}
```

## Frontend Integration

### Dashboard Components
- **ComprehensiveMonitoringDashboard**: Main monitoring dashboard
- **RealtimeMetricsChart**: Real-time metrics visualization
- **AlertManagement**: Alert configuration and management

### WebSocket Integration
```javascript
const ws = new WebSocket('ws://localhost:8002/api/v1/monitoring/ws/metrics')
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'system_overview') {
    updateSystemMetrics(data.data)
  }
}
```

## Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  observability:
    build: ./observability
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/observability
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=observability
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: observability-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: observability-service
  template:
    metadata:
      labels:
        app: observability-service
    spec:
      containers:
      - name: observability
        image: observability-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: observability-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: observability-secrets
              key: redis-url
---
apiVersion: v1
kind: Service
metadata:
  name: observability-service
spec:
  selector:
    app: observability-service
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

## Integration Guide

### Team A (Core Framework) Integration
```python
from observability.integration import CoreFrameworkIntegration

# Initialize integration
integration = CoreFrameworkIntegration()

# Record message processing metrics
await integration.record_message_processing_time(
    agent_id="agent-123",
    message_type="user_query",
    processing_time=0.5,
    success=True
)

# Record workflow execution
await integration.record_workflow_execution(
    workflow_id="workflow-456",
    agent_id="agent-123",
    duration=2.3,
    success=True
)
```

### Team B (Agent Management) Integration
```python
from observability.integration import AgentLifecycleMonitor

# Initialize monitoring
monitor = AgentLifecycleMonitor()

# Track agent lifecycle
await monitor.on_agent_created(agent_id="agent-789", agent_type="customer_support")
await monitor.on_agent_deployed(agent_id="agent-789", deployment_config={})
await monitor.on_agent_scaled(agent_id="agent-789", replicas=3)
await monitor.on_agent_terminated(agent_id="agent-789", reason="user_request")
```

## Monitoring and Alerting

### Key Metrics
- **System Metrics**: CPU, memory, disk usage
- **Agent Metrics**: Active/inactive agents, success rates, response times
- **Request Metrics**: Request count, latency, error rates
- **Custom Metrics**: Business-specific KPIs

### Alert Severities
- **Critical**: System down, high error rates (>5%)
- **High**: High latency (>1s), agent failures
- **Medium**: Resource usage (>80%), slow response times
- **Low**: Info alerts, maintenance notifications

### Notification Channels
- **Email**: SMTP integration for email alerts
- **Slack**: Webhook integration for team notifications
- **Webhook**: Custom HTTP endpoints for integration

## Troubleshooting

### Common Issues
1. **WebSocket Connection Failures**: Check firewall settings and port availability
2. **Database Connection Errors**: Verify database credentials and network connectivity
3. **Redis Cache Issues**: Ensure Redis is running and accessible
4. **Alert Not Firing**: Check alert rule configuration and thresholds

### Performance Optimization
- Configure Redis clustering for high availability
- Implement database connection pooling
- Use read replicas for metrics queries
- Enable compression for WebSocket messages

## Security Considerations

### Authentication
- API key authentication for external integrations
- JWT tokens for frontend access
- Role-based access control (RBAC)

### Data Protection
- Encrypt sensitive configuration data
- Use secure WebSocket connections (WSS)
- Implement rate limiting for API endpoints
- Regular security audits and updates

## Maintenance

### Regular Tasks
- Database cleanup of old metrics and logs
- Alert rule review and optimization
- Performance monitoring and tuning
- Security updates and patches

### Monitoring the Monitor
- Health checks for all services
- Self-monitoring alerts
- Performance dashboards
- Availability metrics

This comprehensive observability system provides the foundation for monitoring, alerting, and maintaining the Agent Mesh infrastructure with real-time visibility and proactive problem detection.
