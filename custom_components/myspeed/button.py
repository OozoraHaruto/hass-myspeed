"""Button platform for MySpeed."""

from __future__ import annotations

from homeassistant.components.button import (
    ENTITY_ID_FORMAT,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MySpeedConnectionError
from .coordinator import MySpeedConfigEntry
from .entity import MySpeedEntity

RUN_TEST = ButtonEntityDescription(key="run_test", translation_key="run_test")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MySpeedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the run-test button."""
    async_add_entities([MySpeedRunButton(entry.runtime_data)])


class MySpeedRunButton(MySpeedEntity, ButtonEntity):
    """Triggers a custom speed test."""

    entity_description = RUN_TEST

    def __init__(self, coordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, RUN_TEST.key, ENTITY_ID_FORMAT)

    async def async_press(self) -> None:
        """Run a speed test, then refresh shortly after."""
        try:
            await self.coordinator.client.async_run_test()
        except MySpeedConnectionError as err:
            raise HomeAssistantError(
                f"Could not start a MySpeed test: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
