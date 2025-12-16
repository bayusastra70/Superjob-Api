from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


class OpenRouterService:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or getattr(settings, "OPENROUTER_API_KEY", "")
        self.model = model or getattr(settings, "OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]


