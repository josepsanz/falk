"""ESIOS (REE) API client for hourly electricity spot prices (PVPC)."""

from __future__ import annotations
import datetime

import logging

import pandas as pd
from sqlalchemy import func, select

from falk.db import session_factory
from falk.models.pricing import EsiosPrice


logger = logging.getLogger(__name__)


def get_day_prices(date=None):
    date = date if date else datetime.datetime.now().date()
    url = f'http://api.esios.ree.es/archives/71/download?date_type=&start_date={date}&end_date={date}'
    df = pd.read_excel(url).fillna('')
    columns = df.iloc[:(len(df) - 24)].apply(lambda column: ' '.join(column), axis=0).str.replace('\n', ' ').str.strip().values
    df.columns = columns
    df = df[(len(df) - 24):].reset_index(drop=True)
    df['hour'] = df['Hora'] % 24
    df = df.set_index('hour').sort_index()

    df['price_kWh'] = df[df.columns[4]] / 1000
    return df


def save_day_prices(date: datetime.date | None = None) -> int:
    """Fetch and persist PVPC hourly prices for one day.

    Args:
        date: Date to fetch. Defaults to today.

    Returns:
        Number of rows inserted (0 if already present, skips silently).
    """
    df = get_day_prices(date)
    pricing_date = pd.Timestamp(df.iloc[0, 0]).date()

    Session = session_factory()
    with Session() as session:
        existing = session.scalar(
            select(func.count()).where(EsiosPrice.date == pricing_date)
        )
        if existing:
            logger.info("ESIOS prices for %s already stored, skipping", pricing_date)
            return 0

        def _f(v: object) -> float:
            return float(v) if v != "" else 0.0

        prices = [
            EsiosPrice(
                date=pricing_date,
                hour=int(hour),
                tariff=str(row.iloc[2]),
                period=int(row.iloc[3]),
                feu=_f(row.iloc[4]),
                teu=_f(row.iloc[5]),
                tcu=_f(row.iloc[6]),
                perd=_f(row.iloc[7]),
                perd_std=_f(row.iloc[8]),
                cp=_f(row.iloc[9]),
                oc=_f(row.iloc[10]),
                os_fin=_f(row.iloc[11]),
                om_fin=_f(row.iloc[12]),
                cap=_f(row.iloc[13]),
                interrup=_f(row.iloc[14]),
                renew_bal=_f(row.iloc[15]),
                ccv_rcv=_f(row.iloc[16]),
                ccv_rfe=_f(row.iloc[17]),
                ccv_rmr=_f(row.iloc[18]),
                ccv_ru=_f(row.iloc[19]),
                sah=_f(row.iloc[20]),
                adj_other=_f(row.iloc[21]),
                dev_cost=_f(row.iloc[22]),
                band_cost=_f(row.iloc[23]),
                dem_resp=_f(row.iloc[24]),
                tech_rest=_f(row.iloc[25]),
                pmh=_f(row.iloc[26]),
                intra1=_f(row.iloc[27]),
                spot=_f(row.iloc[28]),
                tah=_f(row.iloc[29]),
                futures=_f(row.iloc[30]),
                fch=_f(row.iloc[31]),
                profile=_f(row.iloc[32]),
                price_kwh=_f(row.iloc[33]),
            )
            for hour, row in df.iterrows()
        ]

        session.add_all(prices)
        session.commit()

    logger.info("Stored %d ESIOS price rows for %s", len(prices), pricing_date)
    return len(prices)
