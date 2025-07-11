"""
Enhanced Observability Service
Comprehensive monitoring, logging, metrics, and alerting for Agent Mesh
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from app.core.config import get_settings
import logging
import time
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
settings = get_settings()


class ObservabilityService:
    """Enhanced service for comprehensive observability"""
    
    def __init__(self):
        self.active_traces: Dict[str, Dict[str, Any]] = {}
        self.metrics_cache: Dict[str, Dict[str, Any]] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        # Legacy support for existing code
        self.transactions = {}
        self.logs = []
        self.metrics = []
    
    # Enhanced Logging Methods
    async def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        level: str = "INFO",
        source: str = "system",
        user_id: Optional[str] = None,
        db: Optional[Any] = None
    ) -> None:
        """Log an event with structured data"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": f"{event_type}: {json.dumps(data, default=str)}",
                "event_type": event_type,
                "source": source,
                "user_id": user_id,
                "data": data
            }
            
            self.logs.append(log_entry)
            print(f"[OBSERVABILITY] Event logged: {event_type}")
            
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "counter",
        tags: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
        db: Optional[Any] = None
    ) -> None:
        """Record a metric"""
        try:
            metric = {
                "timestamp": datetime.utcnow().isoformat(),
                "name": name,
                "value": value,
                "metric_type": metric_type,
                "tags": tags or {},
                "unit": unit
            }
            
            self.metrics.append(metric)
            
            # Update metrics cache
            self._update_metrics_cache(name, value, metric_type)
            
            print(f"[OBSERVABILITY] Metric recorded: {name}={value}")
            
        except Exception as e:
            logger.error(f"Error recording metric: {str(e)}")
    
    def _update_metrics_cache(self, name: str, value: float, metric_type: str) -> None:
        """Update in-memory metrics cache"""
        try:
            if name not in self.metrics_cache:
                self.metrics_cache[name] = {
                    "current_value": value,
                    "total_count": 1,
                    "last_updated": datetime.utcnow(),
                    "metric_type": metric_type
                }
            else:
                cache_entry = self.metrics_cache[name]
                if metric_type == "counter":
                    cache_entry["current_value"] += value
                else:
                    cache_entry["current_value"] = value
                cache_entry["total_count"] += 1
                cache_entry["last_updated"] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error updating metrics cache: {str(e)}")
    
    # Tracing Methods
    async def start_trace(
        self,
        operation_name: str,
        tags: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None,
        db: Optional[Any] = None
    ) -> str:
        """Start a new trace"""
        try:
            trace_id = str(uuid.uuid4())
            
            # Store in active traces
            self.active_traces[trace_id] = {
                "operation_name": operation_name,
                "start_time": datetime.utcnow(),
                "tags": tags or {},
                "user_id": user_id,
                "spans": []
            }
            
            await self.log_event(
                "trace_started",
                {
                    "trace_id": trace_id,
                    "operation_name": operation_name,
                    "tags": tags or {},
                    "user_id": user_id
                },
                user_id=user_id
            )
            
            return trace_id
            
        except Exception as e:
            logger.error(f"Error starting trace: {str(e)}")
            return str(uuid.uuid4())  # Return a dummy trace ID
    
    async def finish_trace(
        self,
        trace_id: str,
        status: str = "completed",
        db: Optional[Any] = None
    ) -> None:
        """Finish a trace"""
        try:
            if trace_id in self.active_traces:
                trace_data = self.active_traces[trace_id]
                duration = (datetime.utcnow() - trace_data["start_time"]).total_seconds()
                
                # Record trace duration as metric
                await self.record_metric(
                    f"trace.duration.{trace_data['operation_name']}",
                    duration,
                    "histogram",
                    tags={"trace_id": trace_id, "status": status},
                    unit="seconds"
                )
                
                await self.log_event(
                    "trace_finished",
                    {
                        "trace_id": trace_id,
                        "operation_name": trace_data["operation_name"],
                        "duration": duration,
                        "status": status
                    },
                    user_id=trace_data.get("user_id")
                )
                
                del self.active_traces[trace_id]
                
        except Exception as e:
            logger.error(f"Error finishing trace: {str(e)}")
    
    @asynccontextmanager
    async def trace_context(
        self,
        operation_name: str,
        tags: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None,
        db: Optional[Any] = None
    ):
        """Context manager for tracing operations"""
        trace_id = await self.start_trace(operation_name, tags, user_id, db)
        try:
            yield trace_id
            await self.finish_trace(trace_id, "completed", db)
        except Exception as e:
            await self.finish_trace(trace_id, "failed", db)
            raise
    
    # Legacy Methods (for backward compatibility)
    async def log_transaction_start(
        self,
        trace_id: str,
        session_id: Optional[str],
        entity_type: str,
        entity_id: str,
        user_id: str,
        input_data: Dict[str, Any]
    ):
        """Legacy method - log the start of a transaction"""
        transaction = {
            "trace_id": trace_id,
            "session_id": session_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "input_data": input_data,
            "start_time": datetime.utcnow(),
            "status": "started"
        }
        
        self.transactions[trace_id] = transaction
        
        # Log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"Transaction started: {entity_type}/{entity_id}",
            "trace_id": trace_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id
        }
        
        self.logs.append(log_entry)
        print(f"[OBSERVABILITY] Transaction started: {trace_id}")
    
    async def log_transaction_end(
        self,
        trace_id: str,
        output_data: Dict[str, Any],
        llm_usage: Optional[Dict[str, Any]] = None
    ):
        """Log the end of a transaction"""
        if trace_id in self.transactions:
            transaction = self.transactions[trace_id]
            transaction["end_time"] = datetime.utcnow()
            transaction["output_data"] = output_data
            transaction["llm_usage"] = llm_usage
            transaction["status"] = "completed"
            
            # Calculate duration
            duration = (transaction["end_time"] - transaction["start_time"]).total_seconds()
            transaction["duration_seconds"] = duration
            
            # Log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": f"Transaction completed: {transaction['entity_type']}/{transaction['entity_id']} ({duration:.2f}s)",
                "trace_id": trace_id,
                "entity_type": transaction["entity_type"],
                "entity_id": transaction["entity_id"],
                "user_id": transaction["user_id"],
                "duration_seconds": duration
            }
            
            self.logs.append(log_entry)
            
            # Record metrics
            await self._record_metric(
                entity_type=transaction["entity_type"],
                entity_id=transaction["entity_id"],
                metric_name="execution_time",
                value=duration,
                tags={"status": "success"}
            )
            
            if llm_usage:
                await self._record_metric(
                    entity_type=transaction["entity_type"],
                    entity_id=transaction["entity_id"],
                    metric_name="llm_tokens",
                    value=llm_usage.get("tokens", 0),
                    tags={"model": llm_usage.get("model", "unknown")}
                )
            
            print(f"[OBSERVABILITY] Transaction completed: {trace_id} ({duration:.2f}s)")
    
    async def log_transaction_error(
        self,
        trace_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """Log a transaction error"""
        if trace_id in self.transactions:
            transaction = self.transactions[trace_id]
            transaction["end_time"] = datetime.utcnow()
            transaction["error_message"] = error_message
            transaction["error_details"] = error_details
            transaction["status"] = "error"
            
            # Calculate duration
            duration = (transaction["end_time"] - transaction["start_time"]).total_seconds()
            transaction["duration_seconds"] = duration
            
            # Log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "message": f"Transaction failed: {transaction['entity_type']}/{transaction['entity_id']} - {error_message}",
                "trace_id": trace_id,
                "entity_type": transaction["entity_type"],
                "entity_id": transaction["entity_id"],
                "user_id": transaction["user_id"],
                "error_message": error_message,
                "error_details": error_details
            }
            
            self.logs.append(log_entry)
            
            # Record error metrics
            await self._record_metric(
                entity_type=transaction["entity_type"],
                entity_id=transaction["entity_id"],
                metric_name="error_count",
                value=1,
                tags={"status": "error"}
            )
            
            print(f"[OBSERVABILITY] Transaction error: {trace_id} - {error_message}")
    
    async def get_agent_logs(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get logs for a specific agent"""
        agent_logs = [
            log for log in self.logs 
            if log.get("entity_id") == agent_id
        ]
        
        # Sort by timestamp desc and limit
        agent_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return agent_logs[:limit]
    
    async def get_agent_metrics(
        self,
        agent_id: str,
        period: str = "1h"
    ) -> List[Dict[str, Any]]:
        """Get metrics for a specific agent"""
        # Calculate time range
        now = datetime.utcnow()
        if period == "1h":
            start_time = now - timedelta(hours=1)
        elif period == "24h":
            start_time = now - timedelta(days=1)
        elif period == "7d":
            start_time = now - timedelta(days=7)
        elif period == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=1)
        
        # Filter metrics
        agent_metrics = [
            metric for metric in self.metrics
            if (metric.get("entity_id") == agent_id and 
                datetime.fromisoformat(metric["timestamp"]) >= start_time)
        ]
        
        return agent_metrics
    
    async def _record_metric(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric"""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {}
        }
        
        self.metrics.append(metric)
        print(f"[OBSERVABILITY] Metric recorded: {metric_name}={value} for {entity_type}/{entity_id}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        # Count transactions in the last hour
        recent_transactions = [
            t for t in self.transactions.values()
            if t["start_time"] >= last_hour
        ]
        
        success_count = len([t for t in recent_transactions if t.get("status") == "completed"])
        error_count = len([t for t in recent_transactions if t.get("status") == "error"])
        
        return {
            "timestamp": now.isoformat(),
            "status": "healthy" if error_count < success_count else "degraded",
            "metrics": {
                "transactions_last_hour": len(recent_transactions),
                "success_rate": (success_count / len(recent_transactions)) * 100 if recent_transactions else 0,
                "error_rate": (error_count / len(recent_transactions)) * 100 if recent_transactions else 0,
                "total_logs": len(self.logs),
                "total_metrics": len(self.metrics)
            }
        }
    
    async def get_transaction_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed trace information for a transaction"""
        if trace_id in self.transactions:
            transaction = self.transactions[trace_id]
            
            # Get related logs
            related_logs = [
                log for log in self.logs
                if log.get("trace_id") == trace_id
            ]
            
            # Get related metrics
            related_metrics = [
                metric for metric in self.metrics
                if metric.get("entity_id") == transaction["entity_id"]
            ]
            
            return {
                "transaction": transaction,
                "related_logs": related_logs,
                "related_metrics": related_metrics
            }
        
        return None
    
    # Enhanced Analytics Methods
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(days=1)
            
            # Get recent metrics
            recent_metrics = [
                metric for metric in self.metrics
                if datetime.fromisoformat(metric["timestamp"]) >= last_24h
            ]
            
            # Calculate performance stats
            response_times = [m for m in recent_metrics if m["name"] == "response_time"]
            throughput = [m for m in recent_metrics if m["name"] == "requests_per_second"]
            
            avg_response_time = (
                sum(m["value"] for m in response_times) / len(response_times)
                if response_times else 0
            )
            
            avg_throughput = (
                sum(m["value"] for m in throughput) / len(throughput)
                if throughput else 0
            )
            
            return {
                "avg_response_time": avg_response_time,
                "avg_throughput": avg_throughput,
                "total_requests": len(response_times),
                "time_period": "24h",
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        try:
            now = datetime.utcnow()
            
            # Count active traces
            active_traces_count = len(self.active_traces)
            
            # Count metrics by type
            metrics_by_type = {}
            for metric in self.metrics:
                metric_type = metric.get("metric_type", "unknown")
                metrics_by_type[metric_type] = metrics_by_type.get(metric_type, 0) + 1
            
            # Count logs by level
            logs_by_level = {}
            for log in self.logs:
                level = log.get("level", "unknown")
                logs_by_level[level] = logs_by_level.get(level, 0) + 1
            
            return {
                "active_traces": active_traces_count,
                "total_transactions": len(self.transactions),
                "total_logs": len(self.logs),
                "total_metrics": len(self.metrics),
                "metrics_by_type": metrics_by_type,
                "logs_by_level": logs_by_level,
                "metrics_cache_size": len(self.metrics_cache),
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Clean up old observability data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old logs
            old_logs = [
                log for log in self.logs
                if datetime.fromisoformat(log["timestamp"]) < cutoff_date
            ]
            
            # Clean up old metrics
            old_metrics = [
                metric for metric in self.metrics
                if datetime.fromisoformat(metric["timestamp"]) < cutoff_date
            ]
            
            # Clean up old transactions
            old_transactions = [
                trace_id for trace_id, transaction in self.transactions.items()
                if transaction["start_time"] < cutoff_date
            ]
            
            # Remove old data
            self.logs = [
                log for log in self.logs
                if datetime.fromisoformat(log["timestamp"]) >= cutoff_date
            ]
            
            self.metrics = [
                metric for metric in self.metrics
                if datetime.fromisoformat(metric["timestamp"]) >= cutoff_date
            ]
            
            for trace_id in old_transactions:
                del self.transactions[trace_id]
            
            return {
                "logs_deleted": len(old_logs),
                "metrics_deleted": len(old_metrics),
                "transactions_deleted": len(old_transactions)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            return {}
    
    async def export_data(
        self,
        start_time: datetime,
        end_time: datetime,
        data_types: List[str] = None
    ) -> Dict[str, Any]:
        """Export observability data for analysis"""
        try:
            if not data_types:
                data_types = ["logs", "metrics", "transactions"]
            
            export_data = {}
            
            if "logs" in data_types:
                filtered_logs = [
                    log for log in self.logs
                    if start_time <= datetime.fromisoformat(log["timestamp"]) <= end_time
                ]
                export_data["logs"] = filtered_logs
            
            if "metrics" in data_types:
                filtered_metrics = [
                    metric for metric in self.metrics
                    if start_time <= datetime.fromisoformat(metric["timestamp"]) <= end_time
                ]
                export_data["metrics"] = filtered_metrics
            
            if "transactions" in data_types:
                filtered_transactions = [
                    transaction for transaction in self.transactions.values()
                    if start_time <= transaction["start_time"] <= end_time
                ]
                export_data["transactions"] = filtered_transactions
            
            export_data["export_metadata"] = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_types": data_types,
                "exported_at": datetime.utcnow().isoformat()
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {}
    
    # Search and Analytics
    async def search_logs(
        self,
        query: str,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search logs by query"""
        try:
            filtered_logs = []
            
            for log in self.logs:
                # Check time range
                if start_time and datetime.fromisoformat(log["timestamp"]) < start_time:
                    continue
                if end_time and datetime.fromisoformat(log["timestamp"]) > end_time:
                    continue
                
                # Check level
                if level and log.get("level") != level:
                    continue
                
                # Check query match
                if query.lower() in log.get("message", "").lower():
                    filtered_logs.append(log)
            
            # Sort by timestamp desc and limit
            filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return filtered_logs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            return []
    
    async def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        try:
            now = datetime.utcnow()
            start_time = now - timedelta(hours=hours)
            
            error_logs = [
                log for log in self.logs
                if (log.get("level") == "ERROR" and 
                    datetime.fromisoformat(log["timestamp"]) >= start_time)
            ]
            
            # Group errors by type
            error_types = {}
            for log in error_logs:
                error_msg = log.get("error_message", log.get("message", "Unknown error"))
                error_types[error_msg] = error_types.get(error_msg, 0) + 1
            
            return {
                "total_errors": len(error_logs),
                "error_types": error_types,
                "time_period": f"{hours}h",
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {str(e)}")
            return {}
    
    def get_cached_metrics(self) -> Dict[str, Any]:
        """Get cached metrics for quick access"""
        try:
            return {
                "metrics_cache": self.metrics_cache,
                "cache_size": len(self.metrics_cache),
                "last_updated": max(
                    [entry["last_updated"] for entry in self.metrics_cache.values()],
                    default=datetime.utcnow()
                ).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cached metrics: {str(e)}")
            return {}
