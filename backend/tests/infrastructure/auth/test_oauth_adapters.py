"""
Tests for OAuth infrastructure adapters.

All HTTP calls are mocked via pytest-httpx or unittest.mock.patch
so no real network traffic is made.
"""
import json
import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.core.config import OAuthProviderConfig
from app.domain.models.auth import OAuthProvider as OAuthProviderEnum
from app.domain.models.oauth import OAuthTokenBundle
from app.domain.exceptions import DomainException
from app.services.oauth_registry import OAuthProviderRegistry
from app.infrastructure.auth.oauth.google import GoogleOAuthAdapter
from app.infrastructure.auth.oauth.github import GitHubOAuthAdapter
from app.infrastructure.auth.oauth.apple import AppleOAuthAdapter
from app.infrastructure.auth.oauth.microsoft import MicrosoftOAuthAdapter
from app.infrastructure.auth.oauth.twitter import TwitterOAuthAdapter, generate_pkce_pair
from app.infrastructure.auth.oauth.base import OAuthHTTPError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_config(**kwargs) -> OAuthProviderConfig:
    defaults = dict(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="http://localhost/callback",
        authorization_endpoint="https://provider.example.com/auth",
        token_endpoint="https://provider.example.com/token",
        userinfo_endpoint="https://provider.example.com/userinfo",
        scopes=["openid", "email"],
    )
    defaults.update(kwargs)
    return OAuthProviderConfig(**defaults)


def _mock_response(status_code: int, json_body: dict | None = None, text: str = "") -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = (200 <= status_code < 300)
    resp.json.return_value = json_body or {}
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# PKCE utility
# ---------------------------------------------------------------------------

def test_generate_pkce_pair():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) > 40
    assert len(challenge) > 40
    assert verifier != challenge


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------

class TestGoogleOAuthAdapter:
    @pytest.fixture
    def adapter(self):
        return GoogleOAuthAdapter(make_config(
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            userinfo_endpoint="https://www.googleapis.com/oauth2/v2/userinfo",
            scopes=["openid", "email", "profile"],
        ))

    @pytest.mark.asyncio
    async def test_authorization_url_contains_required_params(self, adapter):
        url = await adapter.get_authorization_url("state123", "http://localhost/callback")
        assert "state=state123" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
        assert "client_id=test-client-id" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, adapter):
        token_payload = {"access_token": "acc", "refresh_token": "ref", "expires_in": 3600, "token_type": "Bearer"}
        adapter._client.post = AsyncMock(return_value=_mock_response(200, token_payload))

        bundle = await adapter.exchange_code("code123", "http://localhost/callback")

        assert bundle.access_token == "acc"
        assert bundle.refresh_token == "ref"
        assert bundle.expires_in == 3600

    @pytest.mark.asyncio
    async def test_exchange_code_invalid_code_raises(self, adapter):
        adapter._client.post = AsyncMock(return_value=_mock_response(400, text="invalid_grant"))

        with pytest.raises(OAuthHTTPError) as exc_info:
            await adapter.exchange_code("bad-code", "http://localhost/callback")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_fetch_user_profile(self, adapter):
        profile_payload = {
            "id": "12345",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "http://pic.url",
            "verified_email": True,
        }
        bundle = OAuthTokenBundle(access_token="acc")
        adapter._client.get = AsyncMock(return_value=_mock_response(200, profile_payload))

        profile = await adapter.fetch_user_profile(bundle)

        assert profile.provider_id == "12345"
        assert profile.email == "user@example.com"
        assert profile.display_name == "Test User"
        assert profile.avatar_url == "http://pic.url"

    @pytest.mark.asyncio
    async def test_fetch_user_profile_invalid_token(self, adapter):
        bundle = OAuthTokenBundle(access_token="bad")
        adapter._client.get = AsyncMock(return_value=_mock_response(401, text="Unauthorized"))

        with pytest.raises(OAuthHTTPError):
            await adapter.fetch_user_profile(bundle)

    @pytest.mark.asyncio
    async def test_refresh_token(self, adapter):
        token_payload = {"access_token": "new_acc", "expires_in": 3600, "token_type": "Bearer"}
        adapter._client.post = AsyncMock(return_value=_mock_response(200, token_payload))

        bundle = await adapter.refresh_token("old_refresh")
        assert bundle.access_token == "new_acc"

    @pytest.mark.asyncio
    async def test_network_timeout_raises(self, adapter):
        adapter._client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with pytest.raises(httpx.TimeoutException):
            await adapter.exchange_code("code", "http://localhost/callback")


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

