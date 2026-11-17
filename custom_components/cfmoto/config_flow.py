"""Config flow for CFMOTO RIDE."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CfmotoApi, CfmotoAuthError, CfmotoError
from .const import CONF_AREA, CONF_BASE_URL, DEFAULT_AREA, DEFAULT_BASE_URL, DOMAIN


class CfmotoConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, data: dict[str, Any]) -> tuple[str | None, int]:
        api = CfmotoApi(async_get_clientsession(self.hass), data[CONF_EMAIL], data[CONF_PASSWORD],
                        data[CONF_AREA], data[CONF_BASE_URL], self.hass.config.time_zone)
        try:
            await api.login()
            return None, len(await api.vehicles())
        except CfmotoAuthError:
            return "invalid_auth", 0
        except CfmotoError:
            return "cannot_connect", 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].strip().lower())
            self._abort_if_unique_id_configured()
            error, count = await self._validate(user_input)
            if error:
                errors["base"] = error
            elif count == 0:
                errors["base"] = "no_vehicles"
            else:
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_AREA, default=DEFAULT_AREA): str,
            vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            data = {**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            error, _ = await self._validate(data)
            if not error:
                return self.async_update_reload_and_abort(entry, data=data)
            errors["base"] = error
        return self.async_show_form(step_id="reauth_confirm", errors=errors,
                                    data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}))
