from __future__ import annotations

import pandas as pd
import streamlit as st


def format_match_metadata(match_info: dict) -> str:
    if not match_info:
        return "Partida indisponível"
    home = match_info.get("home_team") or "Casa"
    away = match_info.get("away_team") or "Fora"
    match_date = match_info.get("match_date") or "Data indisponível"
    return f"{home} x {away} • {match_date}"


def download_csv_button(filtered_df: pd.DataFrame):
    if filtered_df.empty:
        return
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Baixar CSV",
        data=csv,
        file_name="eventos_filtrados.csv",
        mime="text/csv",
    )
