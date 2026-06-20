"""Binary sensor platform for MySpeed."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MySpeedConfigEntry, MySpeedData
from .entity import MySpeedEntity


@dataclass(frozen=True, kw_only=True)
class MySpeedBinaryDescription(BinarySensorEntityDescription):
    """Describes a MySpeed binary sensor."""

    value_fn: Callable[[MySpeedData], bool | None]


BINARY_SENSORS: tuple[MySpeedBinaryDescription, ...] = (
    MySpeedBinaryDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: bool(d.status.get("running")),
    ),
    MySpeedBinaryDescription(
        key="paused",
        translation_key="paused",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: bool(d.status.get("paused")),
    ),
    MySpeedBinaryDescription(
        key="last_test_failed",
        translation_key="last_test_failed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: bool((d.latest or {}).get("error")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MySpeedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MySpeed binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        MySpeedBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class MySpeedBinarySensor(MySpeedEntity, BinarySensorEntity):
    """A single MySpeed binary sensor."""

    entity_description: MySpeedBinaryDescription

    def __init__(self, coordinator, description: MySpeedBinaryDescription) -> None:
        """Initialize."""
        super().__init__(coordinator, description.key, ENTITY_ID_FORMAT)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the state."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the error text on the problem sensor."""
        if (
            self.entity_description.key == "last_test_failed"
            and self.coordinator.data
            and (latest := self.coordinator.data.latest)
        ):
            return {"error": latest.get("error")}
        return None
