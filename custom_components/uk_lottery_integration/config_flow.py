import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import DOMAIN, GAMES

GAME_LABELS = {
    "lotto": "Lotto",
    "euromillions": "EuroMillions",
    "set_for_life": "Set For Life",
    "thunderball": "Thunderball",
    "lotto_hotpicks": "Lotto HotPicks",
    "euromillions_hotpicks": "EuroMillions HotPicks",
    "powerball": "Powerball",
}

class UKLotteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        # Filter out games already configured
        configured_games = {
            entry.data.get("game") for entry in self._async_current_entries()
        }
        available_games = [g for g in GAMES if g not in configured_games]

        if not available_games:
            return self.async_abort(reason="all_games_configured")

        if user_input is not None:
            game = user_input["game"]
            await self.async_set_unique_id(f"{DOMAIN}_{game}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=GAME_LABELS.get(game, game),
                data={"game": game},
                options={"lines": user_input.get("lines", "")},
            )

        schema = vol.Schema({
            vol.Required("game"): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": g, "label": GAME_LABELS.get(g, g)} for g in available_games],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional("lines", default=""): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return UKLotteryOptionsFlowHandler()


class UKLotteryOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_lines = self.config_entry.options.get("lines", "")
        schema = vol.Schema({
            vol.Optional("lines", default=current_lines): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)