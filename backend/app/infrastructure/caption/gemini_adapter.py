"""
Google Gemini Caption Generation Adapter.

Implements CaptionGenerator using the Gemini generateContent API.
Caption generation is text-only so this is simpler than the vision adapter —
just maps text messages to Gemini `contents` and parses the plain-text reply.
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


class GeminiCaptionAdapter(CaptionGenerator):
    """
    Concrete adapter for the Gemini generateContent API (text-only captions).
    Supports connection pooling, retries with exponential backoff, and strict
    error mapping.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, settings: AIProviderSettings):
        self._settings = settings
        if not self._settings.api_key:
            raise CaptionGenerationException("Gemini API key is not configured.")

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        )

    @property
    def _endpoint(self) -> str:
        return f"{self.BASE_URL}/{self._settings.default_model}:generateContent"

    def _map_messages(self, messages: List[AIMessage]) -> tuple[List[Dict[str, Any]], Dict[str, Any] | None]:
        """
        Returns (contents, systemInstruction) for the Gemini request.
        System messages are separated out into systemInstruction.
        """
        contents: List[Dict[str, Any]] = []
        system_instruction = None

        for msg in messages:
            role = msg.role.value
            text = " ".join(
                block.text for block in msg.content if hasattr(block, "text")
            ).strip()
            if not text:
                continue

            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
            else:
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({"role": gemini_role, "parts": [{"text": text}]})

        return contents, system_instruction

    async def generate(self, request: CaptionGenerationRequest) -> CaptionGenerationResult:
        """Executes the generation request against the Gemini API."""
        contents, system_instruction = self._map_messages(request.messages)

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        params = {"key": self._settings.api_key}
        headers = {"Content-Type": "application/json"}

        for attempt in range(self._settings.max_retries):
            start_time = time.time()
            try:
                logger.info(
                    f"Gemini Caption request starting. Model: {self._settings.default_model} "
                    f"Attempt: {attempt + 1}"
                )

                response = await self._client.post(
                    self._endpoint, json=payload, params=params, headers=headers
                )
                latency = time.time() - start_time

                if response.status_code == 400:
                    raise CaptionGenerationException(
                        f"Gemini bad request (400): {response.text[:300]}"
                    )
                elif response.status_code in (401, 403):
                    raise CaptionGenerationException(
                        f"Gemini authentication failed ({response.status_code}). "
                        "Check AI__API_KEY."
                    )
                elif response.status_code == 404:
                    raise CaptionGenerationException(
                        f"Gemini model '{self._settings.default_model}' not found (404). "
                        "Update AI__DEFAULT_MODEL."
                    )
                elif response.status_code == 429:
                    logger.warning(f"Gemini rate limit (429). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        # Free tier enforces a per-minute window; short exponential
                        # backoff never clears it. Wait long enough to re-enter.
                        await asyncio.sleep(20 * (attempt + 1))
                        continue
                    raise CaptionGenerationException(
                        "Gemini rate limit exceeded after maximum retries."
                    )
                elif response.status_code >= 500:
                    logger.warning(
                        f"Gemini server error ({response.status_code}). Latency: {latency:.2f}s"
                    )
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise CaptionGenerationException(
                        f"Gemini provider failed permanently: {response.status_code}"
                    )

                response.raise_for_status()
                json_data = response.json()
                logger.info(f"Gemini Caption request complete. Latency: {latency:.2f}s")
                return self._parse_response(json_data, request)

            except httpx.TimeoutException:
                logger.warning(f"Gemini Caption timeout on attempt {attempt + 1}.")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise CaptionGenerationException(
                    "Gemini request timed out after maximum retries."
                )
            except httpx.RequestError as e:
                logger.warning(f"Gemini Caption network error on attempt {attempt + 1}: {e}")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise CaptionGenerationException(f"Gemini network failure: {e}")

        raise CaptionGenerationException(
            "Failed to generate captions due to unknown retry failure."
        )

    def _parse_response(
        self, json_data: Dict[str, Any], request: CaptionGenerationRequest
    ) -> CaptionGenerationResult:
        """Parses the Gemini generateContent response into a CaptionGenerationResult."""
        try:
            candidates = json_data.get("candidates", [])
            if not candidates:
                feedback = json_data.get("promptFeedback", {})
                raise CaptionGenerationException(
                    f"Gemini returned no candidates. "
                    f"Block reason: {feedback.get('blockReason', 'unknown')}"
                )

            text = "".join(
                p.get("text", "")
                for p in candidates[0].get("content", {}).get("parts", [])
            ).strip()

            if not text:
                raise CaptionGenerationException("Gemini returned empty caption.")

            usage_meta = json_data.get("usageMetadata", {})
            metadata = CaptionMetadata(
                model_info=AIModelInfo(
                    provider_name="gemini",
                    model_name=self._settings.default_model,
                ),
                usage=AIUsage(
                    prompt_tokens=usage_meta.get("promptTokenCount", 0),
                    completion_tokens=usage_meta.get("candidatesTokenCount", 0),
                    total_tokens=usage_meta.get("totalTokenCount", 0),
                ),
                provider_metadata={},
            )

            return CaptionGenerationResult(
                candidates=[
                    CaptionCandidate(
                        text=text,
                        tone=request.target_tone,
                        statistics=CaptionStatistics(
                            word_count=len(text.split()),
                            character_count=len(text),
                        ),
                    )
                ],
                metadata=metadata,
            )

        except CaptionGenerationException:
            raise
        except Exception as e:
            raise CaptionGenerationException(f"Failed to parse Gemini response: {e}")
