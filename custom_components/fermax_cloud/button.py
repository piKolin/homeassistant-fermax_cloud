"""Button platform for Fermax Cloud."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DOOR_KEY_GENERAL, DOOR_KEY_ONE, DOOR_KEY_ZERO, DOOR_NAMES
from .coordinator import FermaxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fermax Cloud button entities."""
    coordinator: FermaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Get all devices
    devices = coordinator.get_all_devices()

    for device_id, device_data in devices.items():
        pairing = device_data.get("pairing", {})
        access_door_map = pairing.get("accessDoorMap", {})

        # Create button for each visible door
        for door_key, door_info in access_door_map.items():
            if door_info.get("visible", False):
                entities.append(
                    FermaxDoorButton(
                        coordinator,
                        device_id,
                        door_key,
                        door_info,
                        pairing,
                    )
                )
                _LOGGER.debug(
                    "Created button for device %s, door %s", device_id, door_key
                )

    async_add_entities(entities)


class FermaxDoorButton(CoordinatorEntity[FermaxDataUpdateCoordinator], ButtonEntity):
    """Button entity to open a Fermax door."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        door_key: str,
        door_info: dict[str, Any],
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._door_key = door_key
        self._door_info = door_info
        self._pairing = pairing

        # Get device tag for naming
        device_tag = pairing.get("tag", device_id)

        # Get door name - use custom title from API if available
        door_title = door_info.get("title", "").strip()
        if not door_title:
            # Fallback to default names if no custom title
            door_title = DOOR_NAMES.get(door_key, door_key)

        self._attr_name = f"Abrir {door_title}"
        self._attr_unique_id = f"{device_id}_door_{door_key}"

        # Device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_tag,
            manufacturer="Fermax",
            model=self._get_device_model(),
        )

    def _get_device_model(self) -> str:
        """Get device model from coordinator data."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if device_data:
            info = device_data.get("info", {})
            device_type = info.get("type", "Unknown")
            subtype = info.get("subtype", "")
            if subtype:
                return f"{device_type} ({subtype})"
            return device_type
        return "Unknown"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return False

        info = device_data.get("info", {})
        connection_state = info.get("connectionState", "")

        return connection_state == "Connected"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.coordinator.async_open_door(self._device_id, self._door_key)
        except Exception as err:
            _LOGGER.error(
                "Failed to open door %s for device %s: %s",
                self._door_key,
                self._device_id,
                err,
            )
            raise
