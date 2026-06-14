"""Data update coordinator for MySpeed."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MySpeedAuthError,
    MySpeedClient,
    MySpeedConnectionError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MySpeedData:
    """Aggregated snapshot of one MySpeed instance."""

    latest: dict[str, Any] | None
    """Newest test of any kind (may contain an ``error``)."""

    latest_ok: dict[str, Any] | None
    """Newest test without an error; speed sensors read from this."""

    status: dict[str, Any]
    """``{"paused": bool, "running": bool}``."""

    version: dict[str, Any]
    """``{"local": str, "remote": str}``."""


type MySpeedConfigEntry = ConfigEntry[MySpeedCoordinator]


class MySpeedCoordinator(DataUpdateCoordinator[MySpeedData]):
    """Polls a single MySpeed instance and exposes a normalized snapshot."""

    config_entry: MySpeedConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MySpeedConfigEntry,
        client: MySpeedClient,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({client.host})",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> MySpeedData:
        """Fetch tests, status and version concurrently."""
        try:
            tests, status, version = await asyncio.gather(
                self.client.async_get_tests(limit=10),
                self.client.async_get_status(),
                self.client.async_get_version(),
            )
        except MySpeedAuthError as err:
            # Triggers HA's reauth flow.
            raise ConfigEntryAuthFailed(str(err)) from err
        except MySpeedConnectionError as err:
            raise UpdateFailed(str(err)) from err

        latest = tests[0] if tests else None
        latest_ok = next((t for t in tests if not t.get("error")), None)

        return MySpeedData(
            latest=latest,
            latest_ok=latest_ok,
            status=status,
            version=version,
        )
