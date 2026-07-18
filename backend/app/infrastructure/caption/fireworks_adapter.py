"""
Fireworks Caption Generation Adapter.

Implements CaptionGenerator using the Fireworks AI REST API.
Operates completely agnostically from business logic, dealing only in HTTP transactions
and mapping responses to standard domain types.
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
    CaptionStatistics
)
from app.domain.models.ai import AIMessage, AIModelInfo, AIUsage


class FireworksCaptionAdapter(CaptionGenerator):
    """
    Concrete adapter for Fireworks Text/Chat completion API.
    Supports connection pooling, retries with exponential backoff, and strict error mapping.
    """
    
    FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
    
    def __init__(self, settings: AIProviderSettings):
        self._settings = settings
        if not self._settings.api_key:
            raise CaptionGenerationException("Fireworks API Key is not configured.")
            
        # Initialize a shared client for connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
        )
        
    def _map_messages(self, messages: List[AIMessage]) -> List[Dict[str, Any]]:
        """Maps standard AIMessage domain objects to Fireworks API JSON array format."""
        mapped = []
        for msg in messages:
            # We assume text-only content for caption generation since vision is done
            content_text = ""
            for block in msg.content:
                if hasattr(block, 'text'):
                    content_text += block.text + "\n"
            mapped.append({
                "role": msg.role.value,
                "content": content_text.strip()
            })
        return mapped

    async def generate(self, request: CaptionGenerationRequest) -> CaptionGenerationResult:
        """
        Executes the generation request against the Fireworks API with exponential backoff.
        """
        payload = {
            "model": self._settings.default_model,
            "messages": self._map_messages(request.messages),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            # We explicitly ask for 1 choice to keep standard flow, but n could be mapped later
            "n": 1,
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self._settings.max_retries):
            start_time = time.time()
            try:
                logger.info(f"Fireworks API request starting. Model: {self._settings.default_model} Attempt: {attempt + 1}")
                
                response = await self._client.post(
                    self.FIREWORKS_API_URL,
                    json=payload,
                    headers=headers
                )
                
                latency = time.time() - start_time
                
                # Check explicit status codes
                if response.status_code == 401:
                    raise CaptionGenerationException("Fireworks authentication failed (401). Check API Key.")
                elif response.status_code == 403:
                    raise CaptionGenerationException("Fireworks authorization failed (403).")
                elif response.status_code == 404:
                    raise CaptionGenerationException(
                        f"Fireworks model '{self._settings.default_model}' not found (404). "
                        "The model may be deprecated — update AI__DEFAULT_MODEL."
                    )
                elif response.status_code == 429:
                    logger.warning(f"Fireworks rate limit reached (429). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise CaptionGenerationException("Fireworks rate limit exceeded after maximum retries.")
                elif response.status_code >= 500:
                    logger.warning(f"Fireworks server error ({response.status_code}). Latency: {latency:.2f}s")
                    if attempt < self._settings.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise CaptionGenerationException(f"Fireworks provider failed permanently: {response.status_code}")
                
                # Raise for any other unexpected HTTP status
                response.raise_for_status()
                
                json_data = response.json()
                
                logger.info(f"Fireworks API request complete. Latency: {latency:.2f}s")
                return self._parse_response(json_data, request)
                
            except httpx.TimeoutException:
                logger.warning(f"Fireworks API timeout on attempt {attempt + 1}.")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise CaptionGenerationException("Fireworks request timed out after maximum retries.")
            except httpx.RequestError as e:
                logger.warning(f"Fireworks API network error on attempt {attempt + 1}: {str(e)}")
                if attempt < self._settings.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise CaptionGenerationException(f"Fireworks network failure: {str(e)}")
            except ValueError:
                raise CaptionGenerationException("Fireworks returned malformed JSON.")

        # Fallback if loops exit weirdly
        raise CaptionGenerationException("Failed to generate captions due to unknown retry failure.")

    def _parse_response(self, json_data: Dict[str, Any], request: CaptionGenerationRequest) -> CaptionGenerationResult:
        """Parses the Fireworks response into a standard CaptionGenerationResult."""
        try:
            choices = json_data.get("choices", [])
            if not choices:
                raise CaptionGenerationException("Fireworks API returned empty choices.")
                
            candidates = []
            for choice in choices:
                text = choice.get("message", {}).get("content", "").strip()
                if not text:
                    continue
                    
                stats = CaptionStatistics(
                    word_count=len(text.split()),
                    character_count=len(text)
                )
                
                candidates.append(
                    CaptionCandidate(
                        text=text,
                        tone=request.target_tone,
                        statistics=stats
                    )
                )
                
            usage = json_data.get("usage", {})
            metadata = CaptionMetadata(
                model_info=AIModelInfo(
                    provider_name="fireworks",
                    model_name=json_data.get("model", self._settings.default_model)
                ),
                usage=AIUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0)
                ),
                provider_metadata={"system_fingerprint": json_data.get("system_fingerprint", "")}
            )
            
            return CaptionGenerationResult(candidates=candidates, metadata=metadata)
            
        except KeyError as e:
            raise CaptionGenerationException(f"Fireworks JSON schema invalid. Missing key: {str(e)}")
        except Exception as e:
            raise CaptionGenerationException(f"Failed to parse Fireworks response: {str(e)}")
