"""AWS Cognito authentication helpers for Fluidra cloud."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .const import COGNITO_CLIENT_ID, COGNITO_REGION, TOKEN_REFRESH_MARGIN


class FluidraAuthenticationError(Exception):
    """Raised when authentication with Fluidra fails."""


@dataclass(slots=True)
class FluidraTokens:
    """Container for Fluidra auth tokens."""

    access_token: str
    id_token: str
    refresh_token: str | None
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Return True when the token should be renewed."""
        return datetime.now(timezone.utc) + TOKEN_REFRESH_MARGIN >= self.expires_at


class FluidraAuth:
    """Authenticate against the Fluidra AWS Cognito pool."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._tokens: FluidraTokens | None = None

    async def async_get_access_token(self, *, force: bool = False) -> str:
        """Return a valid access token."""
        if force or self._tokens is None or self._tokens.is_expired:
            self._tokens = await self._async_authenticate()
        return self._tokens.access_token

    async def async_get_headers(self) -> dict[str, str]:
        """Return API headers with a fresh token."""
        token = await self.async_get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant/FluidraZ250iQ",
            "x-access-token": token,
            "x-api-key": token,
        }

    async def _async_authenticate(self) -> FluidraTokens:
        """Authenticate in an executor because boto3 is blocking."""
        loop = asyncio.get_running_loop()
        try:
            auth_result = await loop.run_in_executor(None, self._authenticate_sync)
        except Exception as err:  # pragma: no cover - defensive
            raise FluidraAuthenticationError(str(err)) from err

        expires_in = int(auth_result["ExpiresIn"])
        return FluidraTokens(
            access_token=auth_result["AccessToken"],
            id_token=auth_result["IdToken"],
            refresh_token=auth_result.get("RefreshToken"),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        )

    def _authenticate_sync(self) -> dict:
        """Perform Cognito authentication synchronously."""
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError as err:
            raise FluidraAuthenticationError(
                "The boto3 dependency is not available yet. Restart Home Assistant and try again."
            ) from err

        client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
        try:
            response = client.initiate_auth(
                ClientId=COGNITO_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": self._username,
                    "PASSWORD": self._password,
                },
            )
            return response["AuthenticationResult"]
        except (BotoCoreError, ClientError) as err:
            raise FluidraAuthenticationError(str(err)) from err
