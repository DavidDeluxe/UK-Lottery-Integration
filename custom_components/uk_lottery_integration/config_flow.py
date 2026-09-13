import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN, GAMES, GAME_RULES

GAME_LABELS = {
    "euromillions": "EuroMillions",
    "euromillions_hotpicks": "EuroMillions HotPicks",
    "lotto": "Lotto",
    "lotto_hotpicks": "Lotto HotPicks",
    "powerball": "Powerball",
    "set_for_life": "Set For Life",
    "thunderball": "Thunderball", 
}

def build_line_schema(game: str, existing_values: dict = None) -> vol.Schema:
    """Build schema containing separate fields for each ball."""
    rules = GAME_RULES.get(game, GAME_RULES["lotto"])
    existing = existing_values or {}
    schema_dict = {}

    # Main ball fields
    for i in range(1, rules["main_count"] + 1):
        field_key = f"ball_{i}"
        schema_dict[vol.Optional(field_key, default=existing.get(field_key))] = NumberSelector(
            NumberSelectorConfig(
                min=1,
                max=rules["main_max"],
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        )

    # Special / Bonus ball fields (Lucky Stars, Life Ball, Thunderball, etc.)
    for s in range(1, rules["special_count"] + 1):
        field_key = f"special_{s}"
        schema_dict[vol.Optional(field_key, default=existing.get(field_key))] = NumberSelector(
            NumberSelectorConfig(
                min=1,
                max=rules["special_max"],
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        )

    return vol.Schema(schema_dict)


def validate_and_serialize_line(game: str, user_input: dict) -> tuple[str, dict]:
    """Validate uniqueness and format numbers into storage string."""
    rules = GAME_RULES.get(game, GAME_RULES["lotto"])
    errors = {}

    main_balls = []
    for i in range(1, rules["main_count"] + 1):
        val = user_input.get(f"ball_{i}")
        if val is not None:
            main_balls.append(int(val))

    special_balls = []
    for s in range(1, rules["special_count"] + 1):
        val = user_input.get(f"special_{s}")
        if val is not None:
            special_balls.append(int(val))

    # Check for duplicates in main balls
    if len(main_balls) != len(set(main_balls)):
        errors["base"] = "duplicate_main_balls"

    # Check for duplicates in special balls (e.g. EuroMillions 2 Lucky Stars)
    if len(special_balls) != len(set(special_balls)):
        errors["base"] = "duplicate_special_balls"

    # Assemble line string: "2, 14, 25, 33, 49"
    formatted_line = ", ".join(str(n) for n in sorted(main_balls))
    return formatted_line, errors


class UKLotteryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._selected_game = None

    async def async_step_user(self, user_input=None):
        configured_games = {
            entry.data.get("game") for entry in self._async_current_entries()
        }
        available_games = [g for g in GAMES if g not in configured_games]

        if not available_games:
            return self.async_abort(reason="all_games_configured")

        if user_input is not None:
            self._selected_game = user_input["game"]
            await self.async_set_unique_id(f"{DOMAIN}_{self._selected_game}")
            self._abort_if_unique_id_configured()
            return await self.async_step_line()

        schema = vol.Schema({
            vol.Required("game"): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": g, "label": GAME_LABELS.get(g, g)}
                        for g in available_games
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_line(self, user_input=None):
        errors = {}

        if user_input is not None:
            formatted_line, errors = validate_and_serialize_line(self._selected_game, user_input)
            if not errors:
                return self.async_create_entry(
                    title=GAME_LABELS.get(self._selected_game, self._selected_game),
                    data={"game": self._selected_game},
                    options={"lines": formatted_line},
                )

        schema = build_line_schema(self._selected_game, user_input)
        return self.async_show_form(step_id="line", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return UKLotteryOptionsFlowHandler()


class UKLotteryOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        game = self.config_entry.data.get("game")

        if user_input is not None:
            formatted_line, errors = validate_and_serialize_line(game, user_input)
            if not errors:
                return self.async_create_entry(title="", data={"lines": formatted_line})

        # Pre-populate fields from existing stored line
        existing_inputs = {}
        current_lines = self.config_entry.options.get("lines", "")
        if current_lines:
            tokens = [int(x.strip()) for x in current_lines.split(",") if x.strip().isdigit()]
            for idx, val in enumerate(tokens, start=1):
                existing_inputs[f"ball_{idx}"] = val

        schema = build_line_schema(game, existing_inputs)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)