"""
nba_travel.py
=============
Python port of the {airball} R package's nba_travel() function.

Computes schedule and travel metrics for NBA teams across seasons 2010–2026,
ready to merge with a player-level DataFrame on (player_team, game_date).

Dependencies:
    pip install nba_api geopy timezonefinder pytz pandas numpy requests

Usage:
    from nba_travel import build_team_travel

    # Build full 2010–2026 dataset (takes ~10–20 min due to API rate limits)
    df = build_team_travel(start_season=2010, end_season=2026)
    df.to_parquet("nba_travel_2010_2026.parquet", index=False)

    # Merge with your player DataFrame
    player_df = player_df.merge(
        df,
        left_on=["player_team_name", "game_date"],
        right_on=["team_name", "game_date"],
        how="left"
    )
"""

# The following code was mostly written via Claude, as was allowed in our course

import time
import logging
from datetime import datetime, date
from typing import Optional

import numpy as np
import pandas as pd
import pytz
from geopy.distance import geodesic
from timezonefinder import TimezoneFinder

from nba_api.stats.endpoints import leaguegamelog
from nba_api.stats.static import teams as nba_teams_static

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Arena coordinates  (lat, lon)
# Covers relocations, new arenas, and name changes across 2010–2026.
# Key: NBA team abbreviation as used in the game log API.
# ---------------------------------------------------------------------------

# Map full team names (as returned by game log) to abbreviations
# and canonical display names. Built dynamically but supplemented below.
TEAM_NAME_OVERRIDES: dict[str, str] = {
    "LA Clippers": "LAC",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "New Jersey Nets": "NJN",
    "Brooklyn Nets": "BKN",
    "New Orleans Hornets": "NOH",
    "New Orleans/Oklahoma City Hornets": "NOK",
    "Charlotte Bobcats": "CHA",
    "Charlotte Hornets": "CHA",
    "Seattle SuperSonics": "SEA",
    "Oklahoma City Thunder": "OKC",
    "New Orleans Pelicans": "NOP",
}

_all_nba_teams = nba_teams_static.get_teams()
_abbr_map_static = {t["full_name"]: t["abbreviation"] for t in _all_nba_teams}

stadium_coords = pd.read_csv('data/stadiums.csv')
stadium_coords = stadium_coords[stadium_coords['League'] == 'NBA']
# Need to individually change the Clippers arena coords because this dataset
# is before the move to the Intuit Dome

# Build ARENA_COORDS: abbrev → (lat, lon)
# Uses nba_api to resolve abbreviation; falls back to first 3 chars
ARENA_COORDS: dict[str, tuple[float, float]] = {}
for _, row in stadium_coords.iterrows():
    team_full = row["Team"]
    abbrev = (
        TEAM_NAME_OVERRIDES.get(team_full)          # manual override first
        or _abbr_map_static.get(team_full)           # nba_api static lookup
        or team_full[:3].upper()                     # last resort
    )
    ARENA_COORDS[abbrev] = (float(row["Lat"]), float(row["Long"]))

# Historical/relocated teams not in current stadiums.csv
ARENA_COORDS_HISTORICAL: dict[str, tuple[float, float]] = {
    "NJN": (40.813056, -74.069722),   # Nets pre-Brooklyn (Prudential Center)
    "NOH": (29.948889, -90.082222),   # New Orleans Hornets
    "NOK": (30.300000, -89.750000),   # NO/OKC Hornets (Katrina era)
    "SEA": (47.622222, -122.354167),  # Seattle SuperSonics,
    "LAC": (33.9451, -118.3431),  # Intuit Dome
}
ARENA_COORDS.update(ARENA_COORDS_HISTORICAL)

# ---------------------------------------------------------------------------
# Helper: season string  2010 → "2010-11"
# ---------------------------------------------------------------------------

def _season_str(year: int) -> str:
    return f"{year}-{str(year + 1)[-2:]}"


# ---------------------------------------------------------------------------
# Helper: team abbreviation lookup
# ---------------------------------------------------------------------------

def _abbrev(team_name: str, abbr_map: dict[str, str]) -> str:
    if team_name in TEAM_NAME_OVERRIDES:
        return TEAM_NAME_OVERRIDES[team_name]
    return abbr_map.get(team_name, team_name[:3].upper())


# ---------------------------------------------------------------------------
# Helper: timezone offset (hours from UTC) for a coordinate on a given date
# ---------------------------------------------------------------------------

_tf = TimezoneFinder()


