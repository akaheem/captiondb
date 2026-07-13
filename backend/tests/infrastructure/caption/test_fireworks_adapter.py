import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.core.config import AIProviderSettings
from app.core.exceptions import CaptionGenerationException
from app.infrastructure.caption.fireworks_adapter import FireworksCaptionAdapter
from app.domain.models.caption import CaptionGenerationRequest
from app.domain.models.video import CaptionTone
from app.domain.models.ai import AIMessage, AIMessageRole, AITextContent


@pytest.fixture
def settings():
    return AIProviderSettings(
        provider="fireworks",
        api_key="test-key",
        default_model="test-model",
        max_retries=2,
        timeout_seconds=5
    )

@pytest.fixture
def adapter(settings):
    # Do not execute real HTTP calls
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.post = AsyncMock()
        adapter = FireworksCaptionAdapter(settings)
        adapter._client = mock_instance  # explicitly set the mocked instance
        yield adapter

@pytest.fixture
def valid_request():
    return CaptionGenerationRequest(
        messages=[
            AIMessage(role=AIMessageRole.SYSTEM, content=[AITextContent(text="System prompt.")]),
            AIMessage(role=AIMessageRole.USER, content=[AITextContent(text="Generate a caption.")])
        ],
        target_tone=CaptionTone.HUMOROUS_NON_TECH
    )

def create_mock_response(status_code: int, json_data: dict = None, raise_exc=None):
    mock = AsyncMock()
    mock.status_code = status_code
    if raise_exc:
        mock.raise_for_status.side_effect = raise_exc
    elif status_code >= 400:
        mock.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=None, response=mock)
    if json_data is not None:
        mock.json.return_value = json_data
    else:
        mock.json.side_effect = ValueError("Malformed JSON")
    return mock


@pytest.mark.asyncio
async def test_successful_completion(adapter, valid_request):
    mock_payload = {
        "id": "123",
        "model": "test-model",
        "choices": [
            {
                "message": {"content": "This is a great caption."}
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }
    adapter._client.post.return_value = create_mock_response(200, mock_payload)
    
    result = await adapter.generate(valid_request)
    
    assert len(result.candidates) == 1
    assert result.candidates[0].text == "This is a great caption."
    assert result.metadata.usage.prompt_tokens == 10
    adapter._client.post.assert_called_once()


@pytest.mark.asyncio
async def test_401_authentication_failure(adapter, valid_request):
    adapter._client.post.return_value = create_mock_response(401, {})
    
    with pytest.raises(CaptionGenerationException) as exc:
        await adapter.generate(valid_request)
    assert "authentication failed" in str(exc.value)


@pytest.mark.asyncio
async def test_403_authorization_failure(adapter, valid_request):
    adapter._client.post.return_value = create_mock_response(403, {})
    
    with pytest.raises(CaptionGenerationException) as exc:
        await adapter.generate(valid_request)
    assert "authorization failed" in str(exc.value)


@pytest.mark.asyncio
async def test_429_rate_limit_retry(adapter, valid_request):
    # First call returns 429, second returns 200
    mock_success = {
        "choices": [{"message": {"content": "Retried success"}}]
    }
    adapter._client.post.side_effect = [
        create_mock_response(429, {}),
        create_mock_response(200, mock_success)
    ]
    
    # We patch asyncio.sleep to avoid actually waiting during tests
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await adapter.generate(valid_request)
        
        assert result.candidates[0].text == "Retried success"
        assert adapter._client.post.call_count == 2
        mock_sleep.assert_called_once()


@pytest.mark.asyncio
async def test_500_server_error_retry_failure(adapter, valid_request):
    # Always returns 500
    adapter._client.post.return_value = create_mock_response(500, {})
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(CaptionGenerationException) as exc:
            await adapter.generate(valid_request)
            
    assert "provider failed permanently" in str(exc.value)
    assert adapter._client.post.call_count == 2  # max_retries = 2


@pytest.mark.asyncio
async def test_timeout_retry(adapter, valid_request):
    adapter._client.post.side_effect = httpx.TimeoutException("Timeout")
    
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(CaptionGenerationException) as exc:
            await adapter.generate(valid_request)
            
    assert "timed out after maximum retries" in str(exc.value)
    assert adapter._client.post.call_count == 2


@pytest.mark.asyncio
async def test_malformed_json(adapter, valid_request):
    adapter._client.post.return_value = create_mock_response(200, None)
    
    with pytest.raises(CaptionGenerationException) as exc:
        await adapter.generate(valid_request)
        
    assert "malformed JSON" in str(exc.value)


@pytest.mark.asyncio
async def test_empty_choices(adapter, valid_request):
    adapter._client.post.return_value = create_mock_response(200, {"choices": []})
    
    with pytest.raises(CaptionGenerationException) as exc:
        await adapter.generate(valid_request)
        
    assert "empty choices" in str(exc.value)


@pytest.mark.asyncio
async def test_invalid_schema(adapter, valid_request):
    # Missing 'choices' completely
    adapter._client.post.return_value = create_mock_response(200, {"not_choices": "here"})
    
    with pytest.raises(CaptionGenerationException) as exc:
        await adapter.generate(valid_request)
        
    assert "empty choices" in str(exc.value)  # The logic does .get("choices", []) which is empty
