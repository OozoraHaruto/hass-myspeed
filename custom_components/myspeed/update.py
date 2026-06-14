"""Update platform for MySpeed (installed vs latest release)."""

from __future__ import annotations

from homeassistant.components.update import UpdateEntity, UpdateEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MySpeedConfigEntry
from .entity import MySpeedEntity

VERSION = UpdateEntityDescription(key="version", translation_key="version")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MySpeedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the update entity."""
    async_add_entities([MySpeedUpdate(entry.runtime_data)])


class MySpeedUpdate(MySpeedEntity, UpdateEntity):
    """Reports whether a newer MySpeed release is available.

    This is informational only — MySpeed has no in-app upgrade API, so no
    install feature is advertised.
    """

    entity_description = VERSION
    _attr_release_url = "https://github.com/gnmyt/MySpeed/releases"

    def __init__(self, coordinator) -> None:
        """Initialize."""
        super().__init__(coordinator, VERSION.key)

    @property
    def installed_version(self) -> str | None:
        """Return the running version."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.version.get("local")

    @property
    def latest_version(self) -> str | None:
        """Return the latest release (falls back to installed if unknown)."""
        if self.coordinator.data is None:
            return None
        remote = self.coordinator.data.version.get("remote")
        if not remote or remote == "0":
            return self.installed_version
        return remote
