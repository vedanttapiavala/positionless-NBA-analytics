# positionless-NBA-analytics
Basketball analytics project examining the rise of positionless basketball in the NBA and exploring its link, if any, to injury risk.

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
## Exploratory Data Analysis of Player Positions
* 004_general_EDA.ipynb
    * **Inputs:** Processed positions data from 003_preprocessing.ipynb
    * **Function:** Exploratory data analysis
    * **Outputs:**
        * Heatmap indicating the general profiles of different positions
        * How certain features have changed over time for the five positions
        * Distribution of player positions in the dataset
        * Distribution of the five major stats (points, rebounds, assists, blocks, and steals) per position.
        * Position homogeneity over time using pairwise Euclidean distance
## Evaluating the Rise of Positionless Basketball
* 005_feature_selection.ipynb
    * **Inputs:** Processed positions data from 003_preprocessing.ipynb
    * **Function:** Select features for player position prediction using a networks-based algorithm aimed at lowering multicollinearity, followed by Boruta selection.
    * **Outputs:** A list of features selected for predicting player positions.
* 006_change_point_detection.ipynb
    * **Inputs:** Processed positions data from 003_preprocessing.ipynb. Important features selected by 005_feature_selection.ipynb.
    * **Function:** Predict player positions within each season's data using a LightGBM Classifier. Uses the PELT algorithm on smoothed and unsmoothed data to find when model performance changed over seasons. This drop in AUC is operationally defined to signal increasing positionless behavior across the association.
    * **Outputs:** Player-game level data, with a column for that player's positionless index (using entropy of the model's prediction).
## Scraping NBA Injuries
* 007_injury_list_scraper.py
    * **Inputs:** Base URL (https://hashtagbasketball.com/nba-injury)
    * **Function:** Scrapes injury keywords (search queries) that are potentially useful for Hastag Basketball's injury database.
    * **Outputs:** List of many of the most common NBA injuries with URLs within Hashtag Basketball's injury database (injury_url_suffixes.txt).
* 008_injury_data_scraper.py
    * **Inputs:** injury_url_suffixes_txt (see 002_injury_list_scraper.py).
    * **Function:** Searches Hashtag Basketball's NBA Injury Database for given url suffixes and appends them into a dataframe.
    * **Outputs:** List of NBA players' injuries from Hashtag Basketball's NBA Injury Database with columns including player, team, date injured, data returned, days missed, and the specific injury (injury_data.csv).
* 009_injury_data_merge_eda.ipynb
    * **Inputs:** Injury data (from 008_injury_data_scraper.py), player-games with positionless index (from 006_change_point_detection.ipynb).
    * **Function:** Merge injury data and the player-game observations and perform exploratory data analysis. Calculate rolling 3- and 7-game statistics and merge them into the parquet as well.
    * **Output:** Player-game observations with injury data.
* 010_injury_prediction_rolling_stats.ipynb
    * **Inputs:** Player-game observations with injury data (from 009_injury_data_merge_eda.ipynb).
    * **Function:** Create logistic regression models for 3- and 7-game rolling statistics for injury prediction and evaluate their area under the curve and average precision score.
    * **Output:** AUC and average precision scores for 3- and 7-game rolling stat models, alongside forest plots for injury risk.
## Scraping Travel Data
* 011_travel_data.py
    * **Inputs:** NBA API data for team games.
    * **Function:** Calculate how far NBA teams had to travel between games and how much rest they had.
    * **Output:** nba_travel.parquet, which contains travel-related information for NBA teams from 2010 onwards.
* 012_travel_data_merge.ipynb
    * **Inputs:** Player-game observations with injury data (from 009_injury_data_merge_eda.ipynb) and NBA team travel data (011_travel_data.py).
    * **Function:** Find travel information for each player and merge it into the player-game observations. Perform initial exploratory data analysis.
    * **Output:** Player-game observations with both injury and travel data.
* 013_injury_prediction_log_reg.py
    * **Inputs:** Player-game observations with travel and injury data (012_travel_data_merge.ipynb).
    * **Function:** Test a logistic regression model consisting of 7-game rolling statistics, travel-related data, and positionless index.
    * **Output:** AUC (0.5867) and average precision score (0.2465).
## Scraping Biographical Information
* 014_common_player_info.py
    * **Inputs:** Saved NBA player info (014_common_player_info.py) so far, if any. Player-game observations with injury and travel data.
    * **Function:** Use the NBA API to find height, weight, age, and years of experience for NBA players covered in the player-game observations with injury and travel data.
    * **Outputs:** Saved NBA player info so far and a parquet file consisting of player-game observations with travel, injury, and biographical information.
* 015_adjusted_log_reg.py
    * **Inputs:** Player-game observations with travel, injury, and biographical information (014_common_player_info.py)
    * **Function:** Test a logistic regression model similar to in 013_injury_prediction_log_reg.py but adding biographical information.
    * **Output:** AUC (0.5850) and average precision score (0.2463).
## Predicting Injuries
* 016_injury_prediction.ipynb
    * **Inputs:** Player-game observations with travel, injury, and biographical information (014_common_player_info.py)
    * **Function:** Selects features and evaluates untuned machine learning models in predicting injuries. Then, a CatBoost classifier is used to predict injuries, and the following metrics are calculated: AUC, average precision, precision at top-k%, and Brier calibration score. SHAP values are also calculated.
    * **Output:** The above scores, a SHAP summary plot, a SHAP dependence plot on positionless index, and decile plots for injury risk at different deciles of positionless index. 
## Interaction Term Analyses
* 017_log_reg_interactions.ipynb
    * **Inputs:** Player-game observations with travel, injury, and biographical information (014_common_player_info.py)
    * **Function:** Create interaction terms of variables with the z-score normalized positionless index. 
    * **Output:** A forest plot of odds ratios for interaction terms using positionless index.
## Sensitivity Analyses
* 018_injury_predict_sensitivity_analyses.ipynb
    * **Inputs:** Player-game observations with travel, injury, and biographical information.
    * **Function:** Train a CatBoost classifier on 7-day and 30-day injury windows rather than the earlier 14-day window.
    * **Output:** Most important features in terms of SHAP values.
* 019_change_point_euclidean.ipynb
    * **Inputs:** Processed positions data including player and team-level data.
    * **Function:** Change-point detection using PELT of mean pairwise Euclidean distance between positions.
    * **Output:** Year of change for mean pairwise Euclidean distance between positions.