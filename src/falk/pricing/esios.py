"""ESIOS (REE) API client for hourly electricity spot prices (PVPC)."""

from __future__ import annotations

import logging

import pandas as pd


logger = logging.getLogger(__name__)


def get_daily_prices(date):
    url = f'http://api.esios.ree.es/archives/71/download?date_type=&start_date={date}&end_date={date}'
    df = pd.read_excel(url).fillna('')
    columns = df.iloc[:(len(df) - 24)].apply(lambda column: ' '.join(column), axis=0).str.replace('\n', ' ').str.strip().values
    df.columns = columns
    df = df[(len(df) - 24):].reset_index(drop=True)
    df['hour'] = df['Hora'] % 24
    df = df.set_index('hour').sort_index()
    # df.rename(columns={
    #     '':''
    # })

    return df
