"""
Template Service
Handles management of agent and tool templates
"""

import json
import uuid
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.template import Template, TemplateVersion
from app.models.user import User
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateVersionCreate, TemplateVersionResponse
)
from app.services.observability_service import ObservabilityService
from app.core.exceptions import TemplateError, ValidationError
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class TemplateService:
    """Service for managing agent and tool templates"""
    
    def __init__(self):
        self.observability_service = ObservabilityService()
    
    # Template Management
    async def create_template(
        self,
        template_data: TemplateCreate,
        user_id: str,
        db: AsyncSession
    ) -> TemplateResponse:
        """Create a new template"""
        try:
            # Validate template data
            await self._validate_template_data(template_data)
            
            # Create template
            template = Template(
                id=str(uuid.uuid4()),
                name=template_data.name,
                display_name=template_data.display_name,
                description=template_data.description,
                template_type=template_data.template_type,
                category=template_data.category,
                definition=template_data.definition,
                json_schema=template_data.json_schema,
                parameters=template_data.parameters,
                template_metadata=template_data.template_metadata,
                tags=template_data.tags,
                version="1.0.0",
                is_public=template_data.is_public,
                status="active",
                created_by=user_id,
                organization_id=None  # TODO: Get from user context
            )
            
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            # Create initial version
            await self._create_template_version(template, template_data.definition, user_id, db)
            
            # Log template creation
            await self.observability_service.log_event(
                "template_created",
                {
                    "template_id": template.id,
                    "template_name": template.name,
                    "template_type": template.template_type,
                    "created_by": user_id
                }
            )
            
            return TemplateResponse.model_validate(template)
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            await db.rollback()
            raise TemplateError(f"Failed to create template: {str(e)}")
    
    async def get_template(
        self,
        template_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[TemplateResponse]:
        """Get template by ID"""
        try:
            stmt = select(Template).where(Template.id == template_id)
            result = await db.execute(stmt)
            template = result.scalar_one_or_none()
            
            if not template:
                return None
            
            return TemplateResponse.model_validate(template)
            
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {str(e)}")
            raise TemplateError(f"Failed to get template: {str(e)}")
    
    async def get_template_by_name(
        self,
        name: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[TemplateResponse]:
        """Get template by name"""
        try:
            stmt = select(Template).where(Template.name == name)
            result = await db.execute(stmt)
            template = result.scalar_one_or_none()
            
            if not template:
                return None
            
            return TemplateResponse.model_validate(template)
            
        except Exception as e:
            logger.error(f"Error getting template by name {name}: {str(e)}")
            raise TemplateError(f"Failed to get template: {str(e)}")
    
    async def list_templates(
        self,
        user_id: str,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        template_type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        is_public: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[TemplateResponse]:
        """List templates with filtering"""
        try:
            stmt = select(Template)
            
            # Apply filters
            if template_type:
                stmt = stmt.where(Template.template_type == template_type)
            
            if category:
                stmt = stmt.where(Template.category == category)
            
            if status:
                stmt = stmt.where(Template.status == status)
            
            if is_public is not None:
                stmt = stmt.where(Template.is_public == is_public)
            
            if search:
                stmt = stmt.where(
                    or_(
                        Template.name.ilike(f"%{search}%"),
                        Template.display_name.ilike(f"%{search}%"),
                        Template.description.ilike(f"%{search}%")
                    )
                )
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            templates = result.scalars().all()
            
            return [TemplateResponse.model_validate(t) for t in templates]
            
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            raise TemplateError(f"Failed to list templates: {str(e)}")
    
    async def update_template(
        self,
        template_id: str,
        template_data: TemplateUpdate,
        user_id: str,
        db: AsyncSession
    ) -> Optional[TemplateResponse]:
        """Update template"""
        try:
            # Get existing template
            template = await self.get_template(template_id, user_id, db)
            if not template:
                return None
            
            # Validate data if provided
            if template_data.definition:
                await self._validate_template_data(template_data)
            
            # Update template
            update_data = template_data.model_dump(exclude_unset=True)
            if update_data:
                # If definition changed, create new version
                if "definition" in update_data:
                    # Get current template for version creation
                    current_template = await db.get(Template, template_id)
                    await self._create_template_version(current_template, update_data["definition"], user_id, db)
                
                stmt = update(Template).where(Template.id == template_id).values(**update_data)
                await db.execute(stmt)
                await db.commit()
            
            # Return updated template
            return await self.get_template(template_id, user_id, db)
            
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            await db.rollback()
            raise TemplateError(f"Failed to update template: {str(e)}")
    
    async def delete_template(
        self,
        template_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete template"""
        try:
            # Delete template versions first
            await db.execute(delete(TemplateVersion).where(TemplateVersion.template_id == template_id))
            
            # Delete template
            stmt = delete(Template).where(Template.id == template_id)
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            await db.rollback()
            raise TemplateError(f"Failed to delete template: {str(e)}")
    
    # Template Version Management
    async def get_template_versions(
        self,
        template_id: str,
        user_id: str,
        db: AsyncSession
    ) -> List[TemplateVersionResponse]:
        """Get all versions of a template"""
        try:
            stmt = select(TemplateVersion).where(TemplateVersion.template_id == template_id)
            result = await db.execute(stmt)
            versions = result.scalars().all()
            
            return [TemplateVersionResponse.model_validate(v) for v in versions]
            
        except Exception as e:
            logger.error(f"Error getting template versions for {template_id}: {str(e)}")
            raise TemplateError(f"Failed to get template versions: {str(e)}")
    
    async def get_template_version(
        self,
        template_id: str,
        version: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[TemplateVersionResponse]:
        """Get specific version of a template"""
        try:
            stmt = select(TemplateVersion).where(
                and_(
                    TemplateVersion.template_id == template_id,
                    TemplateVersion.version == version
                )
            )
            result = await db.execute(stmt)
            template_version = result.scalar_one_or_none()
            
            if not template_version:
                return None
            
            return TemplateVersionResponse.model_validate(template_version)
            
        except Exception as e:
            logger.error(f"Error getting template version {template_id}:{version}: {str(e)}")
            raise TemplateError(f"Failed to get template version: {str(e)}")
    
    async def _create_template_version(
        self,
        template: Template,
        definition: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> TemplateVersionResponse:
        """Create a new version of a template"""
        try:
            # Get next version number
            stmt = select(func.count(TemplateVersion.id)).where(TemplateVersion.template_id == template.id)
            version_count = await db.scalar(stmt)
            next_version = f"1.{version_count or 0}.0"
            
            # Create template version
            template_version = TemplateVersion(
                id=str(uuid.uuid4()),
                template_id=template.id,
                version=next_version,
                definition=definition,
                created_by=user_id
            )
            
            db.add(template_version)
            await db.commit()
            await db.refresh(template_version)
            
            return TemplateVersionResponse.model_validate(template_version)
            
        except Exception as e:
            logger.error(f"Error creating template version: {str(e)}")
            await db.rollback()
            raise TemplateError(f"Failed to create template version: {str(e)}")
    
    # Template Instantiation
    async def instantiate_template(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Instantiate a template with given parameters"""
        try:
            # Get template
            template = await self.get_template(template_id, user_id, db)
            if not template:
                raise TemplateError(f"Template {template_id} not found")
            
            # Validate parameters against template schema
            await self._validate_template_parameters(template, parameters)
            
            # Instantiate template
            instantiated = await self._process_template_definition(template.definition, parameters)
            
            # Log template instantiation
            await self.observability_service.log_event(
                "template_instantiated",
                {
                    "template_id": template.id,
                    "template_name": template.name,
                    "user_id": user_id,
                    "parameters_count": len(parameters)
                }
            )
            
            return instantiated
            
        except Exception as e:
            logger.error(f"Error instantiating template {template_id}: {str(e)}")
            raise TemplateError(f"Failed to instantiate template: {str(e)}")
    
    async def preview_template(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Preview template instantiation without creating anything"""
        try:
            # Get template
            template = await self.get_template(template_id, user_id, db)
            if not template:
                raise TemplateError(f"Template {template_id} not found")
            
            # Validate parameters against template schema
            await self._validate_template_parameters(template, parameters)
            
            # Process template definition
            preview = await self._process_template_definition(template.definition, parameters, preview_mode=True)
            
            return {
                "template_id": template.id,
                "template_name": template.name,
                "preview": preview,
                "parameters": parameters
            }
            
        except Exception as e:
            logger.error(f"Error previewing template {template_id}: {str(e)}")
            raise TemplateError(f"Failed to preview template: {str(e)}")
    
    # Template Categories and Types
    async def get_template_categories(self, db: AsyncSession) -> List[str]:
        """Get all template categories"""
        try:
            stmt = select(Template.category.distinct())
            result = await db.execute(stmt)
            categories = result.scalars().all()
            
            return [cat for cat in categories if cat]
            
        except Exception as e:
            logger.error(f"Error getting template categories: {str(e)}")
            raise TemplateError(f"Failed to get template categories: {str(e)}")
    
    async def get_template_types(self, db: AsyncSession) -> List[str]:
        """Get all template types"""
        try:
            stmt = select(Template.template_type.distinct())
            result = await db.execute(stmt)
            types = result.scalars().all()
            
            return [t for t in types if t]
            
        except Exception as e:
            logger.error(f"Error getting template types: {str(e)}")
            raise TemplateError(f"Failed to get template types: {str(e)}")
    
    # Template Import/Export
    async def export_template(
        self,
        template_id: str,
        user_id: str,
        db: AsyncSession,
        format: str = "yaml"
    ) -> str:
        """Export template to YAML or JSON"""
        try:
            # Get template
            template = await self.get_template(template_id, user_id, db)
            if not template:
                raise TemplateError(f"Template {template_id} not found")
            
            # Prepare export data
            export_data = {
                "name": template.name,
                "display_name": template.display_name,
                "description": template.description,
                "template_type": template.template_type,
                "category": template.category,
                "definition": template.definition,
                "schema": template.schema,
                "parameters": template.parameters,
                "metadata": template.metadata,
                "tags": template.tags,
                "version": template.version,
                "is_public": template.is_public
            }
            
            # Format output
            if format.lower() == "yaml":
                return yaml.dump(export_data, default_flow_style=False)
            else:
                return json.dumps(export_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting template {template_id}: {str(e)}")
            raise TemplateError(f"Failed to export template: {str(e)}")
    
    async def import_template(
        self,
        template_data: str,
        user_id: str,
        db: AsyncSession,
        format: str = "yaml"
    ) -> TemplateResponse:
        """Import template from YAML or JSON"""
        try:
            # Parse input data
            if format.lower() == "yaml":
                data = yaml.safe_load(template_data)
            else:
                data = json.loads(template_data)
            
            # Create template from imported data
            template_create = TemplateCreate(**data)
            
            # Create template
            template = await self.create_template(template_create, user_id, db)
            
            # Log template import
            await self.observability_service.log_event(
                "template_imported",
                {
                    "template_id": template.id,
                    "template_name": template.name,
                    "imported_by": user_id,
                    "format": format
                }
            )
            
            return template
            
        except Exception as e:
            logger.error(f"Error importing template: {str(e)}")
            raise TemplateError(f"Failed to import template: {str(e)}")
    
    # Validation Methods
    async def _validate_template_data(self, template_data: Union[TemplateCreate, TemplateUpdate]) -> None:
        """Validate template data"""
        try:
            if hasattr(template_data, 'name') and template_data.name:
                if len(template_data.name) < 2:
                    raise ValidationError("Template name must be at least 2 characters")
            
            if hasattr(template_data, 'definition') and template_data.definition:
                # Validate definition structure
                if not isinstance(template_data.definition, dict):
                    raise ValidationError("Template definition must be a dictionary")
                
                # Validate required fields based on template type
                if hasattr(template_data, 'template_type') and template_data.template_type:
                    await self._validate_template_type_structure(template_data.template_type, template_data.definition)
                    
        except Exception as e:
            logger.error(f"Error validating template data: {str(e)}")
            raise ValidationError(f"Invalid template data: {str(e)}")
    
    async def _validate_template_type_structure(self, template_type: str, definition: Dict[str, Any]) -> None:
        """Validate template definition structure based on type"""
        try:
            if template_type == "agent":
                required_fields = ["name", "description", "model", "prompt"]
                for field in required_fields:
                    if field not in definition:
                        raise ValidationError(f"Agent template missing required field: {field}")
            
            elif template_type == "tool":
                required_fields = ["name", "description", "function"]
                for field in required_fields:
                    if field not in definition:
                        raise ValidationError(f"Tool template missing required field: {field}")
            
            elif template_type == "workflow":
                required_fields = ["name", "description", "steps"]
                for field in required_fields:
                    if field not in definition:
                        raise ValidationError(f"Workflow template missing required field: {field}")
                        
        except Exception as e:
            logger.error(f"Error validating template type structure: {str(e)}")
            raise ValidationError(f"Invalid template structure: {str(e)}")
    
    async def _validate_template_parameters(self, template: TemplateResponse, parameters: Dict[str, Any]) -> None:
        """Validate parameters against template schema"""
        try:
            if not template.schema:
                return  # No schema to validate against
            
            # Basic parameter validation
            if "required" in template.schema:
                for required_param in template.schema["required"]:
                    if required_param not in parameters:
                        raise ValidationError(f"Missing required parameter: {required_param}")
            
            # Type validation
            if "properties" in template.schema:
                for param_name, param_value in parameters.items():
                    if param_name in template.schema["properties"]:
                        param_schema = template.schema["properties"][param_name]
                        if "type" in param_schema:
                            expected_type = param_schema["type"]
                            if not self._validate_parameter_type(param_value, expected_type):
                                raise ValidationError(f"Parameter {param_name} has invalid type. Expected: {expected_type}")
                                
        except Exception as e:
            logger.error(f"Error validating template parameters: {str(e)}")
            raise ValidationError(f"Invalid template parameters: {str(e)}")
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if expected_type in type_mapping:
            return isinstance(value, type_mapping[expected_type])
        
        return True  # Unknown type, allow it
    
    async def _process_template_definition(
        self,
        definition: Dict[str, Any],
        parameters: Dict[str, Any],
        preview_mode: bool = False
    ) -> Dict[str, Any]:
        """Process template definition with parameters"""
        try:
            # Deep copy definition to avoid modifying original
            processed = json.loads(json.dumps(definition))
            
            # Replace parameter placeholders
            processed = self._replace_parameters(processed, parameters)
            
            if preview_mode:
                # In preview mode, just return the processed definition
                return processed
            
            # Additional processing for actual instantiation
            processed["instantiated_at"] = datetime.utcnow().isoformat()
            processed["parameters_used"] = parameters
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing template definition: {str(e)}")
            raise TemplateError(f"Failed to process template definition: {str(e)}")
    
    def _replace_parameters(self, obj: Any, parameters: Dict[str, Any]) -> Any:
        """Recursively replace parameter placeholders in object"""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = self._replace_parameters(value, parameters)
            return result
        elif isinstance(obj, list):
            return [self._replace_parameters(item, parameters) for item in obj]
        elif isinstance(obj, str):
            # Replace parameter placeholders like {{parameter_name}}
            for param_name, param_value in parameters.items():
                placeholder = f"{{{{{param_name}}}}}"
                if placeholder in obj:
                    obj = obj.replace(placeholder, str(param_value))
            return obj
        else:
            return obj
    
    # Utility Methods
    async def get_template_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get template statistics"""
        try:
            # Get counts by type
            agent_count = await db.scalar(select(func.count(Template.id)).where(Template.template_type == "agent"))
            tool_count = await db.scalar(select(func.count(Template.id)).where(Template.template_type == "tool"))
            workflow_count = await db.scalar(select(func.count(Template.id)).where(Template.template_type == "workflow"))
            
            # Get public vs private counts
            public_count = await db.scalar(select(func.count(Template.id)).where(Template.is_public == True))
            private_count = await db.scalar(select(func.count(Template.id)).where(Template.is_public == False))
            
            # Get total versions
            total_versions = await db.scalar(select(func.count(TemplateVersion.id)))
            
            return {
                "agent_templates": agent_count or 0,
                "tool_templates": tool_count or 0,
                "workflow_templates": workflow_count or 0,
                "public_templates": public_count or 0,
                "private_templates": private_count or 0,
                "total_templates": (agent_count or 0) + (tool_count or 0) + (workflow_count or 0),
                "total_versions": total_versions or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting template stats: {str(e)}")
            raise TemplateError(f"Failed to get template stats: {str(e)}")
    
    async def search_templates(
        self,
        query: str,
        user_id: str,
        db: AsyncSession,
        template_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[TemplateResponse]:
        """Search templates"""
        try:
            stmt = select(Template).where(
                or_(
                    Template.name.ilike(f"%{query}%"),
                    Template.display_name.ilike(f"%{query}%"),
                    Template.description.ilike(f"%{query}%")
                )
            )
            
            if template_type:
                stmt = stmt.where(Template.template_type == template_type)
            
            if category:
                stmt = stmt.where(Template.category == category)
            
            stmt = stmt.limit(limit)
            
            result = await db.execute(stmt)
            templates = result.scalars().all()
            
            return [TemplateResponse.model_validate(t) for t in templates]
            
        except Exception as e:
            logger.error(f"Error searching templates: {str(e)}")
            raise TemplateError(f"Failed to search templates: {str(e)}")
