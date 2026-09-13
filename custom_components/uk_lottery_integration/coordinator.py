import logging
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

UK_XML_ENDPOINTS = {
    "lotto": "https://www.national-lottery.co.uk/results/lotto/draw-history/xml",
    "euromillions": "https://www.national-lottery.co.uk/results/euromillions/draw-history/xml",
    "set_for_life": "https://www.national-lottery.co.uk/results/set-for-life/draw-history/xml",
    "thunderball": "https://www.national-lottery.co.uk/results/thunderball/draw-history/xml",
    "powerball": "https://www.national-lottery.co.uk/results/powerball/draw-history/xml",
}

POWERBALL_ENDPOINT = "https://data.ny.gov/resource/d6yy-54nr.json?$limit=2&$order=draw_date%20DESC"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

class UKLotteryCoordinator(DataUpdateCoordinator):
    """Coordinator fetching official lottery draw XML feeds."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession):
        super().__init__(
            hass,
            _LOGGER,
            name="Lottery Coordinator",
            update_interval=timedelta(hours=3),
        )
        self.session = session

    def _fetch_and_parse_uk_xml(self, url: str, game: str) -> dict:
        """Fetch and extract draw information from the official XML schema."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read()
            root = ET.fromstring(content)

            game_elem = root.find(f".//game[@type='{game}']") or root.find(".//game")
            if game_elem is None:
                _LOGGER.warning("No <game> tag found in XML for %s", game)
                return {}

            # 1. Date
            draw_date = ""
            date_elem = game_elem.find(".//draw/draw-date")
            if date_elem is not None and date_elem.text:
                draw_date = date_elem.text.strip()

            # 2. Main balls & Specials
            balls = []
            specials = []
            balls_elem = game_elem.find("balls")
            if balls_elem is not None:
                for b in balls_elem.findall("ball"):
                    if b.text and b.text.strip().isdigit():
                        balls.append(int(b.text.strip()))

                # Captures bonus-ball, powerball, or life-ball tags
                for bonus in balls_elem.findall("bonus-ball"):
                    if bonus.text and bonus.text.strip().isdigit():
                        specials.append(int(bonus.text.strip()))

            parsed = {
                "date": draw_date,
                "balls": sorted(balls),
            }

            if game == "lotto":
                parsed["bonus_ball"] = specials[0] if specials else None
            elif game == "euromillions":
                parsed["lucky_stars"] = specials
            elif game == "set_for_life":
                parsed["life_ball"] = specials[0] if specials else None
            elif game == "thunderball":
                parsed["thunderball"] = specials[0] if specials else None
            elif game == "powerball":
                parsed["powerball"] = specials[0] if specials else None

            next_date_elem = game_elem.find("next-draw-date")
            if next_date_elem is not None and next_date_elem.text:
                parsed["next_draw_feed"] = next_date_elem.text.strip()

            return parsed

    async def _async_update_data(self):
        data = {}

        # Fetch all XML feeds
        for game, url in UK_XML_ENDPOINTS.items():
            try:
                latest_draw = await self.hass.async_add_executor_job(
                    self._fetch_and_parse_uk_xml, url, game
                )
                if latest_draw and latest_draw.get("balls"):
                    data[game] = {
                        "latest": latest_draw,
                        "previous": {},
                    }
                    _LOGGER.info("Successfully parsed %s: %s", game, latest_draw)
                else:
                    _LOGGER.warning("Parsed empty draw for %s", game)
            except Exception as err:
                _LOGGER.error("Error parsing %s XML: %s", game, err)

        # HotPicks derived games
        if "lotto" in data and "latest" in data["lotto"]:
            data["lotto_hotpicks"] = {
                "latest": {
                    "date": data["lotto"]["latest"].get("date"),
                    "balls": data["lotto"]["latest"].get("balls", []),
                },
                "previous": {},
            }

        if "euromillions" in data and "latest" in data["euromillions"]:
            data["euromillions_hotpicks"] = {
                "latest": {
                    "date": data["euromillions"]["latest"].get("date"),
                    "balls": data["euromillions"]["latest"].get("balls", []),
                },
                "previous": {},
            }

        if not data:
            raise UpdateFailed("No lottery feeds could be retrieved.")

        return data