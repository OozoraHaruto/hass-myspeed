"""Sensor platform for MySpeed."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfDataRate,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import MySpeedConfigEntry, MySpeedData
from .entity import MySpeedEntity


@dataclass(frozen=True, kw_only=True)
class MySpeedSensorDescription(SensorEntityDescription):
    """Describes a MySpeed sensor."""

    value_fn: Callable[[MySpeedData], Any]


def _ok(data: MySpeedData) -> dict[str, Any]:
    return data.latest_ok or {}


def _latest(data: MySpeedData) -> dict[str, Any]:
    return data.latest or {}


def _parse_created(data: MySpeedData) -> datetime | None:
    created = _latest(data).get("created")
    if not created:
        return None
    parsed = dt_util.parse_datetime(created)
    if parsed is None:
        return None
    # MySpeed stores UTC ISO strings; assume UTC if naive.
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt_util.UTC)


SENSORS: tuple[MySpeedSensorDescription, ...] = (
    MySpeedSensorDescription(
        key="download",
        translation_key="download",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: _ok(d).get("download"),
    ),
    MySpeedSensorDescription(
        key="upload",
        translation_key="upload",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: _ok(d).get("upload"),
    ),
    MySpeedSensorDescription(
        key="ping",
        translation_key="ping",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _ok(d).get("ping"),
    ),
    MySpeedSensorDescription(
        key="jitter",
        translation_key="jitter",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: _ok(d).get("jitter"),
    ),
    MySpeedSensorDescription(
        key="test_duration",
        translation_key="test_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _latest(d).get("time"),
    ),
    MySpeedSensorDescription(
        key="last_test",
        translation_key="last_test",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_parse_created,
    ),
    MySpeedSensorDescription(
        key="server_name",
        translation_key="server_name",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _latest(d).get("serverName"),
    ),
    MySpeedSensorDescription(
        key="test_type",
        translation_key="test_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=["auto", "custom"],
        value_fn=lambda d: _latest(d).get("type"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MySpeedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MySpeed sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        MySpeedSensor(coordinator, description) for description in SENSORS
    )


class MySpeedSensor(MySpeedEntity, SensorEntity):
    """A single MySpeed sensor."""

    entity_description: MySpeedSensorDescription

    def __init__(self, coordinator, description: MySpeedSensorDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
