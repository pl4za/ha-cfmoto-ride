"""Binary sensors for CFMOTO RIDE."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import CfmotoConfigEntry
from .entity import CfmotoEntity


async def async_setup_entry(hass: HomeAssistant, entry: CfmotoConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for vid in coordinator.vehicles:
        entities.append(CfmotoOnline(coordinator, vid, "online"))
        entities.append(CfmotoIgnition(coordinator, vid, "ignition"))
    async_add_entities(entities)


class CfmotoOnline(CfmotoEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        v = self.status.get("isOnline")
        return None if v is None else bool(v)


class CfmotoIgnition(CfmotoEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_icon = "mdi:key"

    @property
    def is_on(self) -> bool | None:
        v = self.status.get("kl")
        return None if v is None else str(v) == "1"
