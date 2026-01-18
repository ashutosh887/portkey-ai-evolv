"""
Step 8: Template Exposure
Safe template rendering and parameter validation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import re

from packages.template_engine.slot_detector import Slot, SlotType, SlotValidator, SlotValidationResult
from packages.template_engine.template_builder import CanonicalTemplate


@dataclass
class RenderResult:
    """Result of template rendering."""
    success: bool
    rendered_text: Optional[str] = None
    validation: Optional[SlotValidationResult] = None
    errors: List[str] = field(default_factory=list)


def validate_params(
    template: CanonicalTemplate,
    params: Dict[str, Any]
) -> SlotValidationResult:
    """
    Validate parameters against a template's slot definitions.
    
    Args:
        template: Template to validate against
        params: Parameters to validate
        
    Returns:
        SlotValidationResult with validity and errors
    """
    validator = SlotValidator(template.slots)
    return validator.validate(params)


def render_template(
    template: CanonicalTemplate,
    params: Dict[str, Any],
    strict: bool = True
) -> RenderResult:
    """
    Render a template with the provided parameters.
    
    Args:
        template: Template to render
        params: Slot values to fill in
        strict: If True, validate params before rendering
        
    Returns:
        RenderResult with rendered text or errors
    """
    # Validate if strict mode
    if strict:
        validation = validate_params(template, params)
        if not validation.is_valid:
            return RenderResult(
                success=False,
                validation=validation,
                errors=validation.errors
            )
    else:
        validation = None
    
    # Apply default values for missing optional slots
    final_params = {}
    for slot in template.slots:
        if slot.name in params:
            final_params[slot.name] = params[slot.name]
        elif slot.default_value is not None:
            final_params[slot.name] = slot.default_value
        elif not slot.required:
            final_params[slot.name] = ""
    
    # Render the template
    try:
        rendered = _interpolate(template.text, final_params)
        return RenderResult(
            success=True,
            rendered_text=rendered,
            validation=validation
        )
    except Exception as e:
        return RenderResult(
            success=False,
            errors=[f"Rendering error: {str(e)}"],
            validation=validation
        )


def _interpolate(template_text: str, params: Dict[str, Any]) -> str:
    """
    Safe string interpolation with {{slot_name}} syntax.
    
    Args:
        template_text: Template with {{slot_name}} placeholders
        params: Values to substitute
        
    Returns:
        Interpolated string
    """
    result = template_text
    
    for name, value in params.items():
        placeholder = f"{{{{{name}}}}}"
        result = result.replace(placeholder, str(value))
    
    return result


def render_template_safe(
    template_text: str,
    slots: List[Slot],
    params: Dict[str, Any]
) -> RenderResult:
    """
    Render a template from raw components (text + slots).
    
    Convenience function when you don't have a CanonicalTemplate object.
    
    Args:
        template_text: Template text with {{slot}} placeholders
        slots: Slot definitions
        params: Parameter values
        
    Returns:
        RenderResult
    """
    template = CanonicalTemplate(
        text=template_text,
        slots=slots,
        source_prompts=[],
        slot_map={s.name: s.position for s in slots}
    )
    return render_template(template, params)


@dataclass
class TemplateAPI:
    """
    Exposes a template as a callable API-like interface.
    
    This is the main exposure mechanism for end users.
    """
    template_id: str
    family_id: str
    version: str
    template: CanonicalTemplate
    description: Optional[str] = None
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON Schema for this template's parameters.
        
        Returns:
            JSON Schema dict
        """
        properties = {}
        required = []
        
        for slot in self.template.slots:
            prop = {
                "description": slot.description or f"Value for {slot.name}",
            }
            
            if slot.slot_type == SlotType.NUMERIC:
                prop["type"] = "number"
            elif slot.slot_type == SlotType.ENUM:
                prop["type"] = "string"
                if slot.enum_values:
                    prop["enum"] = slot.enum_values
            else:
                prop["type"] = "string"
            
            if slot.examples:
                prop["examples"] = slot.examples[:3]
            
            if slot.default_value is not None:
                prop["default"] = slot.default_value
            
            properties[slot.name] = prop
            
            if slot.required:
                required.append(slot.name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
    
    def render(self, params: Dict[str, Any]) -> RenderResult:
        """
        Render the template with parameters.
        
        Args:
            params: Slot values
            
        Returns:
            RenderResult
        """
        return render_template(self.template, params)
    
    def __call__(self, **kwargs) -> str:
        """
        Callable interface for rendering.
        
        Raises:
            ValueError: If rendering fails
        """
        result = self.render(kwargs)
        if not result.success:
            raise ValueError(f"Template rendering failed: {result.errors}")
        return result.rendered_text


def create_template_api(
    template_id: str,
    family_id: str,
    version: str,
    template: CanonicalTemplate,
    description: Optional[str] = None
) -> TemplateAPI:
    """
    Create a TemplateAPI instance.
    
    Args:
        template_id: Unique template identifier
        family_id: Family this template belongs to
        version: Semantic version string
        template: The CanonicalTemplate
        description: Optional description
        
    Returns:
        TemplateAPI instance
    """
    return TemplateAPI(
        template_id=template_id,
        family_id=family_id,
        version=version,
        template=template,
        description=description
    )
