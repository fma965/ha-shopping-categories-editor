"""Config flow for Shopping Categories Editor."""
from __future__ import annotations

import json
import os
from pathlib import Path

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_FILE_PATH, DEFAULT_FILE_PATH, DOMAIN


def _check_file(path: str) -> str | None:
    """Return an error key if an existing file is not a JSON object."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "invalid_json"
    return None if isinstance(data, dict) else "invalid_json"


class ShoppingCategoriesEditorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-step flow that asks for the JSON file path."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            full = self.hass.config.path(user_input[CONF_FILE_PATH])
            in_config = Path(os.path.realpath(full)).is_relative_to(
                os.path.realpath(self.hass.config.config_dir)
            )
            if not in_config and not self.hass.config.is_allowed_path(full):
                errors["base"] = "path_not_allowed"
            elif err := await self.hass.async_add_executor_job(_check_file, full):
                errors["base"] = err
            else:
                return self.async_create_entry(
                    title="Shopping Categories Editor", data=user_input
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_FILE_PATH, default=DEFAULT_FILE_PATH): str}
            ),
            errors=errors,
        )
