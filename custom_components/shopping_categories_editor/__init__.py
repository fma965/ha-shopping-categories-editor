"""Shopping Categories Editor: a sidebar panel that edits a categories JSON file."""
from __future__ import annotations

import json
import os
from pathlib import Path

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_FILE_PATH,
    DOMAIN,
    EVENT_SAVED,
    PANEL_URL_PATH,
    SIGNAL_UPDATED,
    STATIC_URL,
)


def _read(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _write(path: str, data: dict) -> None:
    """Write atomically, keeping one .bak of the previous version."""
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if p.exists():
        p.replace(p.with_suffix(p.suffix + ".bak"))
    os.replace(tmp, p)


def _path(hass: HomeAssistant) -> str | None:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None
    return hass.config.path(entries[0].data[CONF_FILE_PATH])


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get"})
@websocket_api.async_response
async def ws_get(hass, connection, msg):
    path = _path(hass)
    if path is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return
    try:
        data = await hass.async_add_executor_job(_read, path)
    except (OSError, ValueError) as err:
        connection.send_error(msg["id"], "read_failed", str(err))
        return
    connection.send_result(msg["id"], data)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/save", vol.Required("data"): dict}
)
@websocket_api.async_response
async def ws_save(hass, connection, msg):
    path = _path(hass)
    if path is None:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return
    try:
        await hass.async_add_executor_job(_write, path, msg["data"])
    except OSError as err:
        connection.send_error(msg["id"], "write_failed", str(err))
        return
    hass.bus.async_fire(EVENT_SAVED, {"path": path})
    async_dispatcher_send(hass, SIGNAL_UPDATED)
    connection.send_result(msg["id"])


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not hass.data.get(DOMAIN):
        websocket_api.async_register_command(hass, ws_get)
        websocket_api.async_register_command(hass, ws_save)
        hass.data[DOMAIN] = True
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "www"), False)]
    )
    frontend.async_register_built_in_panel(
        hass,
        "iframe",
        sidebar_title="Shopping editor",
        sidebar_icon="mdi:cart-edit",
        frontend_url_path=PANEL_URL_PATH,
        config={"url": f"{STATIC_URL}/editor.html"},
        require_admin=True,
        update=True,
    )
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
    return await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
