"""ESIOS (REE) API client for hourly electricity spot prices (PVPC)."""

from __future__ import annotations
import datetime
from zoneinfo import ZoneInfo

import logging

import requests
import pandas as pd
from sqlalchemy import select

from falk.config import load_config
from falk.db import session_factory
from falk.models.pricing import EsiosPrice


logger = logging.getLogger(__name__)


def get_day_prices(dt=None):
    dt = dt if dt else datetime.datetime.now()
    #url = f'http://api.esios.ree.es/archives/71/download?date_type=&start_date={date}&end_date={date}&locale=es'
    url = f'http://api.esios.ree.es/archives/71/download?start_date={dt.isoformat()}'
    df = pd.read_excel(url).fillna('')
    columns = df.iloc[:(len(df) - 24)].apply(lambda column: ' '.join(column), axis=0).str.replace('\n', ' ').str.strip().values
    df.columns = columns
    df = df[(len(df) - 24):].reset_index(drop=True)
    df['hour'] = df['Hora'] 
    df = df.set_index('hour').sort_index()
    df['dt_utc'] = pd.to_datetime(df['Hora Día']).dt.tz_localize('UTC') + pd.Series(datetime.timedelta(hours=hour) for hour in df.index)
    df['dt_local'] =  df['dt_utc'].dt.tz_convert('Europe/Madrid')

    df['price_kWh'] = df[df.columns[4]] / 1000
    return df

def get_day_prices_v2(dt=None):
    dt = dt if dt else datetime.datetime.now().date()
    response = requests.get('https://api.esios.ree.es/indicators/1001')
    response.raise_for_status()

    data = response.json()
    df = pd.DataFrame(data['indicator']['values'])
    df = df[df['geo_id'] == 8741]
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
    df = df.sort_values('datetime').reset_index(drop=True)
    df['price_kWh'] = df['value'] / 1000

    df = df.rename(columns={'datetime': 'tz_local', 'datetime_utc': 'tz_utc'})
    return df[['tz_local', 'tz_utc',  'price_kWh']]

def get_day_prices_with_token(token, dt=None):
    dt = dt if dt else datetime.datetime.now().date()
    headers = {'x-api-key': token, 'Accept': 'application/json'}

    url = 'https://api.esios.ree.es/indicators/1001'
    params = {
        'start_date': f'{dt}T00:00:00',
        'end_date':   f'{dt}T23:59:59',
        'geo_ids[]':  '8741'  # Península
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    
    df = pd.DataFrame(data['indicator']['values'])
    df = df[df['geo_id'] == 8741]
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
    df = df.sort_values('datetime').reset_index(drop=True)
    df['price_kWh'] = df['value'] / 1000

    df = df.rename(columns={'datetime': 'tz_local', 'datetime_utc': 'tz_utc'})
    return df[['tz_local', 'tz_utc',  'price_kWh']]


def get_price(df, dt=None, tz=None):
    dt = dt if dt else datetime.datetime.now()
    dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour)

    # Uses stdlib zoneinfo (replaced pytz, which was never a declared dependency).
    tz = tz if tz else ZoneInfo('Europe/Madrid')
    dt_aware = dt.replace(tzinfo=tz)

    return df.loc[dt_aware.hour]


def save_day_prices(date: datetime.date | None = None) -> int:
    """Fetch and persist PVPC hourly prices (ESIOS indicator 1001) for one day.

    Args:
        date: Date to fetch. Defaults to today.

    Returns:
        Number of new rows inserted (rows already present are skipped).
    """
    token = load_config()["esios"]["token"]
    date = date if date else (datetime.datetime.today().date() + datetime.timedelta(days=1))
    df = get_day_prices_with_token(token, date)

    Session = session_factory()
    with Session() as session:
        rows = [
            EsiosPrice(
                datetime_utc=row['tz_utc'].tz_localize(None).to_pydatetime(),
                datetime_local=row['tz_local'].tz_localize(None).to_pydatetime(),
                price_kwh=float(row['price_kWh']),
            )
            for _, row in df.iterrows()
        ]

        utcs = [r.datetime_utc for r in rows]
        existing = set(
            session.scalars(
                select(EsiosPrice.datetime_utc).where(
                    EsiosPrice.datetime_utc.in_(utcs)
                )
            )
        )
        new_rows = [r for r in rows if r.datetime_utc not in existing]
        if not new_rows:
            logger.info('ESIOS prices already stored, skipping')
            return 0

        session.add_all(new_rows)
        session.commit()

    logger.info(f'Stored {len(new_rows)} ESIOS price rows')
    return len(new_rows)
