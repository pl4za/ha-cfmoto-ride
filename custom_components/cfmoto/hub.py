"""Entry setup for CFMOTO RIDE (kept out of __init__.py so updates never need to touch it)."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CfmotoApi
from .const import CONF_AREA, CONF_BASE_URL, DEFAULT_AREA, DEFAULT_BASE_URL
from .coordinator import CfmotoCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]

type CfmotoConfigEntry = ConfigEntry[CfmotoCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CfmotoConfigEntry) -> bool:
    api = CfmotoApi(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_AREA, DEFAULT_AREA),
        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        hass.config.time_zone,
    )
    coordinator = CfmotoCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CfmotoConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
