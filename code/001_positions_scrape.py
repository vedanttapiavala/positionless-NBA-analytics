import pandas as pd
import requests
import time
from io import StringIO

all_positions = []
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive"
}

for year in range(1974, 2027):
    try:
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}_totals.html"

        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url)
        response.encoding = response.apparent_encoding
        df = pd.read_html(StringIO(response.text))[0]

        time.sleep(3)
        df = df[df["Player"] != "Player"]

        df = df[["Player", "Pos", "Team"]]
        df["Season"] = year

        if "TOT" in df["Team"].values:
            tot_players = df[df["Team"] == "TOT"]["Player"].unique()
            df = df[
                (df["Team"] == "TOT") |
                (~df["Player"].isin(tot_players))
            ]

        all_positions.append(df)
        df.to_csv(
            f'data/Player Positions Data/Player Positions_{year}.csv',
            index=False,
            encoding="utf-8-sig"
        )
        print(f"Done: {year}")

    except Exception as e:
        print(f"Failed: {year}", e)

all_positions = pd.concat(all_positions, ignore_index=True)
all_positions.to_csv(
    'data/Player Positions.csv',
    index=False,
    encoding="utf-8-sig"
)