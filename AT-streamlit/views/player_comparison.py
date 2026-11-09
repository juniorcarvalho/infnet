from __future__ import annotations

import pandas as pd
import streamlit as st

from data_loader import load_players


def render_player_comparison(events_df: pd.DataFrame) -> None:
    st.title("Comparação de jogadores")
    st.write("Compare volume de passes, acerto e finalizações no recorte analítico atualmente aplicado.")
    players = load_players(events_df)
    if not players:
        st.info("Não há jogadores disponíveis para comparação.")
        return
    selected = st.multiselect("Jogadores", players, default=players[:2], max_selections=2, key="comparison_players")
    subset = events_df.loc[events_df["player_name"].isin(selected)]
    passes, shots = subset.loc[subset.event_type.eq("Pass")], subset.loc[subset.event_type.eq("Shot")]
    comparison = pd.DataFrame({"jogador": selected})
    comparison["passes"] = comparison.jogador.map(passes.groupby("player_name").size()).fillna(0).astype(int)
    comparison["passes completos"] = comparison.jogador.map(passes.loc[passes.outcome.eq("Complete")].groupby("player_name").size()).fillna(0).astype(int)
    comparison["finalizações"] = comparison.jogador.map(shots.groupby("player_name").size()).fillna(0).astype(int)
    comparison["gols"] = comparison.jogador.map(shots.loc[shots.outcome.eq("Goal")].groupby("player_name").size()).fillna(0).astype(int)
    comparison["acerto de passe (%)"] = comparison["passes completos"].div(comparison.passes).fillna(0).mul(100).round(1)
    st.dataframe(comparison, use_container_width=True, hide_index=True)
