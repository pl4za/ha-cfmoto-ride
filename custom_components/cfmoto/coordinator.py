"""Polling coordinator for CFMOTO RIDE."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CfmotoApi, CfmotoAuthError, CfmotoError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class CfmotoCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Fetches live status for every bike on the account."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: CfmotoApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN,
                         update_interval=SCAN_INTERVAL)
        self.api = api
        self.vehicles: dict[str, dict] = {}

    async def _async_setup(self) -> None:
        try:
            self.vehicles = {str(v["vehicleId"]): v for v in await self.api.vehicles()}
        except CfmotoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except CfmotoError as err:
            raise UpdateFailed(str(err)) from err

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            return {vid: await self.api.status(vid) for vid in self.vehicles}
        except CfmotoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except CfmotoError as err:
            raise UpdateFailed(str(err)) from err
