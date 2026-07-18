"""
Fireworks Vision Analysis Adapter.

Implements VisionAnalyzer using the Fireworks AI REST API (chat completions
with multimodal image_url content). Deals purely in HTTP transactions and
maps provider responses to standard domain types, mirroring the design of
FireworksCaptionAdapter.
"""
import asyncio
import json
import time
from typing import Dict, Any, List

from loguru import logger
import httpx

from app.core.config import AIProviderSettings
from app.core.exceptions import VisionAnalysisException
from app.domain.interfaces.vision import VisionAnalyzer
from app.domain.models.ai import AIMessage, AIModelInfo, AIUsage
from app.domain.models.vision import (
    VisionAnalysisRequest,
    VisionAnalysisResult,
    VisionAnalysisMetadata,
)


class FireworksVisionAdapter(VisionAnalyzer):
    """
    Concrete adapter for the Fireworks multimodal chat completion API.
    Supports connection pooling, retries with exponential backoff, and strict error mapping.
    """

    FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

    def __init__(self, settings: AIProviderSettings):
        self._settings = settings
        if not self._settings.api_key:
            raise VisionAnalysisException("Fireworks API Key is not configured.")

        # Initialize a shared client for connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
        )

    def _map_messages(self, messages: List[AIMessage]) -> List[Dict[str, Any]]:
        """Maps AIMessage domain objects to Fireworks multimodal JSON array format."""
        mapped = []
        for msg in messages:
            blocks: List[Dict[str, Any]] = []
            for block in msg.content:
                if hasattr(block, "text"):
                    blocks.append({"type": "text", "text": block.text})
                elif hasattr(block, "data_uri"):
                    blocks.append({
                        "type": "image_url",
                        "image_url": {"url": block.data_uri}
                    })
            mapped.append({"role": msg.role.value, "content": blocks})
        return mapped

    async def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResult:
        """
        Executes the analysis request against the Fireworks API with exponential backoff.
        """
        payload: Dict[str, Any] = {
            "model": self._settings.default_model,
            "messages": self._map_messages(request.messages),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "n": 1,
            "stream": False
        }
        if request.response_format:
            payload["response_format"] = request.response_format

        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(self._settings.max_retries):
            start_time = time.time()
            try:
                logger.info(f"Fireworks Vision request starting. Model: {self._settings.default_model} Attempt: {attempt + 1}")

                response = await self._client.post(
                    self.FIREWORKS_API_URL,
                    json=payload,
                    headers=headers
                )

                latency = time.time() - start_time

                if response.status_code == 401:
                    raise VisionAnalysisException("Fireworks authentication failed (401). Check API Key.")
                elif response.status_code == 403:
                    raise VisionAnalysisException("Fireworks authorization failed (403).")
                elif response.status_code == 404:
                    raise VisionAnalysisException(
                        f"Fireworks model '{self._settings.default_model}' not found (404). "
                        "The model may be deprecated — update AI__DEFAULT_MODEL."
                    )
                elif response.status_code == 402 or response.status_code == 412:
                    raise VisionAnalysisException(
                        "Fireworks account is suspended or out of credit "
                        f"({response.status_code}). Check billing at "
                        "https://fireworks.ai/account/billing."
                    )
                elif response.status_code == 429:
                    logger.warning(f"Fireworks rate limit reached (429). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise VisionAnalysisException("Fireworks rate limit exceeded after maximum retries.")
                elif response.status_code >= 500:
                    logger.warning(f"Fireworks server error ({response.status_code}). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise VisionAnalysisException(f"Fireworks provider failed permanently: {response.status_code}")

                response.raise_for_status()
                json_data = response.json()

                logger.info(f"Fireworks Vision request complete. Latency: {latency:.2f}s")
                return self._parse_response(json_data, processing_time_ms=int(latency * 1000))

            except httpx.TimeoutException:
                logger.warning(f"Fireworks Vision timeout on attempt {attempt + 1}.")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise VisionAnalysisException("Fireworks request timed out after maximum retries.")
            except httpx.RequestError as e:
                logger.warning(f"Fireworks Vision network error on attempt {attempt + 1}: {str(e)}")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise VisionAnalysisException(f"Fireworks network failure: {str(e)}")
            except ValueError:
                raise VisionAnalysisException("Fireworks returned malformed JSON.")

        raise VisionAnalysisException("Failed to analyze scene due to unknown retry failure.")

    def _parse_response(self, json_data: Dict[str, Any], processing_time_ms: int) -> VisionAnalysisResult:
        """Parses the Fireworks response into a standard VisionAnalysisResult."""
        try:
            choices = json_data.get("choices", [])
            if not choices:
                raise VisionAnalysisException("Fireworks API returned empty choices.")

            content = choices[0].get("message", {}).get("content", "").strip()
            if not content:
                raise VisionAnalysisException("Fireworks API returned empty content.")

            # The model is instructed (via response_format) to return the
            # VisionAnalysisResult JSON schema. Strip code fences defensively.
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:]
            parsed = json.loads(content)

            usage = json_data.get("usage", {})
            metadata = VisionAnalysisMetadata(
                model_info=AIModelInfo(
                    provider_name="fireworks",
                    model_name=json_data.get("model", self._settings.default_model)
                ),
                usage=AIUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0)
                ),
                raw_response_metadata={"system_fingerprint": json_data.get("system_fingerprint", "")},
                processing_time_ms=processing_time_ms
            )

            return VisionAnalysisResult(
                scene_summary=parsed.get("scene_summary", ""),
                objects=parsed.get("objects", []) or [],
                people=parsed.get("people", []) or [],
                activities=parsed.get("activities", []) or [],
                environment=parsed.get("environment", "") or "",
                mood=parsed.get("mood", "") or "",
                dominant_colors=parsed.get("dominant_colors", []) or [],
                ocr_placeholder=parsed.get("ocr_placeholder", "") or "",
                safety_flags=parsed.get("safety_flags", []) or [],
                metadata=metadata
            )

        except json.JSONDecodeError:
            raise VisionAnalysisException("Fireworks vision response was not valid JSON matching the analysis schema.")
        except VisionAnalysisException:
            raise
        except Exception as e:
            raise VisionAnalysisException(f"Failed to parse Fireworks vision response: {str(e)}")
