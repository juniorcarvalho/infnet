from __future__ import annotations

import pandas as pd
import streamlit as st

from data_loader import (
    filter_events_by_player,
    load_competitions,
    load_match_events,
    load_matches,
    load_players,
    load_seasons,
    normalize_events,
)


@st.cache_data(show_spinner=False)
def get_competitions() -> pd.DataFrame:
    return load_competitions()


@st.cache_data(show_spinner=False)
def get_seasons(competition_id: int) -> pd.DataFrame:
    return load_seasons(competition_id)


@st.cache_data(show_spinner=False)
def get_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    return load_matches(competition_id, season_id)


@st.cache_data(show_spinner=False)
def get_events(match_id: int) -> pd.DataFrame:
    return normalize_events(load_match_events(match_id))


def split_event_sets(events_df: pd.DataFrame, filters: dict, event_limit: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna o recorte analítico inteiro e a amostra limitada para exibição."""
    filtered = events_df.copy()
    if filtered.empty:
        return filtered, filtered
    minute_start = int(filters.get("minute_start", filtered["minute"].min()))
    minute_end = int(filters.get("minute_end", filtered["minute"].max()))
    filtered = filtered.loc[filtered["minute"].between(min(minute_start, minute_end), max(minute_start, minute_end))]
    text_query = str(filters.get("text_query", "")).strip().casefold()
    if text_query:
        searchable = filtered[["event_type", "team_name", "player_name"]].fillna("").astype(str).agg(" ".join, axis=1).str.casefold()
        filtered = filtered.loc[searchable.str.contains(text_query, regex=False)]
    selected_types = filters.get("selected_types")
    if selected_types is not None:
        filtered = filtered.loc[filtered["event_type"].isin(selected_types)]
    filtered = filter_events_by_player(filtered, filters.get("player_name", "Todos"))
    return filtered.copy(), filtered.head(max(1, int(event_limit))).copy()


def _save_match_selection(field: str, widget_key: str) -> None:
    """Copia a seleção de um widget para um estado que não pertence à página."""
    selection = dict(st.session_state.get("match_selection", {}))
    selection[field] = int(st.session_state[widget_key])
    st.session_state["match_selection"] = selection


def render_filters(competitions: pd.DataFrame, page_key: str):
    """Renderiza seleção StatsBomb e formulário persistente de filtros."""
    st.sidebar.header("Filtros")
    page_changed = st.session_state.get("active_filter_page") != page_key
    st.session_state["active_filter_page"] = page_key
    st.session_state["restore_filter_widgets"] = page_key if page_changed else st.session_state.get("restore_filter_widgets")
    competition_ids = competitions["competition_id"].astype(int).drop_duplicates().tolist()
    competition_lookup = competitions.drop_duplicates("competition_id").set_index("competition_id")
    selection = st.session_state.setdefault("match_selection", {})
    competition_widget = f"{page_key}_competition_id_input"
    season_widget = f"{page_key}_season_id_input"
    match_widget = f"{page_key}_match_id_input"
    previous_competition_id = st.session_state.get("active_competition_id")
    competition_id = int(selection.get("competition_id", competition_ids[0]))
    if competition_id not in competition_ids:
        competition_id = competition_ids[0]
    if page_changed or competition_widget not in st.session_state:
        st.session_state[competition_widget] = competition_id
    competition_id = st.sidebar.selectbox(
        "Campeonato",
        competition_ids,
        format_func=lambda value: f"{competition_lookup.loc[value, 'competition_name']} ({competition_lookup.loc[value, 'country_name']})",
        key=competition_widget,
        on_change=_save_match_selection,
        args=("competition_id", competition_widget),
    )
    selection["competition_id"] = int(competition_id)
    st.session_state["match_selection"] = selection
    competition_changed = previous_competition_id is not None and int(previous_competition_id) != int(competition_id)
    st.session_state["active_competition_id"] = int(competition_id)
    seasons = get_seasons(int(competition_id))
    if seasons.empty:
        st.sidebar.warning("Não há temporadas disponíveis para este campeonato.")
        return None, None, None
    season_ids = seasons["season_id"].astype(int).tolist()
    season_lookup = seasons.set_index("season_id")["season_name"]
    previous_season_id = st.session_state.get("active_season_id")
    season_id = int(selection.get("season_id", season_ids[0]))
    if season_id not in season_ids:
        season_id = season_ids[0]
    if page_changed or competition_changed or season_widget not in st.session_state:
        st.session_state[season_widget] = season_id
    season_id = st.sidebar.selectbox(
        "Temporada",
        season_ids,
        format_func=lambda value: season_lookup.loc[value],
        key=season_widget,
        on_change=_save_match_selection,
        args=("season_id", season_widget),
    )
    selection["season_id"] = int(season_id)
    st.session_state["match_selection"] = selection
    season_changed = competition_changed or (previous_season_id is not None and int(previous_season_id) != int(season_id))
    st.session_state["active_season_id"] = int(season_id)
    matches = get_matches(int(competition_id), int(season_id))
    if matches.empty:
        st.sidebar.warning("Não há partidas disponíveis para esta temporada.")
        return None, None, None
    match_lookup = matches.set_index("match_id")
    match_ids = matches["match_id"].astype(int).tolist()
    match_id = int(selection.get("match_id", match_ids[0]))
    if match_id not in match_ids:
        match_id = match_ids[0]
    if page_changed or season_changed or match_widget not in st.session_state:
        st.session_state[match_widget] = match_id
    match_id = st.sidebar.selectbox(
        "Partida",
        match_ids,
        format_func=lambda value: f"{match_lookup.loc[value, 'home_team']} x {match_lookup.loc[value, 'away_team']} — {match_lookup.loc[value, 'match_date']}",
        key=match_widget,
        on_change=_save_match_selection,
        args=("match_id", match_widget),
    )
    selection["match_id"] = int(match_id)
    st.session_state["match_selection"] = selection
    return competition_lookup.loc[competition_id], season_lookup.loc[season_id], match_lookup.loc[match_id]


def render_event_filter_form(events: pd.DataFrame, page_key: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Renderiza filtros StatsBomb e devolve recorte analítico e amostra visível."""
    players = ["Todos", *load_players(events)]
    types = sorted(events["event_type"].dropna().unique().tolist())
    teams = ["Todos", *dict.fromkeys(events["team_name"].dropna().tolist())]
    minute_min = int(events["minute"].min()) if not events.empty else 0
    minute_max = int(events["minute"].max()) if not events.empty else 0
    event_max = max(1, len(events))
    event_min = min(10, event_max)
    match_id = str(events["match_id"].iloc[0]) if not events.empty else ""
    defaults = {
        "text_query": "",
        "minute_start": minute_min,
        "minute_end": minute_max,
        "player_name": "Todos",
        "selected_types": types,
        "team_name": "Todos",
        "event_limit": min(100, event_max),
        "include_coordinates": False,
        "match_id": match_id,
    }
    applied = st.session_state.get("applied_event_filters", defaults)
    new_match = applied.get("match_id") != match_id
    if new_match:
        applied = defaults
        st.session_state["applied_event_filters"] = applied

    widget_values = {
        f"{page_key}_event_text_query": applied["text_query"],
        f"{page_key}_minute_start": applied["minute_start"],
        f"{page_key}_minute_end": applied["minute_end"],
        f"{page_key}_selected_player": applied["player_name"],
        f"{page_key}_selected_event_types": applied["selected_types"],
        f"{page_key}_selected_team": applied["team_name"],
        f"{page_key}_event_limit": applied["event_limit"],
        f"{page_key}_include_coordinates": applied["include_coordinates"],
    }
    restore_page = st.session_state.get("restore_filter_widgets") == page_key
    for key, value in widget_values.items():
        if new_match or restore_page or key not in st.session_state:
            st.session_state[key] = value

    # Valores persistidos podem não existir na partida recém-selecionada.
    keys = {name: f"{page_key}_{name}" for name in ("selected_player", "selected_event_types", "selected_team", "minute_start", "minute_end", "event_limit")}
    st.session_state[keys["selected_player"]] = st.session_state[keys["selected_player"]] if st.session_state[keys["selected_player"]] in players else "Todos"
    st.session_state[keys["selected_event_types"]] = [value for value in st.session_state[keys["selected_event_types"]] if value in types]
    st.session_state[keys["selected_team"]] = st.session_state[keys["selected_team"]] if st.session_state[keys["selected_team"]] in teams else "Todos"
    st.session_state[keys["minute_start"]] = max(minute_min, min(int(st.session_state[keys["minute_start"]]), minute_max))
    st.session_state[keys["minute_end"]] = max(minute_min, min(int(st.session_state[keys["minute_end"]]), minute_max))
    st.session_state[keys["event_limit"]] = max(event_min, min(int(st.session_state[keys["event_limit"]]), event_max))
    with st.sidebar.form(f"{page_key}_event_filters"):
        text_query = st.text_input("Buscar jogador, equipe ou evento", key=f"{page_key}_event_text_query")
        start = st.number_input("Minuto inicial", min_value=minute_min, max_value=minute_max, value=minute_min, key=f"{page_key}_minute_start")
        end = st.number_input("Minuto final", min_value=minute_min, max_value=minute_max, value=minute_max, key=f"{page_key}_minute_end")
        player = st.selectbox("Jogador", players, key=f"{page_key}_selected_player")
        selected_types = st.multiselect("Tipos de evento", types, default=types, key=f"{page_key}_selected_event_types")
        team = st.radio("Equipe nos mapas", teams, key=f"{page_key}_selected_team")
        limit = st.slider("Quantidade de eventos exibidos", event_min, event_max, min(100, event_max), key=f"{page_key}_event_limit")
        coordinates = st.checkbox("Exibir coordenadas na tabela", key=f"{page_key}_include_coordinates")
        submitted = st.form_submit_button("Aplicar filtros")
    if submitted:
        st.session_state["applied_event_filters"] = {"text_query": text_query, "minute_start": start, "minute_end": end, "player_name": player, "selected_types": selected_types, "team_name": team, "event_limit": limit, "include_coordinates": coordinates, "match_id": match_id}
    filters = st.session_state.get("applied_event_filters", defaults)
    if restore_page:
        st.session_state["restore_filter_widgets"] = None
    return (*split_event_sets(events, filters, int(filters.get("event_limit", event_max))), filters)
