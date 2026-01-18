"""
Template Engine Package
Transforms prompt families into reusable, versioned, slot-validated templates.
"""

from packages.template_engine.alignment import align_prompts, find_lcs
from packages.template_engine.slot_detector import detect_slots, Slot, SlotType
from packages.template_engine.template_builder import build_template
from packages.template_engine.versioning import TemplateVersion, compute_version_bump
from packages.template_engine.intent_mapper import IntentMapper
from packages.template_engine.exposure import render_template, validate_params
from packages.template_engine.pipeline import TemplatePipeline, on_prompt_added_to_family

__all__ = [
    "align_prompts",
    "find_lcs",
    "detect_slots",
    "Slot",
    "SlotType",
    "build_template",
    "TemplateVersion",
    "compute_version_bump",
    "IntentMapper",
    "render_template",
    "validate_params",
    "TemplatePipeline",
    "on_prompt_added_to_family",
]
