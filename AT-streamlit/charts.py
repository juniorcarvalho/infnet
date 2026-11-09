from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from mplsoccer import Pitch


def _team_events(events_df: pd.DataFrame, team: str) -> pd.DataFrame:
    return events_df.loc[events_df["team_name"].eq(team)].copy() if team else events_df.copy()


def _pitch_figure(title: str):
    pitch = Pitch(pitch_color="#f7f7f7", line_color="#1f2937", goal_type="line")
    fig, ax = pitch.draw(figsize=(10, 6))
    ax.set_title(title, fontsize=14, pad=12)
    return pitch, fig, ax


def event_counts(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=["event_type", "count"])
    return events_df["event_type"].value_counts().rename_axis("event_type").reset_index(name="count")


def events_per_minute(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=["minute", "events"])
    return events_df.groupby("minute").size().rename("events").reset_index().sort_values("minute")


def plot_pass_map(events_df: pd.DataFrame, team: str = ""):
    pitch, fig, ax = _pitch_figure(f"Mapa de passes — {team or 'todos os times'}")
    passes = _team_events(events_df, team).query("event_type == 'Pass'").dropna(subset=["x", "y", "end_x", "end_y"])
    if passes.empty:
        ax.text(60, 40, "Sem passes para os filtros selecionados", ha="center", va="center")
        return fig
    completed = passes["outcome"].eq("Complete")
    for success, color, label in ((True, "#16a34a", "Completo"), (False, "#dc2626", "Incompleto")):
        subset = passes.loc[completed.eq(success)]
        pitch.arrows(subset["x"], subset["y"], subset["end_x"], subset["end_y"], ax=ax, color=color, width=1.2, headwidth=4, alpha=.7, label=label)
    ax.legend(loc="upper left")
    return fig


def plot_shot_map(events_df: pd.DataFrame, team: str = ""):
    pitch, fig, ax = _pitch_figure(f"Mapa de finalizações — {team or 'todos os times'}")
    shots = _team_events(events_df, team).query("event_type == 'Shot'").dropna(subset=["x", "y"])
    if shots.empty:
        ax.text(60, 40, "Sem finalizações para os filtros selecionados", ha="center", va="center")
        return fig
    colors = shots["outcome"].eq("Goal").map({True: "#16a34a", False: "#f59e0b"})
    sizes = shots["shot_xg"].fillna(0).clip(lower=.03).mul(900)
    pitch.scatter(shots["x"], shots["y"], s=sizes, c=colors, edgecolors="#111827", alpha=.8, ax=ax)
    ax.legend(handles=[Line2D([0], [0], marker="o", color="w", label="Gol", markerfacecolor="#16a34a", markersize=9), Line2D([0], [0], marker="o", color="w", label="Não convertido", markerfacecolor="#f59e0b", markersize=9)], loc="upper left")
    return fig


def plot_event_distribution(events_df: pd.DataFrame):
    counts = events_df["event_type"].value_counts().head(10)
    if counts.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(x=counts.values, y=counts.index, hue=counts.index, palette="viridis", legend=False, ax=ax)
    ax.set(title="Distribuição dos eventos", xlabel="Quantidade", ylabel="Evento")
    fig.tight_layout()
    return fig


def plot_passes_vs_goals(events_df: pd.DataFrame):
    if events_df.empty:
        return None
    grouped = events_df.groupby("team_name").agg(passes=("event_type", lambda values: values.eq("Pass").sum()), goals=("outcome", lambda values: values.eq("Goal").sum())).reset_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.scatterplot(data=grouped, x="passes", y="goals", hue="team_name", s=160, ax=ax)
    for row in grouped.itertuples():
        ax.annotate(row.team_name, (row.passes, row.goals), xytext=(5, 5), textcoords="offset points")
    ax.set(title="Passes e gols por equipe", xlabel="Passes", ylabel="Gols")
    fig.tight_layout()
    return fig


def plot_player_comparison(events_df: pd.DataFrame):
    data = events_df.loc[events_df["event_type"].eq("Pass")].groupby("player_name").size().sort_values(ascending=False).head(10)
    if data.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(x=data.values, y=data.index, hue=data.index, palette="Set2", legend=False, ax=ax)
    ax.set(title="Jogadores com mais passes", xlabel="Passes", ylabel="Jogador")
    fig.tight_layout()
    return fig


def build_subplots_for_match_statistics(events_df: pd.DataFrame):
    if events_df.empty:
        return None
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    teams = events_df.groupby("team_name").size().sort_values(ascending=False)
    sns.barplot(x=teams.values, y=teams.index, hue=teams.index, palette="Blues_d", legend=False, ax=axes[0])
    axes[0].set(title="Eventos por equipe", xlabel="Eventos", ylabel="Equipe")
    per_minute = events_df.groupby("minute").size()
    axes[1].plot(per_minute.index, per_minute.values, color="#2563eb")
    axes[1].set(title="Eventos por minuto", xlabel="Minuto", ylabel="Eventos")
    fig.tight_layout()
    return fig
