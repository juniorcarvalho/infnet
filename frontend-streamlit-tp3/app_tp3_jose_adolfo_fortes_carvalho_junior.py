# Diária média, gasto médio e permanência média por dia do visitante hospedado em hotéis 
# do Município do Rio de Janeiro entre 1997-2002)

from __future__ import annotations

import io
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


FILE_TYPES = ["xls", "xlsx"]
MONTHS = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


@st.cache_data(show_spinner=False)
def load_tourism_data(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    source = io.BytesIO(file_bytes)
    source.name = file_name

    try:
        raw = pd.read_excel(source, sheet_name="T 468", header=None)
    except Exception as exc: 
        raise ValueError(f"Arquivo inválido ou corrompido: {exc}") from exc

    rows = []
    for _, row in raw.iterrows():
        value_row = row.tolist()
        if len(value_row) < 4:
            continue

        label = value_row[0]
        if pd.isna(label):
            continue

        label_str = str(label).strip()
        if not label_str or label_str.startswith("Tabela") or label_str.startswith("Fonte"):
            continue

        if label_str in {"Período", "Média", "Nota:", "Armazém de Dados"}:
            continue

        if label_str.startswith("Nota") or label_str.startswith("Fonte"):
            continue

        try:
            period = label_str
            year = None
            if "Média" in label_str:
                year = int(label_str.split()[-1])
                period_type = "Média anual"
                month_name = None
            elif label_str in MONTHS:
                month_name = label_str
                period_type = "Mês"
                year = None
            else:
                continue

            if year is None:
                year = 0

            diaria = _clean_numeric(value_row[1])
            gasto = _clean_numeric(value_row[2])
            permanencia = _clean_numeric(value_row[3])

            if pd.isna(diaria) and pd.isna(gasto) and pd.isna(permanencia):
                continue

            rows.append(
                {
                    "periodo": period,
                    "tipo_periodo": period_type,
                    "mes": month_name,
                    "ano": year,
                    "diaria_media": diaria,
                    "gasto_medio": gasto,
                    "permanencia_media": permanencia,
                }
            )
        except (TypeError, ValueError):
            continue

    if not rows:
        raise ValueError("Nenhum dado válido encontrado no arquivo enviado.")

    df = pd.DataFrame(rows)
    ordered = []
    current_year = None
    for _, row in df.iterrows():
        record = row.to_dict()
        if record["tipo_periodo"] == "Média anual":
            current_year = int(record["ano"])
            record["ano"] = current_year
            ordered.append(record)
        elif record["mes"] and current_year is not None:
            record["ano"] = current_year
            ordered.append(record)

    if not ordered:
        raise ValueError("Não foi possível extrair anos e meses do arquivo enviado.")

    clean_df = pd.DataFrame(ordered)
    clean_df = clean_df.sort_values(["ano", "mes"], na_position="last").reset_index(drop=True)
    return clean_df


def _clean_numeric(value):
    if pd.isna(value):
        return float("nan")
    if isinstance(value, str):
        cleaned = value.strip().replace(".", "").replace(",", ".").replace("-", "")
        if not cleaned:
            return float("nan")
        try:
            return float(cleaned)
        except ValueError:
            return float("nan")
    return float(value)


def initialize_session_state():
    defaults = {
        "uploaded_file_name": None,
        "metric": "diaria_media",
        "selected_years": [],
        "chart_color": "#4CC9F0",
        "sort_by": "ano",
        "analysis_type": "Todos os meses",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.selected_years:
        st.session_state.selected_years = []


def format_metric(value: float, metric_name: str) -> str:
    if metric_name in {"diaria_media", "gasto_medio"}:
        return f"R$ {value:,.2f}"
    if metric_name == "permanencia_media":
        return f"{value:,.2f} dias"
    return f"{value:,.2f}"


def get_metric_label(metric):
    labels = {
        "diaria_media": "Diária média",
        "gasto_medio": "Gasto médio",
        "permanencia_media": "Permanência média",
    }
    return labels.get(metric, metric)


def build_filtered_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    years = sorted(df["ano"].dropna().unique().tolist())
    if not st.session_state.selected_years:
        st.session_state.selected_years = years

    selected_years = [int(year) for year in st.session_state.selected_years]
    filtered = df[df["ano"].isin(selected_years)].copy()

    if st.session_state.analysis_type == "Somente médias anuais":
        filtered = filtered[filtered["tipo_periodo"] == "Média anual"].copy()
    elif st.session_state.analysis_type == "Todos os meses":
        filtered = filtered[filtered["mes"].notna() | (filtered["tipo_periodo"] == "Média anual")].copy()

    if st.session_state.sort_by == "ano":
        filtered = filtered.sort_values(["ano", "mes"], na_position="last")
    elif st.session_state.sort_by == "diaria_media":
        filtered = filtered.sort_values("diaria_media", ascending=False)
    elif st.session_state.sort_by == "gasto_medio":
        filtered = filtered.sort_values("gasto_medio", ascending=False)
    elif st.session_state.sort_by == "permanencia_media":
        filtered = filtered.sort_values("permanencia_media", ascending=False)

    return filtered.reset_index(drop=True)


def render_metrics(df: pd.DataFrame, metric_name: str):
    metric_col = df[metric_name].dropna()
    if metric_col.empty:
        st.warning("Não há dados para a seleção atual.")
        return

    columns = st.columns(5)
    stats = {
        "Registros": len(metric_col),
        "Média": metric_col.mean(),
        "Soma": metric_col.sum(),
        "Mínimo": metric_col.min(),
        "Máximo": metric_col.max(),
        "Desvio": metric_col.std(ddof=1) if len(metric_col) > 1 else 0.0,
    }

    values = list(stats.values())
    labels = ["Registros", "Média", "Soma", "Mínimo", "Máximo"]
    for col, label in zip(columns, labels):
        value = stats[label]
        if label in {"Média", "Soma", "Mínimo", "Máximo"}:
            col.metric(label, format_metric(value, metric_name))
        else:
            col.metric(label, f"{int(value):,}")

    cols = st.columns(2)
    cols[0].metric("Desvio padrão", format_metric(stats["Desvio"], metric_name))
    cols[1].metric("Ano(s) selecionados", f"{len(st.session_state.selected_years)}")


def render_charts(df: pd.DataFrame, metric_name: str):
    if df.empty:
        return

    year_summary = df.groupby("ano", as_index=False)[metric_name].mean()
    year_summary = year_summary.sort_values("ano")

    col1, col2 = st.columns(2)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(year_summary["ano"].astype(str), year_summary[metric_name], color=st.session_state.chart_color)
    ax.set_title(f"Comparativo anual — {get_metric_label(metric_name)}")
    ax.set_xlabel("Ano")
    ax.set_ylabel(get_metric_label(metric_name))
    plt.xticks(rotation=45)
    fig.tight_layout()
    col1.pyplot(fig)
    plt.close(fig)

    monthly = df[df["mes"].notna()].copy()
    if not monthly.empty:
        monthly["mes_ordem"] = month_order(monthly["mes"])
        monthly = monthly.sort_values(["ano", "mes_ordem"]).drop(columns=["mes_ordem"])
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        for ano, group in monthly.groupby("ano"):
            ax2.plot(group["mes"], group[metric_name], marker="o", label=str(ano))
        ax2.set_title(f"Evolução por mês — {get_metric_label(metric_name)}")
        ax2.set_xlabel("Mês")
        ax2.set_ylabel(get_metric_label(metric_name))
        ax2.legend(title="Ano", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.xticks(rotation=45)
        fig2.tight_layout()
        col2.pyplot(fig2)
        plt.close(fig2)

    fig3, ax3 = plt.subplots(figsize=(7, 4))
    if metric_name != "permanencia_media":
        ax3.hist(
            df[metric_name].dropna(),
            bins=12,
            color=st.session_state.chart_color,
            edgecolor="black",
        )
        ax3.set_title(f"Histograma — {get_metric_label(metric_name)}")
        ax3.set_xlabel(get_metric_label(metric_name))
        ax3.set_ylabel("Frequência")
    else:
        df_plot = df[["diaria_media", "permanencia_media"]].dropna()
        ax3.scatter(
            df_plot["diaria_media"],
            df_plot["permanencia_media"],
            color=st.session_state.chart_color,
            alpha=0.7,
        )
        ax3.set_title("Correlação: diária x permanência")
        ax3.set_xlabel("Diária média")
        ax3.set_ylabel("Permanência média")
    fig3.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)


def month_order(series):
    month_mapping = {mes: idx for idx, mes in enumerate(MONTHS)}
    return series.map(month_mapping)


def export_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados Turísticos RJ")
    return output.getvalue()


def main():
    st.set_page_config(page_title="Turismo RJ", page_icon="🏨", layout="wide")
    initialize_session_state()

    st.title("Plataforma de Análise de Dados de Turismo - Rio de Janeiro")
    st.caption("Diária média, gasto médio e permanência média por dia do visitante hospedado em hotéis do Município do Rio de Janeiro entre 1997-2002")
    st.caption("TP3 - José Adolfo Fortes Carvalho Júnior")

    with st.sidebar:
        st.header("Controles")

        uploaded_file = st.file_uploader("Carregar arquivo XLS/XLSX", type=FILE_TYPES)
        if uploaded_file is None:
            st.info("Carregue o arquivo 468.xls para iniciar a análise.")
            st.stop()

        st.session_state.uploaded_file_name = uploaded_file.name
        st.info(f"Arquivo carregado: {uploaded_file.name}")
        file_bytes = uploaded_file.getvalue()
        progress = st.progress(0)
        progress.progress(20)

        with st.spinner("Processando dados..."):
            try:
                data = load_tourism_data(file_bytes, uploaded_file.name)
            except ValueError as exc:
                st.error(str(exc))
                st.stop()

        progress.progress(100)
        st.success("Dados carregados com sucesso.")

        st.subheader("Filtros")
        st.session_state.metric = st.radio(
            "Métrica principal",
            options=["diaria_media", "gasto_medio", "permanencia_media"],
            format_func=get_metric_label,
            index=["diaria_media", "gasto_medio", "permanencia_media"].index(st.session_state.metric),
        )

        available_years = sorted(data["ano"].dropna().unique().tolist())
        st.session_state.selected_years = st.multiselect(
            "Anos disponíveis",
            options=available_years,
            default=available_years if not st.session_state.selected_years else st.session_state.selected_years,
        )

        st.session_state.analysis_type = st.selectbox(
            "Tipo de análise",
            ["Todos os meses", "Somente médias anuais", "Dados completos"],
            index=["Todos os meses", "Somente médias anuais", "Dados completos"].index(st.session_state.analysis_type),
        )

        st.session_state.sort_by = st.selectbox(
            "Ordenação",
            ["ano", "diaria_media", "gasto_medio", "permanencia_media"],
            index=["ano", "diaria_media", "gasto_medio", "permanencia_media"].index(st.session_state.sort_by),
        )

        if st.button("Resetar filtros"):
            st.session_state.selected_years = []
            st.session_state.metric = "diaria_media"
            st.session_state.analysis_type = "Todos os meses"
            st.session_state.sort_by = "ano"
            st.rerun()

        st.session_state.chart_color = st.color_picker(
            "Cor dos gráficos",
            st.session_state.chart_color,
        )

    filtered_data = build_filtered_dataframe(data)

    if filtered_data.empty:
        st.warning("Nenhum dado atende aos filtros selecionados.")
        return

    st.subheader(f"Visualização: {get_metric_label(st.session_state.metric)}")
    render_metrics(filtered_data, st.session_state.metric)

    st.dataframe(
        filtered_data[["ano", "mes", "tipo_periodo", "diaria_media", "gasto_medio", "permanencia_media"]]
        .rename(
            columns={
                "ano": "Ano",
                "mes": "Mês",
                "tipo_periodo": "Tipo de período",
                "diaria_media": "Diária média",
                "gasto_medio": "Gasto médio",
                "permanencia_media": "Permanência média",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    render_charts(filtered_data, st.session_state.metric)

    st.subheader("Download dos dados")
    export_name = f"dados_turismo_RJ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    excel_bytes = export_excel(filtered_data)
    st.download_button(
        label="Baixar dados filtrados em Excel",
        data=excel_bytes,
        file_name=export_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    main()
