import logging
import asyncio

from homeassistant.components.climate import (
    ClimateEntity,
    HVACMode,
    ClimateEntityFeature,
    HVACAction,
)

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import DOMAIN
from .core import RikaFirenetCoordinator
from .entity import RikaFirenetEntity

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON

MIN_TEMP = 14
MAX_TEMP = 28

HVAC_MODES = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up platform."""
    _LOGGER.info("setting up platform climate")
    coordinator: RikaFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    stove_entities = []

    # Create stove sensors
    for stove in coordinator.get_stoves():
        stove_entities.append(RikaFirenetStoveClimate(entry, stove, coordinator))

    if stove_entities:
        async_add_entities(stove_entities, True)


class RikaFirenetStoveClimate(RikaFirenetEntity, ClimateEntity):
    _enable_turn_on_off_backwards_compatibility = False
    def __init__(self, config_entry, stove, coordinator):
        super().__init__(config_entry, stove, coordinator)
        self._attr_translation_key = "stove_climate"  # Key used for translation

    @property
    def entity_picture(self):
        # Use self._stove_data if available, otherwise self._stove as a fallback
        # or better, directly self._stove which has its own get_status_picture logic
        return self._stove.get_status_picture() # self._stove is updated by the coordinator

    @property
    def current_temperature(self):
        return self._stove.get_room_temperature()

    @property
    def min_temp(self):
        return MIN_TEMP

    @property
    def max_temp(self):
        return MAX_TEMP

    @property
    def target_temperature(self):
        return self._stove.get_room_thermostat()

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_modes(self) -> HVACMode:
        return HVAC_MODES

    @property
    def hvac_mode(self):
        return self._stove.get_hvac_mode()

    @property
    def hvac_action(self) -> HVACAction:
        """Return current operation ie. heat, cool, idle."""
        return self._stove.get_hvac_action()

    @property
    def supported_features(self):
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    async def async_set_temperature(self, **kwargs):
        temperature = int(kwargs.get(ATTR_TEMPERATURE))
        _LOGGER.debug(f'set_temperature(): {temperature}')
        if kwargs.get(ATTR_TEMPERATURE) is None:
            return
        # Checking if the stove is on can be done here or in self._stove.set_stove_temperature
        # if not (self._stove_data and self._stove_data.get('controls', {}).get('onOff')):
        #     _LOGGER.debug(f"Stove {self._stove.get_name()} is off, not setting temperature.")
        #     return
            
        self._stove.set_stove_temperature(temperature) # Modifies the "desired" state on the stove object
        await self.coordinator.async_request_refresh() # Asks the coordinator to send the command and refresh

    async def async_set_hvac_mode(self, hvac_mode):
        _LOGGER.debug(f'set_hvac_mode() for {self.name}: {hvac_mode}')

        if hvac_mode == HVACMode.OFF:
            # Just turn off the stove, don't change mode
            self._stove.set_stove_on_off(False)
            await self.coordinator.async_request_refresh()

        elif hvac_mode == HVACMode.HEAT:
            # Set to manual mode and turn on
            current_mode = self._stove.get_stove_operation_mode()

            if current_mode != 0:  # Not in manual mode
                _LOGGER.debug(f'Switching to manual mode before turning on')
                self._stove.set_mode_manual()
                await self.coordinator.async_request_refresh()
                await asyncio.sleep(1)

            # Turn on the stove
            self._stove.set_stove_on_off(True)
            await self.coordinator.async_request_refresh()

        elif hvac_mode == HVACMode.AUTO:
            # Get the preferred mode from the auto mode preference select
            auto_pref_entity_id = f"select.{self._stove.get_name().lower().replace(' ', '_')}_auto_mode_preference"
            auto_pref_state = self.hass.states.get(auto_pref_entity_id)

            if auto_pref_state and auto_pref_state.state:
                preferred_mode_str = auto_pref_state.state
                _LOGGER.debug(f'Auto mode preference: {preferred_mode_str}')

                # Map preference to mode value
                mode_map = {"Manual": 0, "Automatic": 1, "Comfort": 2}
                preferred_mode = mode_map.get(preferred_mode_str, 1)  # Default to Automatic

                current_mode = self._stove.get_stove_operation_mode()

                if current_mode != preferred_mode:
                    _LOGGER.debug(f'Switching to {preferred_mode_str} mode before turning on')

                    if preferred_mode == 0:
                        self._stove.set_mode_manual()
                    elif preferred_mode == 1:
                        self._stove.set_mode_auto()
                    elif preferred_mode == 2:
                        self._stove.set_mode_comfort()

                    await self.coordinator.async_request_refresh()
                    await asyncio.sleep(1)

                # Turn on the stove
                self._stove.set_stove_on_off(True)
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning(f'Could not get auto mode preference, defaulting to Automatic mode')
                current_mode = self._stove.get_stove_operation_mode()

                if current_mode != 1:
                    self._stove.set_mode_auto()
                    await self.coordinator.async_request_refresh()
                    await asyncio.sleep(1)

                self._stove.set_stove_on_off(True)
                await self.coordinator.async_request_refresh()
