import re
import uuid
from typing import Tuple


def normalize_prompt(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\r\n|\r|\n', ' ', text)
    text = re.sub(r' +', ' ', text)
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")
    text = text.lower()
    return text


def create_prompt_id() -> str:
    return str(uuid.uuid4())


def normalize_and_id(text: str) -> Tuple[str, str]:
    normalized = normalize_prompt(text)
    prompt_id = create_prompt_id()
    return normalized, prompt_id
