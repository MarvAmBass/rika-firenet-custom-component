import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.restore_state import RestoreEntity
from .entity import RikaFirenetEntity
from .const import DOMAIN
from .core import RikaFirenetCoordinator, RikaFirenetStove

_LOGGER = logging.getLogger(__name__)

OPERATING_MODE_OPTIONS = ["Manual", "Automatic", "Comfort"]
OPERATING_MODE_MAP = {
    "Manual": 0,
    "Automatic": 1,
    "Comfort": 2,
}
OPERATING_MODE_REVERSE_MAP = {
    0: "Manual",
    1: "Automatic",
    2: "Comfort",
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up platform."""
    _LOGGER.info("Setting up platform select")
    coordinator: RikaFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    select_entities = []

    for stove in coordinator.get_stoves():
        select_entities.append(RikaFirenetOperatingModeSelect(entry, stove, coordinator))
        select_entities.append(RikaFirenetAutoModePreferenceSelect(entry, stove, coordinator))

    if select_entities:
        async_add_entities(select_entities, True)


class RikaFirenetOperatingModeSelect(RikaFirenetEntity, SelectEntity):
    """Select entity for stove operating mode."""

    def __init__(self, config_entry, stove: RikaFirenetStove, coordinator: RikaFirenetCoordinator):
        super().__init__(config_entry, stove, coordinator, "operating_mode")
        self._attr_translation_key = "operating_mode"

    @property
    def options(self):
        """Return the list of available options."""
        return OPERATING_MODE_OPTIONS

    @property
    def current_option(self):
        """Return the current selected option."""
        mode = self._stove.get_stove_operation_mode()
        if mode is not None:
            return OPERATING_MODE_REVERSE_MAP.get(mode, "Manual")
        return "Manual"

    @property
    def icon(self):
        """Return the icon based on current mode."""
        mode = self._stove.get_stove_operation_mode()
        if mode == 0:
            return "mdi:hand-back-right"
        elif mode == 1:
            return "mdi:thermostat-auto"
        elif mode == 2:
            return "mdi:sofa"
        return "mdi:cog"

    async def async_select_option(self, option: str):
        """Change the selected option."""
        mode_value = OPERATING_MODE_MAP.get(option)
        if mode_value is None:
            _LOGGER.error(f"Invalid option: {option}")
            return

        _LOGGER.info(f"Setting operating mode to {option} ({mode_value}) for stove {self._stove.get_name()}")

        if mode_value == 0:
            self._stove.set_mode_manual()
        elif mode_value == 1:
            self._stove.set_mode_auto()
        elif mode_value == 2:
            self._stove.set_mode_comfort()

        await self.coordinator.async_request_refresh()


class RikaFirenetAutoModePreferenceSelect(RikaFirenetEntity, RestoreEntity, SelectEntity):
    """Select entity for climate auto mode preference."""

    def __init__(self, config_entry, stove: RikaFirenetStove, coordinator: RikaFirenetCoordinator):
        super().__init__(config_entry, stove, coordinator, "auto_mode_preference")
        self._attr_translation_key = "auto_mode_preference"
        self._current_option = "Automatic"  # Default value

    @property
    def options(self):
        """Return the list of available options."""
        return OPERATING_MODE_OPTIONS

    @property
    def current_option(self):
        """Return the current selected option."""
        return self._current_option

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:auto-mode"

    async def async_select_option(self, option: str):
        """Change the selected option."""
        if option not in OPERATING_MODE_OPTIONS:
            _LOGGER.error(f"Invalid option: {option}")
            return

        _LOGGER.info(f"Setting auto mode preference to {option} for stove {self._stove.get_name()}")
        self._current_option = option
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore last state when entity is added to hass."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state and last_state.state in OPERATING_MODE_OPTIONS:
            self._current_option = last_state.state
            _LOGGER.debug(f"Restored auto mode preference to {self._current_option}")
        else:
            _LOGGER.debug(f"No previous state found, using default: {self._current_option}")
