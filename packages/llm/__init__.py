"""
LLM abstraction layer with Portkey integration
"""

from packages.llm.client import LLMClient, TEMPLATE_EXTRACTION_PROMPT
from packages.llm.mock_client import MockLLMClient

__all__ = [
    "LLMClient",
    "MockLLMClient",
    "TEMPLATE_EXTRACTION_PROMPT",
]
