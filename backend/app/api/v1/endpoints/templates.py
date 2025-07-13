"""
Template API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user_from_db, get_current_admin_user
from app.models.user import User
from app.services.template_service import TemplateService

router = APIRouter()
template_service = TemplateService()

# Template endpoints
@router.post("/templates")
async def create_template(
    template_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Create a new template"""
    try:
        return await template_service.create_template(template_data, current_user.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get template by ID"""
    template = await template_service.get_template(template_id, current_user.id, db)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.get("/templates")
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    template_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """List templates with filtering"""
    return await template_service.list_templates(
        current_user.id, db, skip, limit, template_type, category, status, is_public, search
    )

@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    template_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Update template"""
    template = await template_service.update_template(template_id, template_data, current_user.id, db)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Delete template"""
    success = await template_service.delete_template(template_id, current_user.id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}

# Template Version endpoints
@router.get("/templates/{template_id}/versions")
async def get_template_versions(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get all versions of a template"""
    return await template_service.get_template_versions(template_id, current_user.id, db)

@router.get("/templates/{template_id}/versions/{version}")
async def get_template_version(
    template_id: str,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get specific version of a template"""
    template_version = await template_service.get_template_version(template_id, version, current_user.id, db)
    if not template_version:
        raise HTTPException(status_code=404, detail="Template version not found")
    return template_version

# Template Instantiation endpoints
@router.post("/templates/{template_id}/instantiate")
async def instantiate_template(
    template_id: str,
    parameters: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Instantiate a template with given parameters"""
    try:
        return await template_service.instantiate_template(template_id, parameters, current_user.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    parameters: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Preview template instantiation without creating anything"""
    try:
        return await template_service.preview_template(template_id, parameters, current_user.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Template Categories and Types
@router.get("/templates/categories")
async def get_template_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get all template categories"""
    return await template_service.get_template_categories(db)

@router.get("/templates/types")
async def get_template_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get all template types"""
    return await template_service.get_template_types(db)

# Template Import/Export
@router.get("/templates/{template_id}/export")
async def export_template(
    template_id: str,
    format: str = Query("yaml", regex="^(yaml|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Export template to YAML or JSON"""
    try:
        return await template_service.export_template(template_id, current_user.id, db, format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/templates/import")
async def import_template(
    template_data: str,
    format: str = Query("yaml", regex="^(yaml|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Import template from YAML or JSON"""
    try:
        return await template_service.import_template(template_data, current_user.id, db, format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Template Search and Analytics
@router.get("/templates/search")
async def search_templates(
    query: str = Query(..., min_length=1),
    template_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Search templates"""
    return await template_service.search_templates(
        query, current_user.id, db, template_type, category, limit
    )

@router.get("/templates/stats")
async def get_template_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get template statistics"""
    try:
        return await template_service.get_template_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Template by name lookup
@router.get("/templates/by-name/{name}")
async def get_template_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_db)
):
    """Get template by name"""
    template = await template_service.get_template_by_name(name, current_user.id, db)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
