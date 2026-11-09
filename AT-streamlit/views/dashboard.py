from __future__ import annotations

import pandas as pd
import streamlit as st

from charts import (build_subplots_for_match_statistics, event_counts, events_per_minute, plot_event_distribution, plot_pass_map, plot_passes_vs_goals, plot_player_comparison, plot_shot_map)
from data_loader import build_match_summary
from utils import download_csv_button, format_match_metadata


def render_dashboard(filtered_events: pd.DataFrame, display_events: pd.DataFrame, match: pd.Series, competition: pd.Series, season_name: str, filters: dict) -> None:
    st.title("Análise da partida")
    st.caption("Indicadores e gráficos representam todos os eventos do recorte analítico; a tabela e download usam a amostra limitada.")
    st.subheader(format_match_metadata(match.to_dict()))
    st.caption(f"{competition['competition_name']} — temporada {season_name}")
    summary = build_match_summary(filtered_events)
    if filtered_events.empty:
        st.warning("Nenhum evento corresponde aos filtros analíticos selecionados.")
    metrics = st.columns(4)
    conversion = f"{summary['shot_conversion']:.1f}".rstrip("0").rstrip(".")
    metrics[0].metric("Gols", summary["total_goals"])
    metrics[1].metric("Finalizações", summary["total_shots"])
    metrics[2].metric("Passes completos", summary["successful_passes"], f"de {summary['total_passes']} passes")
    metrics[3].metric("Conversão", f"{conversion}%")
    summary_tab, charts_tab, data_tab = st.tabs(["Resumo", "Gráficos", "Dados"])
    with summary_tab:
        st.header("Leitura do recorte analítico")
        table = pd.DataFrame([summary]).rename(columns={"total_goals": "gols", "total_shots": "finalizações", "total_passes": "passes", "successful_passes": "passes completos", "shot_conversion": "conversão (%)", "event_count": "eventos"})
        st.table(table.style.format({"conversão (%)": "{:.1f}"}))
        st.markdown("### Taxa de conversão de finalizações em gol")
        st.latex(r"\text{Conversão} = \frac{\text{Gols}}{\text{Finalizações}} \times 100")
        with st.expander("Informações da partida"):
            st.write(f"Fase da competição: {match.get('competition_stage') or 'não informada'}")
            st.write(f"Data: {match.get('match_date') or 'não informada'}")
    with charts_tab:
        team = "" if filters.get("team_name", "Todos") == "Todos" else filters["team_name"]
        st.caption("Setas verdes/vermelhas indicam passes completos/incompletos. Nos mapas de finalização, verde indica gol e o tamanho do ponto é proporcional ao xG.")
        left, right = st.columns(2)
        with left:
            counts = event_counts(filtered_events).set_index("event_type")
            if counts.empty: st.caption("Sem eventos no recorte.")
            else: st.bar_chart(counts, y="count", height=260)
        with right:
            timeline = events_per_minute(filtered_events).set_index("minute")
            if timeline.empty: st.caption("Sem eventos no recorte.")
            else: st.line_chart(timeline, y="events", height=260)
        left, right = st.columns(2)
        with left: st.pyplot(plot_pass_map(filtered_events, team), use_container_width=True)
        with right: st.pyplot(plot_shot_map(filtered_events, team), use_container_width=True)
        for chart in (plot_event_distribution(filtered_events), plot_passes_vs_goals(filtered_events), plot_player_comparison(filtered_events), build_subplots_for_match_statistics(filtered_events)):
            if chart is not None: st.pyplot(chart, use_container_width=True)
    with data_tab:
        limited = len(display_events) < len(filtered_events)
        st.subheader("Amostra de eventos" if limited else "Eventos do recorte analítico")
        st.caption(f"Exibindo {len(display_events)} de {len(filtered_events)} eventos filtrados." if limited else "Tabela e download contêm todos os eventos filtrados.")
        columns = ["minute", "event_type", "team_name", "player_name", "outcome", "pass_length", "shot_xg"]
        if filters.get("include_coordinates"): columns += ["x", "y", "end_x", "end_y"]
        st.dataframe(display_events[columns], use_container_width=True, hide_index=True)
        download_csv_button(display_events)
