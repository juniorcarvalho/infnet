from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Dashboard de Futebol - StatsBomb", layout="wide")


def main() -> None:
    navigation = st.navigation([
        st.Page("pages/1_Analise_da_partida.py", title="Análise da partida", icon="⚽", default=True),
        st.Page("pages/2_Comparacao_de_jogadores.py", title="Comparação de jogadores", icon="👥"),
    ])
    navigation.run()


if __name__ == "__main__":
    main()
