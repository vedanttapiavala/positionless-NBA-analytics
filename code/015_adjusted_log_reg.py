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
or_df, auc, ap = test_model(df_injury_features.dropna(),
                            {
                                'home_player': 'Game at Home',
                                'positionless_index': 'Positionless Index',
                                'rolling_7g_minutes': 'Minutes (Rolling: 7 Games)',
                                'rolling_7g_points_per36': 'Points per 36 Minutes (Rolling: 7 Games)',
                                'rolling_7g_three_pointers_attempted': '3PA (Rolling: 7 Games)',
                                'rolling_7g_assists_per36': 'Assists per 36 Minutes (Rolling: 7 Games)',
                                'rolling_7g_USG': 'Usage Rate (Rolling: 7 Games)',
                                'rolling_7g_three_pointers_made': '3PM (Rolling: 7 Games)',
                                'games_last_14d': 'Games Played over the Last 14 Days',
                                'distance_miles': 'Flight Distance (miles)',
                                'tz_shift_hrs': 'Timezone Shift',
                                'rest_days': 'Number of Rest Days',
                                'age': 'Age',
                                'height': 'Height (inches)',
                                'weight': 'Weight (lbs)'
                            })

print(or_df)

# ROC-AUC: 0.5850438285293822
# PR-AUC: 0.24625741885085772
# Positionless index is still significant
print(auc, ap)