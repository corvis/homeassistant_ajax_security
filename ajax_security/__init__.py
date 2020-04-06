import asyncio
import logging
import re
from concurrent.futures import CancelledError
from typing import NamedTuple, Dict, Optional

import serial_asyncio
import voluptuous as vol
from homeassistant.const import (
    CONF_TYPE,
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
)
import homeassistant.helpers.config_validation as cv
from serial import SerialException

from .protocol import ClassifiedMessage, BaseMessage, AlarmMessage, StatusMessage
from .errors import UnknownMessageError

_LOGGER = logging.getLogger(__name__)

DEFAULT_BRIDGE = "uart_bridge0"
DEFAULT_BAUDRATE = 57600
DOMAIN = "ajax_security"

CONF_BAUDRATE = "baudrate"
CONF_TIMEOUT = "timeout"
CONF_PORT = "port"

BASE_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default=DEFAULT_BRIDGE): cv.string})

UART_BRIDGE_SCHEMA = SERIAL_SCHEMA = BASE_SCHEMA.extend(
    {
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
        vol.Required(CONF_PORT): cv.string,
        vol.Optional(CONF_TIMEOUT, default=3): cv.socket_timeout,
        vol.Optional(CONF_TYPE, default=DEFAULT_BRIDGE): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.Any(SERIAL_SCHEMA)])},
    extra=vol.ALLOW_EXTRA,
)


class SerialConnection(NamedTuple):
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


SUPPORTED_MESSAGE_CLASSES = (AlarmMessage, StatusMessage)
SUPPORTED_MESSAGE_CLASSES_DICT = {}
for x in SUPPORTED_MESSAGE_CLASSES:
    SUPPORTED_MESSAGE_CLASSES_DICT[x.type()] = x


def parse_message(msg: ClassifiedMessage) -> BaseMessage:
    klass = SUPPORTED_MESSAGE_CLASSES_DICT.get(msg.type, None)
    if klass is None:
        raise UnknownMessageError("Message is not supported: " + msg.original)
    res = klass()
    res.update_from_classified_message(msg)
    return res


async def async_setup(hass, config):
    """Set up Ajax Security Bridge connection."""
    hass.data[DOMAIN] = bridge_objects = {}  # type: Dict[str, AjaxUartBridge]

    for client_config in config[DOMAIN]:
        name, type = client_config[CONF_NAME], client_config[CONF_TYPE]
        bridge_objects[name] = AjaxUartBridge(hass.loop, client_config, name)
        _LOGGER.debug("Setting up Ajax Component(%s): %s", type, client_config)

    async def start_ajax_uart(event):
        for bridge in bridge_objects.values():
            await bridge.start()

        # TODO: Register service here
        # E.g. hass.services.register(
        #             DOMAIN, SERVICE_WRITE_COIL, write_coil, schema=SERVICE_WRITE_COIL_SCHEMA
        #         )

    async def stop_ajax_uart(event):
        for bridge in bridge_objects.values():
            await bridge.stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_ajax_uart)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_ajax_uart)

    return True


class AjaxUartBridge:
    SUPPORTED_MESSAGES_REGEX = re.compile(
        '^(' + '|'.join([x.type() for x in SUPPORTED_MESSAGE_CLASSES]) + ');.*$')

    def __init__(self, loop, client_config: dict, name: str):
        self.__name = name
        self.__loop = loop
        self.__config = client_config
        self.__loop_task = None
        self.__reconnect_attempt_number = 0
        self.max_reconnect_attempts_number = -1  #
        '''
        Negative value means indefinite amount of attempts
        '''
        self.reconnect_interval = 4
        '''
        Amount of time in seconds between attempts
        '''
        self._serial = None  # type: SerialConnection

    async def open_connection(self):
        client_type, device, rate = self.__config[CONF_TYPE], self.__config[CONF_PORT], self.__config[CONF_BAUDRATE]
        self._serial = SerialConnection(*(await serial_asyncio.open_serial_connection(
            url=device, baudrate=rate, timeout=3
        )))  # type: SerialConnection
        _LOGGER.info("Connection established")
        return self._serial

    async def close_connection(self):
        if self._serial:
            try:
                self._serial.writer.close()
                self._serial = None
            except Exception as e:
                _LOGGER.exception("Unable to close serial connection")

    async def start(self):
        while True:
            try:
                if not self._serial:
                    await self.open_connection()
                if self.__loop_task and self.__loop_task.done():
                    # This shouldn't happen but if for some reason it happens let's ensure connection is closed...
                    await self.stop()
                if not self.__loop_task:
                    self.__loop_task = self.__loop.create_task(self.step())
                    self.__loop_task.add_done_callback(
                        lambda data: self.__loop.create_task(self._on_execution_interrupted(data)))
                    self.__reconnect_attempt_number = 0
                elif not self.__loop_task.done():
                    raise ValueError("UART bridge is already started")
                return
            except SerialException as e:
                # Serial exception might mean temporary equipment failure so it makes sense to reconnect a bit later
                if 0 < self.max_reconnect_attempts_number < self.__reconnect_attempt_number:
                    # Means we shouldn't apply reconnect logic and could just raise exception
                    raise e
                else:
                    _LOGGER.exception(
                        "Serial communication error. Another attempt will be performed in {} seconds".format(
                            self.reconnect_interval))
                    self.__reconnect_attempt_number += 1
                    await asyncio.sleep(self.reconnect_interval, loop=self.__loop)
                    _LOGGER.info(
                        "Starting serial communication session. Attempt #{}".format(
                            self.__reconnect_attempt_number + 1))

    async def stop(self):
        if self._serial:
            await self.close_connection()
        if self.__loop_task:
            self.__loop_task.cancel()
            self.__loop_task = None

    async def _on_execution_interrupted(self, data):
        if isinstance(data.exception(), SerialException):
            _LOGGER.warning("Serial Communication error. Re-connecting...")
            delay_before_new_connection = int(self.reconnect_interval / 2)
            _LOGGER.info(
                "Closing serial connection. Will try to reconnect in {} sec".format(delay_before_new_connection))
            await self.stop()
            await asyncio.sleep(delay_before_new_connection, loop=self.__loop)
            _LOGGER.info("Starting new serial connection")
            await self.start()

    async def step(self):
        while True:
            try:
                if self._serial is None:
                    return False
                msg = await self._serial.reader.readline()
                msg = msg.decode("utf-8").strip()
                # _LOGGER.debug("Received: %s", msg)
                classified_msg = self._classify_msg(msg)
                if classified_msg:
                    # _LOGGER.debug("MATCH: %s", msg)
                    try:
                        parsed_message = parse_message(classified_msg)
                        _LOGGER.debug("PARSED MESSAGE: %s | %s", str(parsed_message.type()), str(vars(parsed_message)))
                    except ValueError as e:
                        _LOGGER.debug(str(e))
                    except UnknownMessageError:
                        pass  # Just skip unknown messages
            except SerialException as e:
                _LOGGER.exception("Serial communication error")
                raise e
            except CancelledError:
                return True  # Gracefully shutdown
            except Exception as e:
                _LOGGER.debug("Can't process ajax security message", exc_info=e)

    def _classify_msg(self, msg: str) -> Optional[ClassifiedMessage]:
        if not msg:
            return None
        match = self.SUPPORTED_MESSAGES_REGEX.match(msg)
        if match:
            return ClassifiedMessage(type=match.group(1), original=msg, args=msg.split(';')[1:])

    @property
    def name(self):
        return self.__name
