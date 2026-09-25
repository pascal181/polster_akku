from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    CONF_NOTIFY,
    CONF_THRESHOLD,
    DOMAIN,
    PLATFORMS,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .coordinator import AkkuCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    www = Path(__file__).parent / "www"
    if www.is_dir():
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/polster_akku", str(www), False)]
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load() or {}
    ignored = list(data.get("ignored", []))

    coordinator = AkkuCoordinator(hass, entry, ignored)
    await coordinator.async_config_entry_first_refresh()

    async def _persist() -> None:
        await store.async_save({"ignored": coordinator.ignored})

    async def svc_ignore(call: ServiceCall) -> None:
        eid = call.data["entity_id"]
        if eid not in coordinator.ignored:
            coordinator.ignored.append(eid)
            await _persist()
            await coordinator.async_request_refresh()

    async def svc_restore(call: ServiceCall) -> None:
        eid = call.data["entity_id"]
        coordinator.ignored = [x for x in coordinator.ignored if x != eid]
        await _persist()
        await coordinator.async_request_refresh()

    async def svc_restore_all(_call: ServiceCall) -> None:
        coordinator.ignored = []
        await _persist()
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "ignore",
        svc_ignore,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )
    hass.services.async_register(
        DOMAIN,
        "restore",
        svc_restore,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )
    hass.services.async_register(DOMAIN, "restore_all", svc_restore_all)

    async def _on_low(event) -> None:
        notify = entry.options.get(CONF_NOTIFY) or entry.data.get(CONF_NOTIFY) or ""
        if not notify or "." not in notify:
            return
        domain, service = notify.split(".", 1)
        name = event.data.get("name")
        level = event.data.get("level")
        await hass.services.async_call(
            domain,
            service,
            {
                "title": "Akku leer",
                "message": f"{name}: {level} %",
                "data": {"tag": f"polster_akku_{event.data.get('entity_id')}", "group": "akkus"},
            },
            blocking=False,
        )
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "notification_id": f"polster_akku_{event.data.get('entity_id')}",
                "title": f"Akku leer – {name}",
                "message": f"{name} hat nur noch {level} %.",
            },
            blocking=False,
        )

    unsub = hass.bus.async_listen("polster_akku_low", _on_low)
    entry.async_on_unload(unsub)

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.services.async_remove(DOMAIN, "ignore")
        hass.services.async_remove(DOMAIN, "restore")
        hass.services.async_remove(DOMAIN, "restore_all")
    return unload
