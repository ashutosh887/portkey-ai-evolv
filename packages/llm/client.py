"""
LLM client with Portkey integration and fallbacks
"""

import os
from typing import Optional
from packages.core.models import PromptDNA, CanonicalTemplate


TEMPLATE_EXTRACTION_PROMPT = """
You are analyzing a cluster of similar prompts to extract a canonical template.

Here are {count} prompts that belong to the same family:

{prompts}

Your task:
1. Identify the COMMON STRUCTURE across all prompts
2. Identify VARIABLE PARTS (things that change between prompts)
3. Create a CANONICAL TEMPLATE using {{variable_name}} syntax
4. Explain WHY these prompts belong together

Output in JSON:
{{
  "template": "The canonical template with {{variables}}",
  "variables": ["variable_name_1", "variable_name_2"],
  "common_intent": "What these prompts are trying to achieve",
  "explanation": "Why these prompts form a family"
}}
"""


class LLMClient:
    """LLM client with Portkey integration"""
    
    def __init__(self, api_key: Optional[str] = None, virtual_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PORTKEY_API_KEY")
        self.virtual_key = virtual_key or os.getenv("PORTKEY_VIRTUAL_KEY")
    
    async def extract_template(self, prompt_dnas: list[PromptDNA]) -> CanonicalTemplate:
        """
        Extract canonical template from a cluster of prompts
        
        Args:
            prompt_dnas: List of prompts in the same family
        
        Returns:
            CanonicalTemplate object
        """
        prompts_text = "\n\n---\n\n".join([dna.raw_text for dna in prompt_dnas])
        
        prompt = TEMPLATE_EXTRACTION_PROMPT.format(
            count=len(prompt_dnas),
            prompts=prompts_text,
        )
        
        return CanonicalTemplate(
            text="Template extraction not yet implemented",
            variables=[],
        )
    
    async def generate_explanation(self, prompt_dnas: list[PromptDNA]) -> str:
        """Generate human-readable explanation for why prompts belong together"""
        return "Explanation generation not yet implemented"
