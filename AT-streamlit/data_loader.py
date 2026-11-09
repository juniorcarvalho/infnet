from __future__ import annotations

import pandas as pd
from statsbombpy import sb


EVENT_COLUMNS = ["match_id", "minute", "event_type", "team_name", "player_name", "x", "y", "end_x", "end_y", "outcome", "pass_length", "pass_angle", "shot_xg", "event_id"]


def _empty_events() -> pd.DataFrame:
    return pd.DataFrame(columns=EVENT_COLUMNS)


def _as_name(value):
    return value.get("name") if isinstance(value, dict) else value


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _location_coordinates(location):
    if isinstance(location, (list, tuple)) and len(location) >= 2:
        return _as_float(location[0]), _as_float(location[1])
    return float("nan"), float("nan")


def _column_or_default(df: pd.DataFrame, column: str, default=None) -> pd.Series:
    if column in df.columns:
        return df[column]
    if isinstance(default, pd.Series):
        return default.reindex(df.index)
    return pd.Series([default] * len(df), index=df.index)


def load_competitions() -> pd.DataFrame:
    competitions = pd.DataFrame(sb.competitions())
    required = ["competition_id", "season_id", "competition_name", "country_name", "season_name"]
    for column in required:
        if column not in competitions:
            competitions[column] = None
    return competitions[required].dropna(subset=["competition_id", "season_id"]).drop_duplicates().sort_values(["competition_name", "season_name"], ascending=[True, False]).reset_index(drop=True)


def load_seasons(competition_id: int) -> pd.DataFrame:
    competitions = load_competitions()
    seasons = competitions.loc[competitions["competition_id"] == competition_id, ["season_id", "season_name"]]
    return seasons.drop_duplicates().sort_values("season_name", ascending=False).reset_index(drop=True)


def load_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    columns = ["match_id", "home_team", "away_team", "match_date", "competition_stage"]
    matches = pd.DataFrame(sb.matches(competition_id=competition_id, season_id=season_id))
    for column in columns:
        if column not in matches:
            matches[column] = None
    for column in ("home_team", "away_team"):
        matches[column] = matches[column].map(_as_name)
    return matches[columns].dropna(subset=["match_id"]).drop_duplicates().sort_values("match_date").reset_index(drop=True)


def load_match_events(match_id: int) -> pd.DataFrame:
    events = pd.DataFrame(sb.events(match_id=match_id))
    if "event_id" not in events:
        events["event_id"] = events.index.astype(str)
    return events


def normalize_events(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df is None or events_df.empty:
        return _empty_events()
    df = events_df.copy()
    result = pd.DataFrame(index=df.index)
    result["match_id"] = _column_or_default(df, "match_id", 0)
    result["minute"] = pd.to_numeric(_column_or_default(df, "minute", 0), errors="coerce").fillna(0).astype(int)
    result["event_type"] = _column_or_default(df, "type").map(_as_name).fillna("Evento")
    result["team_name"] = _column_or_default(df, "team").map(_as_name).fillna("Desconhecida")
    result["player_name"] = _column_or_default(df, "player").map(_as_name).fillna("Desconhecido")
    result[["x", "y"]] = pd.DataFrame(_column_or_default(df, "location").map(_location_coordinates).tolist(), index=df.index)
    result[["end_x", "end_y"]] = pd.DataFrame(_column_or_default(df, "pass_end_location").map(_location_coordinates).tolist(), index=df.index)
    pass_outcome = _column_or_default(df, "pass_outcome").map(_as_name)
    result["outcome"] = pass_outcome.where(pass_outcome.notna(), _column_or_default(df, "pass").map(_as_name))
    result.loc[result["event_type"].eq("Pass") & result["outcome"].isna(), "outcome"] = "Complete"
    shot_outcome = _column_or_default(df, "shot_outcome").map(_as_name)
    result.loc[result["event_type"].eq("Shot") & shot_outcome.notna(), "outcome"] = shot_outcome
    result["pass_length"] = pd.to_numeric(_column_or_default(df, "pass_length"), errors="coerce")
    result["pass_angle"] = pd.to_numeric(_column_or_default(df, "pass_angle"), errors="coerce")
    result["shot_xg"] = pd.to_numeric(_column_or_default(df, "shot_statsbomb_xg"), errors="coerce")
    event_ids = pd.Series(df.index.astype(str), index=df.index)
    result["event_id"] = _column_or_default(df, "event_id", event_ids).astype(str)
    return result[EVENT_COLUMNS]


def load_players(events_df: pd.DataFrame) -> list[str]:
    if events_df.empty or "player_name" not in events_df:
        return []
    return sorted(events_df.loc[events_df["player_name"] != "Desconhecido", "player_name"].dropna().unique().tolist())


def filter_events_by_player(events_df: pd.DataFrame, player_name: str) -> pd.DataFrame:
    if events_df.empty or player_name in (None, "", "Todos"):
        return events_df
    return events_df.loc[events_df["player_name"].eq(player_name)].copy()


def build_match_summary(events_df: pd.DataFrame) -> dict[str, float | int]:
    if events_df.empty:
        return {"total_goals": 0, "total_passes": 0, "successful_passes": 0, "total_shots": 0, "shot_conversion": 0.0, "event_count": 0}
    passes = events_df.loc[events_df["event_type"].eq("Pass")]
    shots = events_df.loc[events_df["event_type"].eq("Shot")]
    total_goals = int(shots["outcome"].eq("Goal").sum())
    total_shots = len(shots)
    successful_passes = int(passes["outcome"].eq("Complete").sum())
    return {"total_goals": total_goals, "total_passes": len(passes), "successful_passes": successful_passes, "total_shots": total_shots, "shot_conversion": round(total_goals / total_shots * 100, 1) if total_shots else 0.0, "event_count": len(events_df)}
