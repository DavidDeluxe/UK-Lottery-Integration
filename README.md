# UK-Lottery-Integration
A custom Home Assistant integration for tracking official UK National Lottery games. It fetches verified draw results, evaluates personal ticket lines for winning matches, calculates upcoming draw schedules, and registers each game as an independent device.

---

## Features

* **Multi-Device Architecture**: Add each lottery game independently as a standalone Home Assistant device.
* **Automated Ticket Checking**: Configure up to 10 lines per game (separated by newlines, commas, or spaces). The integration automatically verifies your numbers against the latest draw and sets `has_win: true` when a winning threshold is met.
* **Direct Feed Retrieval**: Uses redirect-aware, SSL-tolerant XML and API parsers to fetch verified draw results and bonus balls directly from official sources.
* **Next Draw Countdown**: Automatically calculates the next upcoming draw date and time for each game in the `Europe/London` timezone.
* **Dashboard-Ready Attributes**: Structured attributes designed for easy integration with Lovelace, Mushroom cards, and automation notifications.

---

## Supported Games

| Game | Main Balls | Special / Bonus | Draw Schedule |
| :--- | :--- | :--- | :--- |
| **EuroMillions** | 5 | 2 Lucky Stars | Tue & Fri (20:45 UK) |
| **EuroMillions HotPicks** | 5 | — (Derived from EuroMillions) | Tue & Fri (20:45 UK) |
| **Lotto** | 6 | Bonus Ball | Wed & Sat (20:00 UK) |
| **Lotto HotPicks** | 6 | — (Derived from Lotto) | Wed & Sat (20:00 UK) |
| **Powerball** | 5 | Powerball | Tue, Thu, Sun 04:30 (UK) |
| **Set For Life** | 5 | Life Ball | Mon & Thu (20:00 UK) |
| **Thunderball** | 5 | Thunderball | Tue, Wed, Fri & Sat (20:00 UK) |

---

## Installation

### Manual Installation

1. Copy the `custom_components/uk_lottery_integration` folder into your Home Assistant directory:
   ```text
   /config/custom_components/uk_lottery_integration/

Disclaimer: This integration is an unofficial tool and is not affiliated with, endorsed by, or connected to Camelot UK Lotteries Limited, Allwyn Entertainment, or the Multi-State Lottery Association (MUSL). Always verify ticket results with official lottery operators before disposing of any tickets.
