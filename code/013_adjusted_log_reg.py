import pandas as pd
from utils import test_model

df = pd.read_parquet('data/Player-Games_Injuries_Travel_Bio.parquet')
injury_features = ['home_player', 'positionless_index',
                   'rolling_7g_minutes', 'rolling_7g_points_per36',
                   'rolling_7g_three_pointers_attempted',
                   'rolling_7g_assists_per36',
                   'rolling_7g_USG', 'rolling_7g_three_pointers_made',
                   'games_last_14d', 'distance_miles',
                   'tz_shift_hrs', 'rest_days', 'age', 'height', 'weight']
df_injury_features = df[injury_features + ['gameDateTimeEst_player', 'injury_within_14d']]
or_df, auc, ap = test_model(df_injury_features.dropna())

print(or_df)

# ROC-AUC: 0.5862788615014256
# PR-AUC: 0.24860775785047556
# Positionless index is still significant
print(auc, ap)