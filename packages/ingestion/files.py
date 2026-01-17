"""
File-based ingestion (JSON, CSV, TXT)
"""

import json
import csv
from pathlib import Path
from typing import Any


async def ingest_from_file(file_path: str) -> list[dict]:
    """Ingest prompts from a file (JSON, CSV, or TXT)"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.suffix == ".json":
        return await _ingest_json(file_path)
    elif path.suffix == ".csv":
        return await _ingest_csv(file_path)
    else:
        return await _ingest_text(file_path)


async def _ingest_json(file_path: str) -> list[dict]:
    """Ingest from JSON file"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both list and single object
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        return []


async def _ingest_csv(file_path: str) -> list[dict]:
    """Ingest from CSV file"""
    prompts = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row)
    return prompts


async def _ingest_text(file_path: str) -> list[dict]:
    """Ingest from plain text file (one prompt per line)"""
    prompts = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                prompts.append({"text": line})
    return prompts
