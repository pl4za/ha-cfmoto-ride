"""Sensors for CFMOTO RIDE."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfElectricPotential, UnitOfLength, UnitOfSpeed, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import CfmotoConfigEntry
from .entity import CfmotoEntity


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _km_from_m(v: Any) -> float | None:
    n = _num(v)
    return round(n / 1000, 1) if n is not None else None


def _fuel_pct(s: dict) -> float | None:
    bars, total = _num(s.get("remainingOil")), _num(s.get("totalOilNum"))
    return round(bars / total * 100) if bars is not None and total else None


def _ts(v: Any) -> datetime | None:
    n = _num(v)
    return datetime.fromtimestamp(n / 1000, tz=timezone.utc) if n else None


@dataclass(frozen=True, kw_only=True)
class CfmotoSensorDescription(SensorEntityDescription):
    value: Callable[[dict], Any]
    attrs: Callable[[dict], dict] | None = None


SENSORS: tuple[CfmotoSensorDescription, ...] = (
    CfmotoSensorDescription(
        key="range", icon="mdi:gas-station",
        device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS, suggested_display_precision=0,
        value=lambda s: _num(s.get("hmiRidableMile")),
    ),
    CfmotoSensorDescription(
        key="fuel_level", icon="mdi:fuel", native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, value=_fuel_pct,
        attrs=lambda s: {"bars": s.get("remainingOil"), "total_bars": s.get("totalOilNum"),
                         "status": s.get("remainingOilDisplay")},
    ),
    CfmotoSensorDescription(
        key="odometer", icon="mdi:counter",
        device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.KILOMETERS, suggested_display_precision=0,
        value=lambda s: _km_from_m(s.get("totalRideMile")),
    ),
    CfmotoSensorDescription(
        key="distance_this_month", icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfLength.KILOMETERS, suggested_display_precision=1,
        value=lambda s: _km_from_m(s.get("rideMileageMonth")),
    ),
    CfmotoSensorDescription(
        key="speed", device_class=SensorDeviceClass.SPEED, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, suggested_display_precision=0,
        value=lambda s: _num(s.get("speed")),
    ),
    CfmotoSensorDescription(
        key="average_speed", icon="mdi:speedometer-medium", device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, suggested_display_precision=1,
        value=lambda s: _num(s.get("avgRideSpeed")),
    ),
    CfmotoSensorDescription(
        key="fuel_consumption", icon="mdi:gas-station-outline", native_unit_of_measurement="L/100 km",
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
        value=lambda s: _num(s.get("powerUseAvg")),
    ),
    CfmotoSensorDescription(
        key="riding_time_this_month", icon="mdi:timer-outline", device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL, native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS, suggested_display_precision=1,
        value=lambda s: _num(s.get("ridingTimeMonth")),
    ),
    CfmotoSensorDescription(
        key="battery_voltage", device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, suggested_display_precision=1,
        value=lambda s: _num(s.get("fireVoltage")),
    ),
    CfmotoSensorDescription(
        key="last_update", device_class=SensorDeviceClass.TIMESTAMP,
        value=lambda s: _ts(s.get("dataLastUpdateTime")),
    ),
    CfmotoSensorDescription(
        key="sim_remaining", icon="mdi:sim", entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.DAYS, device_class=SensorDeviceClass.DURATION,
        value=lambda s: _num(s.get("simRemainingDays")),
    ),
    CfmotoSensorDescription(
        key="signal", icon="mdi:signal", entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda s: s.get("gsmRxLevStr"),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: CfmotoConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        CfmotoSensor(coordinator, vid, desc) for vid in coordinator.vehicles for desc in SENSORS
    )


class CfmotoSensor(CfmotoEntity, SensorEntity):
    entity_description: CfmotoSensorDescription

    def __init__(self, coordinator, vehicle_id: str, description: CfmotoSensorDescription) -> None:
        super().__init__(coordinator, vehicle_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.status)

    @property
    def extra_state_attributes(self) -> dict | None:
        fn = self.entity_description.attrs
        return fn(self.status) if fn else None
