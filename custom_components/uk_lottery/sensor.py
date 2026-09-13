from datetime import datetime, timedelta
import zoneinfo
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .checker import parse_user_lines, evaluate_line

class LotteryGameSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, game: str, entry: ConfigEntry):
        super().__init__(coordinator)
        self._game = game
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{game}"
        self._attr_name = game.replace("_", " ").title()

    @property
    def extra_state_attributes(self):
        game_data = self.coordinator.data.get(self._game, {})
        latest = game_data.get("latest", {})
        previous = game_data.get("previous", {})

        # Load user lines from options flow
        raw_lines = self._entry.options.get(f"lines_{self._game}", "")
        user_lines = parse_user_lines(raw_lines, max_lines=10)

        evaluated_latest = [evaluate_line(self._game, l, latest) for l in user_lines]
        evaluated_previous = [evaluate_line(self._game, l, previous) for l in user_lines]

        has_win = any(l["win"] for l in evaluated_latest)

        return {
            "latest": latest,
            "previous": previous,
            "has_win": has_win,
            "checked_lines_latest": evaluated_latest,
            "checked_lines_previous": evaluated_previous,
        }

GAMES = [
    "lotto",
    "euromillions",
    "powerball",
    "set_for_life",
    "thunderball",
    "lotto_hotpicks",
    "euromillions_hotpicks",
]

# Draw schedules: (Day of week: 0=Mon, 1=Tue... 6=Sun, Hour, Minute, Timezone)
SCHEDULES = {
    "lotto": [(2, 20, 0, "Europe/London"), (5, 19, 45, "Europe/London")],
    "lotto_hotpicks": [(2, 20, 0, "Europe/London"), (5, 19, 45, "Europe/London")],
    "euromillions": [(1, 20, 45, "Europe/London"), (4, 20, 45, "Europe/London")],
    "euromillions_hotpicks": [(1, 20, 45, "Europe/London"), (4, 20, 45, "Europe/London")],
    "set_for_life": [(0, 20, 0, "Europe/London"), (3, 20, 0, "Europe/London")],
    "thunderball": [(1, 20, 0, "Europe/London"), (2, 20, 0, "Europe/London"), (4, 20, 0, "Europe/London"), (5, 19, 0, "Europe/London")],
    "powerball": [(0, 22, 59, "America/New_York"), (2, 22, 59, "America/New_York"), (5, 22, 59, "America/New_York")],
}

def calculate_next_draw(game: str) -> str:
    sched = SCHEDULES.get(game)
    if not sched:
        return None

    tz_str = sched[0][3]
    tz = zoneinfo.ZoneInfo(tz_str)
    now_local = datetime.now(tz)
    candidates = []

    for dow, hour, minute, _ in sched:
        days_ahead = (dow - now_local.weekday()) % 7
        target = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        if target <= now_local:
            target += timedelta(days=7)
        candidates.append(target)

    return min(candidates).isoformat()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data["uk_lottery"][entry.entry_id]
    entities = [LotteryGameSensor(coordinator, game, entry.entry_id) for game in GAMES]
    async_add_entities(entities)

class LotteryGameSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, game: str, entry_id: str):
        super().__init__(coordinator)
        self._game = game
        self._attr_unique_id = f"{entry_id}_{game}"
        self._attr_name = game.replace("_", " ").title()
        self._attr_icon = "mdi:ticket-percent-outline"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._game, {}).get("latest", {}).get("date")

    @property
    def extra_state_attributes(self):
        game_data = self.coordinator.data.get(self._game, {})
        return {
            "latest": game_data.get("latest", {}),
            "previous": game_data.get("previous", {}),
            "next_draw": calculate_next_draw(self._game),
        }