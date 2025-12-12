"""The Fermax Cloud integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FermaxAuthError, FermaxClient, FermaxConnectionError
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .coordinator import FermaxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Fermax Cloud component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fermax Cloud from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    _LOGGER.info("Setting up Fermax Cloud integration for %s", email)

    # Create API client
    session = async_get_clientsession(hass)
    client = FermaxClient(session, email, password)

    # Validate credentials by attempting login
    try:
        await client.async_login()
        _LOGGER.info("Successfully authenticated with Fermax Cloud")
    except FermaxAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except FermaxConnectionError as err:
        _LOGGER.error("Connection error during setup: %s", err)
        raise ConfigEntryNotReady(f"Connection error: {err}") from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during setup: %s", err)
        raise ConfigEntryNotReady(f"Unexpected error: {err}") from err

    # Create coordinator
    coordinator = FermaxDataUpdateCoordinator(
        hass,
        client,
        update_interval=update_interval,
    )

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.info("Successfully fetched initial data")
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady(f"Failed to fetch initial data: {err}") from err

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    _LOGGER.info("Fermax Cloud integration setup complete")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Fermax Cloud integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("Updating Fermax Cloud options")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.info(
        "Migrating Fermax Cloud entry from version %s.%s",
        entry.version,
        entry.minor_version,
    )

    # Currently at version 1, no migrations needed yet
    # Future migrations would go here

    _LOGGER.info(
        "Migration to version %s.%s successful", entry.version, entry.minor_version
    )
    return True
