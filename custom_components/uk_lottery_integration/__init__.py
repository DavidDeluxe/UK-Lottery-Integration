from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import UKLotteryCoordinator

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    
    # Store or reuse shared coordinator across games
    hass.data.setdefault(DOMAIN, {})
    if "shared_coordinator" not in hass.data[DOMAIN]:
        coordinator = UKLotteryCoordinator(hass, session)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN]["shared_coordinator"] = coordinator
    else:
        coordinator = hass.data[DOMAIN]["shared_coordinator"]

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)