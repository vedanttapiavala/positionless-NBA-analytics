import pandas as pd
import json
from pathlib import Path

df = pd.read_parquet('data/Player-Games_Injuries_Travel_Bio.parquet')

# Expanding parquet back further since we don't need injury data for the index explorer
pi_table_df = pd.read_parquet('data/Player-Games with Positionless Index.parquet')
pi_table_df['Name'] = pi_table_df['firstName'] + ' ' + pi_table_df['lastName']
positionless_index_table = pi_table_df[['Name', 'playerteamName', 'season', 'positionless_index']].copy()
positionless_index_table = positionless_index_table.drop_duplicates()

positionless_index_table = (
    pi_table_df[['Name', 'playerteamName', 'season', 'positionless_index']]
    .groupby(['Name', 'season'], as_index=False)
    .agg(
        playerteamName=('playerteamName', lambda x: ' / '.join(sorted(set(x)))),
        positionless_index=('positionless_index', 'mean'),
        games_played=('positionless_index', 'count')
    )
)

players_index_table = positionless_index_table.to_dict(orient="records")

with open("code/website/positionless-analytics/public/data/players_index_table.json", "w") as f:
    json.dump(players_index_table, f)

trend = (
    df.groupby('season_x')['positionless_index'].mean().reset_index()
)

positionless_timeseries = trend.to_dict(orient="records")

with open("code/website/positionless-analytics/public/data/positionless_over_time.json", "w") as f:
    json.dump(positionless_timeseries, f)

player_traj = (
    df.groupby(['Name', 'season_x'])['positionless_index']
    .mean()
    .reset_index()
)

traj_dict = {}

for _, row in player_traj.iterrows():
    p = row["Name"]
    traj_dict.setdefault(p, []).append({
        "season": int(row["season_x"]),
        "positionless_index": float(row["positionless_index"])
    })

with open("code/website/positionless-analytics/public/data/player_trajectories.json", "w") as f:
    json.dump(traj_dict, f)

df_player_games = pd.read_parquet('data/Processed Positions Data.parquet')
stats = {
    "player_games": int(len(df_player_games)),
    "players": df_player_games[["firstName", 'lastName']].value_counts().size,
    "structural_shift_year": 2016,
    "injury_odds_ratio": 1.170414,
}

with open("code/website/positionless-analytics/public/data/dashboard_aggregates.json", "w") as f:
    json.dump(stats, f)