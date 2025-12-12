"""Binary sensor platform for Fermax Cloud."""
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BINARY_SENSOR_MAPPING,
    CONF_DEVICE_CLASS,
    CONF_ENABLED_DEFAULT,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_TRANSLATION_KEY,
    DOMAIN,
)
from .coordinator import FermaxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fermax Cloud binary sensor entities."""
    coordinator: FermaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Get all devices
    devices = coordinator.get_all_devices()

    for device_id, device_data in devices.items():
        pairing = device_data.get("pairing", {})

        # Connected binary sensor
        entities.append(FermaxConnectedBinarySensor(coordinator, device_id, pairing))

        # Activated binary sensor
        entities.append(FermaxActivatedBinarySensor(coordinator, device_id, pairing))

        _LOGGER.debug("Created binary sensors for device %s", device_id)

    async_add_entities(entities)


class FermaxBinarySensorBase(
    CoordinatorEntity[FermaxDataUpdateCoordinator], BinarySensorEntity
):
    """Base class for Fermax binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._pairing = pairing
        self._sensor_type = sensor_type

        device_tag = pairing.get("tag", device_id)

        self._attr_unique_id = f"{device_id}_{sensor_type}"

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
        return device_data is not None


class FermaxConnectedBinarySensor(FermaxBinarySensorBase):
    """Binary sensor for device connection status."""

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id, pairing, "connected")
        
        # Apply configuration from BINARY_SENSOR_MAPPING
        config = BINARY_SENSOR_MAPPING.get("connected", {})
        if config.get(CONF_DEVICE_CLASS):
            self._attr_device_class = config[CONF_DEVICE_CLASS]
        if config.get(CONF_ICON):
            self._attr_icon = config[CONF_ICON]
        if config.get(CONF_ENTITY_CATEGORY):
            self._attr_entity_category = config[CONF_ENTITY_CATEGORY]
        if config.get(CONF_TRANSLATION_KEY):
            self._attr_translation_key = config[CONF_TRANSLATION_KEY]

    @property
    def is_on(self) -> bool | None:
        """Return true if device is connected."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return None

        info = device_data.get("info", {})
        connection_state = info.get("connectionState", "")

        return connection_state == "Connected"


class FermaxActivatedBinarySensor(FermaxBinarySensorBase):
    """Binary sensor for device activation status."""

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id, pairing, "activated")
        
        # Apply configuration from BINARY_SENSOR_MAPPING
        config = BINARY_SENSOR_MAPPING.get("activated", {})
        if config.get(CONF_DEVICE_CLASS):
            self._attr_device_class = config[CONF_DEVICE_CLASS]
        if config.get(CONF_ICON):
            self._attr_icon = config[CONF_ICON]
        if config.get(CONF_ENTITY_CATEGORY):
            self._attr_entity_category = config[CONF_ENTITY_CATEGORY]
        if config.get(CONF_TRANSLATION_KEY):
            self._attr_translation_key = config[CONF_TRANSLATION_KEY]

    @property
    def is_on(self) -> bool | None:
        """Return true if device is activated."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return None

        info = device_data.get("info", {})
        status = info.get("status", "")

        return status == "ACTIVATED"
