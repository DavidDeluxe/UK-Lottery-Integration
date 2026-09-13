"""Constants for the UK Lottery Integration."""

DOMAIN = "uk_lottery_integration"

GAMES = [
    "euromillions",
    "euromillions_hotpicks",
    "lotto",
    "lotto_hotpicks",
    "powerball",
    "set_for_life",
    "thunderball",
]

# (main_balls_count, max_main_ball, special_key, special_count, max_special_ball)
GAME_RULES = {

    "euromillions": {
        "main_count": 5,
        "main_max": 50,
        "special_name": "star",
        "special_count": 2,
        "special_max": 12,
    },
    "euromillions_hotpicks": {
        "main_count": 5,
        "main_max": 50,
        "special_name": None,
        "special_count": 0,
        "special_max": 0,
    },
    "lotto": {
        "main_count": 6,
        "main_max": 59,
        "special_name": None,  # Bonus ball is only drawn, not picked on ticket
        "special_count": 0,
        "special_max": 0,
    },
    "lotto_hotpicks": {
        "main_count": 5,
        "main_max": 59,
        "special_name": None,
        "special_count": 0,
        "special_max": 0,
    },
    "powerball": {
        "main_count": 5,
        "main_max": 69,
        "special_name": "powerball",
        "special_count": 1,
        "special_max": 26,
    },
    "set_for_life": {
        "main_count": 5,
        "main_max": 47,
        "special_name": "life_ball",
        "special_count": 1,
        "special_max": 10,
    },
    "thunderball": {
        "main_count": 5,
        "main_max": 39,
        "special_name": "thunderball",
        "special_count": 1,
        "special_max": 14,
    },
}