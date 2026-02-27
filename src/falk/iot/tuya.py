from dataclasses import dataclass, field

import tinytuya


@dataclass
class Switch:
    id: str
    name: str
    ip: str
    local_key: str = field(repr=False)
    version: float = field(repr=False)

    def __post_init__(self):
        self.__state = None
        self.__current = None
        self.__voltage = None

    @property
    def state(self):
        return self.__state

    @property
    def current(self):
        return int(self.__current)

    @property
    def power(self):
        return round(self.__power, 2)
        
    @property
    def voltage(self):
        return round(self.__voltage, 2)

    def refresh(self):
        raw_device = tinytuya.Device(self.id, self.ip, self.local_key, version=self.version)

        status = raw_device.status()['dps']
        
        result = {
            'state': status['1'],               # State (On/Off)
            'current': status['21'],            # Current (mA)
            'power': status['22'] / 10,         # Power (W)
            'voltage': status['23'] / 10,       # Voltage (V)

            'unknown-9': status.get('9'),           # Unknown
            'unknown-20': status.get('20'),         # Unknown
            'unknown-24': status.get('24'),         # Unknown
            'unknown-29': status.get('29'),         # Unknown
        }

        self.__state = result['state']
        self.__current = result['current']
        self.__power = result['power']
        self.__voltage = result['voltage']

        return result

    def turn_on(self):
        raw_device = tinytuya.Device(self.id, self.ip, self.local_key, version=self.version)
        raw_device.turn_on()
        self.refresh()

    def turn_off(self):
        raw_device = tinytuya.Device(self.id, self.ip, self.local_key, version=self.version)
        raw_device.turn_off()
        self.refresh()
    
