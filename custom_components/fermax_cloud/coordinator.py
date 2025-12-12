"""DataUpdateCoordinator for Fermax Cloud."""
import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FermaxClient, FermaxConnectionError, FermaxError
from .const import DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class FermaxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for updating Fermax device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: FermaxClient,
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Fermax Cloud",
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client
        self._devices: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data for all devices."""
        try:
            # Get all pairings
            pairings = await self.client.async_get_pairings()
            _LOGGER.debug("Retrieved %s pairings", len(pairings))

            devices_data = {}

            # Update each device in parallel
            tasks = []
            device_ids = []

            for pairing in pairings:
                device_id = pairing.get("deviceId")
                if not device_id:
                    continue

                device_ids.append(device_id)
                tasks.append(self._update_device(device_id, pairing))

            # Gather all results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for device_id, result in zip(device_ids, results):
                if isinstance(result, Exception):
                    _LOGGER.warning(
                        "Failed to update device %s: %s", device_id, result
                    )
                    # Keep previous data if available
                    if device_id in self._devices:
                        devices_data[device_id] = self._devices[device_id]
                else:
                    devices_data[device_id] = result
                    self._devices[device_id] = result

            if not devices_data:
                raise UpdateFailed("No devices could be updated")

            return {"devices": devices_data}

        except FermaxConnectionError as err:
            _LOGGER.error("Connection error during update: %s", err)
            raise UpdateFailed(f"Connection error: {err}") from err
        except FermaxError as err:
            _LOGGER.error("API error during update: %s", err)
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during update: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _update_device(
        self, device_id: str, pairing: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a single device."""
        try:
            # Get device info
            device_info = await self.client.async_get_device(device_id)

            # Get services (optional, don't fail if this errors)
            try:
                services = await self.client.async_get_services(device_id)
            except Exception as err:
                _LOGGER.debug("Could not get services for %s: %s", device_id, err)
                services = []

            return {
                "info": device_info,
                "pairing": pairing,
                "services": services,
            }

        except Exception as err:
            _LOGGER.warning("Error updating device %s: %s", device_id, err)
            raise

    async def async_open_door(
        self, device_id: str, door_key: str
    ) -> None:
        """Open a door and request refresh."""
        if device_id not in self._devices:
            raise ValueError(f"Device {device_id} not found")

        device_data = self._devices[device_id]
        pairing = device_data.get("pairing", {})
        access_door_map = pairing.get("accessDoorMap", {})

        if door_key not in access_door_map:
            raise ValueError(f"Door {door_key} not found for device {device_id}")

        door_info = access_door_map[door_key]
        access_id = door_info.get("accessId", {})

        block = access_id.get("block")
        subblock = access_id.get("subblock")
        number = access_id.get("number")

        if block is None or subblock is None or number is None:
            raise ValueError(f"Invalid door configuration for {door_key}")

        _LOGGER.info("Opening door %s for device %s", door_key, device_id)

        try:
            await self.client.async_open_door(device_id, block, subblock, number)
            # Request a refresh after opening the door
            await self.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to open door %s: %s", door_key, err)
            raise

    def get_device_data(self, device_id: str) -> dict[str, Any] | None:
        """Get data for a specific device."""
        if not self.data:
            return None
        return self.data.get("devices", {}).get(device_id)

    def get_all_devices(self) -> dict[str, dict[str, Any]]:
        """Get all devices data."""
        if not self.data:
            return {}
        return self.data.get("devices", {})
