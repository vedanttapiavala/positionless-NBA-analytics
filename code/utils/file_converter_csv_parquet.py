# Converts csv files into parquets for more compressed storage

import pandas as pd

df = pd.read_csv('PlayerStatistics.csv', dtype={
        'numMinutes': 'string',
        'comment': 'string',
    },  usecols=lambda c: c not in ['gameLabel', 'gameSubLabel', 'seriesGameNumber', 'startingPosition'])

df.to_parquet('PlayerStatistics.parquet', compression='snappy')

df_parquet = pd.read_parquet('PlayerStatistics.parquet')

print(df.shape, df_parquet.shape)
print(df.columns.equals(df_parquet.columns))

print(len(df), len(df_parquet))