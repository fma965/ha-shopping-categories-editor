"""Catalog sensor: exposes the whole categories JSON as attributes for ha-shopping-list-card."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import _read
from .const import CONF_FILE_PATH, SIGNAL_UPDATED

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)  # also picks up edits made outside the editor


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([CatalogSensor(hass.config.path(entry.data[CONF_FILE_PATH]), entry.entry_id)], True)


class CatalogSensor(SensorEntity):
    """State is the item count; every category is an attribute (category -> list of items)."""

    _attr_name = "Shopping list items"  # -> sensor.shopping_list_items
    _attr_should_poll = True
    # Attributes are large; keep them out of the recorder database.
    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, path: str, entry_id: str) -> None:
        self._path = path
        self._attr_unique_id = f"{entry_id}_catalog"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        @callback
        def _refresh() -> None:
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATED, _refresh))

    async def async_update(self) -> None:
        try:
            data = await self.hass.async_add_executor_job(_read, self._path)
        except (OSError, ValueError) as err:
            _LOGGER.warning("Could not read %s: %s", self._path, err)
            return  # keep the last good data
        self._attr_native_value = sum(len(v) for v in data.values() if isinstance(v, list))
        self._attr_extra_state_attributes = data
