"""Config flow for MySpeed."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MySpeedAuthError, MySpeedClient, MySpeedConnectionError
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .coordinator import MySpeedConfigEntry


def _user_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=defaults.get(CONF_URL, "")): str,
            vol.Optional(
                CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")
            ): str,
            vol.Optional(
                CONF_VERIFY_SSL, default=defaults.get(CONF_VERIFY_SSL, True)
            ): bool,
        }
    )


async def _validate(
    hass, url: str, password: str | None, verify_ssl: bool
) -> tuple[dict[str, str], MySpeedClient | None]:
    """Return (errors, client). errors is empty on success."""
    errors: dict[str, str] = {}
    session = async_get_clientsession(hass)
    client = MySpeedClient(session, url, password or None, verify_ssl)
    try:
        await client.async_validate()
    except MySpeedAuthError:
        errors["base"] = "invalid_auth"
    except MySpeedConnectionError:
        errors["base"] = "cannot_connect"
    except Exception:  # noqa: BLE001 - surface unexpected failures gracefully
        errors["base"] = "unknown"
    return errors, (client if not errors else None)


class MySpeedConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the MySpeed config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: MySpeedConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a user-initiated setup of a new instance."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = _normalize_url(user_input[CONF_URL])
            errors, client = await _validate(
                self.hass,
                url,
                user_input.get(CONF_PASSWORD),
                user_input.get(CONF_VERIFY_SSL, True),
            )
            if not errors and client is not None:
                # One entry per host; prevents accidental duplicates.
                await self.async_set_unique_id(client.host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=client.host,
                    data={
                        CONF_URL: url,
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD) or "",
                        CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, True),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication (e.g. password changed on the instance)."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm new credentials for an existing entry."""
        assert self._reauth_entry is not None
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, _ = await _validate(
                self.hass,
                self._reauth_entry.data[CONF_URL],
                user_input.get(CONF_PASSWORD),
                self._reauth_entry.data.get(CONF_VERIFY_SSL, True),
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD) or "",
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Optional(CONF_PASSWORD, default=""): str}
            ),
            errors=errors,
            description_placeholders={
                "url": self._reauth_entry.data[CONF_URL]
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: MySpeedConfigEntry,
    ) -> MySpeedOptionsFlow:
        """Return the options flow."""
        return MySpeedOptionsFlow()


class MySpeedOptionsFlow(OptionsFlow):
    """Allow tuning the poll interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=current
                    ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
                }
            ),
        )


def _normalize_url(raw: str) -> str:
    """Add a scheme and the default port if the user omitted them."""
    raw = raw.strip()
    if "://" not in raw:
        raw = f"http://{raw}"
    parsed = urlparse(raw)
    netloc = parsed.netloc
    if parsed.port is None:
        netloc = f"{netloc}:5216"
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{netloc}{path}"
