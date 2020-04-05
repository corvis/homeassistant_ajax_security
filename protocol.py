import logging
from enum import IntEnum
from typing import NamedTuple, List

_LOGGER = logging.getLogger(__name__)

MSG_STATUS = 'STATUS'
MSG_EVENT = 'EVENT'
MSG_SYNC = 'SYNC'
MSG_RSTATE = 'RSTATE'
MSG_ALARM = 'ALARM'


class ClassifiedMessage(NamedTuple):
    type: str
    original: str
    args: List[str]


class DeviceType(IntEnum):
    UNKNOWN = 0
    DOOR_PROTECT = 1
    MOTION_PROTECT = 2
    FIRE_PROTECT = 3
    GLASS_PROTECT = 4
    LEAKS_PROTECT = 5
    COMBI_PROTECT = 8
    FIRE_PROTECT_PLUS = 9
    SPACE_CONTROL = 11
    MOTION_PROTECT_PLUS = 14


class AlarmType(IntEnum):
    TAMPER_ALARM = 1
    TAMPER_RESTORED = 2
    TAMPER_RESTORED_DUAL = 3
    LOOP_ALARM = 4
    LOOP_RESTORED = 5
    LOOP_RESTORED_DUAL = 6
    TERMINAL_OPEN = 7
    TERMINAL_CLOSED = 8
    TERMINAL_CLOSED_DUAL = 9
    SMOKE_ALARM = 10
    SMOKE_ALARM_RESTORED = 11
    SMOKE_ALARM_RESTORED_DUAL = 12
    CO2_ALARM = 13
    CO2_ALARM_RESTORED = 14
    CO2_ALARM_RESTORED_DUAL = 15
    TEMPERATURE_ALARM = 16
    TEMPERATURE_ALARM_RESTORED = 17
    TEMPERATURE_ALARM_RESTORED_DUAL = 18
    FLOOD_ALARM = 19
    FLOOD_ALARM_RESTORED = 20
    FLOOD_ALARM_RESTORED_DUAL = 21
    MOTION_DETECTED = 22
    GLASS_BREAK_ALARM = 23
    EXTREME_TEMPERATURE_ALARM = 32
    EXTREME_TEMPERATURE_RESTORED = 33
    UNKNOWN_ALARM = 39
    LOW_BATTERY_ALARM = 41
    LOW_BATTERY_ALARM_RESTORED = 42
    SENSOR_LOST_ALARM = 43
    SENSOR_LOST_ALARM_RESTORED = 44


class BaseMessage(object):
    def __init__(self) -> None:
        self.deviceId = None  # type: str
        self.deviceType = None  # type: int
        self.msg = None  # type: ClassifiedMessage

    @classmethod
    def type(cls):
        raise NotImplementedError

    def update_from_classified_message(self, msg: ClassifiedMessage):
        self.msg = msg

    def _raise_parse_error(self, msg, err):
        _LOGGER.error(err)
        raise ValueError("Can't parse message \"{}\": {}".format(msg.original, str(err)))


class AlarmMessage(BaseMessage):

    def __init__(self) -> None:
        super().__init__()
        self.alarm = None  # type: AlarmType

    @classmethod
    def type(cls) -> str:
        return MSG_ALARM

    def update_from_classified_message(self, msg: ClassifiedMessage):
        try:
            super().update_from_classified_message(msg)
            self.deviceType = DeviceType(int(msg.args[0]))
            self.deviceId = msg.args[1]
            self.alarm = AlarmType(int(msg.args[2]))
        except Exception as e:
            self._raise_parse_error(msg, e)


class EventMessage(BaseMessage):
    pass


class StatusMessage(BaseMessage):

    def __init__(self) -> None:
        super().__init__()
        self.noise = None  # type: int
        self.rssi = None  # type: int
        self.low_battery = None  # type: bool

    @classmethod
    def type(cls):
        return MSG_STATUS

    def update_from_classified_message(self, msg: ClassifiedMessage):
        try:
            super().update_from_classified_message(msg)
            self.deviceType = DeviceType(int(msg.args[0]))
            self.deviceId = msg.args[1]
            # Only short (ping) type status messages are supported
            if msg.args[-2] == 'PING':
                self.noise = msg.args[6]
                self.rssi = msg.args[7]
                self.low_battery = msg.args[8] == 1
        except Exception as e:
            self._raise_parse_error(msg, e)
