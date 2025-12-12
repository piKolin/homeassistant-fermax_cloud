"""API client for Fermax Cloud."""
import asyncio
import base64
import logging
import time
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import (
    FERMAX_API_BASE,
    FERMAX_CLIENT_ID,
    FERMAX_CLIENT_SECRET,
    FERMAX_OAUTH_BASE,
    INITIAL_RETRY_DELAY,
    MAX_RETRIES,
    MOBILE_HEADERS,
    TIMEOUT_CONNECTION,
    TIMEOUT_READ,
    TIMEOUT_TOTAL,
)

_LOGGER = logging.getLogger(__name__)


class FermaxError(Exception):
    """Base error for Fermax."""


class FermaxAuthError(FermaxError):
    """Authentication error."""


class FermaxConnectionError(FermaxError):
    """Connection error."""


class FermaxAPIError(FermaxError):
    """API error."""


class FermaxClient:
    """Client for Fermax Cloud API."""

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._email = email
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0.0
        self._token_lock = asyncio.Lock()

    def _get_basic_auth(self) -> str:
        """Get Basic Auth header value."""
        credentials = f"{FERMAX_CLIENT_ID}:{FERMAX_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _sanitize_log_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize sensitive data for logging."""
        sensitive_keys = [
            "password",
            "access_token",
            "refresh_token",
            "Authorization",
        ]
        sanitized = data.copy()
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"
        return sanitized

    async def async_login(self) -> dict[str, Any]:
        """Perform login and obtain tokens."""
        url = f"{FERMAX_OAUTH_BASE}/oauth/token"
        payload = {
            "grant_type": "password",
            "username": self._email,
            "password": self._password,
        }
        headers = {
            **MOBILE_HEADERS,
            "Authorization": self._get_basic_auth(),
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

        _LOGGER.debug("Attempting login for user: %s", self._email)

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.post(
                url, data=payload, headers=headers, timeout=timeout
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    _LOGGER.error(
                        "Login failed with status %s: %s", resp.status, error_text
                    )
                    raise FermaxAuthError(f"Login failed: {error_text}")

                data = await resp.json()
                _LOGGER.debug("Login response: %s", self._sanitize_log_data(data))

        except ClientError as err:
            _LOGGER.error("Connection error during login: %s", err)
            raise FermaxConnectionError(f"Connection error: {err}") from err

        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token")
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.time() + expires_in - 60  # 60s buffer

        _LOGGER.info("Login successful, token expires in %s seconds", expires_in)
        return data

    async def async_refresh_token(self) -> dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self._refresh_token:
            _LOGGER.debug("No refresh token available, performing full login")
            return await self.async_login()

        url = f"{FERMAX_OAUTH_BASE}/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }
        headers = {
            **MOBILE_HEADERS,
            "Authorization": self._get_basic_auth(),
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

        _LOGGER.debug("Attempting token refresh")

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.post(
                url, data=payload, headers=headers, timeout=timeout
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning(
                        "Token refresh failed with status %s, will perform full login",
                        resp.status,
                    )
                    return await self.async_login()

                data = await resp.json()

        except ClientError as err:
            _LOGGER.warning(
                "Connection error during token refresh: %s, will perform full login",
                err,
            )
            return await self.async_login()

        self._access_token = data["access_token"]
        if "refresh_token" in data:
            self._refresh_token = data["refresh_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.time() + expires_in - 60

        _LOGGER.info("Token refreshed successfully")
        return data

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token."""
        async with self._token_lock:
            if not self._access_token or time.time() >= self._expires_at:
                _LOGGER.debug("Token expired or missing, refreshing")
                await self.async_refresh_token()

    async def _retry_with_backoff(
        self, func, *args, **kwargs
    ) -> Any:
        """Retry operation with exponential backoff."""
        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (FermaxConnectionError, FermaxAPIError) as err:
                if attempt == MAX_RETRIES - 1:
                    raise
                delay = INITIAL_RETRY_DELAY * (2**attempt)
                _LOGGER.warning(
                    "Attempt %s/%s failed: %s. Retrying in %s seconds",
                    attempt + 1,
                    MAX_RETRIES,
                    err,
                    delay,
                )
                await asyncio.sleep(delay)

    async def async_get_pairings(self) -> list[dict[str, Any]]:
        """Get list of paired devices."""
        await self._ensure_token()
        url = f"{FERMAX_API_BASE}/pairing/api/v4/pairings/me"
        headers = {
            **MOBILE_HEADERS,
            "Authorization": f"Bearer {self._access_token}",
        }

        _LOGGER.debug("Getting pairings from: %s", url)

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 401:
                    _LOGGER.warning("Got 401, refreshing token and retrying")
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.get(
                        url, headers=headers, timeout=timeout
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        data = await retry_resp.json()
                else:
                    resp.raise_for_status()
                    data = await resp.json()

                _LOGGER.debug("Got %s pairings", len(data))
                return data

        except ClientError as err:
            _LOGGER.error("Error getting pairings: %s", err)
            raise FermaxConnectionError(f"Error getting pairings: {err}") from err

    async def async_get_device(self, device_id: str) -> dict[str, Any]:
        """Get detailed device information."""
        await self._ensure_token()
        url = f"{FERMAX_API_BASE}/deviceaction/api/v1/device/{device_id}"
        headers = {
            **MOBILE_HEADERS,
            "Authorization": f"Bearer {self._access_token}",
        }

        _LOGGER.debug("Getting device info for: %s", device_id)

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 401:
                    _LOGGER.warning("Got 401, refreshing token and retrying")
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.get(
                        url, headers=headers, timeout=timeout
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                else:
                    resp.raise_for_status()
                    return await resp.json()

        except ClientError as err:
            _LOGGER.error("Error getting device %s: %s", device_id, err)
            raise FermaxConnectionError(
                f"Error getting device {device_id}: {err}"
            ) from err

    async def async_get_services(self, device_id: str) -> list[str]:
        """Get available services for a device."""
        await self._ensure_token()
        url = f"{FERMAX_API_BASE}/services2/api/v1/services/{device_id}?deviceType=wifi"
        headers = {
            **MOBILE_HEADERS,
            "Authorization": f"Bearer {self._access_token}",
        }

        _LOGGER.debug("Getting services for device: %s", device_id)

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 401:
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.get(
                        url, headers=headers, timeout=timeout
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                else:
                    resp.raise_for_status()
                    return await resp.json()

        except ClientError as err:
            _LOGGER.warning("Error getting services for %s: %s", device_id, err)
            return []

    async def async_get_user_info(self) -> dict[str, Any]:
        """Get user information."""
        await self._ensure_token()
        url = f"{FERMAX_API_BASE}/user/api/v1/users/me"
        headers = {
            **MOBILE_HEADERS,
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        _LOGGER.debug("Getting user info")

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 401:
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.get(
                        url, headers=headers, timeout=timeout
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                else:
                    resp.raise_for_status()
                    return await resp.json()

        except ClientError as err:
            _LOGGER.error("Error getting user info: %s", err)
            raise FermaxConnectionError(f"Error getting user info: {err}") from err

    async def async_open_door(
        self, device_id: str, block: int, subblock: int, number: int
    ) -> str:
        """Open a door."""
        await self._ensure_token()
        url = (
            f"{FERMAX_API_BASE}/deviceaction/api/v1/device/"
            f"{device_id}/directed-opendoor?unitId={device_id}"
        )
        headers = {
            **MOBILE_HEADERS,
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        payload = {"block": block, "subblock": subblock, "number": number}

        _LOGGER.info(
            "Opening door for device %s (block=%s, subblock=%s, number=%s)",
            device_id,
            block,
            subblock,
            number,
        )

        try:
            timeout = ClientTimeout(
                total=TIMEOUT_TOTAL,
                connect=TIMEOUT_CONNECTION,
                sock_read=TIMEOUT_READ,
            )
            async with self._session.post(
                url, json=payload, headers=headers, timeout=timeout
            ) as resp:
                if resp.status == 401:
                    _LOGGER.warning("Got 401, refreshing token and retrying")
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.post(
                        url, json=payload, headers=headers, timeout=timeout
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        result = await retry_resp.text()
                        _LOGGER.info("Door opened successfully: %s", result)
                        return result
                else:
                    resp.raise_for_status()
                    result = await resp.text()
                    _LOGGER.info("Door opened successfully: %s", result)
                    return result

        except ClientError as err:
            _LOGGER.error("Error opening door for device %s: %s", device_id, err)
            raise FermaxAPIError(f"Error opening door: {err}") from err
