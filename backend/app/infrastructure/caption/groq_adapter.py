"""
Groq Caption Generation Adapter.

Implements CaptionGenerator using the Groq REST API (OpenAI-compatible).
Nearly identical to the Fireworks caption adapter — only the base URL and
provider name in metadata differ.
"""
import asyncio
import time
from typing import Dict, Any, List

from loguru import logger
import httpx

from app.core.config import AIProviderSettings
from app.core.exceptions import CaptionGenerationException
from app.domain.interfaces.caption import CaptionGenerator
from app.domain.models.caption import (
    CaptionGenerationRequest,
    CaptionGenerationResult,
    CaptionCandidate,
    CaptionMetadata,
    CaptionStatistics,
)
from app.domain.models.ai import AIMessage, AIModelInfo, AIUsage


class GroqCaptionAdapter(CaptionGenerator):
    """
    Concrete adapter for the Groq chat completion API (text-only captions).
    Supports connection pooling, retries with exponential backoff, and strict
    error mapping.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, settings: AIProviderSettings):
        self._settings = settings
        if not self._settings.api_key:
            raise CaptionGenerationException("Groq API key is not configured.")

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        )

    def _map_messages(self, messages: List[AIMessage]) -> List[Dict[str, Any]]:
        """Maps AIMessage domain objects to Groq text-only JSON array format."""
        mapped = []
        for msg in messages:
            content_text = ""
            for block in msg.content:
                if hasattr(block, "text"):
                    content_text += block.text + "\n"
            mapped.append({"role": msg.role.value, "content": content_text.strip()})
        return mapped

    async def generate(self, request: CaptionGenerationRequest) -> CaptionGenerationResult:
        """Executes the generation request against the Groq API with exponential backoff."""
        payload: Dict[str, Any] = {
            "model": self._settings.default_model,
            "messages": self._map_messages(request.messages),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "n": 1,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self._settings.max_retries):
            start_time = time.time()
            try:
                logger.info(
                    f"Groq Caption request starting. Model: {self._settings.default_model} "
                    f"Attempt: {attempt + 1}"
                )

                response = await self._client.post(
                    self.GROQ_API_URL, json=payload, headers=headers
                )
                latency = time.time() - start_time

                if response.status_code == 401:
                    raise CaptionGenerationException(
                        "Groq authentication failed (401). Check AI__API_KEY."
                    )
                elif response.status_code == 403:
                    raise CaptionGenerationException("Groq authorization failed (403).")
                elif response.status_code == 404:
                    raise CaptionGenerationException(
                        f"Groq model '{self._settings.default_model}' not found (404). "
                        "Update AI__DEFAULT_MODEL."
                    )
                elif response.status_code == 402 or response.status_code == 412:
                    raise CaptionGenerationException(
                        f"Groq account billing issue ({response.status_code}). "
                        "Check https://console.groq.com."
                    )
                elif response.status_code == 429:
                    logger.warning(f"Groq rate limit (429). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise CaptionGenerationException(
                        "Groq rate limit exceeded after maximum retries."
                    )
                elif response.status_code >= 500:
                    logger.warning(
                        f"Groq server error ({response.status_code}). Latency: {latency:.2f}s"
                    )
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise CaptionGenerationException(
                        f"Groq provider failed permanently: {response.status_code}"
                    )

                response.raise_for_status()
                json_data = response.json()
                logger.info(f"Groq Caption request complete. Latency: {latency:.2f}s")
                return self._parse_response(json_data, request)

            except httpx.TimeoutException:
                logger.warning(f"Groq Caption timeout on attempt {attempt + 1}.")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise CaptionGenerationException(
                    "Groq request timed out after maximum retries."
                )
            except httpx.RequestError as e:
                logger.warning(f"Groq Caption network error on attempt {attempt + 1}: {e}")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise CaptionGenerationException(f"Groq network failure: {e}")
            except ValueError:
                raise CaptionGenerationException("Groq returned malformed JSON.")

        raise CaptionGenerationException(
            "Failed to generate captions due to unknown retry failure."
        )

    def _parse_response(
        self, json_data: Dict[str, Any], request: CaptionGenerationRequest
    ) -> CaptionGenerationResult:
        """Parses the Groq response into a standard CaptionGenerationResult."""
        try:
            choices = json_data.get("choices", [])
            if not choices:
                raise CaptionGenerationException("Groq API returned empty choices.")

            candidates = []
            for choice in choices:
                text = choice.get("message", {}).get("content", "").strip()
                if not text:
                    continue
                candidates.append(
                    CaptionCandidate(
                        text=text,
                        tone=request.target_tone,
                        statistics=CaptionStatistics(
                            word_count=len(text.split()),
                            character_count=len(text),
                        ),
                    )
                )

            usage = json_data.get("usage", {})
            metadata = CaptionMetadata(
                model_info=AIModelInfo(
                    provider_name="groq",
                    model_name=json_data.get("model", self._settings.default_model),
                ),
                usage=AIUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                ),
                provider_metadata={
                    "system_fingerprint": json_data.get("system_fingerprint", "")
                },
            )

            return CaptionGenerationResult(candidates=candidates, metadata=metadata)

        except KeyError as e:
            raise CaptionGenerationException(
                f"Groq JSON schema invalid. Missing key: {e}"
            )
        except Exception as e:
            raise CaptionGenerationException(f"Failed to parse Groq response: {e}")
