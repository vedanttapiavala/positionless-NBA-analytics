import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://hashtagbasketball.com"
SUFFIXES_FILE = "data/injury_url_suffixes.txt"

EXPECTED_HEADERS = {"PLAYER", "TEAM", "INJURED ON", "RETURNED", "DAYS MISSED"}

def scrape_injury_page(suffix: str) -> pd.DataFrame:
    url = BASE_URL + suffix
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Get the page title
    title_el = soup.find(id="ContentPlaceHolder1_FormView1_NOTESLabel")
    title = title_el.get_text(strip=True) if title_el else suffix

    rows = []
    for tr in soup.select("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if not cells:
            continue
        # Skip rows that are just repeating the header
        if EXPECTED_HEADERS.issubset(set(cells)):
            continue
        rows.append(cells)

    if not rows:
        print(f"  [!] No rows found for {url}")
        return pd.DataFrame()

    # Use first non-header row to detect column count
    # Find the actual header row (if present as first row)
    first = rows[0]
    if EXPECTED_HEADERS.issubset(set(first)):
        cols = first
        data = rows[1:]
    else:
        cols = ["PLAYER", "TEAM", "INJURED ON", "RETURNED", "DAYS MISSED"]
        data = rows

    # Filter to rows with the right number of columns
    data = [r for r in data if len(r) == len(cols)]

    df = pd.DataFrame(data, columns=cols)
    df["Injury"] = title
    return df

with open(SUFFIXES_FILE) as f:
    suffixes = [line.strip() for line in f if line.strip()]

all_dfs = []
for suffix in suffixes:
    print(f"Scraping: {suffix}")
    try:
        df = scrape_injury_page(suffix)
        if not df.empty:
            all_dfs.append(df)
            print(f"  -> {len(df)} rows | Injury: {df['Injury'].iloc[0]}")
    except Exception as e:
        print(f"  [ERROR] {suffix}: {e}")

combined = pd.concat(all_dfs, ignore_index=True)
combined.to_csv("data/injury_data.csv", index=False)
print(f"\nDone! {len(combined)} total rows saved to injury_data.csv")
print(combined.head())