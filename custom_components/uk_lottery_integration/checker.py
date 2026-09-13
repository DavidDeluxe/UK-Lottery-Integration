import re

def parse_user_lines(raw_text: str, max_lines: int = 10) -> list[dict]:
    """Parse string input into structured user lines."""
    lines = []
    if not raw_text:
        return lines

    for row in raw_text.strip().splitlines()[:max_lines]:
        row = row.strip()
        if not row:
            continue
        
        # Split main numbers and bonus/stars by '+' or '/'
        parts = re.split(r"[\+/]", row)
        main_nums = [int(n) for n in re.findall(r"\b\d+\b", parts[0])]
        specials = [int(n) for n in re.findall(r"\b\d+\b", parts[1])] if len(parts) > 1 else []
        lines.append({"main": main_nums, "special": specials})
    return lines

def evaluate_line(game: str, user_line: dict, draw_result: dict) -> dict:
    """Evaluate a single user ticket against a draw."""
    if not draw_result or "balls" not in draw_result:
        return {"matched_main": [], "matched_special": [], "prize": None, "win": False}

    drawn_main = set(draw_result.get("balls", []))
    matched_main = sorted(list(set(user_line["main"]).intersection(drawn_main)))
    
    # Collect special balls (bonus ball, lucky stars, powerball, etc.)
    drawn_specials = set()
    for key in ["bonus_ball", "lucky_stars", "life_ball", "thunderball", "powerball"]:
        val = draw_result.get(key)
        if isinstance(val, list):
            drawn_specials.update(val)
        elif isinstance(val, int):
            drawn_specials.add(val)

    matched_specials = sorted(list(set(user_line["special"]).intersection(drawn_specials)))
    
    m_count = len(matched_main)
    s_count = len(matched_specials)
    prize = None

    # Official Prize Tier Matching
    if game in ["lotto", "lotto_hotpicks"]:
        if m_count == 6: prize = "Jackpot"
        elif m_count == 5 and s_count == 1: prize = "£1,000,000 (5 + Bonus)"
        elif m_count == 5: prize = "£1,750"
        elif m_count == 4: prize = "£140"
        elif m_count == 3: prize = "£30"
        elif m_count == 2: prize = "Free Lucky Dip"
    elif game in ["euromillions", "euromillions_hotpicks"]:
        if m_count == 5 and s_count == 2: prize = "Jackpot"
        elif m_count == 5 and s_count == 1: prize = "Match 5 + 1 Star"
        elif m_count == 5: prize = "Match 5"
        elif m_count == 4 and s_count == 2: prize = "Match 4 + 2 Stars"
        elif m_count == 4 and s_count == 1: prize = "Match 4 + 1 Star"
        elif m_count == 3 and s_count == 2: prize = "Match 3 + 2 Stars"
        elif m_count == 4: prize = "Match 4"
        elif m_count == 2 and s_count == 2: prize = "Match 2 + 2 Stars"
        elif m_count == 3 and s_count == 1: prize = "Match 3 + 1 Star"
        elif m_count == 3: prize = "Match 3"
        elif m_count == 1 and s_count == 2: prize = "Match 1 + 2 Stars"
        elif m_count == 2 and s_count == 1: prize = "Match 2 + 1 Star"
        elif m_count == 2: prize = "Match 2"
    elif game == "set_for_life":
        if m_count == 5 and s_count == 1: prize = "£10k/Month for 30 Years"
        elif m_count == 5: prize = "£10k/Month for 1 Year"
        elif m_count == 4 and s_count == 1: prize = "£250"
        elif m_count == 4: prize = "£50"
        elif m_count == 3 and s_count == 1: prize = "£30"
        elif m_count == 3: prize = "£20"
        elif m_count == 2 and s_count == 1: prize = "£10"
        elif m_count == 2: prize = "£5"
    elif game == "thunderball":
        if m_count == 5 and s_count == 1: prize = "£500,000 Top Prize"
        elif m_count == 5: prize = "£5,000"
        elif m_count == 4 and s_count == 1: prize = "£250"
        elif m_count == 4: prize = "£100"
        elif m_count == 3 and s_count == 1: prize = "£20"
        elif m_count == 3: prize = "£10"
        elif m_count == 2 and s_count == 1: prize = "£10"
        elif m_count == 1 and s_count == 1: prize = "£5"
        elif s_count == 1: prize = "£3"
    elif game == "powerball":
        if m_count == 5 and s_count == 1: prize = "Jackpot"
        elif m_count == 5: prize = "$1,000,000"
        elif m_count == 4 and s_count == 1: prize = "$50,000"
        elif m_count == 4 or (m_count == 3 and s_count == 1): prize = "$100"
        elif m_count == 3 or (m_count == 2 and s_count == 1): prize = "$7"
        elif s_count == 1: prize = "$4"

    return {
        "line": user_line,
        "matched_main": matched_main,
        "matched_special": matched_specials,
        "win": prize is not None,
        "prize": prize,
    }