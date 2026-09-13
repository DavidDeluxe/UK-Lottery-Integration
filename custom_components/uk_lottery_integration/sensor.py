from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .checker import calculate_next_draw, evaluate_line, parse_user_lines
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    game = entry.data["game"]
    async_add_entities([LotteryGameSensor(coordinator, game, entry)])


class LotteryGameSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, game: str, entry: ConfigEntry):
        super().__init__(coordinator)
        self._game = game
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{game}"
        self._attr_name = game.replace("_", " ").title()
        self._attr_icon = "mdi:ticket-percent-outline"

        # Explicit Home Assistant Device Registration
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, game)},
            name=f"{self._attr_name} Tracker",
            manufacturer="National Lottery" if game != "powerball" else "Multi-State Lottery",
            model=self._attr_name,
        )

    @property
    def native_value(self):
        if not self.coordinator.data:
            return "Awaiting Data"
        game_data = self.coordinator.data.get(self._game, {})
        latest = game_data.get("latest", {})
        return latest.get("date", "Awaiting Data")

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}

        game_data = self.coordinator.data.get(self._game, {})
        latest = game_data.get("latest", {})
        previous = game_data.get("previous", {})

        raw_lines = self._entry.options.get("lines", "")
        user_lines = parse_user_lines(raw_lines, max_lines=10)

        evaluated_latest = [evaluate_line(self._game, l, latest) for l in user_lines]
        evaluated_previous = [evaluate_line(self._game, l, previous) for l in user_lines]

        return {
            "latest": latest,
            "previous": previous,
            "has_win": any(l.get("win", False) for l in evaluated_latest),
            "checked_lines_latest": evaluated_latest,
            "checked_lines_previous": evaluated_previous,
            "next_draw": calculate_next_draw(self._game),
        }