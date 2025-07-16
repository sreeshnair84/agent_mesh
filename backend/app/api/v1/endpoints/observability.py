"""
Observability endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.api.deps import get_current_user_from_db
from app.models.user import User
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.services.observability_service import ObservabilityService
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

# Initialize services
observability_service = ObservabilityService()

router = APIRouter(
    prefix="/observability",
    responses={404: {"description": "Not found"}},)


@router.get("/stats")
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get system metrics
    """
    return {
        "system": {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 33.1,
            "uptime": "2d 14h 32m"
        },
        "agents": {
            "total": 12,
            "active": 8,
            "error": 1,
            "stopped": 3
        },
        "requests": {
            "total_today": 1256,
            "requests_per_minute": 5.2,
            "average_response_time": 0.45,
            "success_rate": 0.96
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def get_health_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get health status
    """
    return {
        "status": "healthy",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "llm_providers": "healthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/logs")
async def get_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
    limit: int = 100,
    level: Optional[str] = None,
):
    """
    Get system logs
    """
    logs = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "service": "agent-mesh-backend",
            "message": "Agent request processed successfully",
            "metadata": {"agent_id": "agent-1", "user_id": str(current_user.id)}
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "level": "warning",
            "service": "agent-mesh-backend",
            "message": "Slow response detected",
            "metadata": {"response_time": 2.5, "agent_id": "agent-2"}
        }
    ]
    
    return {
        "logs": logs,
        "total": len(logs),
        "limit": limit,
        "level": level
    }


@router.get("/traces")
async def get_traces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
    limit: int = 50,
):
    """
    Get distributed traces
    """
    traces = [
        {
            "trace_id": "trace-123",
            "operation": "agent.execute",
            "duration": 1.2,
            "status": "success",
            "spans": [
                {
                    "span_id": "span-1",
                    "operation": "llm.request",
                    "duration": 0.8,
                    "status": "success"
                },
                {
                    "span_id": "span-2",
                    "operation": "tool.execute",
                    "duration": 0.3,
                    "status": "success"
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    return {
        "traces": traces,
        "total": len(traces),
        "limit": limit
    }


@router.get("/alerts")
async def get_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get system alerts
    """
    alerts = [
        {
            "id": "alert-1",
            "severity": "warning",
            "title": "High Response Time",
            "description": "Agent response time exceeded threshold",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {"agent_id": "agent-2", "response_time": 3.2}
        }
    ]
    
    return {
        "alerts": alerts,
        "total": len(alerts)
    }


@router.get("/performance")
async def get_performance_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
    period: str = "1h",
):
    """
    Get performance metrics
    """
    return {
        "period": period,
        "metrics": {
            "requests_per_second": [
                {"timestamp": datetime.utcnow().isoformat(), "value": 5.2},
                {"timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), "value": 4.8}
            ],
            "response_time": [
                {"timestamp": datetime.utcnow().isoformat(), "value": 0.45},
                {"timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), "value": 0.52}
            ],
            "error_rate": [
                {"timestamp": datetime.utcnow().isoformat(), "value": 0.04},
                {"timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), "value": 0.03}
            ]
        }
    }


@router.get("/stats")
async def get_observability_stats(
    timeRange: str = "24h",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get observability statistics
    """
    try:
        # Get system metrics
        usage_stats = await observability_service.get_usage_stats()
        
        # Get agent count from database
        agent_count_result = await db.execute(
            select(func.count(Agent.id)).where(Agent.user_id == current_user.id)
        )
        total_agents = agent_count_result.scalar() or 0
        
        # Get workflow count from database
        workflow_count_result = await db.execute(
            select(func.count(Workflow.id)).where(Workflow.user_id == current_user.id)
        )
        total_workflows = workflow_count_result.scalar() or 0
        
        # Calculate time range
        time_delta = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6), 
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }.get(timeRange, timedelta(hours=24))
        
        cutoff_time = datetime.utcnow() - time_delta
        
        # Filter transactions by time range
        recent_transactions = [
            t for t in observability_service.transactions.values()
            if t.get("start_time", datetime.min) >= cutoff_time
        ]
        
        # Calculate metrics
        total_requests = len(recent_transactions)
        successful_requests = len([t for t in recent_transactions if t.get("status") == "success"])
        error_requests = len([t for t in recent_transactions if t.get("status") == "error"])
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate average latency
        completed_transactions = [t for t in recent_transactions if t.get("duration")]
        avg_latency = sum(t.get("duration", 0) for t in completed_transactions) / len(completed_transactions) if completed_transactions else 0
        
        # Get LLM token usage
        llm_usage = sum(t.get("llm_tokens", 0) for t in recent_transactions) / 1000  # Convert to thousands
        
        return {
            "total_agents": total_agents,
            "total_workflows": total_workflows,
            "success_rate": round(success_rate, 1),
            "error_rate": round(error_rate, 1),
            "avg_latency": round(avg_latency),
            "total_requests": total_requests,
            "active_sessions": usage_stats.get("active_traces", 0),
            "llm_usage": round(llm_usage, 1)
        }
        
    except Exception as e:
        logger.error(f"Error getting observability stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get observability stats")


@router.get("/transactions")
async def get_transactions(
    timeRange: str = "24h",
    search: str = "",
    sort: str = "timestamp",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get transactions with filtering and sorting
    """
    try:
        # Calculate time range
        time_delta = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }.get(timeRange, timedelta(hours=24))
        
        cutoff_time = datetime.utcnow() - time_delta
        
        # Get transactions from observability service
        transactions = []
        for trace_id, transaction in observability_service.transactions.items():
            if transaction.get("start_time", datetime.min) >= cutoff_time:
                # Convert to frontend format
                tx = {
                    "id": trace_id,
                    "session_id": transaction.get("session_id", trace_id),
                    "trace_id": trace_id,
                    "timestamp": transaction.get("start_time", datetime.utcnow()).isoformat(),
                    "status": transaction.get("status", "pending"),
                    "duration": transaction.get("duration", 0),
                    "agent_name": transaction.get("agent_name", "Unknown Agent"),
                    "workflow_name": transaction.get("workflow_name"),
                    "error_message": transaction.get("error_message"),
                    "request_count": transaction.get("request_count", 1),
                    "llm_tokens": transaction.get("llm_tokens", 0)
                }
                transactions.append(tx)
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            transactions = [
                tx for tx in transactions
                if (search_lower in tx["id"].lower() or
                    search_lower in tx["session_id"].lower() or
                    search_lower in tx["trace_id"].lower() or
                    search_lower in tx["agent_name"].lower())
            ]
        
        # Apply sorting
        reverse = order == "desc"
        if sort == "timestamp":
            transactions.sort(key=lambda x: x["timestamp"], reverse=reverse)
        elif sort == "duration":
            transactions.sort(key=lambda x: x["duration"], reverse=reverse)
        elif sort == "status":
            transactions.sort(key=lambda x: x["status"], reverse=reverse)
        elif sort == "agent_name":
            transactions.sort(key=lambda x: x["agent_name"], reverse=reverse)
        
        return transactions
        
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get transactions")


@router.get("/transactions/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get detailed information about a specific transaction
    """
    try:
        # Get transaction from observability service
        transaction = observability_service.transactions.get(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get interactions/spans for this transaction
        interactions = []
        for log in observability_service.logs:
            if log.get("trace_id") == transaction_id:
                interactions.append({
                    "id": log.get("id", f"int_{len(interactions) + 1}"),
                    "agent_name": log.get("agent_name", "Unknown Agent"),
                    "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
                    "duration": log.get("duration", 0),
                    "status": log.get("status", "success"),
                    "input": log.get("input", {}),
                    "output": log.get("output", {}),
                    "llm_tokens": log.get("llm_tokens", 0),
                    "model_name": log.get("model_name", "N/A")
                })
        
        # Convert transaction to detailed format
        detailed_transaction = {
            "id": transaction_id,
            "session_id": transaction.get("session_id", transaction_id),
            "trace_id": transaction_id,
            "timestamp": transaction.get("start_time", datetime.utcnow()).isoformat(),
            "status": transaction.get("status", "pending"),
            "duration": transaction.get("duration", 0),
            "agent_name": transaction.get("agent_name", "Unknown Agent"),
            "workflow_name": transaction.get("workflow_name"),
            "error_message": transaction.get("error_message"),
            "request_count": transaction.get("request_count", 1),
            "llm_tokens": transaction.get("llm_tokens", 0),
            "interactions": interactions,
            "metadata": transaction.get("metadata", {})
        }
        
        return detailed_transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get transaction details")


@router.get("/charts")
async def get_chart_data(
    timeRange: str = "24h",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db),
):
    """
    Get chart data for observability dashboard
    """
    try:
        # Calculate time range
        time_delta = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }.get(timeRange, timedelta(hours=24))
        
        cutoff_time = datetime.utcnow() - time_delta
        
        # Get performance metrics from observability service
        performance_metrics = await observability_service.get_performance_metrics()
        
        # Generate time series data points
        now = datetime.utcnow()
        chart_data = []
        
        # Determine interval based on time range
        if timeRange == "1h":
            interval = timedelta(minutes=10)
            intervals = 6
        elif timeRange == "6h":
            interval = timedelta(hours=1)
            intervals = 6
        elif timeRange == "24h":
            interval = timedelta(hours=4)
            intervals = 6
        elif timeRange == "7d":
            interval = timedelta(days=1)
            intervals = 7
        else:  # 30d
            interval = timedelta(days=5)
            intervals = 6
        
        # Generate data points
        for i in range(intervals):
            time_point = now - (interval * (intervals - 1 - i))
            
            # Filter transactions for this time window
            window_start = time_point - interval
            window_end = time_point
            
            window_transactions = [
                t for t in observability_service.transactions.values()
                if window_start <= t.get("start_time", datetime.min) <= window_end
            ]
            
            requests = len(window_transactions)
            errors = len([t for t in window_transactions if t.get("status") == "error"])
            success_rate = ((requests - errors) / requests * 100) if requests > 0 else 100
            
            # Calculate average latency for this window
            completed_transactions = [t for t in window_transactions if t.get("duration")]
            latency = sum(t.get("duration", 0) for t in completed_transactions) / len(completed_transactions) if completed_transactions else 0
            
            # Format time label
            if timeRange in ["1h", "6h"]:
                time_label = time_point.strftime("%H:%M")
            elif timeRange == "24h":
                time_label = time_point.strftime("%H:%M")
            else:
                time_label = time_point.strftime("%m/%d")
            
            chart_data.append({
                "name": time_label,
                "requests": requests,
                "errors": errors,
                "latency": round(latency),
                "success_rate": round(success_rate, 1)
            })
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chart data")