class TestGitHubOAuthAdapter:
    @pytest.fixture
    def adapter(self):
        return GitHubOAuthAdapter(make_config(
            authorization_endpoint="https://github.com/login/oauth/authorize",
            token_endpoint="https://github.com/login/oauth/access_token",
            userinfo_endpoint="https://api.github.com/user",
            scopes=["read:user", "user:email"],
        ))

    @pytest.mark.asyncio
    async def test_authorization_url(self, adapter):
        url = await adapter.get_authorization_url("state", "http://localhost/cb")
        assert "client_id=test-client-id" in url
        assert "state=state" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, adapter):
        token_payload = {"access_token": "gha_token", "token_type": "bearer"}
        adapter._client.post = AsyncMock(return_value=_mock_response(200, token_payload))

        bundle = await adapter.exchange_code("code", "http://localhost/cb")
        assert bundle.access_token == "gha_token"

    @pytest.mark.asyncio
    async def test_fetch_profile_with_public_email(self, adapter):
        profile_payload = {"id": 99, "login": "octocat", "name": "Octocat", "email": "octo@github.com", "avatar_url": "http://av"}
        bundle = OAuthTokenBundle(access_token="token")
        adapter._client.get = AsyncMock(return_value=_mock_response(200, profile_payload))

        profile = await adapter.fetch_user_profile(bundle)
        assert profile.provider_id == "99"
        assert profile.email == "octo@github.com"
        assert profile.username == "octocat"

    @pytest.mark.asyncio
    async def test_fetch_profile_fetches_email_when_private(self, adapter):
        profile_payload = {"id": 99, "login": "octocat", "name": "Octocat", "email": None, "avatar_url": "http://av"}
        emails_payload = [
            {"email": "private@github.com", "primary": True, "verified": True},
            {"email": "old@github.com", "primary": False, "verified": True},
        ]
        bundle = OAuthTokenBundle(access_token="token")

        responses = [_mock_response(200, profile_payload), _mock_response(200, emails_payload)]
        adapter._client.get = AsyncMock(side_effect=responses)

        profile = await adapter.fetch_user_profile(bundle)
        assert profile.email == "private@github.com"

    @pytest.mark.asyncio
    async def test_refresh_token_raises_not_implemented(self, adapter):
        with pytest.raises(NotImplementedError, match="GitHub OAuth Apps"):
            await adapter.refresh_token("token")


# ---------------------------------------------------------------------------
# Microsoft
# ---------------------------------------------------------------------------

class TestMicrosoftOAuthAdapter:
    @pytest.fixture
    def adapter(self):
        return MicrosoftOAuthAdapter(make_config(
            authorization_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            userinfo_endpoint="https://graph.microsoft.com/v1.0/me",
        ))

    @pytest.mark.asyncio
    async def test_exchange_code(self, adapter):
        adapter._client.post = AsyncMock(return_value=_mock_response(200, {"access_token": "ms_token", "token_type": "Bearer"}))
        bundle = await adapter.exchange_code("code", "http://localhost/cb")
        assert bundle.access_token == "ms_token"

    @pytest.mark.asyncio
    async def test_fetch_profile_uses_mail_field(self, adapter):
        raw = {"id": "ms-user-1", "displayName": "MS User", "mail": "ms@corp.com", "userPrincipalName": "ms_upn@corp.com"}
        bundle = OAuthTokenBundle(access_token="token")
        adapter._client.get = AsyncMock(return_value=_mock_response(200, raw))

        profile = await adapter.fetch_user_profile(bundle)
        assert profile.email == "ms@corp.com"
        assert profile.display_name == "MS User"

    @pytest.mark.asyncio
    async def test_fetch_profile_falls_back_to_upn(self, adapter):
        raw = {"id": "ms-user-1", "displayName": "MS User", "mail": None, "userPrincipalName": "ms@corp.com"}
        bundle = OAuthTokenBundle(access_token="token")
        adapter._client.get = AsyncMock(return_value=_mock_response(200, raw))

        profile = await adapter.fetch_user_profile(bundle)
        assert profile.email == "ms@corp.com"


# ---------------------------------------------------------------------------
# Twitter
# ---------------------------------------------------------------------------

