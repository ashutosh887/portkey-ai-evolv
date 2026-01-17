"""
Mock LLM client for development and testing
"""

from typing import List
from packages.core.models import PromptDNA, CanonicalTemplate
import re


class MockLLMClient:
    """Mock LLM client that generates reasonable templates without API calls"""
    
    async def extract_template(self, prompt_dnas: List[PromptDNA]) -> CanonicalTemplate:
        """
        Extract canonical template using simple heuristics
        
        Args:
            prompt_dnas: List of prompts in the same family
        
        Returns:
            CanonicalTemplate object
        """
        if not prompt_dnas:
            return CanonicalTemplate(text="", variables=[])
        
        base_text = prompt_dnas[0].raw_text
        
        all_variables = set()
        for dna in prompt_dnas:
            all_variables.update(dna.variables.detected)
        
        template_text = base_text
        variables_list = list(all_variables)
        
        for var in variables_list:
            patterns = [
                f"{{{{{var}}}}}" if "{{" not in var else var,
                f"{{{var}}}" if "{" not in var else var,
                f"${var}",
                f"[{var}]",
            ]
            for pattern in patterns:
                if pattern in template_text:
                    template_text = template_text.replace(pattern, f"{{{{{var}}}}}")
        
        example_values = {}
        for var in variables_list[:3]:
            example_values[var] = [f"example_{var}_1", f"example_{var}_2"]
        
        return CanonicalTemplate(
            text=template_text,
            variables=variables_list,
            example_values=example_values,
        )
    
    async def generate_explanation(self, prompt_dnas: List[PromptDNA]) -> str:
        """Generate explanation"""
        if not prompt_dnas:
            return "No prompts provided"
        
        common_vars = set(prompt_dnas[0].variables.detected)
        for dna in prompt_dnas[1:]:
            common_vars &= set(dna.variables.detected)
        
        return (
            f"This family contains {len(prompt_dnas)} prompts with similar structure. "
            f"They share {len(common_vars)} common variables: {', '.join(list(common_vars)[:3])}."
        )
