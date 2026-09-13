import re
from datetime import datetime, time, timedelta
import zoneinfo

UK_TZ = zoneinfo.ZoneInfo("Europe/London")

DRAW_SCHEDULE = {
    
    "euromillions": {"days": [1, 4], "time": time(20, 45)},             # Tue, Fri 20:45
    "euromillions_hotpicks": {"days": [1, 4], "time": time(20, 45)},    # Tue, Fri 20:45
    "lotto": {"days": [2, 5], "time": time(20, 0)},                     # Wed, Sat 20:00
    "lotto_hotpicks": {"days": [2, 5], "time": time(20, 0)},            # Wed, Sat 20:00
    "set_for_life": {"days": [0, 3], "time": time(20, 0)},              # Mon, Thu 20:00
    "powerball": {"days": [1, 3, 6], "time": time(4, 30)},              # Tue, Thu, Sun 04:30 (UK time)
    "thunderball": {"days": [1, 2, 4, 5], "time": time(20, 0)},         # Tue, Wed, Fri, Sat 20:00
}

def calculate_next_draw(game: str) -> str | None:
    """Calculate the ISO 8601 timestamp of the next upcoming draw."""
    sched = DRAW_SCHEDULE.get(game)
    if not sched:
        return None

    now = datetime.now(UK_TZ)
    draw_time = sched["time"]
    target_days = sched["days"]

    # Check up to 8 days into the future
    for day_offset in range(8):
        check_date = now.date() if day_offset == 0 else (now + timedelta(days=day_offset)).date()
        if check_date.weekday() in target_days:
            candidate = datetime.combine(check_date, draw_time, tzinfo=UK_TZ)
            if candidate > now:
                return candidate.isoformat()

    return None

def parse_user_lines(raw_lines: str, max_lines: int = 10) -> list[list[int]]:
    """Parse comma/space/newline-separated lines from options."""
    if not raw_lines:
        return []

    lines = []
    chunks = [c.strip() for c in raw_lines.replace(";", "\n").split("\n") if c.strip()]
    for chunk in chunks[:max_lines]:
        nums = []
        for token in chunk.replace(",", " ").split():
            if token.isdigit():
                nums.append(int(token))
        if nums:
            lines.append(sorted(nums))
    return lines

def evaluate_line(game: str, user_line: list[int], draw_data: dict) -> dict:
    """Check a user's ticket line against drawn numbers."""
    if not draw_data or not draw_data.get("balls"):
        return {"line": user_line, "matched": [], "match_count": 0, "win": False}

    drawn_balls = set(draw_data.get("balls", []))
    matched = sorted(list(drawn_balls.intersection(set(user_line))))
    match_count = len(matched)

    # Basic win thresholds
    is_win = match_count >= 2

    return {
        "line": user_line,
        "matched": matched,
        "match_count": match_count,
        "win": is_win,
    }