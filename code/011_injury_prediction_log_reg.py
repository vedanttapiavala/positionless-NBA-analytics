import pandas as pd
from utils import test_model

df = pd.read_parquet('data/Player-Games with Travel and Injuries.parquet')
injury_features = ['home_player', 'positionless_index',
                   'rolling_7g_minutes', 'rolling_7g_points_per36',
                   'rolling_7g_three_pointers_attempted',
                   'rolling_7g_assists_per36',
                   'rolling_7g_field_goals_attempted',
                   'back_to_back',
                   'games_last_14d', 'distance_miles',
                   'tz_shift_hrs', 'rest_days']
df_injury_features = df[injury_features + ['gameDateTimeEst_player', 'injury_within_14d']]
or_df, auc, ap = test_model(df_injury_features.dropna())

print(or_df)

# ROC-AUC: 0.5993516
# PR-AUC: 0.257589
# Positionless index is still significant
print(auc, ap)