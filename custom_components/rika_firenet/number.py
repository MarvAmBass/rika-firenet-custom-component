import logging

from homeassistant.const import PERCENTAGE, TEMP_CELSIUS
from .entity import RikaFirenetEntity
from homeassistant.components.number import NumberEntity

from .const import (
    DOMAIN
)
from .core import RikaFirenetCoordinator
from .core import RikaFirenetStove

_LOGGER = logging.getLogger(__name__)

DEVICE_NUMBERS = [
    "room power request",
    "heating power",
    "convection fan1 level",
    "convection fan1 area",
    "convection fan2 level",
    "convection fan2 area",
    "temperature offset",
    "set back temperature"
]


async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("setting up platform number")
    coordinator: RikaFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    stove_entities = []

    # Create stove numbers
    for stove in coordinator.get_stoves():
        stove_entities.extend(
            [
                RikaFirenetStoveNumber(entry, stove, coordinator, number)
                for number in DEVICE_NUMBERS
            ]
        )

    if stove_entities:
        async_add_entities(stove_entities, True)


class RikaFirenetStoveNumber(RikaFirenetEntity, NumberEntity):
    def __init__(self, config_entry, stove: RikaFirenetStove, coordinator: RikaFirenetCoordinator, number):
        super().__init__(config_entry, stove, coordinator, number)

        self._number = number

    @property
    def min_value(self) -> float:
        if self._number == "room power request":
            return 1
        elif self._number == "heating power":
            return 30
        elif self._number == "convection fan1 level":
            return 0
        elif self._number == "convection fan1 area":
            return -30
        elif self._number == "convection fan2 level":
            return 0
        elif self._number == "convection fan2 area":
            return -30
        elif self._number == "set back temperature":
            return 12
        elif self._number == "temperature offset":
            return -5    
        return 0

    @property
    def max_value(self) -> float:
        if self._number == "room power request":
            return 4
        elif self._number == "heating power":
            return 100
        elif self._number == "convection fan1 level":
            return 5
        elif self._number == "convection fan1 area":
            return 30
        elif self._number == "convection fan2 level":
            return 5
        elif self._number == "convection fan2 area":
            return 30
        elif self._number == "set back temperature":
            return 20
        elif self._number == "temperature offset":
            return 5    

        return 100

    @property
    def step(self) -> float:
        if self._number == "room power request":
            return 1
        elif self._number == "heating power":
            return 5        
        elif self._number == "convection fan1 level":
            return 1
        elif self._number == "convection fan1 area":
            return 1
        elif self._number == "convection fan2 level":
            return 1
        elif self._number == "convection fan2 area":
            return 1
        elif self._number == "set back temperature":
            return 1
        elif self._number == "temperature offset":
            return 0,1

        return 10

    @property
    def value(self):
        if self._number == "room power request":
            return self._stove.get_room_power_request()
        elif self._number == "heating power":
            return self._stove.get_heating_power()
        elif self._number == "convection fan1 level":
            return self._stove.get_convection_fan1_level()
        elif self._number == "convection fan1 area":
            return self._stove.get_convection_fan1_area()
        elif self._number == "convection fan2 level":
            return self._stove.get_convection_fan2_level()
        elif self._number == "convection fan2 area":
            return self._stove.get_convection_fan2_area()
        elif self._number == "set back temperature":
            return self._stove.get_stove_set_back_temperature()
        elif self._number == "temperature offset":
            return self._stove.get_temperatureOffset

    @property
    def unit_of_measurement(self):
        if self._number == "heating power":
            return PERCENTAGE
        elif self._number == "convection fan1 area":
            return PERCENTAGE
        elif self._number == "convection fan2 area":
            return PERCENTAGE
        elif self._number == "set back temperature":
            return TEMP_CELSIUS
        elif self._number == "temperature offset":
            return TEMP_CELSIUS

    @property
    def icon(self):
        if "temperature" in self._number:
            return "mdi:thermometer"
        return "mdi:speedometer"

    def set_value(self, value: float) -> None:
        _LOGGER.info("set_value " + self._number + " " + str(value))

        if self._number == "room power request":
            self._stove.set_room_power_request(int(value))
        elif self._number == "heating power":
            self._stove.set_heating_power(int(value))
        elif self._number == "convection fan1 level":
            return self._stove.set_convection_fan1_level(int(value))
        elif self._number == "convection fan1 area":
            return self._stove.set_convection_fan1_area(int(value))
        elif self._number == "convection fan2 level":
            return self._stove.set_convection_fan2_level(int(value))
        elif self._number == "convection fan2 area":
            return self._stove.set_convection_fan2_area(int(value))
        elif self._number == "set back temperature":
            return self._stove.set_stove_set_back_temperature
        elif self._number == "temperature offset":
            return self._stove.set_temperatureOffset

        self.schedule_update_ha_state()
