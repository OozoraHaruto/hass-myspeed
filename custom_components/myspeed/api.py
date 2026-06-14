"""Async API client for a single MySpeed instance."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from yarl import URL

from .const import DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class MySpeedError(Exception):
    """Base error for the MySpeed client."""


class MySpeedConnectionError(MySpeedError):
    """Raised when the instance cannot be reached."""


class MySpeedAuthError(MySpeedError):
    """Raised when the instance rejects the supplied password."""


class MySpeedClient:
    """Thin wrapper around the MySpeed REST API.

    Auth model (confirmed from server/middlewares/password.js):
    the plaintext password is sent in the ``password`` request header and the
    server compares it against a stored bcrypt hash. If the instance has no
    password configured, no header is required.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        password: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the client.

        ``url`` is the base address of the instance, e.g.
        ``http://192.168.1.50:5216``. A trailing slash is tolerated.
        """
        self._session = session
        self._base = URL(url.rstrip("/"))
        self._password = password or None
        self._verify_ssl = verify_ssl

    @property
    def base_url(self) -> str:
        """Return the normalized base URL."""
        return str(self._base)

    @property
    def host(self) -> str:
        """Return host[:port] used to build a stable unique id."""
        host = self._base.host or str(self._base)
        if self._base.port and self._base.port not in (80, 443):
            return f"{host}:{self._base.port}"
        return host

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._password:
            # The server reads the raw password from this header.
            headers["password"] = self._password
        return headers

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> Any:
        """Perform a request and return decoded JSON (or None for empty body)."""
        # Concatenate (don't URL.join) so a reverse-proxy subpath in the base
        # URL, e.g. https://host/myspeed, is preserved.
        target = URL(f"{self._base}{path}")
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                resp = await self._session.request(
                    method,
                    target,
                    headers=self._headers(),
                    ssl=self._verify_ssl,
                    **kwargs,
                )
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise MySpeedConnectionError(
                f"Error communicating with MySpeed at {target}: {err}"
            ) from err

        if resp.status == 401:
            raise MySpeedAuthError(
                "MySpeed rejected the request: a password is required or it is incorrect"
            )

        if resp.status >= 400:
            text = await resp.text()
            raise MySpeedConnectionError(
                f"Unexpected status {resp.status} from {target}: {text[:200]}"
            )

        # Some endpoints (e.g. a misconfigured reverse proxy) return HTML.
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await resp.text()
            raise MySpeedConnectionError(
                f"Expected JSON from {target} but received '{content_type}'. "
                "Check that the URL points directly at the MySpeed API."
            )

        if resp.status == 204:
            return None
        return await resp.json()

    async def async_validate(self) -> None:
        """Validate connectivity and credentials. Raises on failure."""
        # /status is cheap and (when a password is set) requires it.
        await self.async_get_status()
        # Confirm the password is accepted for password(false) routes too.
        await self.async_get_version()

    async def async_get_tests(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the most recent speed-test results (newest first)."""
        data = await self._request("GET", f"/api/speedtests?limit={limit}")
        return data if isinstance(data, list) else []

    async def async_get_status(self) -> dict[str, Any]:
        """Return ``{"paused": bool, "running": bool}``."""
        data = await self._request("GET", "/api/speedtests/status")
        return data if isinstance(data, dict) else {}

    async def async_get_version(self) -> dict[str, Any]:
        """Return ``{"local": str, "remote": str}`` (remote "0" if unknown)."""
        data = await self._request("GET", "/api/info/version")
        return data if isinstance(data, dict) else {}

    async def async_run_test(self) -> None:
        """Trigger a custom speed test."""
        await self._request("POST", "/api/speedtests/run")

    async def async_set_pause(self, paused: bool) -> None:
        """Pause indefinitely (resumeIn=-1) or resume the scheduler."""
        if paused:
            await self._request(
                "POST", "/api/speedtests/pause", json={"resumeIn": -1}
            )
        else:
            await self._request("POST", "/api/speedtests/continue")
