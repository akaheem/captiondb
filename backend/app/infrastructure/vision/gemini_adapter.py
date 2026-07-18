"""
Google Gemini Vision Analysis Adapter.

Implements VisionAnalyzer using the Google Generative Language REST API
(generateContent endpoint). Gemini uses a different wire format from the
OpenAI-compatible providers: `contents` array with `parts` containing text
and `inline_data` blobs rather than `image_url`.
"""
import asyncio
import json
import re
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

_DATA_URI_RE = re.compile(r"data:(image/\w+);base64,(.+)", re.DOTALL)


class GeminiVisionAdapter(VisionAnalyzer):
    """
    Concrete adapter for the Google Gemini generateContent API.
    Translates AIMessage/AIImageContent domain objects into Gemini `contents`
    parts and maps the response back to VisionAnalysisResult.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, settings: AIProviderSettings):
        self._settings = settings
        if not self._settings.api_key:
            raise VisionAnalysisException("Gemini API key is not configured.")

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        )

    @property
    def _endpoint(self) -> str:
        return f"{self.BASE_URL}/{self._settings.default_model}:generateContent"

    def _map_messages(self, messages: List[AIMessage]) -> List[Dict[str, Any]]:
        """
        Converts AIMessage list to Gemini `contents` array.

        Gemini does not support a separate system role in the contents array
        for all models; system instructions are passed via `systemInstruction`.
        We collect system messages separately and merge user/model turns here.
        """
        contents: List[Dict[str, Any]] = []
        for msg in messages:
            role = msg.role.value  # "system" | "user" | "assistant"
            if role == "system":
                # handled separately via _extract_system_prompt
                continue
            gemini_role = "model" if role == "assistant" else "user"
            parts: List[Dict[str, Any]] = []
            for block in msg.content:
                if hasattr(block, "text"):
                    parts.append({"text": block.text})
                elif hasattr(block, "data_uri"):
                    m = _DATA_URI_RE.match(block.data_uri)
                    if m:
                        mime_type, b64_data = m.group(1), m.group(2)
                        parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data,
                            }
                        })
            if parts:
                contents.append({"role": gemini_role, "parts": parts})
        return contents

    def _extract_system_prompt(self, messages: List[AIMessage]) -> Dict[str, Any] | None:
        """Returns a Gemini systemInstruction block if a system message exists."""
        for msg in messages:
            if msg.role.value == "system":
                text = " ".join(
                    block.text for block in msg.content if hasattr(block, "text")
                )
                if text:
                    return {"parts": [{"text": text}]}
        return None

    async def analyze(self, request: VisionAnalysisRequest) -> VisionAnalysisResult:
        """Executes the analysis request against the Gemini API with exponential backoff."""
        contents = self._map_messages(request.messages)
        system_instruction = self._extract_system_prompt(request.messages)

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
                "responseMimeType": "application/json",
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
                    f"Gemini Vision request starting. Model: {self._settings.default_model} "
                    f"Attempt: {attempt + 1}"
                )

                response = await self._client.post(
                    self._endpoint, json=payload, params=params, headers=headers
                )
                latency = time.time() - start_time

                if response.status_code == 400:
                    detail = response.text[:300]
                    raise VisionAnalysisException(
                        f"Gemini bad request (400): {detail}"
                    )
                elif response.status_code == 401 or response.status_code == 403:
                    raise VisionAnalysisException(
                        f"Gemini authentication failed ({response.status_code}). "
                        "Check AI__API_KEY."
                    )
                elif response.status_code == 404:
                    raise VisionAnalysisException(
                        f"Gemini model '{self._settings.default_model}' not found (404). "
                        "Update AI__DEFAULT_MODEL."
                    )
                elif response.status_code == 429:
                    logger.warning(f"Gemini rate limit (429). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise VisionAnalysisException(
                        "Gemini rate limit exceeded after maximum retries."
                    )
                elif response.status_code >= 500:
                    logger.warning(
                        f"Gemini server error ({response.status_code}). Latency: {latency:.2f}s"
                    )
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise VisionAnalysisException(
                        f"Gemini provider failed permanently: {response.status_code}"
                    )

                response.raise_for_status()
                json_data = response.json()
                logger.info(f"Gemini Vision request complete. Latency: {latency:.2f}s")
                return self._parse_response(
                    json_data, processing_time_ms=int(latency * 1000)
                )

            except httpx.TimeoutException:
                logger.warning(f"Gemini Vision timeout on attempt {attempt + 1}.")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise VisionAnalysisException(
                    "Gemini request timed out after maximum retries."
                )
            except httpx.RequestError as e:
                logger.warning(f"Gemini Vision network error on attempt {attempt + 1}: {e}")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise VisionAnalysisException(f"Gemini network failure: {e}")

        raise VisionAnalysisException(
            "Failed to analyze scene due to unknown retry failure."
        )

    def _parse_response(
        self, json_data: Dict[str, Any], processing_time_ms: int
    ) -> VisionAnalysisResult:
        """Parses the Gemini generateContent response into a VisionAnalysisResult."""
        try:
            candidates = json_data.get("candidates", [])
            if not candidates:
                # Check for promptFeedback block (safety block)
                feedback = json_data.get("promptFeedback", {})
                block_reason = feedback.get("blockReason", "unknown")
                raise VisionAnalysisException(
                    f"Gemini returned no candidates. Block reason: {block_reason}"
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts).strip()
            if not content:
                raise VisionAnalysisException("Gemini returned empty content.")

            # responseMimeType=application/json means the response IS json,
            # but strip code fences defensively in case the model wraps it.
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:].strip()

            parsed = json.loads(content)

            usage_meta = json_data.get("usageMetadata", {})
            metadata = VisionAnalysisMetadata(
                model_info=AIModelInfo(
                    provider_name="gemini",
                    model_name=self._settings.default_model,
                ),
                usage=AIUsage(
                    prompt_tokens=usage_meta.get("promptTokenCount", 0),
                    completion_tokens=usage_meta.get("candidatesTokenCount", 0),
                    total_tokens=usage_meta.get("totalTokenCount", 0),
                ),
                raw_response_metadata={},
                processing_time_ms=processing_time_ms,
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
                metadata=metadata,
            )

        except json.JSONDecodeError:
            raise VisionAnalysisException(
                "Gemini vision response was not valid JSON matching the analysis schema."
            )
        except VisionAnalysisException:
            raise
        except Exception as e:
            raise VisionAnalysisException(
                f"Failed to parse Gemini vision response: {e}"
            )
