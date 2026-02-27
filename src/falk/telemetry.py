import logging
import argparse

import yaml
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from falk.iot.tuya import Switch
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

def get_device_data(device: dict):
    id = device['id']
    name = device['name']
    ip = device['ip']
    local_key = device['local_key']
    version = device['version']

    switch = Switch(id=id, name=name, ip=ip, local_key=local_key, version=version)
    switch.refresh()

    return switch

def main():
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
                stmt = select(db_devices.TuyaSwitch.id).where(db_devices.TuyaSwitch.tuya_id == device['id'])
                db_id = session.scalar(stmt)

                switch = get_device_data(device)

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
    
    logger.info('Done!')

def add_device(uri, name, ip, tuya_id, local_key, version):
    engine = create_engine(uri)
    Session = sessionmaker(engine)

    with Session() as session:    
        tuya = devices.TuyaSwitch(
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