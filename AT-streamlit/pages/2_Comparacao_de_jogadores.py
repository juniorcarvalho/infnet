import streamlit as st

from views.player_comparison import render_player_comparison
from views.shared import get_competitions, get_events, render_event_filter_form, render_filters

st.caption("Os filtros persistem entre as páginas.")
competitions = get_competitions()
competition, season, match = render_filters(competitions, "comparison")
if match is not None:
    with st.spinner("Carregando eventos da partida..."):
        events = get_events(int(match.name))
    filtered, _display, _filters = render_event_filter_form(events, "comparison")
    render_player_comparison(filtered)
