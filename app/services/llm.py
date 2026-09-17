from __future__ import annotations
import json
from typing import TypeVar, Type
import httpx
from pydantic import BaseModel
from app.core.config import get_settings

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self) -> None:
        self.s = get_settings()

    async def structured(self, system: str, user: str, schema: Type[T]) -> T:
        payload = {
            "model": self.s.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=self.s.llm_timeout_seconds) as client:
            r = await client.post(
                f"{self.s.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.s.llm_api_key}"}, json=payload,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return schema.model_validate(data)

    async def health(self) -> dict[str, object]:
        """Probe the configured OpenAI-compatible local endpoint without fabricating model readiness."""
        url = f"{self.s.llm_base_url.rstrip('/')}/models"
        try:
            async with httpx.AsyncClient(timeout=min(10, self.s.llm_timeout_seconds)) as client:
                r = await client.get(url, headers={"Authorization": f"Bearer {self.s.llm_api_key}"})
                r.raise_for_status()
                return {"available": True, "status_code": r.status_code, "endpoint": url}
        except Exception as exc:
            return {"available": False, "endpoint": url, "error_type": type(exc).__name__, "error": str(exc)[:240]}
