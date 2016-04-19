"""Control TEAC AG-980 receiver via RS232C

Copyright (C) Peter Hollobon 2016

Developed from information available on the public internet.
"""

import logging
import sys
import time

import enum
import serial


EXPECTED_COUNT = 16


logger = logging.getLogger(__name__)


class AG980Exception(Exception):
    pass


class AG980Input(enum.IntEnum):
    FM = 0x0
    TUNER = 0x2
    TUNER_AM = 0x3
    CD = 0x4
    AUX = 0x5
    PHONO = 0x6
    DVD = 0x7
    TAPE = 0x8


class AG980(object):
    def __init__(self, port):
        self.__ser = serial.Serial(port, 9600, timeout=2, xonxoff=True, rtscts=True, dsrdtr=True)

    def send(self, data):
        """Send a command to the AG-980"""

        logger.debug("Sending 0x%x", data)
        command = [0x81, 0x73, data]
        command.append(sum(command) & 0xFF)  # checksum
        self.__ser.write("".join(map(chr, command)))

    def read_status(self):
        """Read pending event status"""

        event = map(ord, self.__ser.read(20))

        logger.debug("read %d bytes: %s", len(event), map(hex, event))

        count = event[2]
        if count != EXPECTED_COUNT:
            raise AG980Exception(
                "Unexpected byte count in EVENT message (got %d, expected %d)"
                % (count, EXPECTED_COUNT))

        checksum = event[-1]
        expected_checksum = sum(event[2:-1]) & 0xFF
        if checksum != expected_checksum:
            raise AG980Exception(
                "Checksum error in EVENT message (got %x, expected %x)"
                % (checksum, expected_checksum))

        system_id = event[0] + event[1] * 256
        logger.debug("system id: %x", system_id)

        self.__text = "".join(map(chr, event[3:13]))

        status1 = event[13]
        self.__power = bool(status1 & 0x01)
        self.__commandrequest = bool(status1 & 0x02)
        self.__zone2power = bool(status1 & 0x04)
        self.__mute = bool(status1 & 0x08)
        self.__zone2mute = bool(status1 & 0x10)
        self.__sleepmode = bool(status1 & 0x20)
        self.__cinemaeq = bool(status1 & 0x40)
        self.__tonedirect = bool(status1 & 0x80)

        self.__input = event[14]
        self.__zone2input = event[15]

        self.__volume = event[16] # 0 : -76dB, 1 : -75dB, .., 89 : 13B, 90 : 14dB
        self.__zone2volume = event[17]

        if self.__commandrequest:
            log.warn("Command Request")

    def refresh_status(self):
        """Request status and read, updating internal state"""

        self.send(0x53)
        self.read_status()

    @property
    def power(self):
        self.refresh_status()
        return self.__power

    @power.setter
    def power(self, value):
        self.refresh_status()
        if value and not self.__power:
            self.send(0x01)
        elif not value and self.__power:
            self.send(0x02)

    @property
    def zone2power(self):
        self.refresh_status()
        return self.__zone2power

    @zone2power.setter
    def zone2power(self, value):
        self.refresh_status()
        if value != self.__zone2power:
            self.send(0x3f)

    def volume_up(self, count=1):
        for _ in range(count):
            self.send(0x0f)

    def volume_down(self, count=1):
        for _ in range(count):
            self.send(0x10)

    def zone2volume_up(self):
        self.send(0x41)

    def zone2volume_down(self):
        self.send(0x42)

    @property
    def muted(self):
        self.refresh_status()
        return self.__mute

    @muted.setter
    def muted(self, value):
        self.refresh_status()
        if value != self.__mute:
            self.send(0x11)

    @property
    def zone2muted(self):
        self.refresh_status()
        return self.__zone2mute

    @zone2muted.setter
    def zone2muted(self, value):
        self.refresh_status()
        if value != self.__zone2mute:
            self.send(0x43)

    @property
    def volume(self):
        self.refresh_status()
        return self.__volume

    @property
    def zone2volume(self):
        self.refresh_status()
        return self.__zone2volume

    @property
    def text(self):
        self.refresh_status()
        return self.__text

    @property
    def input(self):
        self.refresh_status()
        return AG980Input(self.__input)

    @input.setter
    def input(self, value):
        value = AG980Input(value)
        self.send(value + 0x3)

    @property
    def zone2input(self):
        self.refresh_status()
        return AG980Input(self.__zone2input)

    @zone2input.setter
    def zone2input(self, value):
        value = AG980Input(value)
        self.send(value + 0x41)

    @property
    def tonedirect(self):
        self.refresh_status()
        return self.__tonedirect

    @tonedirect.setter
    def tonedirect(self, value):
        if value != self.tonedirect:
            self.send(0x15)


if __name__ == "__main__":
    ag980 = AG980("/dev/tty00")
