import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, GAMES

class UKLotteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="UK & World Lotteries", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return UKLotteryOptionsFlowHandler(config_entry)


class UKLotteryOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = {}

        # Creates a text box for each game (up to 10 lines, formatted: "1, 2, 3, 4, 5 + 6, 7")
        for game in GAMES:
            schema[vol.Optional(f"lines_{game}", default=options.get(f"lines_{game}", ""))] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            description_placeholders={"note": "Enter up to 10 lines per game (one per line). Format: 1, 2, 3, 4, 5 + 6"}
        )