def _tz_offset(lat: float, lon: float, dt: date) -> tuple[str, float]:
    """Returns (tz_name, utc_offset_hours)."""
    tz_name = _tf.timezone_at(lat=lat, lng=lon) or "America/New_York"
    tz = pytz.timezone(tz_name)
    offset_hrs = tz.utcoffset(datetime(dt.year, dt.month, dt.day)).total_seconds() / 3600
    return tz_name, offset_hrs


# ---------------------------------------------------------------------------
# Core fetch: pull team game logs for one season
# ---------------------------------------------------------------------------

def _fetch_season_logs(season_year: int, phase: str = "RS", retries: int = 5) -> pd.DataFrame:
    """
    Fetch team game logs from the NBA Stats API for one season.

    phase: "RS" = Regular Season, "PO" = Playoffs, "RS+PO" = both
    Returns a raw DataFrame with columns from leaguegamelog.
    """
    season_type_map = {
        "RS": ["Regular Season"],
        "PO": ["Playoffs"],
        "RS+PO+PI": ["Regular Season", "Playoffs", 'PlayIn'],
    }
    season_types = season_type_map.get(phase, ["Regular Season"])
    season = _season_str(season_year)
    frames = []

    for stype in season_types:
        if stype == "PlayIn" and season_year < 2020:
            continue
        for attempt in range(retries):
            try:
                log.info(f"Fetching {season} {stype}...")
                gl = leaguegamelog.LeagueGameLog(
                    season=season,
                    season_type_all_star=stype,
                    player_or_team_abbreviation="T",
                    timeout=60,
                )
                df = gl.get_data_frames()[0]
                df["SEASON_TYPE"] = "RS" if stype == "Regular Season" else "PO"
                frames.append(df)
                time.sleep(1.0)  # be polite to the API
                break
            except Exception as e:
                wait = 2 ** attempt
                log.warning(f"Attempt {attempt+1} failed for {season} {stype}: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        else:
            log.error(f"All retries exhausted for {season} {stype}. Skipping.")

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ---------------------------------------------------------------------------
# Core compute: travel metrics for one team's sorted game log
# ---------------------------------------------------------------------------

def _compute_team_travel(
    team_games: pd.DataFrame,
    team_name: str,
    abbrev: str,
    home_coords: tuple[float, float],
    flight_speed: float = 550.0,
    return_home_days: int = 3,
) -> pd.DataFrame:
    """
    Given a team's games sorted by date, compute all travel metrics row by row.

    Returns a DataFrame with one row per game.
    """
    records = []
    prev_city_coords = home_coords  # start of season = at home
    prev_game_date: Optional[date] = None

    for _, row in team_games.iterrows():
        game_date = pd.to_datetime(row["GAME_DATE"]).date()
        matchup: str = row["MATCHUP"]  # e.g. "BOS vs. BKN" or "BOS @ BKN"
        is_home = "vs." in matchup
        wl = row.get("WL", "")
        season_type = row.get("SEASON_TYPE", "RS")

        # Opponent abbreviation
        parts = matchup.replace("@", "vs.").split("vs.")
        opponent_abbr = parts[1].strip() if len(parts) > 1 else ""

        # Destination coordinates
        if is_home:
            dest_coords = home_coords
            location_label = "Home"
        else:
            dest_coords = ARENA_COORDS.get(opponent_abbr, home_coords)
            location_label = "Away"

        # ---- Return-home leg -----------------------------------------------
        # If two consecutive away games are separated by >= return_home_days,
        # insert a virtual return-home flight so mileage is more realistic.
        return_home_flag = "No"
        effective_origin = prev_city_coords

        if (
            prev_game_date is not None
            and not is_home
            and prev_city_coords != home_coords
        ):
            days_gap = (game_date - prev_game_date).days
            if days_gap >= return_home_days:
                return_home_flag = "Yes"
                effective_origin = home_coords  # flew home first

        # ---- Distance & direction ------------------------------------------
        dist_miles = geodesic(effective_origin, dest_coords).miles

        # East/West direction (based on longitude delta)
        lon_delta = dest_coords[1] - effective_origin[1]
        if abs(lon_delta) < 0.5:
            direction = "N/A"
        elif lon_delta > 0:
            direction = "East"
        else:
            direction = "West"

        # ---- Route label ---------------------------------------------------
        if dist_miles < 10:
            route = "No Travel"
        else:
            route = f"{_city_name(effective_origin)} → {_city_name(dest_coords)}"

        # ---- Time zones ----------------------------------------------------
        tz_origin_name, tz_origin_off = _tz_offset(*effective_origin, game_date)
        tz_dest_name, tz_dest_off = _tz_offset(*dest_coords, game_date)
        tz_shift = tz_dest_off - tz_origin_off  # positive = traveling East

        # ---- Flight time ---------------------------------------------------
        flight_minutes = (dist_miles / flight_speed) * 60 if dist_miles > 0 else 0
        flight_h = int(flight_minutes // 60)
        flight_m = int(flight_minutes % 60)
        flight_time_str = f"{flight_h}h {flight_m:02d}m" if dist_miles > 10 else "0h 00m"

        # ---- Rest days -----------------------------------------------------
        rest_days = (game_date - prev_game_date).days - 1 if prev_game_date else None

        # ---- Week & month --------------------------------------------------
        week_num = game_date.isocalendar()[1]

        records.append({
            "season": _season_str(int(row.get("SEASON_ID", "22010")[-4:]) - 1)
                      if "SEASON_ID" in row else "unknown",
            "season_type": season_type,
            "team_name": team_name,
            "team_abbrev": abbrev,
            "game_id": row.get("GAME_ID", ""),
            "game_date": game_date,
            "month": game_date.strftime("%b"),
            "week": week_num,
            "opponent_abbrev": opponent_abbr,
            "location": location_label,
            "wl": wl,
            # Travel
            "origin_lat": effective_origin[0],
            "origin_lon": effective_origin[1],
            "dest_lat": dest_coords[0],
            "dest_lon": dest_coords[1],
            "distance_miles": round(dist_miles, 1),
            "route": route,
            "direction_ew": direction,
            "return_home": return_home_flag,
            # Time zones
            "timezone_origin": tz_origin_name,
            "timezone_dest": tz_dest_name,
            "tz_shift_hrs": tz_shift,
            # Rest
            "rest_days": rest_days,
            # Flight
            "flight_time": flight_time_str,
            "flight_minutes": round(flight_minutes, 1),
        })

        prev_city_coords = dest_coords
        prev_game_date = game_date

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Reverse-lookup city name from coords  (simple nearest-arena lookup)
# ---------------------------------------------------------------------------

def _city_name(coords: tuple[float, float]) -> str:
    """Return a short city label for a coordinate pair."""
    _reverse: dict[tuple[float, float], str] = {v: k for k, v in ARENA_COORDS.items()}
    if coords in _reverse:
        return _reverse[coords]
    # Fallback: find nearest
    best, best_dist = "?", 9999.0
    for abbr, c in ARENA_COORDS.items():
        d = geodesic(coords, c).miles
        if d < best_dist:
            best_dist, best = d, abbr
    return best


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_team_travel(
    start_season: int = 2010,
    end_season: int = 2026,
    teams: Optional[list[str]] = None,
    phase: str = "RS",
    flight_speed: float = 550.0,
    return_home_days: int = 3,
    sleep_between_seasons: float = 2.0,
) -> pd.DataFrame:
    """
    Build a team-level travel metrics DataFrame for every game in the
    specified season range.

    Parameters
    ----------
    start_season : int
        First season year (e.g. 2010 → "2010-11"). Default 2010.
    end_season : int
        Last season year (e.g. 2026 → "2025-26"). Default 2026.
    teams : list[str], optional
        Filter to specific team names (full NBA names, e.g. "Boston Celtics").
        If None, all teams are included.
    phase : str
        "RS" (Regular Season), "PO" (Playoffs), or "RS+PO+PI" (both + play-in).
    flight_speed : float
        Assumed aircraft speed in mph for flight time estimation. Default 550.
    return_home_days : int
        If two consecutive away games are >= this many days apart, a return
        home leg is assumed. Mirrors airball's return_home parameter.
    sleep_between_seasons : float
        Seconds to sleep between season API calls to avoid rate-limiting.

    Returns
    -------
    pd.DataFrame
        One row per team per game with travel metrics. Merge with your player
        DataFrame on ("team_name", "game_date") or ("team_abbrev", "game_date").
    """
    # Build abbreviation map from nba_api static data
    all_nba_teams = nba_teams_static.get_teams()
    abbr_map = {t["full_name"]: t["abbreviation"] for t in all_nba_teams}

    all_frames: list[pd.DataFrame] = []

    for season_year in range(start_season, end_season + 1):
        log.info(f"=== Season {_season_str(season_year)} ===")
        raw = _fetch_season_logs(season_year, phase=phase)
        if raw.empty:
            log.warning(f"No data for {_season_str(season_year)}, skipping.")
            continue

        # Attach canonical season string
        raw["season"] = _season_str(season_year)

        # Filter teams if requested
        if teams:
            raw = raw[raw["TEAM_NAME"].isin(teams)]

        # Process each team
        for team_name, team_games in raw.groupby("TEAM_NAME"):
            abbrev = _abbrev(str(team_name), abbr_map)
            if abbrev not in ARENA_COORDS:
                log.warning(f"No arena coords for {team_name} ({abbrev}), skipping.")
                continue

            home_coords = ARENA_COORDS[abbrev]
            team_games_sorted = team_games.sort_values("GAME_DATE").copy()

            team_df = _compute_team_travel(
                team_games=team_games_sorted,
                team_name=str(team_name),
                abbrev=abbrev,
                home_coords=home_coords,
                flight_speed=flight_speed,
                return_home_days=return_home_days,
            )
            all_frames.append(team_df)

        time.sleep(sleep_between_seasons)

    if not all_frames:
        return pd.DataFrame()

    result = pd.concat(all_frames, ignore_index=True)
    result["game_date"] = pd.to_datetime(result["game_date"])
    result = result.sort_values(["season", "team_name", "game_date"]).reset_index(drop=True)

    log.info(f"Done. {len(result):,} team-game rows across {result['season'].nunique()} seasons.")
    return result


# ---------------------------------------------------------------------------
# Convenience: merge travel metrics onto a player DataFrame
# ---------------------------------------------------------------------------

def merge_player_travel(
    player_df: pd.DataFrame,
    travel_df: pd.DataFrame,
    player_team_col: str = "player_team_name",
    player_date_col: str = "game_date",
) -> pd.DataFrame:
    """
    Left-join travel metrics onto a player-level DataFrame.

    Parameters
    ----------
    player_df : pd.DataFrame
        Must contain columns for player team name and game date.
    travel_df : pd.DataFrame
        Output of build_team_travel().
    player_team_col : str
        Column in player_df with the full team name (e.g. "Boston Celtics").
    player_date_col : str
        Column in player_df with the game date (will be coerced to date).

    Returns
    -------
    pd.DataFrame
        player_df with travel columns appended.
    """
    travel_cols = [
        "team_name", "game_date",
        "season", "season_type", "team_abbrev",
        "location", "opponent_abbrev",
        "distance_miles", "route", "direction_ew", "return_home",
        "timezone_dest", "tz_shift_hrs",
        "rest_days",
        "flight_time", "flight_minutes",
        "dest_lat", "dest_lon",
    ]
    travel_sub = travel_df[travel_cols].copy()
    travel_sub["game_date"] = pd.to_datetime(travel_sub["game_date"])

    player_df = player_df.copy()
    player_df[player_date_col] = pd.to_datetime(player_df[player_date_col])

    merged = player_df.merge(
        travel_sub,
        left_on=[player_team_col, player_date_col],
        right_on=["team_name", "game_date"],
        how="left",
        suffixes=("", "_travel"),
    )
    # Drop duplicate key columns added by merge
    if "game_date_travel" in merged.columns:
        merged = merged.drop(columns=["game_date_travel"])
    if "team_name" in merged.columns and player_team_col != "team_name":
        merged = merged.drop(columns=["team_name"])

    return merged


# ---------------------------------------------------------------------------
# Run block — edit parameters here and just hit Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # ── PARAMETERS ──────────────────────────────────────────────────────────
    START_SEASON     = 2010          # change to 2010 for full pull
    END_SEASON       = 2026          # change to 2026 for full pull
    TEAMS            = None  # None = all teams
    PHASE            = "RS+PO+PI"          # "RS", "PO", or "RS+PO"
    FLIGHT_SPEED     = 550.0         # mph
    RETURN_HOME_DAYS = 3
    OUTPUT_FILE      = "data/nba_travel.parquet" 
    # ────────────────────────────────────────────────────────────────────────

    df = build_team_travel(
        start_season=START_SEASON,
        end_season=END_SEASON,
        teams=TEAMS,
        phase=PHASE,
        flight_speed=FLIGHT_SPEED,
        return_home_days=RETURN_HOME_DAYS,
    )

    if OUTPUT_FILE.endswith(".csv"):
        df.to_csv(OUTPUT_FILE, index=False)
    else:
        df.to_parquet(OUTPUT_FILE, index=False)

    print(f"\nSaved {len(df):,} rows to {OUTPUT_FILE}")
    print(df.to_string())