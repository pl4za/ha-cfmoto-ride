"""Base entity for CFMOTO RIDE."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CfmotoCoordinator


class CfmotoEntity(CoordinatorEntity[CfmotoCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: CfmotoCoordinator, vehicle_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.vehicle_id = vehicle_id
        meta = coordinator.vehicles.get(vehicle_id, {})
        self._attr_unique_id = f"{vehicle_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vehicle_id)},
            name=meta.get("vehicleName") or "CFMOTO",
            manufacturer="CFMOTO",
            model=meta.get("vehicleType"),
        )

    @property
    def status(self) -> dict:
        return (self.coordinator.data or {}).get(self.vehicle_id, {})
