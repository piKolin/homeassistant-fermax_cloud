"""Sensor platform for Fermax Cloud."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_CLASS,
    CONF_ENABLED_DEFAULT,
    CONF_ENTITY_CATEGORY,
    CONF_ICON,
    CONF_STATE_CLASS,
    CONF_TRANSLATION_KEY,
    CONF_UNIT_OF_MEASUREMENT,
    DOMAIN,
    SENSOR_MAPPING,
)
from .coordinator import FermaxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fermax Cloud sensor entities."""
    coordinator: FermaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Get all devices
    devices = coordinator.get_all_devices()

    for device_id, device_data in devices.items():
        pairing = device_data.get("pairing", {})
        info = device_data.get("info", {})

        # Connection state sensor
        entities.append(
            FermaxConnectionStateSensor(coordinator, device_id, pairing)
        )

        # Device status sensor
        entities.append(FermaxDeviceStatusSensor(coordinator, device_id, pairing))

        # Device type sensor
        entities.append(FermaxDeviceTypeSensor(coordinator, device_id, pairing))

        # Wireless signal sensor (if available)
        if info.get("wirelessSignal") is not None:
            entities.append(
                FermaxWirelessSignalSensor(coordinator, device_id, pairing)
            )

        _LOGGER.debug("Created sensors for device %s", device_id)

    async_add_entities(entities)


class FermaxSensorBase(CoordinatorEntity[FermaxDataUpdateCoordinator], SensorEntity):
    """Base class for Fermax sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
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


class FermaxConnectionStateSensor(FermaxSensorBase):
    """Sensor for device connection state."""

    _attr_translation_key = "connection_state"

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id, pairing, "connection_state")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return None

        info = device_data.get("info", {})
        return info.get("connectionState")


class FermaxDeviceStatusSensor(FermaxSensorBase):
    """Sensor for device status."""

    _attr_translation_key = "device_status"

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id, pairing, "device_status")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return None

        info = device_data.get("info", {})
        return info.get("status")


class FermaxDeviceTypeSensor(FermaxSensorBase):
    """Sensor for device type."""

    _attr_translation_key = "device_type"

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id, pairing, "device_type")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return None

        info = device_data.get("info", {})
        device_type = info.get("type", "")
        subtype = info.get("subtype", "")

        if subtype:
            return f"{device_type} ({subtype})"
        return device_type


class FermaxWirelessSignalSensor(FermaxSensorBase):
    """Sensor for wireless signal strength."""

    def __init__(
        self,
        coordinator: FermaxDataUpdateCoordinator,
        device_id: str,
        pairing: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id, pairing, "wireless_signal")
        
        # Apply configuration from SENSOR_MAPPING
        config = SENSOR_MAPPING.get("wirelessSignal", {})
        if config.get(CONF_DEVICE_CLASS):
            self._attr_device_class = config[CONF_DEVICE_CLASS]
        if config.get(CONF_STATE_CLASS):
            self._attr_state_class = config[CONF_STATE_CLASS]
        if config.get(CONF_UNIT_OF_MEASUREMENT):
            self._attr_native_unit_of_measurement = config[CONF_UNIT_OF_MEASUREMENT]
        if config.get(CONF_ICON):
            self._attr_icon = config[CONF_ICON]
        if config.get(CONF_ENTITY_CATEGORY):
            self._attr_entity_category = config[CONF_ENTITY_CATEGORY]
        if config.get(CONF_TRANSLATION_KEY):
            self._attr_translation_key = config[CONF_TRANSLATION_KEY]

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return None

        info = device_data.get("info", {})
        signal = info.get("wirelessSignal")

        if signal is not None and isinstance(signal, int):
            # Fermax uses 1-4 scale for signal strength (4 bars)
            signal_map = {
                1: "Muy débil",
                2: "Débil",
                3: "Buena",
                4: "Excelente",
            }
            return signal_map.get(signal, "Desconocida")

        return None

    @property
    def icon(self) -> str:
        """Return the icon based on signal strength."""
        device_data = self.coordinator.get_device_data(self._device_id)
        if not device_data:
            return "mdi:wifi-off"

        info = device_data.get("info", {})
        signal = info.get("wirelessSignal")

        if signal is not None and isinstance(signal, int):
            # Different WiFi icons based on signal strength (1-4 bars)
            icon_map = {
                1: "mdi:wifi-strength-1",
                2: "mdi:wifi-strength-2",
                3: "mdi:wifi-strength-3",
                4: "mdi:wifi-strength-4",
            }
            return icon_map.get(signal, "mdi:wifi-off")

        return "mdi:wifi-off"
