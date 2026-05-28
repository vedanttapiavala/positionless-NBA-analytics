# positionless-NBA-analytics
Basketball analytics project examining the rise of positionless basketball in the NBA and exploring its link, if any, to injury risk.

## Scraping NBA Injuries
A list of NBA injuries from 2010 onwards was scraped from Hashtag Baskebtall's NBA Injury Database.

### Files
All files referenced in this section are in code/injury_scraping.
* 001_injury_list_scraper.py
    * **Inputs:** Base URL (https://hashtagbasketball.com/nba-injury)
    * **Function:** Scrapes injury keywords (search queries) that are potentially useful for Hastag Basketball's injury database.
    * **Outputs:** List of many of the most common NBA injuries with URLs within Hashtag Basketball's injury database (injury_url_suffixes.txt).
* 002_injury_data_scraper.py
    * **Inputs:** injury_url_suffixes_txt (see 001_injury_list_scraper.py).
    * **Function:** Searches Hashtag Basketball's NBA Injury Database for given url suffixes and appends them into a dataframe.
    * **Outputs:** List of NBA players' injuries from Hashtag Basketball's NBA Injury Database with columns including player, team, date injured, data returned, days missed, and the specific injury (injury_data.csv).

## Scraping Player Positions
* 001_positions_scrape.py
    * **Inputs:** None
    * **Function:** Scrapes Basketball Reference's season-level overviews for players' positions.
    * **Outputs:** Players' primary positions for each season from 1974-2026 (data/Player Positions Data). 
* 002_season_data_cleaning.ipynb
    * **Inputs:** data/Player Positions Data from 001_positions_scrape.py
    * **Function:** Cleans players' primary position data.
    * **Output:** A cleaned dataset of players' primary positions for each season (data/Player Positions.parquet).
* 003_preprocessing.ipynb
    * **Inputs:** 
        * PlayerStatistics (downloaded from [Kaggle](http://kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores))
        * TeamStatistics (downloaded from [Kaggle](http://kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores))
        * Player Positions (from 002_season_data_cleaning.ipynb)
        * Extra Player Positions - manual scrape of players who played playoff games but no regular season games in a season, meaning they are not in the scraped Basketball Reference pages.
        * Manual Player Renaming - aligning player names between sources
    * **Function:** Merges player, team, and position data
    * **Outputs:** Processed positions data including player and team-level data.