import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def fetch_player_bio(name, idx, total):
    print(f'{idx}/{total}: {name}')
    manual_renaming = {
        'nene hilario': 'nene',
        'jianlian yi': 'yi jianlian',
        'kenyon martin jr.': 'kj martin',
        'brandon boston jr.': 'brandon boston',
        'matthew hurt': 'matt hurt',
        'rj nembhard jr.': 'ruben nembhard jr.'
    }
    if name in manual_renaming.keys():
        matches = players.find_players_by_full_name(manual_renaming[name])
    else:
        matches = players.find_players_by_full_name(name)
    if len(matches) == 0:
        print(f'{name} has no match in the NBA API database.')
        return None
    player_id = matches[0]['id']

    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        bio = info.get_data_frames()[0]
        time.sleep(2)

        return {
            'Name': name,
            'height': bio.loc[0, 'HEIGHT'],
            'weight': bio.loc[0, 'WEIGHT'],
            'birthdate': bio.loc[0, 'BIRTHDATE'],
            'experience': bio.loc[0, 'SEASON_EXP'],
        }
    except Exception as e:
        print(f'ERROR on {name}: {e}')
        return None

def height_inches(h):
    if pd.isna(h):
        return None
    feet, inches = h.split('-')
    return int(feet) * 12 + int(inches)

df = pd.read_parquet('data/Player-Games with Travel and Injuries.parquet')
unique_players = df['Name'].dropna().unique().tolist()

results_df = []
if os.path.exists('data/NBA Player Info.csv'):
    existing = pd.read_csv('data/NBA Player Info.csv')
    completed_players = set(existing['Name'].dropna())
    results_df = existing.to_dict('records')
    unique_players = [
        p for p in unique_players if p not in completed_players
    ]

total = len(unique_players)
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = []
    for idx, name in enumerate(unique_players):
        future = executor.submit(fetch_player_bio, name, idx+1, total)
        futures.append(future)
    completed = len(results_df)
    for future in as_completed(futures):
        result = future.result()
        if result is not None:
            results_df.append(result)
            completed+=1
            if completed % 50 == 0:
                pd.DataFrame(results_df).to_csv(
                    'data/NBA Player Info.csv',
                    index=False
                )
                print(f'Hit Checkpoint: {completed} players done.')

results_df = pd.DataFrame(results_df)
print(results_df.head())
results_df.to_csv('data/NBA Player Info.csv', index=False)

results_df['height'] = results_df['height'].apply(height_inches)
results_df['bmi'] = 703 * results_df['weight'] / (results_df['height'] ** 2)

results_df['birthdate'] = pd.to_datetime(results_df['birthdate'])
df = df.merge(results_df, on='Name', how='left')
df['age'] = (
    (df['gameDateTimeEst_player'] - df['birthdate']).dt.days / 365.25
)

results_df.to_csv('data/NBA Player Info.csv')

df.to_parquet('data/Player-Games_Injuries_Travel_Bio.parquet')