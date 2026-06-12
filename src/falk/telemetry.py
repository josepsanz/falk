import logging
import argparse
import datetime
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from falk.config import DEVICES_FILE_ENV, load_config
from falk.db import session_factory
from falk.iot.tuya import Switch
from falk.iot.shelly import EnergyMeter
from falk.models import devices as db_devices
from falk.pricing.esios import save_day_prices

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
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--devices-file', type=str, default='devices.yaml', help='Devices file.')
    common.add_argument('-v', '--verbose', action='store_true', help='Show more info.')

    parser = argparse.ArgumentParser(description='Falk Telemetry')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('poll', parents=[common], help='Poll all enabled devices and store metrics.')

    pricing_parser = subparsers.add_parser('pricing', parents=[common], help='Fetch and store ESIOS PVPC hourly prices.')
    pricing_parser.add_argument(
        '--date', type=datetime.date.fromisoformat, default=None,
        help='Day to fetch (YYYY-MM-DD). Defaults to today.',
    )
    return parser.parse_args()

def tuya_switch_telemetry(session, device):
    stmt = select(db_devices.TuyaSwitch).where(db_devices.TuyaSwitch.tuya_id == device['id'])
    db_switch = session.scalar(stmt)

    try:
        switch = Switch(
            id=device['id'],
            name=device['name'],
            ip=device['ip'],
            local_key=device['local_key'],
            version=device['version'],
        ).refresh()

        db_switch.state = switch.state

        metric = db_devices.SwitchMetric(
            switch_id=db_switch.id,
            current=switch.current,
            voltage=switch.voltage,
            power=switch.power
        )
        session.add(metric)
        session.commit()

        msg = f"{switch.name:>27}: {switch.current:>6}mA, {switch.power:>6}W, {switch.voltage:>6}V"
        logger.debug(msg)
    except Exception:
        logger.warning('Something wrong! Skip!', exc_info=True)

def shelly_em_telemetry(session, device):
    stmt = select(db_devices.ShellyEM.id).where(db_devices.ShellyEM.shelly_id == device['id'])
    db_id = session.scalar(stmt)

    try:
        em = EnergyMeter(device['ip']).refresh()

        metric = db_devices.EMMetric(
            em_id=db_id,
            total_act_power=em.total_act_power,
            total_aprt_power=em.total_aprt_power,
            total_current=em.total_current,
            total_act_energy=em.total_act_energy,
            total_act_ret_energy=em.total_act_ret,
            phases=[
                db_devices.Phase(
                    name=phase.name,
                    current=phase.current,
                    voltage=phase.voltage,
                    act_power=phase.act_power,
                    aprt_power=phase.aprt_power,
                    freq=phase.freq,
                    pf=phase.pf,
                    total_act_energy=phase.total_act_energy,
                    total_act_ret_energy=phase.total_act_ret_energy,
                )
                for phase in em.lines
            ],
        )
        session.add(metric)
        session.commit()

        for phase in em.lines:
            logger.debug(
                f"{device['name']} {phase.name}: "
                f"{phase.current:.3f}A, {phase.act_power:.1f}W, {phase.voltage:.1f}V"
            )
    except Exception:
        logger.warning('Something wrong! Skip!', exc_info=True)
    

def run_poll():
    DEVICE_DISPATCHER = {
        'tuya-smart-plug': tuya_switch_telemetry,
        'shelly-3em-63w': shelly_em_telemetry
    }

    devices = load_config()

    Session = session_factory()

    with Session() as session:
        for device in devices['devices']:
            if device['enabled']:
                device_telemetry_fn = DEVICE_DISPATCHER[device['type']]
                device_telemetry_fn(session, device)

def main():
    arguments = get_arguments()
    level = logging.DEBUG if arguments.verbose else logging.INFO
    set_logger('telemetry.log', level)

    os.environ[DEVICES_FILE_ENV] = arguments.devices_file

    if arguments.command == 'poll':
        run_poll()
    elif arguments.command == 'pricing':
        save_day_prices(arguments.date)

    logger.info('Done!')

def add_switch_device(uri, name, ip, tuya_id, local_key, version):
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

def add_em_device(uri, name, model, ip, shelly_id):
    engine = create_engine(uri)
    Session = sessionmaker(engine)

    with Session() as session:    
        em = db_devices.ShellyEM(
            enabled=True,
            brand='Shelly',
            model=model,
            name=name,
            ip=ip,
            location=None,

            shelly_id=shelly_id
        )
        session.add(em)
        session.commit()

if __name__ == "__main__":
    main()