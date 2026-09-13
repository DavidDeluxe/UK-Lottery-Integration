import csv
import io
import logging
from datetime import datetime, timedelta
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

UK_CSV_ENDPOINTS = {
    "lotto": "https://www.national-lottery.co.uk/results/lotto/draw-history/csv",
    "euromillions": "https://www.national-lottery.co.uk/results/euromillions/draw-history/csv",
    "set_for_life": "https://www.national-lottery.co.uk/results/set-for-life/draw-history/csv",
    "thunderball": "https://www.national-lottery.co.uk/results/thunderball/draw-history/csv",
}

POWERBALL_ENDPOINT = "https://data.ny.gov/resource/d6yy-54nr.json?$limit=2&$order=draw_date%20DESC"

class UKLotteryCoordinator(DataUpdateCoordinator):
    """Coordinator fetching all 7 lottery games."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession):
        super().__init__(
            hass,
            _LOGGER,
            name="Lottery Coordinator",
            update_interval=timedelta(hours=3),
        )
        self.session = session

    async def _async_update_data(self):
        data = {}
        headers = {"User-Agent": "Mozilla/5.0"}

        # 1. Fetch UK National Lottery CSVs
        for game, url in UK_CSV_ENDPOINTS.items():
            try:
                async with self.session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        reader = list(csv.reader(io.StringIO(text)))
                        if len(reader) >= 3:
                            data[game] = {
                                "latest": self._parse_uk_row(game, reader[1]),
                                "previous": self._parse_uk_row(game, reader[2]),
                            }
            except Exception as err:
                _LOGGER.warning("Error fetching %s CSV: %s", game, err)

        # 2. Derive HotPicks from parent draws
        if "lotto" in data:
            data["lotto_hotpicks"] = {
                "latest": {"date": data["lotto"]["latest"]["date"], "balls": data["lotto"]["latest"]["balls"]},
                "previous": {"date": data["lotto"]["previous"]["date"], "balls": data["lotto"]["previous"]["balls"]},
            }

        if "euromillions" in data:
            data["euromillions_hotpicks"] = {
                "latest": {"date": data["euromillions"]["latest"]["date"], "balls": data["euromillions"]["latest"]["balls"]},
                "previous": {"date": data["euromillions"]["previous"]["date"], "balls": data["euromillions"]["previous"]["balls"]},
            }

        # 3. Fetch Powerball (US Open Data JSON)
        try:
            async with self.session.get(POWERBALL_ENDPOINT, timeout=10) as resp:
                if resp.status == 200:
                    pb_json = await resp.json()
                    if len(pb_json) >= 2:
                        data["powerball"] = {
                            "latest": self._parse_powerball_row(pb_json[0]),
                            "previous": self._parse_powerball_row(pb_json[1]),
                        }
        except Exception as err:
            _LOGGER.warning("Error fetching Powerball: %s", err)

        if not data:
            raise UpdateFailed("Failed to fetch lottery data.")
        return data

    def _parse_uk_row(self, game: str, row: list) -> dict:
        date = row[0]
        if game == "lotto":
            return {
                "date": date,
                "balls": [int(x) for x in row[1:7] if x.strip()],
                "bonus_ball": int(row[7]) if row[7].strip() else None,
            }
        elif game == "euromillions":
            return {
                "date": date,
                "balls": [int(x) for x in row[1:6] if x.strip()],
                "lucky_stars": [int(x) for x in row[6:8] if x.strip()],
            }
        elif game == "set_for_life":
            return {
                "date": date,
                "balls": [int(x) for x in row[1:6] if x.strip()],
                "life_ball": int(row[6]) if row[6].strip() else None,
            }
        elif game == "thunderball":
            return {
                "date": date,
                "balls": [int(x) for x in row[1:6] if x.strip()],
                "thunderball": int(row[6]) if row[6].strip() else None,
            }
        return {"date": date}

    def _parse_powerball_row(self, row: dict) -> dict:
        # winning_numbers: "05 14 19 46 64 22" (first 5 white balls, last is Powerball)
        nums = [int(x) for x in row.get("winning_numbers", "").split() if x]
        return {
            "date": row.get("draw_date", "").split("T")[0],
            "balls": nums[:5] if len(nums) >= 5 else [],
            "powerball": nums[5] if len(nums) >= 6 else None,
            "multiplier": row.get("multiplier"),
        }