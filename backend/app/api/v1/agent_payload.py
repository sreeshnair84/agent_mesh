"""
Agent Payload API endpoints for managing input/output specifications
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.enhanced_agent import Agent
from app.models.user import User
from app.schemas.enhanced_schemas import (
    PayloadSchema, AgentPayloadUpdate, SuccessResponse
)

router = APIRouter()


@router.get("/{agent_id}/payload", response_model=Dict[str, Any])
async def get_agent_payload(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent input/output payload specifications"""
    try:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "agent_id": agent_id,
            "input_payload": agent.input_payload,
            "output_payload": agent.output_payload
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent payload: {str(e)}"
        )


@router.put("/{agent_id}/payload", response_model=SuccessResponse)
async def update_agent_payload(
    agent_id: str,
    payload_data: AgentPayloadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update agent input/output payload specifications"""
    try:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if str(agent.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to update this agent"
            )
        
        # Update payload specifications
        if payload_data.input_payload is not None:
            agent.input_payload = payload_data.input_payload.dict()
        
        if payload_data.output_payload is not None:
            agent.output_payload = payload_data.output_payload.dict()
        
        await db.commit()
        
        return SuccessResponse(
            message="Agent payload specifications updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent payload: {str(e)}"
        )


@router.post("/{agent_id}/payload/validate")
async def validate_agent_payload(
    agent_id: str,
    payload_data: Dict[str, Any],
    payload_type: str,  # 'input' or 'output'
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate data against agent payload specification"""
    try:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get the appropriate payload schema
        if payload_type == 'input':
            payload_schema = agent.input_payload
        elif payload_type == 'output':
            payload_schema = agent.output_payload
        else:
            raise HTTPException(
                status_code=400, 
                detail="payload_type must be 'input' or 'output'"
            )
        
        if not payload_schema:
            raise HTTPException(
                status_code=400, 
                detail=f"No {payload_type} payload schema defined for this agent"
            )
        
        # Perform validation
        validation_result = _validate_payload(payload_data, payload_schema)
        
        return {
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "payload_type": payload_type,
            "agent_id": agent_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate payload: {str(e)}"
        )


@router.get("/{agent_id}/payload/examples")
async def get_agent_payload_examples(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get example payloads for the agent"""
    try:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        examples = {
            "input_examples": [],
            "output_examples": []
        }
        
        if agent.input_payload and agent.input_payload.get("examples"):
            examples["input_examples"] = agent.input_payload["examples"]
        
        if agent.output_payload and agent.output_payload.get("examples"):
            examples["output_examples"] = agent.output_payload["examples"]
        
        return examples
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payload examples: {str(e)}"
        )


def _validate_payload(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validate payload data against schema"""
    errors = []
    
    try:
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Check required fields
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate each field
        for field, field_schema in properties.items():
            if field in data:
                field_errors = _validate_field(data[field], field_schema, field)
                errors.extend(field_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }


def _validate_field(value: Any, field_schema: Dict[str, Any], field_name: str) -> list:
    """Validate a single field against its schema"""
    errors = []
    
    field_type = field_schema.get("type", "string")
    
    # Type validation
    if field_type == "string" and not isinstance(value, str):
        errors.append(f"Field '{field_name}' must be a string")
    elif field_type == "number" and not isinstance(value, (int, float)):
        errors.append(f"Field '{field_name}' must be a number")
    elif field_type == "boolean" and not isinstance(value, bool):
        errors.append(f"Field '{field_name}' must be a boolean")
    elif field_type == "array" and not isinstance(value, list):
        errors.append(f"Field '{field_name}' must be an array")
    elif field_type == "object" and not isinstance(value, dict):
        errors.append(f"Field '{field_name}' must be an object")
    
    # Enum validation
    enum_values = field_schema.get("enum")
    if enum_values and value not in enum_values:
        errors.append(f"Field '{field_name}' must be one of: {enum_values}")
    
    # Object property validation
    if field_type == "object" and isinstance(value, dict):
        properties = field_schema.get("properties", {})
        for prop, prop_schema in properties.items():
            if prop in value:
                prop_errors = _validate_field(value[prop], prop_schema, f"{field_name}.{prop}")
                errors.extend(prop_errors)
    
    # Array item validation
    if field_type == "array" and isinstance(value, list):
        items_schema = field_schema.get("items")
        if items_schema:
            for i, item in enumerate(value):
                item_errors = _validate_field(item, items_schema, f"{field_name}[{i}]")
                errors.extend(item_errors)
    
    return errors
