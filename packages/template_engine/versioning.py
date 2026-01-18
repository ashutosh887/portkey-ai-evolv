"""
Step 6: Template Versioning
Semantic versioning for templates (MAJOR.MINOR.PATCH).
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from packages.template_engine.template_builder import CanonicalTemplate, extract_slot_names


class VersionBumpType(Enum):
    """Types of version bumps."""
    NONE = "none"
    PATCH = "patch"   # Wording changes
    MINOR = "minor"   # Slot added
    MAJOR = "major"   # Slot removed / breaking change


@dataclass
class TemplateVersion:
    """Semantic version for a template."""
    major: int = 1
    minor: int = 0
    patch: int = 0
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def from_string(cls, version_str: str) -> "TemplateVersion":
        """Parse version from string like '1.2.3'."""
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 1,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0
        )
    
    def bump(self, bump_type: VersionBumpType) -> "TemplateVersion":
        """Return a new version with the specified bump applied."""
        if bump_type == VersionBumpType.MAJOR:
            return TemplateVersion(self.major + 1, 0, 0)
        elif bump_type == VersionBumpType.MINOR:
            return TemplateVersion(self.major, self.minor + 1, 0)
        elif bump_type == VersionBumpType.PATCH:
            return TemplateVersion(self.major, self.minor, self.patch + 1)
        return TemplateVersion(self.major, self.minor, self.patch)


@dataclass
class VersionBumpResult:
    """Result of computing a version bump."""
    bump_type: VersionBumpType
    old_version: TemplateVersion
    new_version: TemplateVersion
    changes: List[str]


def compute_version_bump(
    old_template: CanonicalTemplate,
    new_template: CanonicalTemplate,
    old_version: Optional[TemplateVersion] = None
) -> VersionBumpResult:
    """
    Compute the version bump needed between two template versions.
    
    Rules:
    - Slot removed → MAJOR (breaking change)
    - Slot added → MINOR (backward compatible addition)
    - Wording only → PATCH (backward compatible fix)
    - No change → NONE
    
    Args:
        old_template: Previous template version
        new_template: New template version
        old_version: Current version (defaults to 1.0.0)
        
    Returns:
        VersionBumpResult with bump type and new version
    """
    if old_version is None:
        old_version = TemplateVersion(1, 0, 0)
    
    old_slots = set(s.name for s in old_template.slots)
    new_slots = set(s.name for s in new_template.slots)
    
    changes = []
    bump_type = VersionBumpType.NONE
    
    # Check for removed slots (MAJOR)
    removed_slots = old_slots - new_slots
    if removed_slots:
        bump_type = VersionBumpType.MAJOR
        changes.append(f"Removed slots: {removed_slots}")
    
    # Check for added slots (MINOR, if not already MAJOR)
    added_slots = new_slots - old_slots
    if added_slots:
        if bump_type != VersionBumpType.MAJOR:
            bump_type = VersionBumpType.MINOR
        changes.append(f"Added slots: {added_slots}")
    
    # Check for slot type changes (MAJOR)
    for old_slot in old_template.slots:
        for new_slot in new_template.slots:
            if old_slot.name == new_slot.name:
                if old_slot.slot_type != new_slot.slot_type:
                    bump_type = VersionBumpType.MAJOR
                    changes.append(
                        f"Slot '{old_slot.name}' type changed: "
                        f"{old_slot.slot_type.value} → {new_slot.slot_type.value}"
                    )
    
    # Check for text changes (PATCH, if nothing else)
    if old_template.text != new_template.text and bump_type == VersionBumpType.NONE:
        bump_type = VersionBumpType.PATCH
        changes.append("Template wording changed")
    
    new_version = old_version.bump(bump_type)
    
    return VersionBumpResult(
        bump_type=bump_type,
        old_version=old_version,
        new_version=new_version,
        changes=changes
    )


def is_breaking_change(bump_result: VersionBumpResult) -> bool:
    """Check if a version bump represents a breaking change."""
    return bump_result.bump_type == VersionBumpType.MAJOR


def get_compatible_versions(
    template_versions: List[TemplateVersion],
    target_version: TemplateVersion
) -> List[TemplateVersion]:
    """
    Get all versions compatible with a target version.
    
    Compatibility rules:
    - Same MAJOR version
    - MINOR >= target's MINOR (has all needed slots)
    
    Args:
        template_versions: List of available versions
        target_version: Version to check compatibility against
        
    Returns:
        List of compatible versions
    """
    compatible = []
    
    for version in template_versions:
        if version.major == target_version.major:
            if version.minor >= target_version.minor:
                compatible.append(version)
    
    return compatible
