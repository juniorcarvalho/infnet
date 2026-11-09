import streamlit as st

from views.dashboard import render_dashboard
from views.shared import get_competitions, get_events, render_event_filter_form, render_filters

competitions = get_competitions()
competition, season, match = render_filters(competitions, "analysis")
if match is not None:
    with st.spinner("Carregando eventos da partida..."):
        events = get_events(int(match.name))
    progress = st.progress(30, text="Processando eventos...")
    progress.progress(100, text="Eventos prontos.")
    progress.empty()
    filtered, display, filters = render_event_filter_form(events, "analysis")
    render_dashboard(filtered, display, match, competition, season, filters)
