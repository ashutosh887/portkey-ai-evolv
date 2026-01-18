import os
import json
import re
import logging
import asyncio
from typing import Optional, List
from packages.core.models import PromptDNA, CanonicalTemplate

try:
    from portkey_ai import Portkey
except ImportError:
    Portkey = None

logger = logging.getLogger(__name__)

TEMPLATE_EXTRACTION_PROMPT = """You are an expert prompt engineer. Your task is to generalize a list of similar prompts into a single CANONICAL TEMPLATE.

### Guidelines:
1. **Analyze Patterns**: Look for static text (intent) vs dynamic text (entities, names, numbers).
2. **Create Variables**: Replace dynamic parts with {{variable_name}}. Use descriptive names (e.g., {{food_item}}, {{code_language}}, {{target_audience}}).
3. **Be Specific but Flexible**: The template should cover all provided examples.
4. **Valid JSON**: Output strictly valid JSON.

### Examples:
Input:
- "Compare the nutritional benefits of quinoa and brown rice"
- "What is better for muscle gain, chicken or beef?"
Output:
{{
  "template": "Compare the nutritional benefits of {{food_1}} and {{food_2}}",
  "variables": ["food_1", "food_2"]
}}

Input:
- "Write a python script to scrape a website"
- "Write a java program to connect to DB"
Output:
{{
  "template": "Write a {{programming_language}} {{script_type}} to {{task}}",
  "variables": ["programming_language", "script_type", "task"]
}}

### Current Data:
Family Size: {count}
Prompts:
{prompts}

### Your Output:
Provide the JSON solution."""

EXPLANATION_PROMPT = """You are analyzing a cluster of similar prompts to explain why they belong together.

Here are {count} prompts in the same family:

{prompts}

Provide a concise explanation (2-3 sentences) of why these prompts are semantically similar and form a family. Focus on:
- Common intent or purpose
- Shared structure or pattern
- Similar use cases

Return only the explanation text, no JSON or formatting."""


class LLMClient:
    def __init__(self, api_key: Optional[str] = None, virtual_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("PORTKEY_API_KEY")
        self.virtual_key = virtual_key or os.getenv("PORTKEY_VIRTUAL_KEY")
        self.model = model
        self._portkey = None
        
        if Portkey is None:
            logger.warning("portkey-ai package not available, LLMClient will use fallback")
            return
        
        if not self.api_key:
            logger.warning("PORTKEY_API_KEY not configured, LLMClient will use fallback")
            return
        
        if self.virtual_key and "your_virtual_key_here" in self.virtual_key:
            logger.warning("Ignoring placeholder PORTKEY_VIRTUAL_KEY")
            self.virtual_key = None
            
        portkey_config = {"api_key": self.api_key}
        if self.virtual_key:
            portkey_config["virtual_key"] = self.virtual_key
        
        try:
            self._portkey = Portkey(**portkey_config)
        except Exception as e:
            logger.warning(f"Failed to initialize Portkey client: {e}, will use fallback")
    
    def _is_available(self) -> bool:
        return self._portkey is not None and Portkey is not None
    
    def _call_portkey_sync(self, messages: List[dict], portkey_model: str, temperature: float) -> str:
        response = self._portkey.chat.completions.create(
            model=portkey_model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )
        content = response.choices[0].message.content.strip()
        if not content:
            raise ValueError("Empty response from LLM")
        return content

    async def _call_with_retry(self, messages: List[dict], max_retries: int = 3, temperature: float = 0.0) -> str:
        if not self._is_available():
            raise RuntimeError("Portkey client not available")
        
        model_map = {
            "gpt-4o-mini": "@openai/gpt-4o-mini",
            "gpt-4": "@openai/gpt-4",
            "gpt-3.5-turbo": "@openai/gpt-3.5-turbo",
            "claude-3-haiku": "@anthropic/claude-3-haiku-20240307",
            "claude-3-sonnet": "@anthropic/claude-3-sonnet-20240229",
        }
        portkey_model = model_map.get(self.model, f"@openai/{self.model}")
        
        last_error = None
        for attempt in range(max_retries):
            try:
                content = await asyncio.to_thread(
                    self._call_portkey_sync,
                    messages,
                    portkey_model,
                    temperature
                )
                return content
            
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"LLM call failed after {max_retries} attempts: {e}")
        
        raise last_error or RuntimeError("LLM call failed")
    
    async def extract_template(self, prompt_dnas: List[PromptDNA]) -> CanonicalTemplate:
        if not prompt_dnas:
            return CanonicalTemplate(text="", variables=[])
        
        if not self._is_available():
            raise RuntimeError("Portkey client not available, use MockLLMClient or configure PORTKEY_API_KEY")
        
        prompts_text = "\n\n---\n\n".join([f"Prompt {i+1}:\n{dna.raw_text}" for i, dna in enumerate(prompt_dnas)])
        
        prompt = TEMPLATE_EXTRACTION_PROMPT.format(
            count=len(prompt_dnas),
            prompts=prompts_text,
        )
        
        try:
            content = await self._call_with_retry(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            
            # Try to find JSON block
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            # Find first { and last }
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx+1]
            else:
                json_str = content

            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON. Raw content: {content[:200]}...")
                # Try soft repair if needed (simple fallback)
                result = {"template": content, "variables": []}
            
            template_text = result.get("template", "")
            variables = result.get("variables", [])
            example_values = {}
            
            for var in variables[:5]:
                example_values[var] = [f"example_{var}_1", f"example_{var}_2"]
            
            return CanonicalTemplate(
                text=template_text,
                variables=variables,
                example_values=example_values,
            )
        
        except Exception as e:
            logger.error(f"Template extraction failed: {e}")
            raise
    
    async def generate_explanation(self, prompt_dnas: List[PromptDNA]) -> str:
        if not prompt_dnas:
            return "No prompts provided"
        
        if not self._is_available():
            raise RuntimeError("Portkey client not available, use MockLLMClient or configure PORTKEY_API_KEY")
        
        prompts_text = "\n\n---\n\n".join([f"Prompt {i+1}:\n{dna.raw_text}" for i, dna in enumerate(prompt_dnas)])
        
        prompt = EXPLANATION_PROMPT.format(
            count=len(prompt_dnas),
            prompts=prompts_text,
        )
        
        try:
            explanation = await self._call_with_retry(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return explanation.strip()
        
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return f"This family contains {len(prompt_dnas)} prompts with similar semantic structure."
