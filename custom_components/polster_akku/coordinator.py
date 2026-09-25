from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_THRESHOLD, DEFAULT_THRESHOLD, DOMAIN, SKIP_SUFFIXES


class AkkuCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, ignored: list[str]) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(minutes=2),
        )
        self.entry = entry
        self.ignored: list[str] = ignored
        self._seen_low: set[str] = set()

    @property
    def threshold(self) -> int:
        return int(self.entry.options.get(CONF_THRESHOLD, self.entry.data.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)))

    def _is_battery(self, state) -> bool:
        if not state.entity_id.startswith("sensor."):
            return False
        if state.attributes.get("device_class") != "battery":
            return False
        eid = state.entity_id
        return not any(eid.endswith(sfx) for sfx in SKIP_SUFFIXES)

    async def _async_update_data(self) -> dict:
        items = []
        for state in self.hass.states.async_all("sensor"):
            if not self._is_battery(state):
                continue
            if state.entity_id in self.ignored:
                continue
            try:
                level = float(state.state)
            except (TypeError, ValueError):
                continue
            if level < 0 or level > 100:
                continue
            name = state.attributes.get("friendly_name") or state.entity_id
            for junk in (" Battery", " battery", " Batterie", " Level", " level"):
                if name.endswith(junk):
                    name = name[: -len(junk)]
            items.append(
                {
                    "entity_id": state.entity_id,
                    "name": name.strip(),
                    "level": round(level),
                }
            )
        items.sort(key=lambda x: (x["level"], x["name"].lower()))
        low = [i for i in items if i["level"] <= self.threshold]

        now_low = {i["entity_id"] for i in low}
        newly = now_low - self._seen_low
        recovered = self._seen_low - now_low
        for eid in newly:
            row = next(i for i in low if i["entity_id"] == eid)
            self.hass.bus.async_fire(
                "polster_akku_low",
                {"entity_id": eid, "name": row["name"], "level": row["level"]},
            )
        for eid in recovered:
            self.hass.bus.async_fire("polster_akku_ok", {"entity_id": eid})
        self._seen_low = now_low

        return {
            "items": items,
            "low": low,
            "count": len(items),
            "critical": len(low),
            "ignored": list(self.ignored),
            "threshold": self.threshold,
        }
