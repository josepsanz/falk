from dataclasses import dataclass, field

import requests


@dataclass
class Phase:
    name: str
    dev_name: str = field(repr=False)
    # status
    current: float = field(default=0)
    voltage: float = field(default=0)
    act_power: float = field(default=0)  # in Watts
    aprt_power: float = field(default=0, repr=False)  # in VA
    freq: float = field(default=0, repr=False)
    pf: float = field(default=0, repr=False)
    # hist
    total_act_energy: float = field(default=0, repr=False)
    total_act_ret_energy: float = field(default=0, repr=False)

    def refresh(self, em_status: dict, em_hist: dict):
        self.current = em_status[f'{self.dev_name}_current']
        self.voltage = em_status[f'{self.dev_name}_voltage']
        self.act_power = em_status[f'{self.dev_name}_act_power']
        self.aprt_power = em_status[f'{self.dev_name}_aprt_power']
        self.freq = em_status[f'{self.dev_name}_freq']
        self.pf = em_status[f'{self.dev_name}_pf']

        self.total_act_energy = em_hist[f'{self.dev_name}_total_act_energy']
        self.total_act_ret_energy = em_hist[f'{self.dev_name}_total_act_ret_energy']

class EnergyMeter:
    def __init__(self, ip: str):
        self.ip = ip
        self.lines = [
            Phase(name='l1', dev_name='a'), 
            Phase(name='l2', dev_name='b'), 
            Phase(name='l3', dev_name='c'), 
        ]
        # status
        self.total_act_power = 0
        self.total_aprt_power = 0
        self.total_current = 0
        # hist
        self.total_act_energy = 0
        self.total_act_ret_energy = 0

        self._current_status_url = f'http://{self.ip}/rpc/EM.GetStatus?id=0'
        self._data_url = f'http://{self.ip}/rpc/EMData.GetStatus?id=0'
        self._total_url = f'http://{self.ip}/rpc/Shelly.GetStatus'

    def refresh(self): 
        resp = requests.get(self._total_url)
        resp.raise_for_status()

        data = resp.json()
        em_status, em_hist = data['em:0'], data['emdata:0']

        for line in self.lines:
            line.refresh(em_status, em_hist)

        self.total_act_power = em_status['total_act_power']
        self.total_aprt_power = em_status['total_aprt_power']
        self.total_current = em_status['total_current']

        self.total_act_energy = em_hist['total_act']
        self.total_act_ret = em_hist['total_act_ret']

        return self
