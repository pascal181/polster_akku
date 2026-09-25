from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_GERAETE, ATTR_IGNORIERT, ATTR_LISTE, DOMAIN
from .coordinator import AkkuCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AkkuCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AkkuCountSensor(coordinator, "kritisch", "Akkus kritisch", "critical", "mdi:battery-alert"),
            AkkuCountSensor(coordinator, "gesamt", "Akkus gesamt", "count", "mdi:battery-heart"),
        ]
    )


class AkkuCountSensor(CoordinatorEntity[AkkuCoordinator], SensorEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator: AkkuCoordinator, key: str, name: str, data_key: str, icon: str) -> None:
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"polster_akku_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = "Geräte"

    @property
    def native_value(self):
        if not self.coordinator.data:
            return 0
        return self.coordinator.data.get(self._data_key, 0)

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        low = data.get("low", [])
        items = data.get("items", [])
        return {
            ATTR_LISTE: ", ".join(f"{i['name']} ({i['level']}%)" for i in low),
            ATTR_GERAETE: items,
            ATTR_IGNORIERT: data.get("ignored", []),
            "threshold": data.get("threshold"),
        }
