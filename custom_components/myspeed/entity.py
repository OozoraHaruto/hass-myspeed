"""Base entity for MySpeed."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import MySpeedCoordinator


class MySpeedEntity(CoordinatorEntity[MySpeedCoordinator]):
    """Common base: ties every entity to the per-instance device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MySpeedCoordinator,
        key: str,
        entity_id_format: str | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        # Force a stable, brand-prefixed object_id that includes the instance
        # name (e.g. sensor.myspeed_living_room_download) instead of one derived
        # solely from the device title / host. The platform domain comes from
        # entity_id_format ("sensor.{}", "switch.{}", ...); the title is
        # slugified by async_generate_entity_id.
        if entity_id_format is not None:
            self.entity_id = async_generate_entity_id(
                entity_id_format,
                f"{DOMAIN}_{entry.title}_{key}",
                hass=coordinator.hass,
            )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=coordinator.client.base_url,
            sw_version=(coordinator.data.version or {}).get("local")
            if coordinator.data
            else None,
        )
