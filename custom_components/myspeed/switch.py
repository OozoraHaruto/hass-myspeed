"""Switch platform for MySpeed (pause/resume the scheduler)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MySpeedConnectionError
from .coordinator import MySpeedConfigEntry
from .entity import MySpeedEntity

PAUSE = SwitchEntityDescription(
    key="pause",
    translation_key="pause",
    device_class=SwitchDeviceClass.SWITCH,
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MySpeedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the pause switch."""
    async_add_entities([MySpeedPauseSwitch(entry.runtime_data)])


class MySpeedPauseSwitch(MySpeedEntity, SwitchEntity):
    """On = scheduler paused; Off = running."""

    entity_description = PAUSE

    def __init__(self, coordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, PAUSE.key, ENTITY_ID_FORMAT)

    @property
    def is_on(self) -> bool | None:
        """Return whether testing is paused."""
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.status.get("paused"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Pause speed tests indefinitely."""
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Resume speed tests."""
        await self._set(False)

    async def _set(self, paused: bool) -> None:
        try:
            await self.coordinator.client.async_set_pause(paused)
        except MySpeedConnectionError as err:
            raise HomeAssistantError(
                f"Could not change the MySpeed pause state: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
