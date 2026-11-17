"""GPS location of the bike, as last reported by the T-Box."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import CfmotoEntity
from .hub import CfmotoConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: CfmotoConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(CfmotoTracker(coordinator, vid, "location") for vid in coordinator.vehicles)


def _f(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class CfmotoTracker(CfmotoEntity, TrackerEntity):
    _attr_icon = "mdi:motorbike"

    @property
    def _geo(self) -> dict:
        return self.status.get("geoLocation") or {}

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        return _f(self._geo.get("latitude"))

    @property
    def longitude(self) -> float | None:
        return _f(self._geo.get("longitude"))

    @property
    def location_accuracy(self) -> float:
        return 10

    @property
    def extra_state_attributes(self) -> dict:
        geo = self._geo
        ts = _f((geo.get("report") or {}).get("datetime"))
        return {
            "altitude": geo.get("altitude"),
            "reported_at": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat() if ts else None,
            "coordinate_system": geo.get("coordinateSystem"),
        }
