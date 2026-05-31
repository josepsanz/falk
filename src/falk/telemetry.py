import logging
import argparse

import yaml
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from falk.iot.tuya import Switch
from falk.iot.shelly import EnergyMeter
from falk.models import devices as db_devices

LOGGER_NAME = 'falk.telemetry'
logger = logging.getLogger(LOGGER_NAME)


def set_logger(log_file, level):
    formatter = logging.Formatter('{asctime} - {levelname:<8} - {name:<16} - {message}', style='{')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
 
    logger.setLevel(level)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

def get_arguments():
    parser = argparse.ArgumentParser(description='Falk Telemetry')
    parser.add_argument('--devices-file', type=str, default='devices.yaml', help='Devices file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show more info.')
    return parser.parse_args()

def tuya_switch_telemetry(session, device):
    stmt = select(db_devices.TuyaSwitch.id).where(db_devices.TuyaSwitch.tuya_id == device['id'])
    db_id = session.scalar(stmt)

    try:
        id = device['id']
        name = device['name']
        ip = device['ip']
        local_key = device['local_key']
        version = device['version']

        switch = Switch(id=id, name=name, ip=ip, local_key=local_key, version=version).refresh()

        metric = db_devices.SwitchMetric(
            switch_id=db_id,
            current=switch.current,
            voltage=switch.voltage,
            power=switch.power
        )
        session.add(metric)
        session.commit()

        msg = f"{switch.name:>27}: {switch.current:>6}mA, {switch.power:>6}W, {switch.voltage:>6}V"
        logger.debug(msg)
    except:
        logger.warning('Something wrong! Skip!', exc_info=True)

def shelly_em_telemetry(session, device):
    try:
        em = shelly_em_telemetry(device['ip']).refresh()
        
    except:
        logger.warning('Something wrong! Skip!', exc_info=True)
    

def main():
    DEVICE_DISPATCHER = {
        'tuya-smart-plug': tuya_switch_telemetry,
        'shelly-3em-63w': shelly_em_telemetry
    }

    arguments = get_arguments()
    level = logging.DEBUG if arguments.verbose else logging.INFO
    set_logger('telemetry.log', level)

    with open(arguments.devices_file, 'r') as fp: 
        devices = yaml.safe_load(fp)

    engine = create_engine(devices['database']['uri'])
    Session = sessionmaker(engine)

    with Session() as session:
        for device in devices['devices']:
            if device['enabled']:
                device_telemetry_fn = DEVICE_DISPATCHER[device['type']]
                device_telemetry_fn(session, device)
    
    logger.info('Done!')

def add_device(uri, name, ip, tuya_id, local_key, version):
    engine = create_engine(uri)
    Session = sessionmaker(engine)

    with Session() as session:    
        tuya = db_devices.TuyaSwitch(
            enabled=True,
            brand='Tuya',
            model='Tuya Smart Plug',
            state=None,
            name=name,
            ip=ip,
            location=None,

            tuya_id=tuya_id,
            local_key=local_key,
            version=version
        )
        session.add(tuya)
        session.commit()

if __name__ == "__main__":
    main()