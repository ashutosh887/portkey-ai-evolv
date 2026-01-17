"""
Portkey Log Ingestion Module

This module handles the ingestion of logs from Portkey AI's Observability Platform.
It uses the "Log Export" API workflow:
1. Trigger an asynchronous export job (POST /logs/exports)
2. Poll for completion (GET /logs/exports/{id})
3. Download the resulting JSONL file
4. Map entries to the internal PromptInstance schema
"""

import asyncio
import json
import logging
import httpx
from datetime import datetime
from typing import List, Optional
from packages.core.models import PromptInstance

logger = logging.getLogger(__name__)

class PortKeyIngestor:
    """
    Client for ingesting logs using the Portkey Log Exports API.
    """
    
    BASE_URL = "https://api.portkey.ai/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize the ingestor with your Portkey API key.
        
        Args:
            api_key: Your x-portkey-api-key
        """
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "x-portkey-api-key": api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def run_ingestion(self, time_min: datetime) -> List[PromptInstance]:
        """
        Run the full ingestion workflow.
        
        Args:
            time_min: Only ingest logs created after this datetime
            
        Returns:
            List of parsed PromptInstance objects
        """
        try:
            logger.info(f"Starting Portkey export for logs since {time_min}")
            export_id = await self.trigger_export(time_min)
            
            logger.info(f"Polling export job {export_id}...")
            download_url = await self.wait_for_export(export_id)
            
            logger.info("Export complete. Downloading logs...")
            logs = await self.download_logs(download_url)
            
            instances = [self.map_log_to_instance(log) for log in logs]
            logger.info(f"Successfully ingested {len(instances)} prompts from Portkey")
            
            return instances
            
        except Exception as e:
            logger.error(f"Portkey ingestion failed: {str(e)}")
            raise
        finally:
            await self.client.aclose()

    async def trigger_export(self, time_min: datetime) -> str:
        """
        Step 1: Create a new export job.
        """
        from datetime import datetime as dt
        
        payload = {
            "description": "Automated ingestion export",
            "filters": {
                "time_of_generation_min": time_min.isoformat(),
                "time_of_generation_max": dt.utcnow().isoformat(),
                "page_size": 50000
            },
            "requested_data": [
                "id",
                "trace_id", 
                "created_at", 
                "request", 
                "response", 
                "is_success",
                "cost",
                "cost_currency",
                "ai_model",
                "response_time", 
                "metadata"
            ]
        }
        
        try:
            response = await self.client.post("/logs/exports", json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"API Error Body: {e.response.text}")
            raise
        
        data = response.json()
        export_id = data["id"]
        logger.info(f"Starting export job {export_id}...")
        start_response = await self.client.post(f"/logs/exports/{export_id}/start")
        start_response.raise_for_status()
        
        return export_id

    async def wait_for_export(self, export_id: str, poll_interval: int = 5) -> str:
        """
        Step 2: Poll the export job status until 'completed'.
        """
        while True:
            response = await self.client.get(f"/logs/exports/{export_id}")
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            logger.info(f"Export status: {status}")
            
            if status in ("completed", "success"):
                logger.info(f"Export complete! Getting download URL...")
                download_response = await self.client.get(f"/logs/exports/{export_id}/download")
                download_response.raise_for_status()
                download_data = download_response.json()
                download_url = download_data.get("signed_url") or download_data.get("url") or download_data.get("download_url")
                logger.info(f"Download URL obtained: {download_url[:50]}..." if download_url else "No URL found")
                return download_url
            elif status in ("failure", "failed", "error"):
                raise Exception(f"Export job {export_id} failed on server side.")
            
            await asyncio.sleep(poll_interval)

    async def download_logs(self, url: str) -> List[dict]:
        async with httpx.AsyncClient() as dl_client:
            response = await dl_client.get(url)
            response.raise_for_status()
            
            logs = []
            for line in response.text.strip().split('\n'):
                if line.strip():
                    logs.append(json.loads(line))
            return logs

    def map_log_to_instance(self, log: dict) -> PromptInstance:
        from packages.ingestion.normalizer import normalize_text, compute_hash
        
        request_body = log.get("request", {})
        messages = request_body.get("messages", [])
        
        user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_text = m.get("content", "")
                break
        
        normalized = normalize_text(user_text)
        dedup_hash = compute_hash(normalized)
        
        from packages.ingestion.dedup import simhash
        simhash_int = simhash(normalized) if normalized else None
        simhash_fingerprint = hex(simhash_int) if simhash_int is not None else None
        
        return PromptInstance(
            prompt_id=log.get("id"),
            original_text=user_text,
            normalized_text=normalized,
            dedup_hash=dedup_hash,
            simhash=simhash_fingerprint,
            created_at=self._parse_date(log.get("created_at")),
            metadata={
                "trace_id": log.get("trace_id"),
                "model": log.get("ai_model"),
                "provider": log.get("ai_provider"),
                "cost": log.get("cost"),
                "currency": log.get("cost_currency"),
                "latency_ms": log.get("response_time"),
                "status": "success" if log.get("is_success") else "failed",
                "custom_metadata": log.get("metadata", {})
            }
        )

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        if not date_str:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return datetime.utcnow()
