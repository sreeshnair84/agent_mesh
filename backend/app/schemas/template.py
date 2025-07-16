"""
Template schemas for request/response validation
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid


class TemplateBase(BaseModel):
    """Base template schema with common fields"""
    
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    template_type: str = Field(..., min_length=2, max_length=50)
    category: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    json_schema: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    template_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: str = "1.0.0"
    is_public: bool = False


class TemplateCreate(TemplateBase):
    """Template creation schema"""
    pass


class TemplateUpdate(BaseModel):
    """Template update schema"""
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    template_type: Optional[str] = Field(None, min_length=2, max_length=50)
    category: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    json_schema: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    template_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    is_public: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Template response schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    created_by: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TemplateVersionBase(BaseModel):
    """Base template version schema"""
    
    version: str = Field(..., min_length=1, max_length=20)
    definition: Dict[str, Any] = Field(..., min_length=1)
    changelog: Optional[str] = None
    is_current: bool = False
    is_published: bool = False


class TemplateVersionCreate(TemplateVersionBase):
    """Template version creation schema"""
    pass


class TemplateVersionUpdate(BaseModel):
    """Template version update schema"""
    
    version: Optional[str] = Field(None, min_length=1, max_length=20)
    definition: Optional[Dict[str, Any]] = None
    changelog: Optional[str] = None
    is_current: Optional[bool] = None
    is_published: Optional[bool] = None


class TemplateVersionResponse(TemplateVersionBase):
    """Template version response schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    template_id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    """Template list response schema"""
    
    templates: List[TemplateResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class TemplateSearchRequest(BaseModel):
    """Template search request schema"""
    
    query: Optional[str] = None
    template_type: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