class TestTwitterOAuthAdapter:
    @pytest.fixture
    def adapter(self):
        return TwitterOAuthAdapter(make_config(
            authorization_endpoint="https://twitter.com/i/oauth2/authorize",
            token_endpoint="https://api.twitter.com/2/oauth2/token",
            userinfo_endpoint="https://api.twitter.com/2/users/me",
            scopes=["tweet.read", "users.read"],
            pkce_enabled=True,
        ))

    @pytest.mark.asyncio
    async def test_authorization_url_includes_pkce(self, adapter):
        url = await adapter.get_authorization_url("state", "http://localhost/cb", code_challenge="challenge123")
        assert "code_challenge=challenge123" in url
        assert "code_challenge_method=S256" in url

    @pytest.mark.asyncio
    async def test_exchange_code_with_verifier(self, adapter):
        adapter._client.post = AsyncMock(return_value=_mock_response(200, {"access_token": "tw_token", "token_type": "bearer"}))
        bundle = await adapter.exchange_code("code", "http://localhost/cb", code_verifier="verifier123")
        assert bundle.access_token == "tw_token"

    @pytest.mark.asyncio
    async def test_fetch_profile(self, adapter):
        raw = {"data": {"id": "tw-1", "name": "Tweeter", "username": "tweeter_handle", "profile_image_url": "http://img"}}
        bundle = OAuthTokenBundle(access_token="tw_token")
        adapter._client.get = AsyncMock(return_value=_mock_response(200, raw))

        profile = await adapter.fetch_user_profile(bundle)
        assert profile.provider_id == "tw-1"
        assert profile.username == "tweeter_handle"
        assert profile.email is None  # Twitter doesn't expose email

    @pytest.mark.asyncio
    async def test_refresh_token(self, adapter):
        adapter._client.post = AsyncMock(return_value=_mock_response(200, {"access_token": "new_tw", "token_type": "bearer"}))
        bundle = await adapter.refresh_token("old_refresh")
        assert bundle.access_token == "new_tw"


# ---------------------------------------------------------------------------
# Apple
# ---------------------------------------------------------------------------

class TestAppleOAuthAdapter:
    @pytest.fixture
    def adapter(self):
        return AppleOAuthAdapter(make_config(
            authorization_endpoint="https://appleid.apple.com/auth/authorize",
            token_endpoint="https://appleid.apple.com/auth/token",
            userinfo_endpoint="",
        ))

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, adapter):
        url = await adapter.get_authorization_url("state", "http://localhost/cb")
        assert "response_mode=form_post" in url

    @pytest.mark.asyncio
    async def test_exchange_code_raises_when_no_private_key(self, adapter):
        with pytest.raises(NotImplementedError, match="private_key_pem"):
            await adapter.exchange_code("code", "http://localhost/cb")

    @pytest.mark.asyncio
    async def test_fetch_profile_from_id_token(self, adapter):
        claims = {"sub": "apple-sub-123", "email": "user@privaterelay.appleid.com", "email_verified": True}
        payload_b64 = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        id_token = f"header.{payload_b64}.sig"
        bundle = OAuthTokenBundle(access_token="acc", id_token=id_token)

        profile = await adapter.fetch_user_profile(bundle)
        assert profile.provider_id == "apple-sub-123"
        assert profile.email == "user@privaterelay.appleid.com"

    @pytest.mark.asyncio
    async def test_fetch_profile_raises_without_id_token(self, adapter):
        bundle = OAuthTokenBundle(access_token="acc", id_token=None)
        with pytest.raises(ValueError, match="id_token"):
            await adapter.fetch_user_profile(bundle)


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

class TestOAuthRegistryIntegration:
    def test_register_and_retrieve_all_providers(self):
        registry = OAuthProviderRegistry()
        cfg = make_config()
        adapters = {
            OAuthProviderEnum.GOOGLE: GoogleOAuthAdapter(cfg),
            OAuthProviderEnum.GITHUB: GitHubOAuthAdapter(cfg),
            OAuthProviderEnum.MICROSOFT: MicrosoftOAuthAdapter(cfg),
            OAuthProviderEnum.TWITTER: TwitterOAuthAdapter(cfg),
        }
        for provider, instance in adapters.items():
            registry.register_provider(provider, instance)

        assert set(registry.list_providers()) == set(adapters.keys())
        for provider in adapters:
            assert registry.get_provider(provider) is adapters[provider]

    def test_duplicate_registration_raises(self):
        registry = OAuthProviderRegistry()
        cfg = make_config()
        registry.register_provider(OAuthProviderEnum.GOOGLE, GoogleOAuthAdapter(cfg))
        with pytest.raises(DomainException, match="already registered"):
            registry.register_provider(OAuthProviderEnum.GOOGLE, GoogleOAuthAdapter(cfg))

    def test_unknown_provider_raises(self):
        registry = OAuthProviderRegistry()
        with pytest.raises(DomainException, match="not registered"):
            registry.get_provider(OAuthProviderEnum.APPLE)
