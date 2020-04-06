"""
Support for Ajax Security devices (https://support.ajax.systems/en/).
EARLY DEVELOPMENT STAGE. At the moment only Fire Protect devices are supported.

This sensor requires AJAX Uart Bridge (https://support.ajax.systems/en/manuals/uartbridge/) and USB-UART adaptor.
"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_VALUE_TEMPLATE, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTR_BATTERY_OK = "battery_charged"
ATTR_RSSI = "signal_level"
ATTR_TAMPER_ALARM = "tamper_alarm"
ATTR_ALARM = "alarm"

CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"

DEFAULT_NAME = "Ajax Sensor"
DEFAULT_BAUDRATE = 57600

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Serial sensor platform."""
    name = config.get(CONF_NAME)
    port = config.get(CONF_SERIAL_PORT)
    baudrate = config.get(CONF_BAUDRATE)

    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

    sensor = SerialSensor(name, port, baudrate, value_template)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, sensor.stop_serial_read())
    async_add_entities([sensor], True)


class AjaxSecuritySensor(Entity):
    """Representation of a Serial sensor."""

    def __init__(self, name, port, baudrate, value_template):
        """Initialize the Serial sensor."""
        self._name = name
        self._state = None
        self._port = port
        self._baudrate = baudrate
        self._serial_loop_task = None
        self._template = value_template
        self._attributes = []

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        self._serial_loop_task = self.hass.loop.create_task(
            self.serial_read(self._port, self._baudrate)
        )

    async def serial_read(self, device, rate, **kwargs):
        """Read the data from the port."""
        import serial_asyncio

        reader, _ = await serial_asyncio.open_serial_connection(
            url=device, baudrate=rate, **kwargs
        )
        while True:
            line = await reader.readline()
            line = line.decode("utf-8").strip()


            if self._template is not None:
                line = self._template.async_render_with_possible_json_value(line)

            _LOGGER.debug("Received: %s", line)
            self._state = line
            self.async_schedule_update_ha_state()

    async def stop_serial_read(self):
        """Close resources."""
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the attributes of the entity (if any JSON present)."""
        return self._attributes

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state